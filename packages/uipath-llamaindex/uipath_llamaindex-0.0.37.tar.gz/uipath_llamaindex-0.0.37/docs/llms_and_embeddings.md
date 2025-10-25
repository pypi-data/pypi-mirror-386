# LLMs and Embeddings

UiPath provides pre-configured LLM and embedding classes that handle authentication, routing, and configuration automatically, allowing you to focus on building your agents.
You do not need to add tokens from OpenAI, usage of these models will consume `Agent Units` on your account.

## UiPathOpenAI

The `UiPathOpenAI` class is a pre-configured Azure OpenAI client that routes requests through UiPath.

### Available Models

The following OpenAI models are available through the `OpenAIModel` enum:

- `GPT_4_1_2025_04_14`
- `GPT_4_1_MINI_2025_04_14`
- `GPT_4_1_NANO_2025_04_14`
- `GPT_4O_2024_05_13`
- `GPT_4O_2024_08_06`
- `GPT_4O_2024_11_20`
- `GPT_4O_MINI_2024_07_18` (default)
- `O3_MINI_2025_01_31`
- `TEXT_DAVINCI_003`

### Basic Usage

```python
from uipath_llamaindex.llms import UiPathOpenAI
from llama_index.core.llms import ChatMessage

# Create an LLM instance with default settings
llm = UiPathOpenAI()

# Create chat messages
messages = [
    ChatMessage(
        role="system", content="You are a pirate with colorful personality."
    ),
    ChatMessage(role="user", content="Hello"),
]

# Generate a response
response = llm.chat(messages)
print(response)
```

### Custom Model Configuration

```python
from uipath_llamaindex.llms import UiPathOpenAI, OpenAIModel

# Use a specific model
llm = UiPathOpenAI(model=OpenAIModel.GPT_4O_2024_11_20)

# Or use a model string directly
llm = UiPathOpenAI(model="gpt-4o-2024-11-20")
```

## UiPathOpenAIEmbedding

The `UiPathOpenAIEmbedding` class provides text embedding capabilities using OpenAI's embedding models through UiPath.

### Available Embedding Models

The following embedding models are available through the `OpenAIEmbeddingModel` enum:

- `TEXT_EMBEDDING_ADA_002` (default)
- `TEXT_EMBEDDING_3_LARGE`

### Basic Usage

```python
from uipath_llamaindex.embeddings import UiPathOpenAIEmbedding

# Create an embedding model instance
embed_model = UiPathOpenAIEmbedding()

# Get embeddings for a single text
result = embed_model.get_text_embedding("the quick brown fox jumps over the lazy dog")
print(f"Embedding dimension: {len(result)}")
```

### Batch Embeddings

```python
from uipath_llamaindex.embeddings import UiPathOpenAIEmbedding

embed_model = UiPathOpenAIEmbedding()

# Get embeddings for multiple texts
texts = [
    "Hello world",
    "How are you?",
    "This is a test"
]

embeddings = embed_model.get_text_embedding_batch(texts)
print(f"Number of embeddings: {len(embeddings)}")
```


## Integration with LlamaIndex

Both classes integrate seamlessly with LlamaIndex components:

### Using with Agents

```python
import asyncio
from llama_index.core.agent.workflow import ReActAgent
from uipath_llamaindex.llms import UiPathOpenAI, OpenAIModel

def multiply(a: int, b: int) -> int:
    """Multiply two integers and returns the result integer"""
    return a * b


def add(a: int, b: int) -> int:
    """Add two integers and returns the result integer"""
    return a + b

# Create agent with UiPath LLM
agent = ReActAgent(
    tools=[multiply, add],
    llm=UiPathOpenAI(model=OpenAIModel.GPT_4O_2024_11_20))

async def main():
    handler = agent.run("What is 2+(2*4)?")
    response = await handler

asyncio.run(main())
```

### Using with VectorStoreIndex

```python
from llama_index.core import VectorStoreIndex, Document
from uipath_llamaindex.llms import UiPathOpenAI
from uipath_llamaindex.embeddings import UiPathOpenAIEmbedding

# Create documents
documents = [
    Document(text="This is a sample document about artificial intelligence."),
    Document(text="Machine learning is a subset of AI that focuses on algorithms."),
]

# Create index with UiPath models
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=UiPathOpenAIEmbedding()
)

# Create query engine with UiPath LLM
query_engine = index.as_query_engine(
    llm=UiPathOpenAI(model=OpenAIModel.GPT_4O_2024_11_20)
)

response = query_engine.query("What is machine learning?")
```

/// warning
Please note that you may get errors related to data residency, as some models are not available on all regions.

Example: `[Enforced Region] No model configuration found for product uipath-python-sdk in EU`.

///
