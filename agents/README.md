# Test Agents

This directory contains agents generated during testing and development.

**Note**: This directory is typically in  and not committed to the repository.

## Usage

Generated agents can be used with:

```bash
# In REPL
kagura repl --agents-dir ./agents

# Direct execution
kagura build run-agent agents/youtube_video_summarizer.py "https://..."

# In Chat (auto-loaded)
kagura chat
```

