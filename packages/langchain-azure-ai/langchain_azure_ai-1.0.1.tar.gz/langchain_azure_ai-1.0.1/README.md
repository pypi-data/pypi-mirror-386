# langchain-azure-ai

This package contains the LangChain integration for Azure AI Foundry. To learn more about how to use this package, see the LangChain documentation in [Azure AI Foundry](https://aka.ms/azureai/langchain).

## Installation

```bash
pip install -U langchain-azure-ai
```

For using tools, including Azure AI Document Intelligence, Azure AI Text Analytics for Health, or Azure LogicApps, please install the extras `tools`:

```bash
pip install -U langchain-azure-ai[tools]
```

For using tracing capabilities with OpenTelemetry, you need to add the extras `opentelemetry`:

```bash
pip install -U langchain-azure-ai[opentelemetry]
```

## Quick Start with langchain-azure-ai

The `langchain-azure-ai` package uses the Azure AI Foundry family of SDKs and client libraries for Azure to provide first-class support of Azure AI Foundry capabilities in LangChain and LangGraph.

This package includes:

* [Azure AI Agent Service](./libs/azure-ai/langchain_azure_ai/agents)
* [Azure AI Foundry Models inference](./libs/azure-ai/langchain_azure_ai/chat_models)
* [Azure AI Search](./libs/azure-ai/langchain_azure_ai/vectorstores)
* [Azure AI Services tools](./libs/azure-ai/langchain_azure_ai/tools)
* [Cosmos DB](./libs/azure-ai/langchain_azure_ai/vectorstores)

Here's a quick start example to show you how to get started with the Chat Completions model. For more details and tutorials see [Develop with LangChain and LangGraph and models from Azure AI Foundry](https://aka.ms/azureai/langchain).

### Azure AI Chat Completions Model with Azure OpenAI 

```python

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import HumanMessage, SystemMessage

model = AzureAIChatCompletionsModel(
    endpoint="https://{your-resource-name}.services.ai.azure.com/openai/v1",
    credential="your-api-key", #if using Entra ID you can should use DefaultAzureCredential() instead
    model="gpt-4o"
)

messages = [
    SystemMessage(
      content="Translate the following from English into Italian"
    ),
    HumanMessage(content="hi!"),
]

model.invoke(messages)
```

```python
AIMessage(content='Ciao!', additional_kwargs={}, response_metadata={'model': 'gpt-4o', 'token_usage': {'input_tokens': 20, 'output_tokens': 3, 'total_tokens': 23}, 'finish_reason': 'stop'}, id='run-0758e7ec-99cd-440b-bfa2-3a1078335133-0', usage_metadata={'input_tokens': 20, 'output_tokens': 3, 'total_tokens': 23})
```

### Azure AI Chat Completions Model with DeepSeek-R1 

```python

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import HumanMessage, SystemMessage

model = AzureAIChatCompletionsModel(
    endpoint="https://{your-resource-name}.services.ai.azure.com/models",
    credential="your-api-key", #if using Entra ID you can should use DefaultAzureCredential() instead
    model="DeepSeek-R1",
)

messages = [
    HumanMessage(content="Translate the following from English into Italian: \"hi!\"")
]

message_stream = model.stream(messages)
print(' '.join(chunk.content for chunk in message_stream))
```

```python
 <think> 
 Okay ,  the  user  just  sent  " hi !"  and  I  need  to  translate  that  into  Italian .  Let  me  think .  " Hi "  is  an  informal  greeting ,  so  in  Italian ,  the  equivalent  would  be  " C iao !"  But  wait ,  there  are  other  options  too .  Sometimes  people  use  " Sal ve ,"  which  is  a  bit  more  neutral ,  but  " C iao "  is  more  common  in  casual  settings .  The  user  probably  wants  a  straightforward  translation ,  so  " C iao !"  is  the  safest  bet  here .  Let  me  double -check  to  make  sure  there 's  no  nuance  I 'm  missing .  N ope ,  " C iao "  is  definitely  the  right  choice  for  translating  " hi !"  in  an  informal  context .  I 'll  go  with  that . 
 </think> 

 C iao ! 
```

## Changelog

- **1.0.0**:

    - We introduce support for LangChain and LangGraph 1.0.

- **0.1.8**:

    - We fixed some issues with `AzureAIOpenTelemetryTracer`, including compliant hierarchy, tool spans under chat, finish reason normalization, conversation id. See [PR #167]
    - We fixed an issue with taking image inputs for declarative agents created with Azure AI Foundry Agents service.
    - We enhanced tool descriptions to improve tool call accuracy. 

- **0.1.7**:

  - **[NEW]**: We introduce LangGraph support for declarative agents created in Azure AI Foundry. You can now compose complex graphs in LangGraph and add nodes that take advantage of Azure AI Agent Service. See [`AgentServiceFactory`](./langchain_azure_ai/agents/agent_service.py#L44)
  - We fix an issue with the interface of `AzureAIEmbeddingsModel` [#158](https://github.com/langchain-ai/langchain-azure/issues/158).
  - We improve the signatures of the tools `AzureAIDocumentIntelligenceTool`, `AzureAIImageAnalysisTool`, and `AzureAITextAnalyticsHealthTool` [PR #160](https://github.com/langchain-ai/langchain-azure/pull/160).

- **0.1.6**:

  - **[Breaking change]:** Using parameter `project_connection_string` to create `AzureAIEmbeddingsModel` and `AzureAIChatCompletionsModel` is not longer supported. Use `project_endpoint` instead.
  - **[Breaking change]:** Class `AzureAIInferenceTracer` has been removed in favor of `AzureAIOpenTelemetryTracer` which has a better support for OpenTelemetry and the new semantic conventions for GenAI.
  - Adding the following tools to the package: `AzureAIDocumentIntelligenceTool`, `AzureAIImageAnalysisTool`, and `AzureAITextAnalyticsHealthTool`. You can also use `AIServicesToolkit` to have access to all the tools in Azure AI Services.

- **0.1.4**:

  - Bug fix [#91](https://github.com/langchain-ai/langchain-azure/pull/91).

- **0.1.3**:

  - **[Breaking change]:** We renamed the parameter `model_name` in `AzureAIEmbeddingsModel` and `AzureAIChatCompletionsModel` to `model`, which is the parameter expected by the method `langchain.chat_models.init_chat_model`.
  - We fixed an issue with JSON mode in chat models [#81](https://github.com/langchain-ai/langchain-azure/issues/81).
  - We fixed the dependencies for NumpPy [#70](https://github.com/langchain-ai/langchain-azure/issues/70).
  - We fixed an issue when tracing Pyndantic objects in the inputs [#65](https://github.com/langchain-ai/langchain-azure/issues/65).
  - We made `connection_string` parameter optional as suggested at [#65](https://github.com/langchain-ai/langchain-azure/issues/65).

- **0.1.2**:

  - Bug fix [#35](https://github.com/langchain-ai/langchain-azure/issues/35).

- **0.1.1**: 

  - Adding `AzureCosmosDBNoSqlVectorSearch` and `AzureCosmosDBNoSqlSemanticCache` for vector search and full text search.
  - Adding `AzureCosmosDBMongoVCoreVectorSearch` and `AzureCosmosDBMongoVCoreSemanticCache` for vector search.
  - You can now create `AzureAIEmbeddingsModel` and `AzureAIChatCompletionsModel` clients directly from your AI project's connection string using the parameter `project_connection_string`. Your default Azure AI Services connection is used to find the model requested. This requires to have `azure-ai-projects` package installed.
  - Support for native LLM structure outputs. Use `with_structured_output(method="json_schema")` to use native structured schema support. Use `with_structured_output(method="json_mode")` to use native JSON outputs capabilities. By default, LangChain uses `method="function_calling"` which uses tool calling capabilities to generate valid structure JSON payloads. This requires to have `azure-ai-inference >= 1.0.0b7`.
  - Bug fix [#18](https://github.com/langchain-ai/langchain-azure/issues/18) and [#31](https://github.com/langchain-ai/langchain-azure/issues/31).

- **0.1.0**:

  - Introduce `AzureAIEmbeddingsModel` for embedding generation and `AzureAIChatCompletionsModel` for chat completions generation using the Azure AI Inference API. This client also supports GitHub Models endpoint.
  - Introduce `AzureAIOpenTelemetryTracer` for tracing with OpenTelemetry and Azure Application Insights.
