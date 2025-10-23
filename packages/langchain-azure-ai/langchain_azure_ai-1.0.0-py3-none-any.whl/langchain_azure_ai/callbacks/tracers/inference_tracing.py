"""Azure AI inference tracing callback (clean implementation).

Emits OpenTelemetry spans for LangChain / LangGraph events (LLM, chain, tool,
retriever, agent). Includes:
    * Attribute normalization (skip None, JSON encode complex values)
    * Optional content recording & redaction
      (env AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED)
    * Legacy compatibility keys (gen_ai.prompt/system/completion) if enabled
    * Async subclass delegating to sync implementation (no logic duplication)

File fully deduplicated (legacy multi-implementation blocks removed).
"""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, LLMResult

from langchain_azure_ai._api.base import experimental

try:  # pragma: no cover
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace as otel_trace
    from opentelemetry.trace import (
        NonRecordingSpan,
        Span,
        SpanKind,
        Status,
        StatusCode,
        set_span_in_context,
    )
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "Install azure-monitor-opentelemetry and opentelemetry packages: "
        "pip install azure-monitor-opentelemetry"
    ) from e

logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(
    logging.WARNING
)


class Attrs:
    PROVIDER_NAME = "gen_ai.provider.name"
    OPERATION_NAME = "gen_ai.operation.name"
    REQUEST_MODEL = "gen_ai.request.model"
    REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
    REQUEST_TEMPERATURE = "gen_ai.request.temperature"
    REQUEST_TOP_P = "gen_ai.request.top_p"
    REQUEST_TOP_K = "gen_ai.request.top_k"
    REQUEST_STOP = "gen_ai.request.stop_sequences"
    REQUEST_FREQ_PENALTY = "gen_ai.request.frequency_penalty"
    REQUEST_PRES_PENALTY = "gen_ai.request.presence_penalty"
    REQUEST_CHOICE_COUNT = "gen_ai.request.choice.count"
    REQUEST_SEED = "gen_ai.request.seed"
    RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
    USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
    USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"  # TODO
    INPUT_MESSAGES = "gen_ai.input.messages"
    OUTPUT_MESSAGES = "gen_ai.output.messages"
    TOOL_NAME = "gen_ai.tool.name"
    TOOL_CALL_ARGS = "gen_ai.tool.call.arguments"
    TOOL_CALL_RESULT = "gen_ai.tool.call.result"
    DATA_SOURCE_ID = "gen_ai.data_source.id"
    AGENT_NAME = "gen_ai.agent.name"
    AGENT_DESCRIPTION = "gen_ai.agent.description"
    CONVERSATION_ID = "gen_ai.conversation.id"
    SERVER_ADDRESS = "server.address"
    SERVER_PORT = "server.port"
    ERROR_TYPE = "error.type"
    LEGACY_SYSTEM = "gen_ai.system"
    LEGACY_PROMPT = "gen_ai.prompt"
    LEGACY_COMPLETION = "gen_ai.completion"
    LEGACY_KEYS_FLAG = "metadata.legacy_keys"
    METADATA_RUN_ID = "metadata.run_id"
    METADATA_PARENT_RUN_ID = "metadata.parent_run_id"
    METADATA_TAGS = "metadata.tags"
    METADATA_THREAD_PATH = "metadata.langgraph.path"
    METADATA_STEP = "metadata.langgraph.step"
    METADATA_NODE = "metadata.langgraph.node"
    METADATA_TRIGGERS = "metadata.langgraph.triggers"
    SYSTEM_INSTRUCTIONS = "gen_ai.system_instructions"
    OUTPUT_TYPE = "gen_ai.output.type"
    TOOL_DEFINITIONS = "gen_ai.tool.definitions"
    TOOL_DESCRIPTION = "gen_ai.tool.description"
    TOOL_TYPE = "gen_ai.tool.type"
    TOOL_CALL_ID = "gen_ai.tool.call.id"
    RESPONSE_ID = "gen_ai.response.id"
    RESPONSE_MODEL = "gen_ai.response.model"
    REQUEST_ENCODING_FORMATS = "gen_ai.request.encoding_formats"
    EMBEDDINGS_DIM_COUNT = "gen_ai.embeddings.dimension.count"
    AGENT_ID = "gen_ai.agent.id"
    REQUEST_MAX_INPUT_TOKENS = "gen_ai.request.max_input_tokens"
    REQUEST_MAX_OUTPUT_TOKENS = "gen_ai.request.max_output_tokens"
    OPENAI_REQUEST_SERVICE_TIER = "openai.request.service_tier"
    OPENAI_RESPONSE_SERVICE_TIER = "openai.response.service_tier"
    OPENAI_RESPONSE_SYSTEM_FINGERPRINT = "openai.response.system_fingerprint"
    AZURE_RESOURCE_NAMESPACE = "azure.resource_provider.namespace"


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except Exception:  # pragma: no cover
        return '"<unserializable>"'


def _try_parse_json(s: Any) -> Any:
    """Best-effort parse a JSON string, otherwise return the original value."""
    if isinstance(s, (str, bytes)):
        try:
            return json.loads(s)
        except Exception:
            return s
    return s


def _msg_dict(msg: BaseMessage) -> Dict[str, Any]:
    d: Dict[str, Any] = {"type": msg.type, "content": msg.content}
    if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
        d["tool_calls"] = _safe_json(getattr(msg, "tool_calls"))
    if isinstance(msg, ToolMessage):
        tcid = getattr(msg, "tool_call_id", None)
        if tcid is not None:
            d["tool_call_id"] = str(tcid)
    return d


def _threads_json(
    threads: List[List[BaseMessage]],
) -> str:  # type: ignore[override]
    return _safe_json([[_msg_dict(m) for m in thread] for thread in threads])


def _extract_port(endpoint: Optional[str]) -> Optional[int]:
    """Extract a non-default port from an endpoint URL.

    Returns None if endpoint is None or if the port is default for the scheme
    (80 for http, 443 for https). If a non-default explicit port is present,
    returns that integer value.
    """
    if not endpoint:
        return None
    try:
        from urllib.parse import urlparse

        p = urlparse(endpoint)
        if not p.netloc:
            return None
        port = p.port
        if port is None:
            return None
        # Default ports: 80 for http, 443 for https
        if (p.scheme == "https" and port == 443) or (p.scheme == "http" and port == 80):
            return None
        return int(port)
    except Exception:  # pragma: no cover
        try:
            # Fallback parsing if urlparse failed; keep robust but conservative
            host_part = endpoint.split("//", 1)[-1].split("/", 1)[0]
            if ":" in host_part:
                cand = host_part.rsplit(":", 1)[-1]
                return int(cand) if cand.isdigit() else None
        except Exception:
            return None
        return None


def _get_model(serialized: Dict[str, Any]) -> Optional[str]:
    if not serialized:
        return None
    kw = serialized.get("kwargs", {})
    return kw.get("deployment_name") or kw.get("model") or kw.get("name")


def _extract_params(serialized: Dict[str, Any]) -> Dict[str, Any]:
    if not serialized:
        return {}
    kw = serialized.get("kwargs", {})
    keep = [
        "max_tokens",
        "temperature",
        "top_p",
        "top_k",
        "stop",
        "frequency_penalty",
        "presence_penalty",
        "n",
        "seed",
    ]
    return {k: kw[k] for k in keep if k in kw}


def _finish_reasons(gens: List[List[ChatGeneration]]) -> List[str]:
    reasons: List[str] = []
    for group in gens:
        for gen in group:
            info = getattr(gen, "generation_info", None) or {}
            if not isinstance(info, dict):
                continue
            fr = (
                info.get("finish_reason")
                or info.get("finishReason")
                or info.get("finish_reasons")
                or info.get("reason")
            )
            if fr is None:
                continue
            if isinstance(fr, list):
                reasons.extend([str(r) for r in fr if r is not None])
            else:
                reasons.append(str(fr))
    dedup: List[str] = []
    seen = set()
    for r in reasons:
        if r not in seen:
            dedup.append(r)
            seen.add(r)
    # Normalize provider variants to schema
    norm = ["tool_call" if r == "tool_calls" else r for r in dedup]
    return norm


def _normalize(v: Any) -> Any:  # returns json-safe primitive or None
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple)):
        if not v:
            return []
        if (
            all(isinstance(x, (str, int, float, bool)) for x in v)
            and len({type(x) for x in v}) == 1
        ):
            return list(v)
        return _safe_json(v)
    return _safe_json(v)


def _redact(messages_json: str) -> str:
    """Redact content while preserving original item structure where possible.

    - For thread-style lists (list of lists), output a list of lists of
      dicts preserving each item's "type" (defaulting to "text") and
      replacing content with "[REDACTED]".
    - For flat lists (e.g., system instructions or outputs), output a list of
      dicts with {"type": <orig or "text">, "content": "[REDACTED]"}.
    - Falls back gracefully on errors.
    """
    try:
        parsed = json.loads(messages_json)
        if isinstance(parsed, list):
            # Nested threads: [[{...}, ...], ...]
            if parsed and isinstance(parsed[0], list):
                red_threads: List[List[Dict[str, Any]]] = []
                for thread in parsed:
                    if isinstance(thread, list):
                        red_thread: List[Dict[str, Any]] = []
                        for item in thread:
                            if isinstance(item, dict):
                                red_thread.append(
                                    {
                                        "type": item.get("type", "text"),
                                        "content": "[REDACTED]",
                                    }
                                )
                            elif isinstance(item, str):
                                red_thread.append(
                                    {"type": "text", "content": "[REDACTED]"}
                                )
                        red_threads.append(red_thread)
                    else:
                        # Preserve unknown shapes
                        red_threads.append([{"type": "text", "content": "[REDACTED]"}])
                return _safe_json(red_threads)
            # Flat list of items: system instructions, outputs, etc.
            red_items: List[Dict[str, Any]] = []
            for item in parsed:
                if isinstance(item, dict):
                    red_items.append(
                        {
                            "type": item.get("type", "text"),
                            "content": "[REDACTED]",
                        }
                    )
                elif isinstance(item, str):
                    red_items.append({"type": "text", "content": "[REDACTED]"})
            return _safe_json(red_items)
    except Exception:
        return '[{"type":"text","content":"[REDACTED]"}]'
    return messages_json


def _message_role(msg: BaseMessage) -> str:
    if isinstance(msg, HumanMessage):
        return "user"
    if isinstance(msg, AIMessage):
        return "assistant"
    if isinstance(msg, ToolMessage):
        return "tool"
    return getattr(msg, "type", "user") or "user"


def _message_to_role_parts(msg: BaseMessage) -> Dict[str, Any]:
    role = _message_role(msg)
    parts: List[Dict[str, Any]] = []
    # Assistant message: include text and any tool_call requests
    if isinstance(msg, AIMessage):
        content = getattr(msg, "content", None)
        if isinstance(content, str) and content:
            parts.append({"type": "text", "content": content})
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    tc_id = tc.get("id")
                    func = tc.get("function") or {}
                    name = func.get("name") or tc.get("name")
                    args = func.get("arguments") if isinstance(func, dict) else None
                    parts.append(
                        {
                            "type": "tool_call",
                            "id": tc_id,
                            "name": name,
                            "arguments": _try_parse_json(
                                args if args is not None else tc.get("arguments")
                            ),
                        }
                    )
                else:
                    tc_id = getattr(tc, "id", None)
                    name = getattr(tc, "name", None)
                    args = getattr(tc, "args", None) or getattr(tc, "arguments", None)
                    parts.append(
                        {
                            "type": "tool_call",
                            "id": str(tc_id) if tc_id is not None else None,
                            "name": name,
                            "arguments": _try_parse_json(args),
                        }
                    )
        return {
            "role": role,
            "parts": parts or [{"type": "text", "content": ""}],
            "finish_reason": "stop",
        }
    # Tool message: represent as tool_call_response
    if isinstance(msg, ToolMessage):
        tcid = getattr(msg, "tool_call_id", None)
        content = getattr(msg, "content", None)
        parts.append(
            {
                "type": "tool_call_response",
                "id": str(tcid) if tcid is not None else None,
                "response": _try_parse_json(content),
            }
        )
        return {"role": role, "parts": parts, "finish_reason": "stop"}
    # Human or other -> text part
    content = getattr(msg, "content", None)
    if isinstance(content, str) and content:
        parts.append({"type": "text", "content": content})
    return {
        "role": role,
        "parts": parts or [{"type": "text", "content": ""}],
        "finish_reason": "stop",
    }


def _redact_role_parts_messages(
    msgs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    red: List[Dict[str, Any]] = []
    for m in msgs or []:
        parts: List[Dict[str, Any]] = []
        for p in m.get("parts", []) or []:
            ptype = p.get("type")
            if ptype == "text":
                parts.append({"type": "text", "content": "[REDACTED]"})
            elif ptype == "tool_call":
                parts.append(
                    {
                        "type": "tool_call",
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "arguments": "[REDACTED]",
                    }
                )
            elif ptype == "tool_call_response":
                parts.append(
                    {
                        "type": "tool_call_response",
                        "id": p.get("id"),
                        "response": "[REDACTED]",
                    }
                )
            else:
                parts.append({"type": ptype, "content": "[REDACTED]"})
        red.append(
            {
                "role": m.get("role", "assistant"),
                "parts": parts,
                "finish_reason": m.get("finish_reason", "stop"),
            }
        )
    return red


@dataclass
class _Run:
    span: Span
    operation: str
    model: Optional[str]
    response_id: Optional[str] = None


class _Core:
    def __init__(
        self,
        *,
        enable_content_recording: bool,
        redact: bool,
        include_legacy: bool,
        provider: str,
        tracer: Any,
        default_name: Optional[str] = None,
        default_id: Optional[str] = None,
        debug_export: bool = False,
    ) -> None:
        self.enable_content_recording = enable_content_recording
        self.redact = redact
        self.include_legacy = include_legacy
        self.provider = provider
        self._tracer = tracer
        self._runs: Dict[UUID, _Run] = {}
        self._finished_span_contexts: Dict[UUID, Any] = {}
        self._finished_context_order: deque[UUID] = deque()
        self._context_cache_limit = 256
        self._executed_tool_call_ids: Set[str] = set()
        # Optional defaults for generic attributes requested by callers
        self._default_name = default_name
        self._default_id = default_id
        # Debug/console export of span lifecycle
        self._debug = False
        self._debug_log: List[str] = []

    def start(
        self,
        *,
        run_id: UUID,
        name: str,
        kind: SpanKind,
        operation: str,
        parent_run_id: Optional[UUID],
        attrs: Dict[str, Any],
    ) -> None:
        # console debug disabled
        parent_ctx = None
        if parent_run_id:
            parent_state = self._runs.get(parent_run_id)
            if parent_state is not None:
                parent_ctx = set_span_in_context(parent_state.span)
            else:
                finished_ctx = self._finished_span_contexts.get(parent_run_id)
                if finished_ctx is not None:
                    parent_ctx = set_span_in_context(NonRecordingSpan(finished_ctx))
        span = self._tracer.start_span(name=name, kind=kind, context=parent_ctx)
        for k, v in attrs.items():
            nv = _normalize(v)
            if nv is not None:
                span.set_attribute(k, nv)
        # Ensure agent identity fields are present and mirrored
        try:
            # Determine values from attrs or defaults
            _nm = (
                attrs.get(Attrs.AGENT_NAME)
                or attrs.get(Attrs.TOOL_NAME)
                or self._default_name
            )
            _idv = (
                attrs.get(Attrs.AGENT_ID)
                or attrs.get(Attrs.TOOL_CALL_ID)
                or self._default_id
            )
            # Ensure gen_ai.agent.* are set when missing
            if _nm is not None and attrs.get(Attrs.AGENT_NAME) is None:
                span.set_attribute(Attrs.AGENT_NAME, _nm)
            if _idv is not None and attrs.get(Attrs.AGENT_ID) is None:
                span.set_attribute(Attrs.AGENT_ID, _idv)
            # Do not set generic convenience keys (name/id).
            # Rely on gen_ai.agent.*
        except Exception:
            pass
        self._runs[run_id] = _Run(
            span=span,
            operation=operation,
            model=attrs.get(Attrs.REQUEST_MODEL),
            response_id=None,
        )

    def end(self, run_id: UUID, error: Optional[BaseException]) -> None:
        state = self._runs.pop(run_id, None)
        if not state:
            return
        # console debug disabled
        try:
            ctx = state.span.get_span_context()
            if ctx is not None and getattr(ctx, "is_valid", False):
                self._finished_span_contexts[run_id] = ctx
                self._finished_context_order.append(run_id)
                if len(self._finished_context_order) > self._context_cache_limit:
                    old = self._finished_context_order.popleft()
                    self._finished_span_contexts.pop(old, None)
        except Exception:
            pass
        if error:
            state.span.set_status(Status(StatusCode.ERROR, str(error)))
            state.span.set_attribute(Attrs.ERROR_TYPE, error.__class__.__name__)
            state.span.record_exception(error)
        state.span.end()

    def set(self, run_id: UUID, attrs: Dict[str, Any]) -> None:
        state = self._runs.get(run_id)
        if not state:
            return
        # console debug disabled
        for k, v in attrs.items():
            nv = _normalize(v)
            if nv is not None:
                state.span.set_attribute(k, nv)
        # Track response id if provided
        try:
            rid = attrs.get(Attrs.RESPONSE_ID)
            if rid is not None:
                state.response_id = str(rid)
        except Exception:
            pass

    def redact_messages(self, messages_json: str) -> Optional[str]:
        # Opt-in: if recording disabled, omit (return None)
        if not self.enable_content_recording:
            return None
        if self.redact:
            return _redact(messages_json)
        return messages_json

    def enrich_langgraph(
        self, attrs: Dict[str, Any], metadata: Optional[Dict[str, Any]]
    ) -> None:
        if not metadata:
            return
        mapping = {
            "langgraph_step": Attrs.METADATA_STEP,
            "langgraph_node": Attrs.METADATA_NODE,
            "langgraph_triggers": Attrs.METADATA_TRIGGERS,
            "langgraph_path": Attrs.METADATA_THREAD_PATH,
            "thread_id": Attrs.CONVERSATION_ID,
            "session_id": Attrs.CONVERSATION_ID,
        }
        for src, dst in mapping.items():
            if src in metadata:
                nv = _normalize(metadata[src])
                if nv is not None:
                    attrs[dst] = nv

    def llm_start_attrs(
        self,
        *,
        serialized: Dict[str, Any],
        run_id: UUID,
        parent_run_id: Optional[UUID],
        tags: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        messages_json: str,
        model: Optional[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        a: Dict[str, Any] = {
            Attrs.PROVIDER_NAME: self.provider,
            Attrs.OPERATION_NAME: "chat",
            Attrs.REQUEST_MODEL: model,
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        endpoint = None
        if serialized:
            kw = serialized.get("kwargs", {}) or {}
            endpoint = (
                kw.get("azure_endpoint")
                or kw.get("base_url")
                or kw.get("api_base")
                or kw.get("endpoint")
            )
        if endpoint:
            a[Attrs.SERVER_ADDRESS] = endpoint
            port = _extract_port(endpoint)
            if port is not None:
                a[Attrs.SERVER_PORT] = port
        # Provider override per backend
        try:
            prov = a.get(Attrs.PROVIDER_NAME)
            ep_l = (endpoint or "").lower()
            if ep_l:
                if (
                    "openai.azure.com" in ep_l
                    or "inference.ai.azure.com" in ep_l
                    or "azure.com" in ep_l
                ):
                    prov = "azure.ai.inference"
                elif "openai.com" in ep_l:
                    prov = "openai"
            elif serialized:
                kw2 = serialized.get("kwargs", {}) or {}
                if kw2.get("azure_endpoint"):
                    prov = "azure.ai.inference"
            if prov:
                a[Attrs.PROVIDER_NAME] = prov
        except Exception:
            pass
        if tags:
            a[Attrs.METADATA_TAGS] = _safe_json(tags)
        self.enrich_langgraph(a, metadata)
        param_map = {
            "max_tokens": Attrs.REQUEST_MAX_TOKENS,
            "temperature": Attrs.REQUEST_TEMPERATURE,
            "top_p": Attrs.REQUEST_TOP_P,
            "top_k": Attrs.REQUEST_TOP_K,
            "stop": Attrs.REQUEST_STOP,
            "frequency_penalty": Attrs.REQUEST_FREQ_PENALTY,
            "presence_penalty": Attrs.REQUEST_PRES_PENALTY,
            "n": Attrs.REQUEST_CHOICE_COUNT,
            "seed": Attrs.REQUEST_SEED,
        }
        for k, v in params.items():
            if k == "n":
                # Only set choice.count when != 1 per spec
                if v is not None and v != 1:
                    a[Attrs.REQUEST_CHOICE_COUNT] = v
                continue
            mapped = param_map.get(k)
            if mapped:
                a[mapped] = v
            if k == "max_input_tokens":
                a[Attrs.REQUEST_MAX_INPUT_TOKENS] = v
            if k == "max_output_tokens":
                a[Attrs.REQUEST_MAX_OUTPUT_TOKENS] = v
        # output.type (conditionally) from response_format / output_format
        rf = (
            (serialized or {}).get("kwargs", {}).get("response_format")
            if serialized
            else None
        )
        if rf and isinstance(rf, dict):
            t = rf.get("type") or rf.get("format")
            if t:
                a[Attrs.OUTPUT_TYPE] = t
        of = (
            (serialized or {}).get("kwargs", {}).get("output_format")
            if serialized
            else None
        )
        if of and isinstance(of, str):
            a[Attrs.OUTPUT_TYPE] = of
        # system instructions (opt-in)
        sys_inst = None
        if serialized:
            kw = serialized.get("kwargs", {}) or {}
            sys_inst = (
                kw.get("system") or kw.get("system_message") or kw.get("instructions")
            )
        # Fallback: allow application to pass via metadata
        if sys_inst is None and metadata:
            sys_inst = metadata.get("system") or metadata.get("system_instructions")
        if sys_inst is not None and self.enable_content_recording:
            a[Attrs.SYSTEM_INSTRUCTIONS] = (
                self.redact_messages(_safe_json(sys_inst)) or None
            )
        # tool definitions (opt-in, prioritized for richer telemetry)
        if serialized:
            tools_def = (serialized.get("kwargs", {}) or {}).get("tools")
            if tools_def:
                a[Attrs.TOOL_DEFINITIONS] = _safe_json(tools_def)
        # Normalize input messages into role/parts threads,
        # then redact (if enabled)
        try:
            parsed = json.loads(messages_json)
        except Exception:
            parsed = []
        # parsed is a List[List[BaseMessage-like dicts]]; coerce to role/parts
        role_parts_threads = []
        for thread in parsed or []:
            if isinstance(thread, list):
                rp_thread = []
                for m in thread or []:
                    if isinstance(m, dict):
                        role = m.get("type")
                        content = m.get("content")
                        parts = []
                        if isinstance(content, str) and content:
                            parts.append({"type": "text", "content": content})
                        rp_thread.append(
                            {
                                "role": (
                                    "assistant"
                                    if role == "ai"
                                    else ("tool" if role == "tool" else "user")
                                ),
                                "parts": parts or [{"type": "text", "content": ""}],
                            }
                        )
                role_parts_threads.append(rp_thread)
        input_msgs = (
            self.redact_messages(_safe_json(role_parts_threads))
            if role_parts_threads
            else None
        )
        if input_msgs is not None:
            a[Attrs.INPUT_MESSAGES] = input_msgs
        agent_name = None
        if metadata:
            agent_name = metadata.get("agent_name") or metadata.get("agent_type")
        if not agent_name and tags:
            for t in tags:
                if t.startswith("agent:"):
                    agent_name = t.split(":", 1)[1]
                    break
        if agent_name:
            a[Attrs.AGENT_NAME] = agent_name
        if self.include_legacy and a.get(Attrs.INPUT_MESSAGES) is not None:
            a[Attrs.LEGACY_PROMPT] = a[Attrs.INPUT_MESSAGES]
            a[Attrs.LEGACY_SYSTEM] = self.provider or "langgraph"
            a[Attrs.LEGACY_KEYS_FLAG] = True
        return a

    def llm_end_attrs(self, result: LLMResult) -> Dict[str, Any]:
        gens: List[List[ChatGeneration]] = getattr(result, "generations", [])
        finish = _finish_reasons(gens)
        # Convert generations to role/parts messages and redact if enabled
        role_parts = _generations_to_role_parts(gens)
        out: Dict[str, Any] = {Attrs.RESPONSE_FINISH_REASONS: finish or None}
        output_json = (
            self.redact_messages(_safe_json(role_parts)) if role_parts else None
        )
        if output_json is not None:
            out[Attrs.OUTPUT_MESSAGES] = output_json
            if self.include_legacy:
                out[Attrs.LEGACY_COMPLETION] = output_json
        llm_output = getattr(result, "llm_output", {}) or {}
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        if usage:
            in_tok = (
                usage.get("prompt_tokens")
                or usage.get("input_tokens")
                or usage.get("promptTokens")
            )
            out_tok = (
                usage.get("completion_tokens")
                or usage.get("output_tokens")
                or usage.get("completionTokens")
            )
            if in_tok is not None:
                out[Attrs.USAGE_INPUT_TOKENS] = in_tok
            if out_tok is not None:
                out[Attrs.USAGE_OUTPUT_TOKENS] = out_tok
            # Note: gen_ai.usage.total_tokens is not in the current registry
            # spec; avoid emitting it to stay compliant.
        resp_model = llm_output.get("model") or llm_output.get("response_model")
        if resp_model:
            out[Attrs.RESPONSE_MODEL] = resp_model
        resp_id = llm_output.get("id") or llm_output.get("response_id")
        if resp_id:
            out[Attrs.RESPONSE_ID] = resp_id
        # OpenAI specific optional attributes if present
        if llm_output:
            service_tier_req = llm_output.get("service_tier") or llm_output.get(
                "request_service_tier"
            )
            if service_tier_req:
                out[Attrs.OPENAI_REQUEST_SERVICE_TIER] = service_tier_req
            service_tier_resp = llm_output.get("response_service_tier")
            if service_tier_resp:
                out[Attrs.OPENAI_RESPONSE_SERVICE_TIER] = service_tier_resp
            sys_fp = llm_output.get("system_fingerprint") or llm_output.get(
                "systemFingerprint"
            )
            if sys_fp:
                out[Attrs.OPENAI_RESPONSE_SYSTEM_FINGERPRINT] = sys_fp
        return out


@experimental()
class AzureAIOpenTelemetryTracer(BaseCallbackHandler):
    """Tracing callback that emits OpenTelemetry spans for GenAI activity.

    Supports LangChain and LangGraph callbacks for LLM/chat, chains, tools,
    retrievers, parsers, transformers, and embeddings. Offers optional
    content recording and redaction, plus legacy compatibility attributes.
    """

    def __init__(
        self,
        *,
        enable_content_recording: Optional[bool] = None,
        connection_string: Optional[str] = None,
        redact: bool = False,
        include_legacy_keys: bool = True,
        provider_name: str = "langchain-azure-ai",
        # Additional optional defaults for generic attributes on spans
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """Create a new tracing callback.

        - enable_content_recording: enable recording of prompts/outputs.
        - connection_string: Application Insights connection string (optional).
        - redact: if True, redact recorded content.
        - include_legacy_keys: include legacy gen_ai.* prompt/completion keys.
        - provider_name: value for gen_ai.provider.name.
        """
        super().__init__()
        if enable_content_recording is None:
            env_val = os.environ.get(
                "AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "false"
            )
            enable_content_recording = env_val.lower() in {"1", "true", "yes"}
        if connection_string:
            configure_azure_monitor(connection_string=connection_string)
        elif os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
            configure_azure_monitor()
        tracer = otel_trace.get_tracer(__name__)
        self._core = _Core(
            enable_content_recording=enable_content_recording,
            redact=redact,
            include_legacy=include_legacy_keys,
            provider=provider_name,
            tracer=tracer,
            default_name=name,
            default_id=id,
            debug_export=False,
        )
        # Track the most recently detected provider (from chat/LLM calls)
        # so downstream tool spans inherit consistent provider attribution.
        self._current_provider: str = provider_name
        # Cache for synthetic tool spans when on_tool_* callbacks are not fired.
        # Keyed by tool_call_id; value carries name, args,
        # and an optional parent hint.
        self._pending_tool_calls: Dict[str, Dict[str, Any]] = {}
        # Track which agents we've already emitted a create_agent span for
        self._created_agents: set[str] = set()
        # Track active invoke_agent spans to avoid duplicates
        # per (parent, agent)
        self._active_agent_keys: set[Tuple[Optional[UUID], Optional[str]]] = set()
        self._agent_run_to_key: Dict[UUID, Tuple[Optional[UUID], Optional[str]]] = {}

        # Helper: detect active invoke_agent spans
        def _has_active_invoke_agent() -> bool:
            try:
                return any(
                    getattr(r, "operation", None) == "invoke_agent"
                    for r in self._core._runs.values()
                )
            except Exception:
                return False

        # Bind helper as method
        setattr(self, "_has_active_invoke_agent", _has_active_invoke_agent)

    def _has_active_invoke_agent(self) -> bool:
        """Return True if any currently active span is an invoke_agent."""
        try:
            return any(
                getattr(r, "operation", None) == "invoke_agent"
                for r in self._core._runs.values()
            )
        except Exception:
            return False

    def _record_tool_definitions(self, tools: Any) -> None:
        if not tools:
            return
        try:
            payload = _safe_json(tools)
        except Exception:
            payload = None
        if not payload:
            return
        try:
            root = getattr(self, "_root_agent_run_id", None)
            if root and root in self._core._runs:
                self._core.set(root, {Attrs.TOOL_DEFINITIONS: payload})
        except Exception:
            pass

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Any:
        """Start a chat span for a chat model call."""
        model = _get_model(serialized)
        params = _extract_params(serialized)
        attrs = self._core.llm_start_attrs(
            serialized=serialized,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            messages_json=_threads_json(messages),
            model=model,
            params=params,
        )
        if serialized:
            tools_def = (serialized.get("kwargs", {}) or {}).get("tools")
            if tools_def:
                self._record_tool_definitions(tools_def)
        # Remember detected provider for consistent tool span attribution
        try:
            prov = attrs.get(Attrs.PROVIDER_NAME)
            if isinstance(prov, str) and prov:
                self._current_provider = prov
        except Exception:
            pass
        # Attach conversation id when available
        try:
            if hasattr(self, "_root_agent_run_id") and self._root_agent_run_id:
                attrs[Attrs.CONVERSATION_ID] = str(self._root_agent_run_id)
        except Exception:
            pass
        # If provided parent is missing or unknown,
        # parent chat under the root invoke_agent
        try:
            if (
                (parent_run_id is None or parent_run_id not in self._core._runs)
                and hasattr(self, "_root_agent_run_id")
                and self._root_agent_run_id
            ):
                parent_run_id = self._root_agent_run_id
                attrs[Attrs.METADATA_PARENT_RUN_ID] = str(parent_run_id)
        except Exception:
            pass
        self._core.start(
            run_id=run_id,
            name=f"chat {model}" if model else "chat",
            kind=SpanKind.CLIENT,
            operation="chat",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )
        # Track last chat span for this agent parent to re-parent tool spans
        try:
            if parent_run_id is not None:
                if not hasattr(self, "_last_chat_for_parent"):
                    self._last_chat_for_parent: Dict[UUID, UUID] = {}
                self._last_chat_for_parent[parent_run_id] = run_id
        except Exception:
            pass

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Any:
        """Start a chat span from a list of prompts."""
        model = _get_model(serialized)
        params = _extract_params(serialized)
        messages: List[List[BaseMessage]] = [[HumanMessage(content=p)] for p in prompts]
        attrs = self._core.llm_start_attrs(
            serialized=serialized,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            messages_json=_threads_json(messages),
            model=model,
            params=params,
        )
        if serialized:
            tools_def = (serialized.get("kwargs", {}) or {}).get("tools")
            if tools_def:
                self._record_tool_definitions(tools_def)
        # Remember detected provider for consistent tool span attribution
        try:
            prov = attrs.get(Attrs.PROVIDER_NAME)
            if isinstance(prov, str) and prov:
                self._current_provider = prov
        except Exception:
            pass
        # Attach conversation id when available
        try:
            if hasattr(self, "_root_agent_run_id") and self._root_agent_run_id:
                attrs[Attrs.CONVERSATION_ID] = str(self._root_agent_run_id)
        except Exception:
            pass
        # If provided parent is missing or unknown,
        # parent chat under the root invoke_agent
        try:
            if (
                (parent_run_id is None or parent_run_id not in self._core._runs)
                and hasattr(self, "_root_agent_run_id")
                and self._root_agent_run_id
            ):
                parent_run_id = self._root_agent_run_id
                attrs[Attrs.METADATA_PARENT_RUN_ID] = str(parent_run_id)
        except Exception:
            pass
        self._core.start(
            run_id=run_id,
            name=f"chat {model}" if model else "chat",
            kind=SpanKind.CLIENT,
            operation="chat",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )
        # No synthetic tool spans; rely on actual tool callbacks
        # or chain_end fallback

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **_: Any,
    ) -> Any:
        """Finish the chat span and attach response attributes."""
        # Derive end attributes via core helper
        # (tool logic was erroneously here before)
        if response is None:
            self._core.end(run_id, None)
            return
        attrs = self._core.llm_end_attrs(result=response)
        if attrs:
            self._core.set(run_id, attrs)
        # Cache tool calls (if any) for synthetic tool spans later
        # when ToolMessage appears
        try:
            gens: List[List[ChatGeneration]] = getattr(response, "generations", [])
            for group in gens:
                for gen in group:
                    msg = getattr(gen, "message", None)
                    tool_calls = getattr(msg, "tool_calls", None)
                    if not tool_calls:
                        continue
                    # tool_calls is a list of dicts like
                    # {id, function:{name, arguments}, type:'function'}
                    for tc in tool_calls:
                        tc_dict: Dict[str, Any] = tc if isinstance(tc, dict) else {}
                        tc_id = tc_dict.get("id") or tc_dict.get("tool_call_id")
                        tool_type = tc_dict.get("type")
                        fn_obj = tc_dict.get("function")
                        fn_dict: Dict[str, Any] = (
                            fn_obj if isinstance(fn_obj, dict) else {}
                        )
                        name = fn_dict.get("name")
                        args_raw = fn_dict.get("arguments")
                        if name is None:
                            name = tc_dict.get("name")
                        if args_raw is None:
                            if "args" in tc_dict:
                                args_raw = tc_dict.get("args")
                            elif "arguments" in tc_dict:
                                args_raw = tc_dict.get("arguments")
                        args_val = args_raw
                        if isinstance(args_val, str):
                            try:
                                args_val = json.loads(args_val)
                            except Exception:
                                pass
                        tc_key = str(tc_id) if tc_id is not None else str(uuid4())
                        entry: Dict[str, Any] = {
                            "name": name,
                            "args": args_val,
                            "id": tc_key,
                            "llm_run_id": run_id,
                            "chain_parent_run_id": parent_run_id,
                        }
                        if tool_type:
                            entry["tool_type"] = tool_type
                        if tc_id is not None and tc_key != tc_id:
                            entry["raw_id"] = tc_id
                        self._pending_tool_calls[tc_key] = entry
        except Exception:
            pass
        self._core.end(run_id, None)

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[Any] = None,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **_: Any,
    ) -> Any:
        """Record a streaming token event on the active chat span."""
        state = self._core._runs.get(run_id)
        if not state:
            return
        try:
            state.span.add_event(
                "gen_ai.token",
                attributes={
                    "gen_ai.token.length": (len(token) if token is not None else 0),
                    "gen_ai.token.preview": (
                        token[:200] if isinstance(token, str) else ""
                    ),
                },
            )
        except Exception:
            pass

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **_: Any,
    ) -> Any:
        """Mark the chat span as errored and end it."""
        self._core.end(run_id, error)

    def on_agent_action(
        self,
        action: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Emit create_agent once per agent; do not create invoke_agent here."""
        name = (
            getattr(action, "tool", None)
            or getattr(action, "log", None)
            or getattr(action, "agent_name", None)
        )
        # Avoid starting duplicate agent spans if one is already
        # active for this parent
        agent_name_hint = (
            getattr(action, "agent_name", None)
            or getattr(action, "name", None)
            or getattr(action, "tool", None)
        )
        key_check: Tuple[Optional[UUID], Optional[str]] = (
            parent_run_id,
            str(agent_name_hint) if agent_name_hint else None,
        )
        # Suppress generic or tool-only agent wrappers and duplicates
        # 1) If an invoke_agent is already active anywhere, skip
        if self._has_active_invoke_agent():
            return
        # 2) If an invoke_agent for this parent was already started, skip
        if key_check in self._active_agent_keys:
            return
        # 3) If parent span is itself an invoke_agent,
        # do not start nested invoke_agent
        try:
            if parent_run_id and parent_run_id in self._core._runs:
                par = self._core._runs[parent_run_id]
                if getattr(par, "operation", None) == "invoke_agent":
                    return
        except Exception:
            pass
        # 4) Suppress generic names and tool-only wrappers
        if isinstance(agent_name_hint, str):
            _nm = agent_name_hint.strip().lower()
            if (
                _nm in {"agent", "tools"}
                or _nm.endswith(" tools")
                or _nm.startswith("tool")
            ):
                return
        # Emit create_agent once per agent name (best-effort detection)
        try:
            if isinstance(name, str) and name and name not in self._created_agents:
                self._created_agents.add(name)
                ca_attrs = {
                    Attrs.PROVIDER_NAME: self._core.provider,
                    Attrs.OPERATION_NAME: "create_agent",
                    Attrs.AGENT_NAME: name,
                    Attrs.AGENT_ID: getattr(action, "agent_id", None),
                    Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
                }
                # If action carries instructions, record as system instructions
                # (opt-in)
                sys_inst = getattr(action, "system_instructions", None) or getattr(
                    action, "instructions", None
                )
                if sys_inst and self._core.enable_content_recording:
                    red = self._core.redact_messages(_safe_json(sys_inst))
                    if red is not None:
                        ca_attrs[Attrs.SYSTEM_INSTRUCTIONS] = red
                ca_run_id = uuid4()
                self._core.start(
                    run_id=ca_run_id,
                    name=f"create_agent {name}",
                    kind=SpanKind.CLIENT,
                    operation="create_agent",
                    parent_run_id=parent_run_id,
                    attrs=ca_attrs,
                )
                self._core.end(run_id=ca_run_id, error=None)
        except Exception:
            pass
        # No invoke_agent span started here
        # system instructions if present
        sys_inst = getattr(action, "system_instructions", None) or getattr(
            action, "instructions", None
        )
        if sys_inst and self._core.enable_content_recording:
            red = self._core.redact_messages(_safe_json(sys_inst))
            if red is not None and isinstance(red, str):
                # Only set when attrs dict exists
                pass
        # Avoid noisy agent spans for tool-only actions
        if getattr(action, "tool", None):
            # Tool actions are recorded as execute_tool spans elsewhere
            return
        # De-duplicate invoke_agent per (parent_run_id, agent_name)
        # attrs may be undefined in the no-op path; skip agent_name lookup
        agent_name = None
        key: Tuple[Optional[UUID], Optional[str]] = (parent_run_id, agent_name)
        if key in self._active_agent_keys:
            # Skip starting a duplicate agent span for the same step/parent
            return
        self._active_agent_keys.add(key)
        self._agent_run_to_key[run_id] = key
        # No invoke_agent span started here

    def on_agent_finish(
        self,
        finish: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Finish the agent span and attach outputs (redacted if enabled)."""
        output = getattr(finish, "return_values", None) or getattr(finish, "log", None)
        if output is not None and not isinstance(output, list):
            out_list = [output]
        else:
            out_list = output or []
        # Normalize to OutputMessages if content recording enabled
        om: Optional[str] = None
        if out_list and self._core.enable_content_recording:
            msgs: List[Dict[str, Any]] = []
            for m in out_list:
                if isinstance(m, BaseMessage):
                    msgs.append(_message_to_role_parts(m))
                elif isinstance(m, dict) and "role" in m and "content" in m:
                    # Simple dict form
                    parts = []
                    c = m.get("content")
                    if isinstance(c, str) and c:
                        parts.append({"type": "text", "content": c})
                    msgs.append(
                        {
                            "role": m.get("role", "assistant"),
                            "parts": parts or [{"type": "text", "content": ""}],
                            "finish_reason": "stop",
                        }
                    )
            om = self._core.redact_messages(_safe_json(msgs)) if msgs else None
        attrs = {
            Attrs.AGENT_DESCRIPTION: getattr(finish, "log", None),
            Attrs.OUTPUT_MESSAGES: om,
        }
        if self._core.include_legacy and attrs.get(Attrs.OUTPUT_MESSAGES):
            attrs[Attrs.LEGACY_COMPLETION] = attrs[Attrs.OUTPUT_MESSAGES]
        self._core.set(run_id, attrs)
        # Clear active key for this agent run
        try:
            key = self._agent_run_to_key.pop(run_id, None)
            if key and key in self._active_agent_keys:
                self._active_agent_keys.discard(key)
        except Exception:
            pass
        self._core.end(run_id, None)

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Fallback: start an invoke_agent span at the top-level only.

        Ensures a single root span exists so downstream
        chat/tool spans share one trace.
        """
        attrs = {
            Attrs.PROVIDER_NAME: self._core.provider,
            Attrs.OPERATION_NAME: "invoke_agent",
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        if tags:
            attrs[Attrs.METADATA_TAGS] = _safe_json(tags)
        agent_name = None
        if metadata:
            agent_name = (
                metadata.get("agent_name")
                or metadata.get("agent_type")
                or metadata.get("langgraph_node")
            )
        if not agent_name and tags:
            for t in tags:
                if t.startswith("agent:"):
                    agent_name = t.split(":", 1)[1]
                    break
        if agent_name:
            attrs[Attrs.AGENT_NAME] = agent_name
        # Normalize inputs to role/parts threads
        if "messages" in inputs and isinstance(inputs["messages"], list):
            msgs = inputs["messages"]
            rp_threads: List[List[Dict[str, Any]]] = []
            if msgs and isinstance(msgs[0], BaseMessage):
                rp_threads = [[_message_to_role_parts(m) for m in msgs]]
            else:
                rp_thread: List[Dict[str, Any]] = []
                for m in msgs:
                    if isinstance(m, dict) and "role" in m and "content" in m:
                        parts = []
                        c = m.get("content")
                        if isinstance(c, str) and c:
                            parts.append({"type": "text", "content": c})
                        rp_thread.append(
                            {
                                "role": m.get("role", "user"),
                                "parts": parts or [{"type": "text", "content": ""}],
                                "finish_reason": "stop",
                            }
                        )
                if rp_thread:
                    rp_threads = [rp_thread]
            if rp_threads:
                msg_attr = self._core.redact_messages(_safe_json(rp_threads))
                if msg_attr is not None:
                    attrs[Attrs.INPUT_MESSAGES] = msg_attr
        self._core.enrich_langgraph(attrs, metadata)
        # Only start a root agent span when there's no parent
        if parent_run_id is not None:
            return None
        # Start top-level invoke_agent and track as root
        self._active_agent_keys.add((None, agent_name))
        self._agent_run_to_key[run_id] = (None, agent_name)
        self._root_agent_run_id = run_id
        self._core.start(
            run_id=run_id,
            name=(f"invoke_agent {agent_name}" if agent_name else "invoke_agent"),
            kind=SpanKind.CLIENT,
            operation="invoke_agent",
            parent_run_id=None,
            attrs=attrs,
        )
        try:
            tool_defs = (inputs or {}).get("tools") if inputs else None
            if not tool_defs and metadata:
                tool_defs = metadata.get("tools")
            if tool_defs:
                self._record_tool_definitions(tool_defs)
        except Exception:
            pass
        return None

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Finish the chain span and attach outputs when relevant."""
        attrs: Dict[str, Any] = {}
        # Attach outputs normalized to OutputMessages
        if (
            isinstance(outputs, dict)
            and "messages" in outputs
            and isinstance(outputs["messages"], list)
        ):
            msgs: List[Dict[str, Any]] = []
            for m in outputs["messages"]:
                if isinstance(m, BaseMessage):
                    msgs.append(_message_to_role_parts(m))
                elif isinstance(m, dict) and "role" in m and "content" in m:
                    parts = []
                    c = m.get("content")
                    if isinstance(c, str) and c:
                        parts.append({"type": "text", "content": c})
                    msgs.append(
                        {
                            "role": m.get("role", "assistant"),
                            "parts": parts or [{"type": "text", "content": ""}],
                            "finish_reason": "stop",
                        }
                    )
            msg_attr = self._core.redact_messages(_safe_json(msgs)) if msgs else None
            if msg_attr is not None:
                attrs[Attrs.OUTPUT_MESSAGES] = msg_attr
            elif (
                hasattr(outputs, "__class__")
                and outputs.__class__.__name__ == "Command"
            ):
                pass
        # Fallback end: if we started an invoke_agent at chain_start,
        # attach outputs
        # and end it so we have a single trace and root for the step.
        if attrs:
            try:
                self._core.set(run_id, attrs)
            except Exception:
                pass
        try:
            key = self._agent_run_to_key.pop(run_id, None)
            if key and key in self._active_agent_keys:
                self._active_agent_keys.discard(key)
            # End the agent span only if it exists
            self._core.end(run_id, None)
        except Exception:
            pass

        # Move synthetic tool spans to chat parent: handled in
        # on_llm_start/on_llm_end
        # Ensure no pending synthetic entries remain for this chain.
        # Only emit synthetic spans when the root agent (if any) finishes;
        # intermediate chain_end events would race actual tool callbacks.
        root_agent_run_id = getattr(self, "_root_agent_run_id", None)
        should_emit_synthetic = root_agent_run_id is None or run_id == root_agent_run_id
        if should_emit_synthetic:
            try:
                for tc_id, meta in list(self._pending_tool_calls.items()):
                    if meta.get("chain_parent_run_id") != run_id:
                        continue
                    if tc_id and tc_id in self._core._executed_tool_call_ids:
                        self._pending_tool_calls.pop(tc_id, None)
                        continue
                    parent_hint = meta.get("llm_run_id") or run_id
                    try:
                        root_parent = getattr(self, "_root_agent_run_id", None)
                    except Exception:
                        root_parent = None
                    if root_parent:
                        parent_hint = root_parent
                    name = meta.get("name") or "tool"
                    syn_run_id = uuid4()
                    attrs_syn = {
                        Attrs.PROVIDER_NAME: self._current_provider
                        or self._core.provider,
                        Attrs.OPERATION_NAME: "execute_tool",
                        Attrs.TOOL_NAME: name,
                        Attrs.METADATA_RUN_ID: str(syn_run_id),
                        Attrs.METADATA_PARENT_RUN_ID: (
                            str(parent_hint) if parent_hint else None
                        ),
                        Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
                    }
                    if tc_id is not None:
                        tcid_str = str(tc_id)
                        attrs_syn[Attrs.TOOL_CALL_ID] = tcid_str
                        self._core._executed_tool_call_ids.add(tcid_str)
                    if (
                        self._core.enable_content_recording
                        and meta.get("args") is not None
                    ):
                        attrs_syn[Attrs.TOOL_CALL_ARGS] = _safe_json(meta["args"])
                    try:
                        if (
                            hasattr(self, "_root_agent_run_id")
                            and self._root_agent_run_id
                        ):
                            attrs_syn[Attrs.CONVERSATION_ID] = str(
                                self._root_agent_run_id
                            )
                    except Exception:
                        pass
                    self._core.start(
                        run_id=syn_run_id,
                        name=f"execute_tool {name}" if name else "execute_tool",
                        kind=SpanKind.INTERNAL,
                        operation="execute_tool",
                        parent_run_id=parent_hint,
                        attrs=attrs_syn,
                    )
                    self._core.end(syn_run_id, None)
                    self._pending_tool_calls.pop(tc_id, None)
            except Exception:
                pass
        try:
            self._core._executed_tool_call_ids.clear()
        except Exception:
            pass
        # No chain span to end; ensure pending synthetic entries
        # are cleared above.

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Mark the chain span as errored and end it."""
        self._core.end(run_id, error)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Start a tool execution span and record arguments (opt-in)."""
        name = (serialized or {}).get("name") or (inputs or {}).get("name") or "tool"
        args_val = inputs if inputs is not None else {"input_str": input_str}
        tool_call_id_raw = None
        if inputs and isinstance(inputs, dict):
            tool_call_id_raw = inputs.get("id") or inputs.get("tool_call_id")
        tool_call_id_str = None
        if tool_call_id_raw is not None:
            tool_call_id_str = str(tool_call_id_raw)
        elif metadata and isinstance(metadata, dict):
            tool_call_id_raw = (
                metadata.get("tool_call_id")
                or metadata.get("id")
                or (metadata.get("tool_call") or {}).get("id")
            )
            if tool_call_id_raw is not None:
                tool_call_id_str = str(tool_call_id_raw)
        pending_entry: Optional[Dict[str, Any]] = None
        if tool_call_id_raw is not None:
            try:
                pending_entry = self._pending_tool_calls.pop(tool_call_id_raw, None)
            except Exception:
                pending_entry = None
        if pending_entry is None and tool_call_id_str is not None:
            try:
                pending_entry = self._pending_tool_calls.pop(tool_call_id_str, None)
            except Exception:
                pending_entry = None
        # If no direct match, attempt name-based match
        if pending_entry is None and self._pending_tool_calls:
            for tcid, meta in list(self._pending_tool_calls.items()):
                if meta.get("name") != name:
                    continue
                pending_entry = self._pending_tool_calls.pop(tcid, None)
                if tool_call_id_str is None:
                    tool_call_id_str = str(tcid)
                break
        attrs = {
            Attrs.PROVIDER_NAME: self._current_provider or self._core.provider,
            Attrs.OPERATION_NAME: "execute_tool",
            Attrs.TOOL_NAME: name,
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            # Respect opt-in content recording for tool arguments
            Attrs.TOOL_CALL_ARGS: (
                _safe_json(args_val) if self._core.enable_content_recording else None
            ),
            # Attempt optional fields per spec
            Attrs.TOOL_DESCRIPTION: (serialized or {}).get("description"),
            Attrs.TOOL_TYPE: (serialized or {}).get("type"),
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        if pending_entry:
            pending_name = pending_entry.get("name")
            if pending_name and not attrs.get(Attrs.TOOL_NAME):
                attrs[Attrs.TOOL_NAME] = pending_name
            if (
                self._core.enable_content_recording
                and not attrs.get(Attrs.TOOL_CALL_ARGS)
                and pending_entry.get("args") is not None
            ):
                attrs[Attrs.TOOL_CALL_ARGS] = _safe_json(pending_entry["args"])
            if not attrs.get(Attrs.TOOL_TYPE) and pending_entry.get("tool_type"):
                attrs[Attrs.TOOL_TYPE] = pending_entry.get("tool_type")
            if not tool_call_id_str and pending_entry.get("id"):
                tool_call_id_str = str(pending_entry.get("id"))
            if not tool_call_id_str and pending_entry.get("raw_id"):
                tool_call_id_str = str(pending_entry.get("raw_id"))
        # If tool_call_id still missing, but pending meta had a key, use it
        if tool_call_id_str is None and pending_entry is not None:
            for cand in (
                pending_entry.get("tool_call_id"),
                pending_entry.get("id"),
            ):
                if cand is not None:
                    tool_call_id_str = str(cand)
                    break
        attrs[Attrs.TOOL_CALL_ID] = tool_call_id_str or tool_call_id_raw
        # Attach conversation id when available
        try:
            if hasattr(self, "_root_agent_run_id") and self._root_agent_run_id:
                attrs[Attrs.CONVERSATION_ID] = str(self._root_agent_run_id)
        except Exception:
            pass
        # Debug: print callback and parent
        # console debug disabled
        # If parent is an agent, re-parent tool under the latest chat span
        root_parent = None
        try:
            root_parent = getattr(self, "_root_agent_run_id", None)
        except Exception:
            root_parent = None
        if root_parent:
            parent_run_id = root_parent
            attrs[Attrs.METADATA_PARENT_RUN_ID] = str(root_parent)
        # Track tool call ids to avoid duplicate synthetic spans later
        try:
            tcid_final = attrs.get(Attrs.TOOL_CALL_ID)
            if tcid_final is not None:
                tcid_str = str(tcid_final)
                attrs[Attrs.TOOL_CALL_ID] = tcid_str
                self._core._executed_tool_call_ids.add(tcid_str)
        except Exception:
            pass
        self._core.start(
            run_id=run_id,
            name=f"execute_tool {name}",
            kind=SpanKind.INTERNAL,
            operation="execute_tool",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Finish the tool span and record result (opt-in)."""
        # Record tool call result only if content recording enabled (opt-in)
        if self._core.enable_content_recording:
            self._core.set(run_id, {Attrs.TOOL_CALL_RESULT: _safe_json(output)})
        self._core.end(run_id, None)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Mark the tool span as errored and end it."""
        self._core.end(run_id, error)

    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Start a retriever span for a query."""
        name = (serialized or {}).get("id") or "retriever"
        attrs = {
            Attrs.PROVIDER_NAME: self._core.provider,
            Attrs.OPERATION_NAME: "retrieve",
            Attrs.DATA_SOURCE_ID: (serialized or {}).get("name"),
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            "retriever.query": query,
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        self._core.start(
            run_id=run_id,
            name=f"retrieve {name}",
            kind=SpanKind.INTERNAL,
            operation="retrieve",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )

    def on_retriever_end(
        self,
        documents: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Finish the retriever span and attach document count."""
        try:
            count = len(documents)
        except Exception:
            count = None
        self._core.set(run_id, {"retriever.documents.count": count})
        self._core.end(run_id, None)

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Mark the retriever span as errored and end it."""
        self._core.end(run_id, error)

    # -------------- Parser callbacks (internal) --------------
    def on_parser_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Start a parser span and optionally record inputs/config."""
        name = (
            (serialized or {}).get("id") or (serialized or {}).get("name") or "parser"
        )
        kw = (serialized or {}).get("kwargs", {}) or {}
        ptype = (serialized or {}).get("type") or kw.get("_type") or kw.get("type")
        attrs: Dict[str, Any] = {
            Attrs.PROVIDER_NAME: self._core.provider,
            Attrs.OPERATION_NAME: "parse",
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            "parser.name": name,
            "parser.type": ptype,
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        if tags:
            attrs[Attrs.METADATA_TAGS] = _safe_json(tags)
        self._core.enrich_langgraph(attrs, metadata)
        if self._core.enable_content_recording and inputs is not None:
            try:
                attrs["parser.input"] = _safe_json(inputs)
            except Exception:
                pass
        if self._core.enable_content_recording and kw:
            try:
                attrs["parser.config"] = _safe_json(kw)
            except Exception:
                pass
        self._core.start(
            run_id=run_id,
            name=f"parse {name}",
            kind=SpanKind.INTERNAL,
            operation="parse",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )

    def on_parser_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Finish the parser span and attach output metadata."""
        attrs: Dict[str, Any] = {}
        if self._core.enable_content_recording and outputs is not None:
            try:
                attrs["parser.output"] = _safe_json(outputs)
            except Exception:
                pass
        try:
            size = len(outputs) if hasattr(outputs, "__len__") else None
            attrs["parser.output.size"] = size
        except Exception:
            pass
        self._core.set(run_id, attrs)
        self._core.end(run_id, None)

    def on_parser_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Mark the parser span as errored and end it."""
        self._core.end(run_id, error)

    # -------------- Transformer callbacks (internal) --------------
    def on_transform_start(
        self,
        serialized: Dict[str, Any],
        inputs: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Start a transform span and optionally record inputs/config."""
        name = (
            (serialized or {}).get("id")
            or (serialized or {}).get("name")
            or "transform"
        )
        kw = (serialized or {}).get("kwargs", {}) or {}
        ttype = (serialized or {}).get("type") or kw.get("_type") or kw.get("type")
        attrs: Dict[str, Any] = {
            Attrs.PROVIDER_NAME: self._core.provider,
            Attrs.OPERATION_NAME: "transform",
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            "transform.name": name,
            "transform.type": ttype,
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
        }
        if tags:
            attrs[Attrs.METADATA_TAGS] = _safe_json(tags)
        self._core.enrich_langgraph(attrs, metadata)
        if self._core.enable_content_recording and inputs is not None:
            try:
                attrs["transform.input"] = _safe_json(inputs)
            except Exception:
                pass
        if self._core.enable_content_recording and kw:
            try:
                attrs["transform.config"] = _safe_json(kw)
            except Exception:
                pass
        # Simple metrics: input count if list-like
        try:
            attrs["transform.inputs.count"] = (
                len(inputs) if hasattr(inputs, "__len__") else None
            )
        except Exception:
            pass
        self._core.start(
            run_id=run_id,
            name=f"transform {name}",
            kind=SpanKind.INTERNAL,
            operation="transform",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )

    def on_transform_end(
        self,
        outputs: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Finish the transform span and attach output metadata."""
        attrs: Dict[str, Any] = {}
        if self._core.enable_content_recording and outputs is not None:
            try:
                attrs["transform.output"] = _safe_json(outputs)
            except Exception:
                pass
        try:
            attrs["transform.outputs.count"] = (
                len(outputs) if hasattr(outputs, "__len__") else None
            )
        except Exception:
            pass
        self._core.set(run_id, attrs)
        self._core.end(run_id, None)

    def on_transform_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Mark the transform span as errored and end it."""
        self._core.end(run_id, error)

    # -------------- Events helpers --------------
    def emit_inference_details_event(
        self,
        *,
        run_id: UUID,
        details: Dict[str, Any],
    ) -> None:
        """Emit a detailed inference operation event on the given run span.

        Event name: "gen_ai.client.inference.operation.details".
        Attributes: pass a dict of additional details (normalized to
        primitives/JSON strings).
        """
        state = self._core._runs.get(run_id)
        if not state:
            return
        attrs: Dict[str, Any] = {}
        # Normalize values to be OTEL attribute safe
        for k, v in (details or {}).items():
            nv = _normalize(v)
            if nv is not None:
                attrs[k] = nv
        try:
            state.span.add_event(
                "gen_ai.client.inference.operation.details",
                attributes=attrs,
            )
        except Exception:
            pass

    def emit_evaluation_event(
        self,
        *,
        run_id: UUID,
        evaluation_name: str,
        score_value: float,
        score_label: str,
        explanation: Optional[str] = None,
        extra_attrs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a model evaluation result event on the given run span.

        Event name: "gen_ai.evaluation.result"
        Attributes include:
          - gen_ai.evaluation.name
          - gen_ai.evaluation.score.value
          - gen_ai.evaluation.score.label
          - gen_ai.evaluation.explanation (optional)
          - gen_ai.response.id (when available for this run)
          - any extra_attrs provided (normalized)
        """
        state = self._core._runs.get(run_id)
        if not state:
            return
        attrs: Dict[str, Any] = {
            "gen_ai.evaluation.name": evaluation_name,
            "gen_ai.evaluation.score.value": float(score_value),
            "gen_ai.evaluation.score.label": str(score_label),
        }
        if explanation is not None:
            attrs["gen_ai.evaluation.explanation"] = str(explanation)
        if getattr(state, "response_id", None):
            attrs[Attrs.RESPONSE_ID] = state.response_id
        for k, v in (extra_attrs or {}).items():
            nv = _normalize(v)
            if nv is not None:
                attrs[k] = nv
        try:
            state.span.add_event("gen_ai.evaluation.result", attributes=attrs)
        except Exception:
            pass

    def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Attach a free-form text event to the active span."""
        state = self._core._runs.get(run_id)
        if not state:
            return
        try:
            state.span.add_event(
                "gen_ai.text",
                {"text.length": len(text), "text.preview": text[:200]},
            )
        except Exception:
            pass

    def on_retry(
        self,
        retry_state: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Record a retry event with the attempt count."""
        state = self._core._runs.get(run_id)
        if not state:
            return
        attempt = getattr(retry_state, "attempt_number", None)
        try:
            ev: Dict[str, Any] = {}
            if attempt is not None:
                try:
                    ev["retry.attempt"] = int(attempt)
                except Exception:
                    pass
            state.span.add_event("retry", ev)
        except Exception:
            pass

    def on_custom_event(
        self,
        name: str,
        data: Any,
        *,
        run_id: UUID,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> Any:
        """Attach a custom event to the active span."""
        state = self._core._runs.get(run_id)
        if not state:
            return
        ev: Dict[str, Any] = {"data": _safe_json(data)}
        if tags:
            ev["event.tags"] = _safe_json(tags)
        if metadata:
            ev["event.metadata"] = _safe_json(metadata)
        try:
            state.span.add_event(name, ev)
        except Exception:
            pass

    # Embeddings span compliance
    def on_embedding_start(
        self,
        serialized: Dict[str, Any],
        inputs: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **__: Any,
    ) -> Any:
        """Start an embeddings span and optionally record inputs."""
        model = _get_model(serialized)
        kw = (serialized or {}).get("kwargs", {}) or {}
        encoding_formats = kw.get("encoding_format") or kw.get("encoding_formats")
        if isinstance(encoding_formats, str):
            encoding_formats = [encoding_formats]
        dims = kw.get("dimensions") or kw.get("embedding_dimensions")
        endpoint = (
            kw.get("azure_endpoint")
            or kw.get("base_url")
            or kw.get("api_base")
            or kw.get("endpoint")
        )
        attrs = {
            Attrs.PROVIDER_NAME: self._core.provider,
            Attrs.OPERATION_NAME: "embeddings",
            Attrs.REQUEST_MODEL: model,
            Attrs.METADATA_RUN_ID: str(run_id),
            Attrs.METADATA_PARENT_RUN_ID: (
                str(parent_run_id) if parent_run_id else None
            ),
            Attrs.AZURE_RESOURCE_NAMESPACE: "Microsoft.CognitiveServices",
            Attrs.REQUEST_ENCODING_FORMATS: encoding_formats,
            Attrs.EMBEDDINGS_DIM_COUNT: dims,
        }
        if endpoint:
            attrs[Attrs.SERVER_ADDRESS] = endpoint
            port = _extract_port(endpoint)
            if port is not None:
                attrs[Attrs.SERVER_PORT] = port
        if tags:
            attrs[Attrs.METADATA_TAGS] = _safe_json(tags)
        self._core.enrich_langgraph(attrs, metadata)
        if self._core.enable_content_recording:
            inputs_json = self._core.redact_messages(
                _safe_json([{"content": i} for i in inputs])
            )
            if inputs_json is not None:
                attrs[Attrs.INPUT_MESSAGES] = inputs_json
        span_name = f"embeddings {model}" if model else "embeddings"
        self._core.start(
            run_id=run_id,
            name=span_name,
            kind=SpanKind.CLIENT,
            operation="embeddings",
            parent_run_id=parent_run_id,
            attrs=attrs,
        )

    def on_embedding_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Finish the embeddings span and attach usage when present."""
        usage: Dict[str, Any] = {}
        try:
            usage = getattr(response, "usage", {}) or {}
        except Exception:
            pass
        set_attrs = {}
        for key in ("input_tokens", "prompt_tokens"):
            if usage.get(key) is not None:
                set_attrs[Attrs.USAGE_INPUT_TOKENS] = usage[key]
                break
        self._core.set(run_id, set_attrs)
        self._core.end(run_id, None)

    def on_embedding_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **__: Any,
    ) -> Any:
        """Mark the embeddings span as errored and end it."""
        self._core.end(run_id, error)

    def shutdown(self) -> None:  # pragma: no cover
        """No-op shutdown hook for exporter lifecycles."""
        pass

    def force_flush(self) -> None:  # pragma: no cover
        """No-op force flush hook for exporter lifecycles."""
        pass


__all__ = ["AzureAIOpenTelemetryTracer"]


def _generations_to_role_parts(
    gens: List[List[ChatGeneration]],
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for group in gens or []:
        for gen in group or []:
            parts: List[Dict[str, Any]] = []
            # Text content
            content = getattr(gen, "text", None)
            if content is None and hasattr(gen, "message"):
                content = getattr(gen.message, "content", None)
            if isinstance(content, str) and content:
                parts.append({"type": "text", "content": content})
            # Tool calls (if present on message)
            msg = getattr(gen, "message", None)
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        tc_id = tc.get("id")
                        func = tc.get("function") or {}
                        name = func.get("name") or tc.get("name")
                        args = func.get("arguments") if isinstance(func, dict) else None
                        parts.append(
                            {
                                "type": "tool_call",
                                "id": tc_id,
                                "name": name,
                                "arguments": _try_parse_json(
                                    args if args is not None else tc.get("arguments")
                                ),
                            }
                        )
                    else:
                        tc_id = getattr(tc, "id", None)
                        name = getattr(tc, "name", None)
                        args = getattr(tc, "args", None) or getattr(
                            tc, "arguments", None
                        )
                        parts.append(
                            {
                                "type": "tool_call",
                                "id": (str(tc_id) if tc_id is not None else None),
                                "name": name,
                                "arguments": _try_parse_json(args),
                            }
                        )
            # Finish reason from generation_info if available
            info = getattr(gen, "generation_info", None) or {}
            finish_reason = None
            if isinstance(info, dict):
                finish_reason = (
                    info.get("finish_reason")
                    or info.get("finishReason")
                    or info.get("reason")
                )
            # Normalize provider variants
            if finish_reason == "tool_calls":
                finish_reason = "tool_call"
            if finish_reason is None:
                finish_reason = "stop"
            messages.append(
                {
                    "role": "assistant",
                    "parts": parts or [{"type": "text", "content": ""}],
                    "finish_reason": finish_reason,
                }
            )
    return messages
