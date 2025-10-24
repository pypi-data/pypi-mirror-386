# JVS CLI

A terminal-based AI chat interface with streaming support and beautiful terminal formatting.

## Features

- Interactive REPL mode with conversation history
- Streaming responses with real-time display
- AI thinking step visualization
- Markdown rendering
- Multiple color themes
- OpenAI-compatible API support

## Installation

```bash
pip install jvs-cli
```

## Quick Start

Initialize configuration:

```bash
jvs-cli config init
```

You'll be prompted for:
- API URL (OpenAI-compatible endpoint)
- Login Code
- Theme (color scheme)

Start chatting:

```bash
jvs-cli
```

One-shot query:

```bash
jvs-cli ask "What is machine learning?"
```

## Commands

Interactive mode commands:
- `/new` - Start new conversation
- `/history` - Show conversation history
- `/config` - Show configuration
- `/help` - Show help
- `/exit` - Exit

CLI commands:
- `jvs-cli` - Interactive mode
- `jvs-cli ask "query"` - One-shot query
- `jvs-cli chat <conv_id>` - Continue conversation
- `jvs-cli config init` - Setup wizard
- `jvs-cli config show` - Show configuration
- `jvs-cli history` - List conversations

## Configuration

Config file: `~/.jvs-cli/config.json`

```json
{
  "api_base_url": "https://api.example.com/v1",
  "login_code": "your_login_code",
  "display": {
    "theme": "claude_dark",
    "live_mode": true
  }
}
```

## Requirements

- Python 3.10+
- OpenAI-compatible API endpoint

## License

Apache License 2.0
