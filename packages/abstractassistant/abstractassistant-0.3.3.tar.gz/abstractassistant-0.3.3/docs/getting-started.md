# 🎯 Getting Started Guide

Complete user guide for AbstractAssistant - learn how to use all features effectively for your daily AI interactions.

**📚 Other Documentation**: [🏠 README](../README.md) | [📖 Installation](installation.md) | [🏗️ Architecture](architecture.md)

---

## 🚀 First Launch

### 1. Start the Application

Choose your preferred launch method:

#### 🍎 macOS App Bundle Users
- **Dock**: Click the AbstractAssistant icon in your Dock
- **Spotlight**: Press `⌘+Space`, search "AbstractAssistant", press Enter
- **Finder**: Open `/Applications/AbstractAssistant.app`

#### 🔧 Terminal Users
```bash
assistant
```

**💡 Tip**: Make sure you've completed the [📖 Installation Guide](installation.md) first!

### 2. Find the System Tray Icon
Look for the AbstractAssistant icon in your **macOS menu bar** (top-right corner, near the clock).

**🎨 Dynamic Icon States**:
- **🟢 Gentle Green Heartbeat**: Ready and waiting for your input
- **🔴 Fast Red Heartbeat**: Thinking, generating, or processing your request  
- **🔵 Gentle Blue Heartbeat**: Speaking (when voice mode is active)

The icon provides visual feedback about what AbstractAssistant is doing at any moment!

### 3. Open the Chat Interface
**Click the icon** to open the modern chat bubble interface.

### 4. Start Your First Conversation
- **Type your message** in the text area
- **Send**: Press `Enter` or click the blue send button (→)
- **New Line**: Press `Shift+Enter` to add a new line without sending
- **Wait for response**: The AI will process and respond to your query

## Main Interface

### Chat Bubble

The main interface is a sleek, dark-themed chat bubble that appears when you click the system tray icon.

#### Header Controls
- **✕ (Close)**: Closes the chat bubble (top-left)
- **Clear**: Starts a new conversation
- **Load**: Loads a saved conversation
- **Save**: Saves the current conversation
- **History**: Opens the conversation history viewer
- **🔊 (TTS Toggle)**: Enables/disables voice responses
- **READY**: Shows current AI status (Ready/Generating)

#### Main Area
- **Text Input**: Large text area for typing your messages
- **Send Button (→)**: Blue circular button to send messages
- **Provider Dropdown**: Select AI provider (LMStudio, OpenAI, etc.)
- **Model Dropdown**: Choose specific model for the selected provider
- **Token Counter**: Shows current/total tokens (e.g., "143 / 262k")

### System Tray Icon

The icon in your menu bar provides visual feedback:

- **Green (Steady)**: Ready for input
- **Red/Purple (Pulsing)**: AI is generating a response
- **Red (Steady)**: Error occurred

## Core Features

## 🤖 Provider and Model Selection

AbstractAssistant supports multiple AI providers through [AbstractCore](https://github.com/lpalbou/abstractcore):

### Local Providers (Privacy-First)

#### LMStudio (Recommended for Beginners)
- **Setup**: Install [LMStudio](https://lmstudio.ai/), download models, start server
- **Benefits**: 🔒 Full privacy, no API costs, works offline
- **Models**: Qwen, Llama, Mistral, and many more
- **How to**: See the [📖 Installation Guide](installation.md#models--providers-setup)

#### Ollama (Command Line)
- **Setup**: `brew install ollama`, then `ollama pull qwen2.5:latest`
- **Benefits**: 🔒 Full privacy, powerful local models
- **Models**: Qwen, Llama, Mistral, and more

#### MLX (Apple Silicon Optimized)
- **Setup**: Advanced setup for Apple Silicon Macs
- **Benefits**: 🔒 Full privacy, optimized for M1/M2/M3/M4 chips
- **Models**: MLX-optimized versions of popular models

#### HuggingFace (Open Source)
- **Setup**: Advanced setup with Transformers library
- **Benefits**: 🔒 Full privacy, vast model selection
- **Models**: Thousands of open-source models

### Cloud Providers (API Required)

#### OpenAI
- **Setup**: Set `OPENAI_API_KEY` environment variable
- **Models**: GPT-4o, GPT-4, GPT-3.5-turbo, and more
- **Benefits**: High quality, fast responses

#### Anthropic
- **Setup**: Set `ANTHROPIC_API_KEY` environment variable
- **Models**: Claude 3.5 Sonnet, Claude 3 Opus, and more
- **Benefits**: Excellent reasoning, long context

## 🎙️ Voice Features

AbstractAssistant includes high-quality text-to-speech powered by [AbstractVoice](https://github.com/lpalbou/abstractvoice):

### Enabling Voice Mode
1. **Click the TTS Toggle** (🔊 icon) in the chat interface
2. **Voice Responses**: AI responses will be spoken aloud automatically
3. **Optimized Responses**: AI uses shorter, more conversational responses
4. **Natural Speech**: High-quality voice synthesis with VITS models

### Voice Controls
- **🔊 Toggle On/Off**: Click the speaker icon to enable/disable voice
- **⏹️ Stop Speaking**: Click the system tray icon while AI is speaking
- **🎛️ Simple Setup**: No configuration required - works out of the box

### Voice Features
- **🗣️ Natural Speech**: Advanced voice synthesis technology
- **⚡ Real-Time**: Optimized for conversational AI responses
- **🎯 Smart Prompting**: AI adapts responses for voice interaction
- **🔧 Zero Config**: Automatically installed and configured

**🔗 Learn More**: [AbstractVoice Repository](https://github.com/lpalbou/abstractvoice)

### Session Management

Keep track of your conversations:

#### Save Conversations
1. Click **Save** button
2. Choose filename and location
3. Conversation saved as JSON file

#### Load Conversations
1. Click **Load** button
2. Select saved conversation file
3. Context restored for continued conversation

#### View History
1. Click **History** button
2. Browse all messages in iPhone Messages-style interface
3. User messages (blue) and AI responses (black) with timestamps
4. Markdown rendering for AI responses

#### Clear Session
- Click **Clear** to start fresh conversation
- Previous context is lost

## Keyboard Shortcuts

### In Chat Bubble
- **Enter**: Send message
- **Shift+Enter**: Add new line (without sending)
- **Escape**: Close chat bubble
- **Tab**: Navigate between controls

### System-wide
- **Click Tray Icon**: Open/close chat bubble
- **Double-click Tray Icon**: Force open (even during TTS)

## Advanced Usage

### Configuration

Create `~/.config/abstractassistant/config.toml`:

```toml
[ui]
theme = "dark"
always_on_top = true

[llm]
default_provider = "lmstudio"
default_model = "qwen/qwen3-next-80b"
max_tokens = 128000
temperature = 0.7

[system_tray]
icon_size = 64
```

### Command Line Options

```bash
# Use specific provider and model
assistant --provider openai --model gpt-4o

# Enable debug mode
assistant --debug

# Use custom config file
assistant --config /path/to/config.toml

# Show help
assistant --help
```

### Environment Variables

Set up API keys:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"

# For session persistence
export ABSTRACTASSISTANT_SESSION_DIR="~/Documents/AI_Sessions"
```

## Tips and Best Practices

### Effective Prompting

#### For General Use
- Be specific and clear in your requests
- Provide context when needed
- Use follow-up questions to refine responses

#### For Voice Mode
- Ask shorter questions
- Expect conversational responses
- Use it for quick information or brainstorming

#### For Coding
- Specify the programming language
- Provide relevant context or error messages
- Ask for explanations along with code

### Provider Selection

#### Choose LMStudio When:
- Privacy is important
- You want to avoid API costs
- Working with sensitive data
- Need offline capability

#### Choose OpenAI When:
- Need highest quality responses
- Working on complex reasoning tasks
- Speed is important
- Using latest models

#### Choose Anthropic When:
- Need excellent reasoning capabilities
- Working with long documents
- Want helpful, harmless responses
- Need nuanced understanding

### Session Management

#### Save Important Conversations
- Research sessions with valuable information
- Complex problem-solving discussions
- Creative writing or brainstorming sessions

#### Use Clear for:
- Switching topics completely
- Starting fresh after errors
- Privacy (clearing sensitive discussions)

#### Load Previous Sessions When:
- Continuing complex projects
- Referencing previous discussions
- Building on earlier work

## Troubleshooting

### Common Issues

#### Chat Bubble Not Appearing
- Check if icon is in menu bar
- Try clicking the icon again
- Run with `--debug` to see error messages

#### No Response from AI
- Check internet connection (for cloud providers)
- Verify API keys are set correctly
- Try switching to a different provider
- Check token limits

#### Voice Not Working
- Ensure AbstractVoice is installed: `pip install abstractvoice`
- Install espeak-ng for best quality: `brew install espeak-ng`
- Check system audio settings
- Try toggling TTS off and on

#### Provider Not Available
- For LMStudio: Ensure local server is running
- For Ollama: Check if service is started (`ollama serve`)
- For cloud providers: Verify API keys and internet connection

### Debug Mode

Run with debug mode for detailed information:

```bash
assistant --debug
```

This shows:
- Configuration loading
- Provider discovery
- Model loading
- Request/response details
- Error messages with stack traces

### Getting Help

1. **Check the logs**: Debug mode provides detailed information
2. **Review configuration**: Ensure settings are correct
3. **Test providers**: Try different providers to isolate issues
4. **GitHub Issues**: Report bugs or request features

## Integration Ideas

### Workflow Integration

#### Writing Assistant
- Use for brainstorming ideas
- Get help with grammar and style
- Generate outlines and structures

#### Coding Helper
- Debug error messages
- Get code explanations
- Generate boilerplate code
- Review and optimize code

#### Research Tool
- Quick fact checking
- Summarize complex topics
- Generate research questions
- Explore different perspectives

#### Creative Partner
- Brainstorm creative ideas
- Get feedback on projects
- Generate variations and alternatives
- Overcome creative blocks

### Shell Integration

Add to your shell profile:

```bash
# Quick aliases
alias ai="assistant"
alias ai-debug="assistant --debug"

# Provider-specific shortcuts
alias ai-gpt4="assistant --provider openai --model gpt-4o"
alias ai-claude="assistant --provider anthropic --model claude-3-5-sonnet-20241022"
alias ai-local="assistant --provider lmstudio"
```

---

## 🎯 Next Steps

**Ready to use AbstractAssistant like a pro!** Here's what to explore next:

### Advanced Usage
- **⚙️ Configuration**: Customize settings and create shortcuts
- **🤖 Try Different Models**: Experiment with various AI providers
- **🎙️ Voice Mode**: Enable voice responses for natural conversations
- **📚 Session Management**: Save important conversations for later

### Need Help?
- **🆘 Troubleshooting**: Check the [📖 Installation Guide](installation.md) for common issues
- **🏗️ Technical Details**: See the [🏗️ Architecture Guide](architecture.md) for development info
- **🏠 Overview**: Return to the [🏠 Main README](../README.md)

## 🔗 Resources

- **📋 GitHub Repository**: [AbstractAssistant](https://github.com/lpalbou/abstractassistant)
- **🐍 PyPI Package**: [AbstractAssistant on PyPI](https://pypi.org/project/abstractassistant/)
- **🧠 AbstractCore**: [Universal LLM Interface](https://github.com/lpalbou/abstractcore)
- **🗣️ AbstractVoice**: [Text-to-Speech Engine](https://github.com/lpalbou/abstractvoice)
