<a href="https://sambanova.ai/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./img/SambaNova-light-logo-1.png" height="60">
  <img alt="SambaNova logo" src="./img/SambaNova-dark-logo-1.png" height="60">
</picture>
</a>

# langchain-sambanova

This package contains the LangChain integration with SambaNova

## Installation

```bash
pip install -U langchain-sambanova
```

And you should configure credentials by setting the following environment variables:

If you are a SambaCloud user:

```bash
export SAMBANOVA_API_KEY="your-sambacloud-api-key-here"
```
> You can obtain a free SambaCloud API key [here](https://cloud.sambanova.ai/)

If you are a SambaStack user:

```bash
export SAMBANOVA_API_BASE="your-sambastack-api-base-url-here"
export SAMBANOVA_API_KEY="your-sambastack-api-key-here"
```

## Chat Models

### SambaNova

`ChatSambaNova` class exposes chat models from SambaNova unified interface for SambaCloud and SambaStack.

```python
from langchain_sambanova import ChatSambaNova

llm = ChatSambaNova(
    model = "Llama-4-Maverick-17B-128E-Instruct",
    temperature = 0.7
)
llm.invoke("Tell me a joke about artificial intelligence.")
```

## Embeddings

### SambaNova

`SambaNovaEmbeddings` class exposes embeddings from SambaNova unified interface for SambaCloud and SambaStack.

```python
from langchain_sambanova import SambaNovaEmbeddings

embeddings = SambaNovaEmbeddings(
    model="E5-Mistral-7B-Instruct"
)
embeddings.embed_query("What is the meaning of life?")
```
