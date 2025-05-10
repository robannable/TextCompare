# TextCompare

A web-based text editor for comparing and rewriting text, featuring side-by-side editing, markdown support, and AI-assisted rewriting powered by Ollama.

## Features

- **Dual-Column Interface**
  - Left column for new text
  - Right column for original text
  - Adjustable column widths
  - Synchronized scrolling option
  - Markdown preview support
  - Word count and last updated timestamps

- **File Management**
  - Organized folder structure for text pairs
  - Save and load text files
  - Automatic file listing
  - Markdown file support
  - File structure:
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

- **AI Integration**
  - Powered by Ollama LLM
  - Multiple model support
  - Adjustable terminal height
  - Commands for text manipulation:
    - `/rewrite` - Rewrite text more concisely
    - `/improve` - Enhance clarity and style
    - `/summarize` - Create brief summary
    - `/expand` - Add details and examples
  - Text reference commands:
    - `/old` - Reference original text
    - `/new` - Reference new text
    - `/both` - Reference both texts

- **Markdown Support**
  - Live markdown preview
  - Full markdown syntax support
  - Preserved formatting in AI operations

## Requirements

- Python 3.6+
- Flask
- Requests
- Ollama (optional, for AI features)

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd textcompare
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install Ollama for AI features:
   - Download from [ollama.com](https://ollama.com)
   - Install and start the Ollama service
   - Download a model (e.g., `llama3`)

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
   Or use the setup script:
   ```bash
   setup.bat
   ```

2. Open your browser to `http://127.0.0.1:5000`

3. Basic Usage:
   - Enter or paste text in either column
   - Adjust column widths by dragging the handle between columns
   - Use the file controls to save/load
   - Toggle markdown preview as needed
   - Enable sync scrolling if desired
   - Monitor word count and last updated timestamps

4. AI Features (requires Ollama):
   - Click "Connect" in the terminal
   - Select a model from the dropdown
   - Adjust terminal height by dragging the handle
   - Use commands or ask questions
   - Reference text using `/old`, `/new`, or `/both`

## Development

The application is built with:
- Flask for the backend
- Vanilla JavaScript for the frontend
- CSS for styling
- Ollama API for AI features

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as long as you provide attribution to the original author.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 