# TextCompare

A powerful web-based text editor for comparing and rewriting text, featuring side-by-side editing, markdown support, and AI-assisted rewriting powered by **Anthropic Claude** and **Ollama**.

## ✨ Features

### 📝 Dual-Column Text Editor
- **Side-by-side interface** - Left column for new text, right column for original text
- **Adjustable column widths** - Drag the resize handle between columns
- **Synchronized scrolling** - Optional sync scrolling between columns
- **Markdown preview** - Live markdown rendering with full syntax support
- **Word count & timestamps** - Track word count and last updated time for both columns
- **Auto-save functionality** - Save and load text pairs with organized folder structure

### 🤖 AI Integration (Dual Provider Support)

#### Anthropic Claude (Cloud-based)
- **Latest Claude 4.x Models (2025):**
  - `claude-sonnet-4-5-20250929` (recommended - 1M context window)
  - `claude-opus-4-1-20250805` (most powerful for agentic tasks)
  - `claude-sonnet-4-20250514` (Claude Sonnet 4)
  - `claude-3-7-sonnet-20250219` (hybrid AI reasoning model)
  - `claude-3-5-haiku-20241022` (fast and efficient)
  - `claude-3-haiku-20240307` (legacy fast model)
- **Streaming support** - See responses in real-time
- **Token usage tracking** - Monitor input/output tokens
- **Advanced temperature controls**
- **Extended context windows** (up to 1M tokens with beta header)

#### Ollama (Local)
- **Local LLM execution** - Run models on your own hardware
- **Privacy-focused** - No data leaves your machine
- **Multiple model support** - llama3.1, mistral, codellama, etc.
- **Streaming responses**
- **No API key required**

### 🎨 AI Terminal Features
- **Interactive terminal interface** - Command-line style AI interaction
- **Provider switching** - Easily switch between Anthropic and Ollama
- **Model selection** - Choose from available models
- **Streaming toggle** - Enable/disable response streaming
- **Adjustable terminal height** - Drag to resize
- **Command system:**
  - `/help` - Show available commands
  - `/models` - List available models
  - `/health` - Check service status
  - `/rewrite` - Rewrite text more concisely
  - `/improve` - Enhance clarity and style
  - `/summarize` - Create brief summary
  - `/expand` - Add details and examples
- **Text references:**
  - `/old` - Reference original text in queries
  - `/new` - Reference new text in queries
  - `/both` - Reference both texts in queries

### 📁 File Management
- **Organized storage** - Each text pair stored in its own folder
- **Markdown file support** - All files saved as .md format
- **Quick load** - Select from dropdown to load saved files
- **Auto-refresh** - File list updates automatically

## 🚀 Installation

### Prerequisites
- Python 3.8+
- (Optional) Anthropic API key for Claude models
- (Optional) Ollama for local LLM support

### Step 1: Clone the Repository
```bash
git clone https://github.com/robannable/TextCompare.git
cd TextCompare
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key (optional)
# ANTHROPIC_API_KEY=your_api_key_here
```

### Step 4: (Optional) Install Ollama
For local AI features:
1. Download Ollama from [ollama.com](https://ollama.com)
2. Install and start the Ollama service
3. Download a model:
   ```bash
   ollama pull llama3.1
   ```

## 💻 Usage

### Starting the Application
```bash
python app.py
```

Or use the setup script (Windows):
```bash
setup.bat
```

Then open your browser to: **http://127.0.0.1:5000**

### Basic Workflow

1. **Enter or paste text** in either column
2. **Choose an AI provider:**
   - Select "Anthropic Claude" for cloud-based models (requires API key)
   - Select "Ollama (Local)" for local models (requires Ollama installation)
3. **Select a model** from the dropdown
4. **Use AI commands:**
   - Type `/rewrite` to rewrite the original text
   - Type `/improve` to enhance text quality
   - Type `/summarize` for a summary
   - Type `/expand` to add more details
   - Or ask questions directly: "What is the main theme of /old?"
5. **Save your work** by entering a filename and clicking Save
6. **Load previous work** from the file dropdown

### Advanced Features

#### Synchronized Scrolling
Enable "Sync Scrolling" to keep both columns aligned when scrolling.

#### Markdown Preview
Toggle "Markdown Preview" to see rendered markdown instead of raw text.

#### Resize Columns
Drag the vertical handle between columns to adjust width.

#### Resize Terminal
Drag the horizontal handle above the terminal to adjust height.

#### Minimize Terminal
Click the ▲/▼ button to minimize/maximize the terminal.

## 📊 Performance Improvements

### Caching
- **Model list caching** - 5-minute TTL reduces API calls
- **Efficient updates** - Only fetch when needed

### Streaming
- **Real-time responses** - See output as it's generated
- **Better UX** - Visual feedback during long operations
- **Reduced perceived latency**

### Error Handling
- **Graceful degradation** - Service works even if one provider is unavailable
- **Clear error messages** - Helpful feedback for troubleshooting
- **Retry logic** - Built-in timeout and connection handling

## 🏗️ Architecture

### Backend (Flask)
```
app.py
├── Core Routes (/, /save, /load, /list_files)
├── Ollama Endpoints (/ollama, /ollama/stream, /list_ollama_models)
├── Anthropic Endpoints (/anthropic, /anthropic/stream, /list_anthropic_models)
├── Unified Endpoints (/list_models, /generate)
└── Health Check (/health)
```

### Frontend (Vanilla JavaScript)
```
static/script.js
├── File Management
├── Editor Controls (sync scroll, markdown preview)
├── AI Provider Management
├── Streaming & Non-streaming API calls
├── Terminal Interface
└── Resize Handlers
```

### Data Structure
```
data/
├── text-pair-1/
│   ├── text-pair-1_original.md
│   └── text-pair-1_new.md
├── text-pair-2/
│   ├── text-pair-2_original.md
│   └── text-pair-2_new.md
└── ...
```

## 🔑 API Configuration

### Anthropic API Key
Get your API key from [Anthropic Console](https://console.anthropic.com/)

Add to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### Ollama Configuration
Default: `http://localhost:11434/api`

To change, edit `.env`:
```env
OLLAMA_BASE_URL=http://your-ollama-server:11434/api
```

## 🛠️ Development

### Project Structure
```
TextCompare/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── setup.bat             # Windows setup script
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── styles.css        # CSS styles
│   └── script.js         # Frontend JavaScript
└── data/                 # User data (gitignored)
```

### Adding New Models

#### For Anthropic
Edit `app.py`, line ~405:
```python
models = [
    "claude-sonnet-4-5-20250929",
    "your-new-model-id",
    # ... other models
]
```

#### For Ollama
Models are auto-detected from your Ollama installation. Just pull the model:
```bash
ollama pull model-name
```

## 🔒 Security

- **API keys** stored in `.env` (gitignored)
- **Local data** never sent to external services (when using Ollama)
- **No telemetry** or tracking
- **HTTPS ready** - works with reverse proxies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as long as you provide attribution to the original author.

## 🐛 Known Issues

- Markdown preview uses simple regex-based rendering (not a full parser)
- Very large texts (>100K words) may cause performance issues
- Streaming may not work with some older browsers

## 📚 Changelog

### Version 2.0.0 (Latest)
- ✨ Added Anthropic Claude API integration
- ✨ Added streaming support for both providers
- ✨ Dual provider support (Anthropic + Ollama)
- ✨ Model caching for improved performance
- ✨ Token usage tracking for Anthropic
- ✨ Health check endpoint
- ✨ Enhanced error handling
- 🔧 Updated to latest Anthropic API (Messages API)
- 🔧 Improved UI with provider selection
- 🔧 Better loading indicators
- 📚 Complete documentation rewrite

### Version 1.0.0
- Initial release with Ollama support
- Basic text comparison features
- Markdown preview
- File management

## 💡 Tips & Tricks

1. **Use streaming for long texts** - Enable streaming to see responses in real-time
2. **Reference texts in queries** - Use /old, /new, or /both to reference specific texts
3. **Combine models** - Use Anthropic for complex tasks, Ollama for quick rewrites
4. **Save frequently** - Work is not auto-saved, remember to click Save
5. **Check /health** - Use `/health` command to verify both services are available

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the `/help` command output

## 🙏 Acknowledgments

- **Anthropic** for Claude AI models
- **Ollama** for local LLM support
- **Flask** web framework
- **GitHub** community for contributions
