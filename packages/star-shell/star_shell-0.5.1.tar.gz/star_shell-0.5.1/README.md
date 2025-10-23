# ⭐ Star Shell

An AI-powered command line assistant that generates and executes shell commands using natural language.

## Features

- 🤖 **AI-Powered**: Uses OpenAI GPT or Google Gemini to understand your requests
- 💬 **Interactive Terminal**: Natural conversation with command execution
- 🧠 **Smart Responses**: AI decides whether to run commands or provide information
- 🔄 **Multi-Command Support**: Execute multiple commands in sequence automatically
- 🧠 **Adaptive Planning**: Gemini Thinking mode creates plans and adapts based on real execution results
- 🛡️ **Safety First**: Built-in command safety checks and confirmations
- 🎯 **Context Aware**: Understands your current directory and system environment
- 🔒 **Secure**: Encrypted API key storage
- 🎨 **Beautiful Output**: Rich formatting and syntax highlighting
- ⚡ **Streamlined UX**: Automatic initialization checks and intuitive commands

## Installation

```bash
pip install star-shell
```

## Quick Start

1. **First time setup**:
   ```bash
   star-shell init
   ```
   Choose your AI backend (OpenAI or Gemini) and provide your API key.

2. **Start the interactive terminal**:
   ```bash
   star-shell run
   ```
   This opens an AI-powered terminal where you can chat and get commands executed.

3. **Switch modes anytime**:
   ```bash
   star-shell mode
   ```
   Change between OpenAI, Gemini Pro, Gemini Flash, or Gemini Thinking modes.

4. **Or ask for specific commands**:
   ```bash
   star-shell ask "list all Python files in this directory"
   ```

## Commands

- `star-shell` - Shows status and current mode
- `star-shell init` - Set up your AI backend and API keys  
- `star-shell run` - Start the interactive AI terminal
- `star-shell mode` - Switch between different AI backends/modes
- `star-shell ask "your request"` - Generate a specific command

## Backend Options

During initialization, you can choose from:
1. **OpenAI GPT-3.5 Turbo** - Reliable, requires API key
2. **Gemini Pro** - Google's flagship model, requires API key  
3. **Gemini Flash** - Faster Google model, requires API key
4. **Gemini Thinking** - Adaptive planning with step-by-step execution, requires API key
5. **Secret option** - For special access (contact developer)

## Supported AI Backends

- **OpenAI GPT-3.5 Turbo** - Requires OpenAI API key
- **Google Gemini Pro** - Requires Google AI API key
- **Google Gemini Flash** - Requires Google AI API key (faster, optimized model)
- **Google Gemini Thinking** - Adaptive multi-step execution with planning (requires Google AI API key)
- **Secret Backend** - Free access for select users (no API key needed)

## Safety Features

Star Shell includes built-in safety checks for potentially dangerous commands:
- Warns about destructive operations (rm, format, etc.)
- Confirms before executing system-level changes
- Provides clear descriptions of what commands do

## Examples

### Interactive Terminal Mode
```bash
star-shell run

⭐ > create a new directory called projects
# AI will generate and offer to execute: mkdir projects

⭐ > create a directory and navigate to it
# AI will offer to execute multiple commands:
# 1. mkdir new_directory
# 2. cd new_directory

⭐ > set up a complete Python project (Gemini Thinking mode)
# AI creates adaptive plan:
# 1. Create project directory
# 2. Initialize virtual environment  
# 3. Create requirements.txt
# 4. Set up project structure
# Then executes each step, adapting based on results

⭐ > what's the difference between git merge and rebase?
# AI will explain the concepts in natural language

⭐ > help
# Shows available commands and examples
```

### Direct Command Mode
```bash
# File operations
star-shell ask "create a backup of my config files"

# System information  
star-shell ask "show me disk usage"

# Development tasks
star-shell ask "start a Python web server on port 8000"
```

## Requirements

- Python 3.8+
- OpenAI API key OR Google AI API key

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.