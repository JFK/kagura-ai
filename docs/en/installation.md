# Installation

## Prerequisites

- Python 3.11+
- Redis (optional, for persistence)

---

## Installation Steps

### Using Git

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
poetry install
```

### Starting Kagura

Kagura is a console-based chatbot assistant. You can start Kagura using the following command:

```bash
kagura
# Or, if the above doesn't work
poetry run kagura
```

After the first run, the configuration file `system.yml` will be created in `~/.config/kagura/`.

### Verifying Installation

To verify that Kagura is installed correctly, use the following command:

```bash
kagura --help
# Or
poetry run kagura --help
```

Expected output:

```
Usage: kagura [OPTIONS] COMMAND [ARGS]...

  Kagura AI - A flexible AI agent framework

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  chat    Start interactive chat with Kagura AI
  create  Create a new Kagura agent
```

---

## Redis Setup (Optional)

Redis provides persistent memory for the Kagura assistant.

1. Install Redis:

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

2. Verify Redis installation:

```bash
redis-cli ping
# Output: PONG
```

---

## Environment Variables

### API Keys

Kagura uses LiteLLM for LLM integration. Please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/set_keys#environment-variables) for more details.

Export the following API keys in your environment to enable respective LLMs:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export REPLICATE_API_KEY="your-replicate-api-key"
export TOGETHERAI_API_KEY="your-togetherai-api-key"
```

### Logging Level

To set the logging level, use the following command:

```bash
export LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
```

---

[Configuration →](configuration.md){: .md-button .md-button--primary }
