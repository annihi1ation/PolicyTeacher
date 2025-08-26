# Teaching Agent CLI

A pure command-line interface version of the Chinese teaching agent for ABC kids.

## Features

- Interactive Chinese teaching sessions
- Emotion tracking and adaptive responses
- Language level assessment and progression
- Dynamic teaching policy generation
- Word knowledge management

## Usage

```bash
python cli_teaching_agent.py
```

## Architecture

- `cli_teaching_agent.py` - Main CLI interface
- `teaching_agent_core.py` - Core teaching agent logic (without web dependencies)
- `prompts.py` - Teaching prompts and templates
- `models.py` - Data models and types
- `utils.py` - Utility functions

## Dependencies

The CLI version removes all web-related dependencies and focuses on terminal-based interaction.
