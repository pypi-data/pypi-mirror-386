# Ollama Invokers
[![PyPI version](https://badge.fury.io/py/genie-flow-invoker-ollama.svg?icon=si%3Apython)](https://badge.fury.io/py/genie-flow-invoker-ollama)
![PyPI - Downloads](https://img.shields.io/pypi/dm/genie-flow-invoker-ollama)

This package contains Genie Flow invokers for different Ollama invocations.

## Installing the ollama invoker

```bash
pip install genie-flow-invoker-ollama
```

## Installing Ollama

To run models locally, you'll need to install Ollama. We recommend using the official native installer for your platform:

[Install Ollama](https://ollama.com/download)

This will set up the Ollama runtime and make the ollama command available in your terminal.

Once installed, you can start a model like:

```bash
ollama run llama3
```

For advanced users, Ollama also provides a Docker image: [Ollama for Docker](https://hub.docker.com/r/ollama/ollama) which you can use in containerized environments.

## Select model and query
List all available ollama models run:

```bash
ollama list
```
To start using the selected model, create a meta.yaml and a prompt like described here: [Create LLM templates](https://genieversum.github.io/getting_started/#locally-running-llm:~:text=to%20the%20user.-,Create%20the%20LLM%20Templates,-The%20template%20that)

There are three different types of invokers available:

- OllamaChatInvoker, includes dialogue history in your prompt
- OllamaGenerateInvoker, includes base64-encoded images in your prompt, using the model defined in meta.yaml
- OllamaEmbedInvoker, vectorizes text using the embedding model specified in meta.yaml

### Include base64 encoded images in prompt

For images to be included, the prompt template **must** be structured as follows, or else, the query will only contain plain text.

```jinja
prompt: |
    Some prompt text
images:
    - {{ image_as_base64 }}
```