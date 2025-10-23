# Codicent CLI

Codicent CLI is a command-line interface for interacting with the Codicent API. It provides both one-shot command execution and interactive chat sessions with comprehensive error handling and user-friendly features.

## Features

- **One-shot mode**: Execute single commands and get responses
- **Interactive mode**: Continuous chat sessions with conversation tracking
- **Message types**: Support for regular chat and @-prefixed info messages
- **Input flexibility**: Command arguments, stdin pipes, or interactive prompts
- **Rich output**: Markdown-formatted responses with beautiful terminal UI
- **Error handling**: Comprehensive error messages and graceful failure handling
- **Logging**: Configurable logging levels for debugging

## Installation

### Prerequisites

- Python 3.6 or higher
- `pip` (Python package installer)

### Quick Installation

```bash
# Install from PyPI
pip install codicent-py codicent-cli
```

### Development Installation

#### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/izaxon/codicent-cli.git
   cd codicent-cli
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

### Direct Installation from GitHub

You can also install directly from GitHub:

```bash
# Install the latest version
pip install git+https://github.com/izaxon/codicent-cli.git

# Install a specific version
pip install git+https://github.com/izaxon/codicent-cli.git@v0.4.8
```

## Usage

### Basic Setup

1. Set the `CODICENT_TOKEN` environment variable with your Codicent API token:
   ```bash
   export CODICENT_TOKEN="YOUR_API_TOKEN"
   ```

### Command Options

```
codicent [OPTIONS] [QUESTION]

OPTIONS:
  -t, --interactive    Start interactive chat mode
  -h, --help          Show help message
  -v, --version       Show version information
  --verbose           Enable verbose logging
  --quiet             Suppress non-essential output
```

### Examples

**One-shot questions:**
```bash
codicent "What can you help me with?"
codicent "Explain Python decorators"
```

**Interactive mode:**
```bash
codicent -t
# or
codicent --interactive
```

**Piped input:**
```bash
echo "What is machine learning?" | codicent
codicent < questions.txt
cat code.py | codicent "Review this code"
```

**Info messages (@ prefix):**
```bash
codicent "@mention This is an info message"
```

**With logging:**
```bash
codicent --verbose "Debug this issue"
codicent --quiet "Silent operation"
```

## Interactive Mode

In interactive mode, you can have ongoing conversations with enhanced visual clarity:

```
$ codicent -t
🤖 Codicent CLI Interactive Mode
Type your questions or use Ctrl+C to exit.
Prefix with @ for info messages.
──────────────────────────────────────────────────
¤ What is Python?

Python is a high-level, interpreted programming language known for its 
simplicity and readability. It was created by Guido van Rossum and first 
released in 1991.

Key features:
• Easy to learn and use
• Extensive standard library
• Cross-platform compatibility
• Strong community support
──────────────────────────────────────────────────
¤ Can you give me an example?

Here's a simple Python example:

# Hello World in Python
print("Hello, World!")

# Working with variables
name = "Alice"
age = 25
print(f"My name is {name} and I am {age} years old.")

Python's syntax is clean and intuitive!
──────────────────────────────────────────────────
¤ @mention Save this conversation
✅ Message posted successfully.
──────────────────────────────────────────────────
¤ ^C
👋 Goodbye!
```

**Visual Features:**
- **Colored messages**: User input appears in cyan, bot responses in green
- **Clean prompting**: Original `¤` prompt character maintained
- **Visual separators**: Clear lines between conversations
- **Rich formatting**: Markdown responses with syntax highlighting
- **Status indicators**: Animated thinking indicators and success messages
- **Emojis**: Friendly visual cues throughout the interface

## Error Handling

The CLI provides helpful error messages for common issues:

- **Missing token**: Clear instructions on setting up `CODICENT_TOKEN`
- **Network errors**: Graceful handling of connection issues
- **API errors**: Detailed error messages from the Codicent API
- **Input validation**: Prevents empty or overly long inputs
- **Keyboard interrupts**: Clean exit handling

## Development

### Running Tests

```bash
python -m pytest test_app.py -v
```

### Project Structure

- `app.py` - Main application logic (single-file architecture)
- `test_app.py` - Comprehensive test suite
- `setup.py` - Package configuration
- `requirements.txt` - Dependencies (now uses PyPI packages)

### Dependencies

- **codicent-py**: Core API client for Codicent services (now available on PyPI)
- **rich**: Terminal formatting, markdown rendering, and animations

## Troubleshooting

### Common Issues

1. **"CODICENT_TOKEN environment variable is not set"**
   - Set the token: `export CODICENT_TOKEN="your_token"`
   - Verify it's set: `echo $CODICENT_TOKEN`

2. **"Network error: Unable to connect to Codicent API"**
   - Check your internet connection
   - Verify the Codicent API is accessible
   - Try again with `--verbose` for more details

3. **"Failed to initialize Codicent API client"**
   - Verify your token is valid
   - Check if the codicent-py package is properly installed

### Getting Help

- Use `codicent --help` for usage information
- Use `codicent --verbose` for detailed logging
- Check the [Codicent documentation](https://github.com/izaxon/codicent-py) for API details

## License

This project is licensed under the MIT License.
