# Installation

## Prerequisites

- Python 3.11+
- Redis (optional, for persistence)

---

## Installation Steps

```bash
uv add kagura-ai
```

### Starting Kagura

You can start Kagura using the following command:
`kagura` command to initiate system setup.
After the first run, the configuration file `system.yml` will be created in `~/.config/kagura/`.

```bash
$ uv run kagura
Welcome to Kagura AI!
Here are some of Kagura's Zen principles:
----------------------------------------
Harmony is better than discord.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Composition is better than inheritance.
YAML is better than JSON for human configuration.
Types are better than any.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Agents should be one thing, rather than everything.
Dependencies are both necessary and a liability.
While reactivity matters, thoughtfulness is key.
Although practicality beats purity.
Errors should never fail to inform.
In the face of many options, take the one most explicit.
Unless that path is fraught with danger.
Beautiful is better than ugly.
Understanding is better than magic.
Although black boxes are sometimes necessary.
Agent composition should be intuitive.
Even though agents can be complex.
Simple tasks should be simple.
Complex tasks should be possible.
The present is more important than the past.
The future is more important than the present.
But the past holds lessons we shouldn't forget.
```


### Verifying Installation

To verify that Kagura is installed correctly, use the following command:

```bash
uv run kagura --help
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

[System Configuration →](system-configuration.md){: .md-button .md-button--primary }
