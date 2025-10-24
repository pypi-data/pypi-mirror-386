# Aii — AI-Powered Terminal Assistant

**Aii** (pronounced *"eye"*) is your intelligent command-line companion that brings AI directly into your terminal through natural language.

**One CLI. 39 AI Functions + 25 Content Prompts. Multiple LLM Providers.**

Stop context-switching between your terminal and ChatGPT. Get instant AI assistance for git commits, code generation, translation, content writing, shell automation, and analysis—all without leaving your terminal.

[![PyPI version](https://badge.fury.io/py/aiiware-cli.svg)](https://pypi.org/project/aiiware-cli/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ What Can Aii Do?

### 🔀 AI Git Workflows
```bash
# Smart commit messages
aii run git commit
# → Analyzes changes → Generates conventional commit

# Create pull requests
aii run git pr
# → Analyzes commits → Generates PR → Creates on GitHub

# Smart branch names
aii run git branch "add user authentication"
# → feature/add-user-authentication
```

### 💻 Code Generation
```bash
aii create a python function to validate emails
# → Complete function with typing, docstrings, tests
```

### 🌍 Translation
```bash
aii translate "hello world" to spanish
# → "hola mundo"
```

### 📝 Content Writing
```bash
aii write professional email declining meeting
# → Polished, contextual draft

aii write tweet about launching Aii CLI
# → Engaging product launch tweet
```

### 🐚 Shell Automation
```bash
aii find files larger than 100MB
# → Shows safe command + explanation
```

### 🧠 Analysis & Research
```bash
aii explain "how do transformers work"
# → Clear explanation with web research

aii "summarize the README.md file"
# → Key points extracted from file
```

---

## 🚀 Quick Start

### Installation

```bash
# With uv (recommended)
uv tool install aiiware-cli

# Or with pip
pip install aiiware-cli

# Verify installation
aii --version
```

### Setup

```bash
# Interactive setup wizard (2 minutes)
aii config init

# Choose your LLM provider:
#  1. Anthropic Claude (Sonnet, Opus, Haiku)
#  2. OpenAI GPT (GPT-4o, GPT-4 Turbo)
#  3. Google Gemini (2.5 Flash, 2.0 Pro)

# Verify configuration
aii doctor
```

**Get API Keys:**
- **Claude**: [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)
- **Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### First Commands

```bash
# Try these examples:
aii translate "hello" to french
aii "what is the current directory"
aii run git commit  # (after git add .)
aii                 # Interactive mode (just type 'aii')
```

---

## 📋 Core Features

### 🎯 Natural Language Interface
Just describe what you want—no commands to memorize:
- **39 AI Functions** + **25 Content Prompts** across multiple categories
- **Multiple LLM Providers**: Claude, GPT, Gemini
- **Smart Confirmations**: Safe by default, asks only when needed
- **Session Memory**: Multi-turn conversations

### 🛠️ Developer Tools
- **Git Integration**: Commits, PRs, branch naming
- **GitHub API Access**: Via MCP (Model Context Protocol)
- **Code Generation**: Language-agnostic with best practices
- **Shell Safety**: Dangerous commands require confirmation

### 📝 Content Tools
- **Translation**: 100+ languages with context
- **Writing Assistant**: Emails, blogs, social media
- **Summarization**: Extract key points from documents
- **Prompt Library** (v0.6.1): 25 ready-to-use prompts for common tasks

### 📚 Prompt Library (New in v0.6.1)

**Generate professional content in seconds** with 25 ready-to-use prompts.

```bash
# Launch a product on Twitter
aii prompt use tweet-launch "launching Aii CLI with 25 content prompts"
# → 🚀 Engaging product launch tweet ready to post

# Write your daily standup
aii prompt use daily-standup "yesterday: fixed bugs, today: adding features, blockers: none"
# → Yesterday: ... Today: ... Blockers: ...

# Create a blog outline
aii prompt use blog-outline "Getting Started with AI for developers"
# → Complete blog structure with introduction, sections, takeaways

# Generate PR description
aii prompt use pr-description "add prompt library with 25 prompts and 4 commands"
# → Professional PR description with summary and test plan
```

**Discover Prompts:**
```bash
aii prompt list                    # Browse all 25 prompts
aii prompt list --category social  # Filter by category
aii prompt show tweet-launch       # View details & variables
```

**25 Ready-to-Use Prompts:**
- **Business** (4): Daily standups, incident reports, meeting notes, professional emails
- **Content** (4): Blog outlines & intros, newsletters, landing pages
- **Development** (7): PR descriptions, release notes, commit messages, code reviews, bug reports, API docs, architecture docs
- **Social** (5): Tweet launches, LinkedIn posts, Instagram captions, thread builders, general posts
- **Marketing** (2): Product announcements, feature highlights
- **Productivity** (3): Task lists, brainstorming, dictionaries

**Create Custom Prompts:**
Save your own prompts in `~/.aii/prompts/` with YAML format and natural language input for instant reuse.

### ⚙️ Platform Features
- **Unified Server**: One AI instance shared across terminal windows and VSCode
- **Real-Time Streaming**: 60-80% faster perceived speed
- **Cost Tracking**: Transparent pricing per request
- **Usage Analytics**: Track function usage and costs
- **Shell Autocomplete**: Tab completion for bash/zsh/fish

---

## 🎨 Advanced Usage

### Interactive Mode

```bash
# Start interactive session (just type 'aii')
aii

# Use AI naturally
> translate "hello" to spanish
hola

> explain how LLMs work
[explanation...]

> generate python code for email validation
[code generated...]
```

### MCP Server Management

```bash
# Browse available MCP servers
aii mcp catalog

# Install GitHub integration
aii mcp install github

# Use GitHub tools
aii "list my repositories"
aii "create issue in myrepo about adding tests"
```

### Configuration

```bash
# Switch LLM provider
aii config provider anthropic

# Switch model
aii config model claude-haiku-4-5

# View all available models
aii config model

# Configure web search
aii config web-search enable
```

---

## 📊 Output Modes

Aii uses smart output modes based on the task:

| Mode | When | Example |
|------|------|---------|
| **CLEAN** | Quick queries (67% of functions) | `aii translate hello` → Just "hola" |
| **STANDARD** | Status checks (21% of functions) | `aii git status` → Status + summary |
| **THINKING** | Complex operations (12% of functions) | `aii commit` → Full reasoning + metrics |

**Override per command:**
```bash
aii translate hello --thinking  # Show full reasoning
aii commit --clean              # Minimal output
```

---

## 🔌 Using Aii with IDEs

Aii runs a background server that lets you use AI from both your terminal and IDEs like VSCode.

### Managing the Server

```bash
# Start server in daemon mode (background)
aii serve start --daemon

# Start in foreground (see logs)
aii serve start

# Check server status
aii serve status
# → Shows: Process, Health, Address, Uptime, Version

# Stop server
aii serve stop

# Restart server
aii serve restart
```

### Connecting to Different Servers

```bash
# Use a different port
aii translate hello --host localhost:16170

# Start server on custom port (must start manually)
aii serve start --daemon --port 16170
```

**Using with VSCode:** The [Aii VSCode Extension](https://marketplace.visualstudio.com/items?itemName=aiiware.aii) automatically connects to your Aii server. Both CLI and VSCode share the same AI instance, so you can seamlessly switch between them.

---

## 🆘 Troubleshooting

### Health Check

```bash
# Check your configuration
aii doctor

# Check server status
aii serve status

# Together these verify:
# ✓ Configuration files
# ✓ LLM provider setup
# ✓ Server health and uptime
```

### Common Issues

**"No LLM provider configured"**
```bash
aii config init  # Run setup wizard
```

**"API key invalid"**
```bash
aii config provider anthropic  # Reconfigure provider
```

**"Command not found: aii"**
```bash
# Ensure uv tool path is in PATH
export PATH="$HOME/.local/bin:$PATH"  # Add to ~/.bashrc or ~/.zshrc
```

---

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

---

## 💰 Pricing

Aii uses your own API keys, so you pay only for actual LLM usage. Prices shown per million tokens (MTok).

### All Supported Models

| Provider | Model ID | Input | Output | Cost/10k* | Updated | Notes |
|----------|----------|-------|--------|-----------|---------|-------|
| **Google** | `gemini-2.0-flash-lite-001` 🥇 | $0.075 | $0.30 | **$0.0023** | 2025-10-16 | Cheapest |
| **Google** | `gemini-2.5-flash-lite` 🥈 | $0.10 | $0.40 | **$0.0030** | 2025-10-16 | Very cost-efficient |
| **Google** | `gemini-2.0-flash-001` 🥉 | $0.10 | $0.40 | **$0.0030** | 2025-10-16 | Fast |
| **OpenAI** | `gpt-4o-mini` | $0.15 | $0.60 | $0.0045 | 2025-10-16 | Verified |
| **OpenAI** | `gpt-3.5-turbo` | $0.50 | $1.50 | $0.0125 | 2025-10-16 | Verified |
| **Google** | `gemini-2.5-flash` | $0.30 | $2.50 | $0.0155 | 2025-10-16 | Recommended ⭐ |
| **OpenAI** | `gpt-5-nano` | $1.00 | $3.00 | $0.0250 | 2025-10-16 | Estimated |
| **Anthropic** | `claude-3-5-haiku-20241022` | $0.80 | $4.00 | $0.0280 | 2025-10-16 | Verified |
| **Anthropic** | `claude-haiku-4-5` | $1.00 | $5.00 | $0.0350 | 2025-10-16 | Near-frontier ⭐ |
| **OpenAI** | `gpt-4.1-mini` | $2.00 | $6.00 | $0.0500 | 2025-10-16 | Estimated |
| **Google** | `gemini-2.5-pro` | $1.25 | $10.00 | $0.0625 | 2025-10-16 | Verified |
| **OpenAI** | `gpt-5-mini` | $3.00 | $9.00 | $0.0750 | 2025-10-16 | Estimated |
| **Anthropic** | `claude-sonnet-4-5-20250929` | $3.00 | $15.00 | $0.1050 | 2025-10-16 | Recommended ⭐ |
| **Anthropic** | `claude-sonnet-4-20250514` | $3.00 | $15.00 | $0.1050 | 2025-10-16 | Verified |
| **Anthropic** | `claude-3-7-sonnet-20250219` | $3.00 | $15.00 | $0.1050 | 2025-10-16 | Verified |
| **OpenAI** | `gpt-4.1` | $5.00 | $15.00 | $0.1250 | 2025-10-16 | Estimated |
| **OpenAI** | `gpt-4o` | $5.00 | $15.00 | $0.1250 | 2025-10-16 | Verified |
| **OpenAI** | `gpt-5` | $10.00 | $30.00 | $0.2500 | 2025-10-16 | Estimated |
| **OpenAI** | `gpt-4-turbo` | $10.00 | $30.00 | $0.2500 | 2025-10-16 | Verified |
| **Anthropic** | `claude-opus-4-1-20250805` | $15.00 | $75.00 | $0.5250 | 2025-10-16 | Most capable |
| **OpenAI** | `gpt-4` | $30.00 | $60.00 | $0.6000 | 2025-10-16 | Legacy |

**\*Cost based on 10k input + 5k output tokens (typical Aii command)**

🥇🥈🥉 **Top 3 Cheapest Models** | **Verified** = Confirmed from official docs | **Estimated** = GPT-5/4.1 not yet released

**Track your usage:**
```bash
aii stats  # View function usage and costs
```

---

## 🤝 Support

**Need Help?**
- 📖 Check the [CHANGELOG](CHANGELOG.md) for recent updates
- 🩺 Run `aii doctor` to diagnose configuration issues
- 💡 Suggest features or report bugs via feedback

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **PyPI**: <https://pypi.org/project/aiiware-cli/>
- **VSCode Extension**: <https://marketplace.visualstudio.com/items?itemName=aiiware.aii>

---

**Made with ❤️ by the AiiWare team**

*Stay in your terminal. Get AI assistance. Maintain flow state.*
