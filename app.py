from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import requests
import json
import threading
import time

app = Flask(__name__)

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "llama3.1"  # Change to your preferred model

@app.route('/')
def index():
    files = []
    for item in os.listdir('data'):
        item_path = os.path.join('data', item)
        if os.path.isdir(item_path):
            # Check if this is a valid text pair folder
            original_filename = f"{item}_original.md"
            if os.path.exists(os.path.join(item_path, original_filename)):
                files.append(item + '.md')  # Add .md extension for consistency
    return render_template('index.html', 
                         title="TextCompare",
                         files=files,
                         current_file=None)

@app.route('/save', methods=['POST'])
def save():
    original_text = request.form.get('original_text', '')
    new_text = request.form.get('new_text', '')
    filename = request.form.get('filename', 'untitled.md')
    
    # Create a folder for this pair using the filename (without extension)
    folder_name = os.path.splitext(filename)[0]
    folder_path = os.path.join('data', folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Use filename as prefix for both files
    original_filename = f"{folder_name}_original.md"
    new_filename = f"{folder_name}_new.md"
    
    # Save both texts to files in the folder
    with open(os.path.join(folder_path, original_filename), 'w', encoding='utf-8') as f:
        f.write(original_text)
    
    with open(os.path.join(folder_path, new_filename), 'w', encoding='utf-8') as f:
        f.write(new_text)
    
    return {'success': True, 'message': f'Saved as {filename}'}

@app.route('/load', methods=['POST'])
def load():
    filename = request.form.get('filename', '')
    
    # Get the folder name from the filename
    folder_name = os.path.splitext(filename)[0]
    folder_path = os.path.join('data', folder_name)
    
    original_content = ''
    new_content = ''
    
    try:
        # Use filename as prefix for both files
        original_filename = f"{folder_name}_original.md"
        new_filename = f"{folder_name}_new.md"
        
        with open(os.path.join(folder_path, original_filename), 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        try:
            with open(os.path.join(folder_path, new_filename), 'r', encoding='utf-8') as f:
                new_content = f.read()
        except:
            # It's okay if the new file doesn't exist yet
            pass
            
        return {'success': True, 'original_text': original_content, 'new_text': new_content}
    except:
        return {'success': False, 'message': 'File not found'}

@app.route('/list_files')
def list_files():
    files = []
    for item in os.listdir('data'):
        item_path = os.path.join('data', item)
        if os.path.isdir(item_path):
            # Check if this is a valid text pair folder
            original_filename = f"{item}_original.md"
            if os.path.exists(os.path.join(item_path, original_filename)):
                files.append(item + '.md')  # Add .md extension for consistency
    return {'files': files}

@app.route('/spell_check', methods=['POST'])
def spell_check():
    # Removing spell check endpoint
    pass

@app.route('/ollama', methods=['POST'])
def ollama_generate():
    try:
        data = request.json
        text = data.get('text', '')
        instruction = data.get('instruction', 'Rewrite the following text:')
        model = data.get('model', DEFAULT_MODEL)
        
        # Format the prompt
        prompt = f"{instruction}\n\n{text}"
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "response": result.get("response", "")
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Ollama API error: {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

@app.route('/list_models')
def list_models():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags")
        if response.status_code == 200:
            models = [model['name'] for model in response.json()['models']]
            return jsonify({"success": True, "models": models})
        else:
            return jsonify({"success": False, "message": "Could not retrieve models"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    # Create the templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Create the index.html file
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Text Editor</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="header">
        <div class="file-controls">
            <input type="text" id="filename" placeholder="filename.md">
            <button id="save-btn">Save</button>
            <button id="load-btn">Load</button>
            <select id="file-list">
                <option value="">Select a file</option>
            </select>
            <div class="option-controls">
                <label>
                    <input type="checkbox" id="sync-scroll"> Sync Scrolling
                </label>
                <label>
                    <input type="checkbox" id="markdown-preview"> Markdown Preview
                </label>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="column">
            <div class="column-header">
                <h2>New Text</h2>
                <div class="column-stats">
                    <span id="newWordCount">0 words</span>
                    <span id="newLastUpdated"></span>
                </div>
            </div>
            <div class="editor-container">
                <textarea id="newText" placeholder="Enter new text here..."></textarea>
                <div class="markdown-preview" id="newPreview"></div>
            </div>
            <div class="resize-handle"></div>
        </div>
        <div class="column">
            <div class="column-header">
                <h2>Original Text</h2>
                <div class="column-stats">
                    <span id="originalWordCount">0 words</span>
                    <span id="originalLastUpdated"></span>
                </div>
            </div>
            <div class="editor-container">
                <textarea id="originalText" placeholder="Enter original text here..."></textarea>
                <div class="markdown-preview" id="originalPreview"></div>
            </div>
        </div>
    </div>
    
    <div class="terminal-container">
        <div class="terminal-header">
            <span>AI Assistant Terminal</span>
            <div class="terminal-controls">
                <select id="model-list">
                    <option value="">Loading models...</option>
                </select>
                <button id="terminal-clear">Clear</button>
                <button id="terminal-toggle">▲</button>
            </div>
        </div>
        <div class="terminal-content" id="terminal-content">
            <div class="terminal-output" id="terminal-output">
                <p>Welcome to the AI Assistant Terminal. Connect to Ollama to get started.</p>
                <p>Type /help for available commands.</p>
            </div>
            <div class="terminal-input-container">
                <span class="prompt">></span>
                <input type="text" id="terminal-input" placeholder="Type a command or question...">
            </div>
        </div>
        <div class="terminal-resize-handle"></div>
    </div>

    <div id="status-message"></div>
    
    <script src="/static/script.js"></script>
</body>
</html>''')
    
    # Create the CSS file
    with open('static/styles.css', 'w', encoding='utf-8') as f:
        f.write('''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    background-color: #f1f1f1;
    padding: 10px;
    border-bottom: 1px solid #ddd;
}

.file-controls {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}

.option-controls {
    margin-left: auto;
    display: flex;
    gap: 15px;
}

.container {
    display: flex;
    flex: 1;
    height: calc(100vh - 180px); /* Adjust for terminal */
    min-height: 0;  /* Important for flex child scrolling */
    overflow: hidden;  /* Contain the scrolling */
    position: relative;  /* For resize handle positioning */
}

.column {
    flex: 1;
    padding: 30px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    position: relative;
    min-width: 200px;  /* Minimum width for columns */
}

.resize-handle {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 5px;
    background: #ddd;
    cursor: col-resize;
    z-index: 10;
}

.resize-handle:hover {
    background: #999;
}

.column:first-child {
    border-right: 1px solid #ddd;
    background-color: #f9f9f9;
}

.column:first-child .resize-handle {
    right: 0;
}

.column-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.column-stats {
    font-size: 0.9em;
    color: #666;
    display: flex;
    gap: 15px;
}

.column-stats span {
    white-space: nowrap;
}

h2 {
    margin: 0;
    font-size: 1.2em;
    color: #333;
}

.editor-container {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    padding: 5px;  /* Added padding */
    background: #fff;  /* Added background */
    border-radius: 4px;  /* Added rounded corners */
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);  /* Added subtle shadow */
}

.markdown-preview {
    display: none;
    padding: 15px;  /* Increased from 10px */
    background: white;
    border: 1px solid #ddd;
    overflow-y: auto;
    flex: 1;
    height: 100%;
    box-sizing: border-box;
    min-height: 0;
    border-radius: 3px;  /* Added rounded corners */
}

.markdown-preview.active {
    display: block;
}

textarea {
    width: 100%;
    height: 100%;
    border: 1px solid #ddd;
    resize: none;
    flex: 1;
    padding: 15px;  /* Increased from 10px */
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
    line-height: 1.5;
    box-sizing: border-box;
    min-height: 0;
    border-radius: 3px;  /* Added rounded corners */
}

.spelling-error {
    text-decoration: wavy underline red;
}

button {
    padding: 5px 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
}

button:hover {
    background-color: #45a049;
}

input, select {
    padding: 5px;
    border: 1px solid #ddd;
}

#status-message {
    padding: 10px;
    text-align: center;
    color: #666;
}

/* Terminal Styles */
.terminal-container {
    background-color: #1e1e1e;
    color: #f0f0f0;
    border-top: 1px solid #333;
    height: 180px;
    display: flex;
    flex-direction: column;
    transition: height 0.3s ease;
    position: relative;  /* For resize handle positioning */
    min-height: 100px;  /* Minimum height for terminal */
}

.terminal-resize-handle {
    position: absolute;
    left: 0;
    right: 0;
    top: -5px;
    height: 5px;
    background: #333;
    cursor: row-resize;
    z-index: 10;
}

.terminal-resize-handle:hover {
    background: #666;
}

.terminal-container.minimized {
    height: 30px;
}

.terminal-container.minimized .terminal-resize-handle {
    display: none;
}

.terminal-header {
    background-color: #2d2d2d;
    padding: 5px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
}

.terminal-controls {
    display: flex;
    gap: 5px;
}

.terminal-controls button {
    background-color: #444;
    font-size: 12px;
    padding: 2px 8px;
}

.terminal-controls button:hover {
    background-color: #555;
}

.terminal-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.terminal-output {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
}

.terminal-output p {
    margin: 2px 0;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.terminal-input-container {
    display: flex;
    padding: 5px 10px;
    background-color: #2d2d2d;
}

.prompt {
    color: #4CAF50;
    font-weight: bold;
    margin-right: 8px;
    font-family: 'Courier New', Courier, monospace;
}

#terminal-input {
    background-color: transparent;
    border: none;
    color: #f0f0f0;
    flex: 1;
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
}

#terminal-input:focus {
    outline: none;
}

.output-user {
    color: #64B5F6;
}

.output-system {
    color: #FFD54F;
}

.output-error {
    color: #EF5350;
}

/* Spell check highlighting */
.spelling-highlight {
    position: relative;
    text-decoration: wavy underline red;
}

.spelling-highlight:hover::after {
    content: attr(data-suggestion);
    position: absolute;
    left: 0;
    bottom: 20px;
    background: #333;
    color: white;
    padding: 3px 6px;
    border-radius: 3px;
    font-size: 12px;
    white-space: nowrap;
    z-index: 10;
}

.editor-container {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.markdown-preview {
    display: none;
    padding: 10px;
    background: white;
    border: 1px solid #ddd;
    overflow-y: auto;
    flex: 1;
}

.markdown-preview.active {
    display: block;
}

.markdown-preview h1 { font-size: 2em; margin: 0.67em 0; }
.markdown-preview h2 { font-size: 1.5em; margin: 0.75em 0; }
.markdown-preview h3 { font-size: 1.17em; margin: 0.83em 0; }
.markdown-preview p { margin: 1em 0; }
.markdown-preview code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
.markdown-preview pre { background: #f5f5f5; padding: 1em; border-radius: 3px; overflow-x: auto; }
.markdown-preview blockquote { border-left: 4px solid #ddd; margin: 1em 0; padding-left: 1em; }
.markdown-preview ul, .markdown-preview ol { margin: 1em 0; padding-left: 2em; }
.markdown-preview table { border-collapse: collapse; width: 100%; margin: 1em 0; }
.markdown-preview th, .markdown-preview td { border: 1px solid #ddd; padding: 8px; }
.markdown-preview th { background: #f5f5f5; }
''')
    
    # Create the JavaScript file
    with open('static/script.js', 'w', encoding='utf-8') as f:
        f.write(r'''document.addEventListener('DOMContentLoaded', function() {
    // Main editor elements
    const originalText = document.getElementById('originalText');
    const newText = document.getElementById('newText');
    const filenameInput = document.getElementById('filename');
    const saveBtn = document.getElementById('save-btn');
    const loadBtn = document.getElementById('load-btn');
    const fileList = document.getElementById('file-list');
    const statusMessage = document.getElementById('status-message');
    
    // Feature toggles
    const syncScrollCheckbox = document.getElementById('sync-scroll');
    const markdownPreviewCheckbox = document.getElementById('markdown-preview');
    
    // Terminal elements
    const terminalContent = document.getElementById('terminal-content');
    const terminalOutput = document.getElementById('terminal-output');
    const terminalInput = document.getElementById('terminal-input');
    const terminalToggle = document.getElementById('terminal-toggle');
    const terminalClear = document.getElementById('terminal-clear');
    const modelList = document.getElementById('model-list');
    
    // Terminal state
    let currentModel = '';
    let isOllamaConnected = false;
    
    // Load the list of files
    function loadFileList() {
        fetch('/list_files')
            .then(response => response.json())
            .then(data => {
                fileList.innerHTML = '<option value="">Select a file</option>';
                data.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.textContent = file;
                    fileList.appendChild(option);
                });
            });
    }
    
    // Load file list on page load
    loadFileList();
    
    // Save button click handler
    saveBtn.addEventListener('click', function() {
        const filename = filenameInput.value || 'untitled.md';
        
        const formData = new FormData();
        formData.append('original_text', originalText.value);
        formData.append('new_text', newText.value);
        formData.append('filename', filename);
        
        fetch('/save', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            statusMessage.textContent = data.message;
            loadFileList();
        });
    });
    
    // Load button click handler
    loadBtn.addEventListener('click', function() {
        const filename = filenameInput.value;
        if (!filename) {
            statusMessage.textContent = 'Please enter a filename';
            return;
        }
        
        const formData = new FormData();
        formData.append('filename', filename);
        
        fetch('/load', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                originalText.value = data.original_text;
                newText.value = data.new_text;
                statusMessage.textContent = `Loaded ${filename}`;
            } else {
                statusMessage.textContent = data.message;
            }
        });
    });
    
    // File list change handler
    fileList.addEventListener('change', function() {
        if (this.value) {
            filenameInput.value = this.value;
            
            const formData = new FormData();
            formData.append('filename', this.value);
            
            fetch('/load', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    originalText.value = data.original_text;
                    newText.value = data.new_text;
                    statusMessage.textContent = `Loaded ${this.value}`;
                } else {
                    statusMessage.textContent = data.message;
                }
            });
        }
    });
    
    // Synchronized scrolling
    function syncScroll(source, target) {
        if (syncScrollCheckbox.checked) {
            target.scrollTop = source.scrollTop;
        }
    }
    
    originalText.addEventListener('scroll', () => syncScroll(originalText, newText));
    newText.addEventListener('scroll', () => syncScroll(newText, originalText));
    
    // Terminal toggle
    terminalToggle.addEventListener('click', function() {
        const terminalContainer = document.querySelector('.terminal-container');
        terminalContainer.classList.toggle('minimized');
        
        if (terminalContainer.classList.contains('minimized')) {
            terminalToggle.textContent = '▼';
        } else {
            terminalToggle.textContent = '▲';
        }
    });
    
    // Terminal clear button
    terminalClear.addEventListener('click', function() {
        terminalOutput.innerHTML = '';
        addTerminalMessage('Terminal cleared', 'system');
    });
    
    // Terminal input handler
    terminalInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            
            const input = this.value.trim();
            if (!input) return;
            
            processTerminalCommand(input);
            this.value = '';
        }
    });
    
    // Add message to terminal
    function addTerminalMessage(message, type = 'normal') {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = `output-${type}`;
        terminalOutput.appendChild(p);
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }
    
    // Markdown preview toggle
    function updateMarkdownPreview() {
        if (markdownPreviewCheckbox.checked) {
            newPreview.classList.add('active');
            originalPreview.classList.add('active');
            newText.style.display = 'none';
            originalText.style.display = 'none';
            // Update previews immediately when toggled
            updatePreviews();
        } else {
            newPreview.classList.remove('active');
            originalPreview.classList.remove('active');
            newText.style.display = 'block';
            originalText.style.display = 'block';
        }
    }
    
    function renderMarkdown(text) {
        if (!text) return '';  // Return empty string if text is empty
        // Simple markdown rendering
        return text
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }
    
    function updatePreviews() {
        if (markdownPreviewCheckbox.checked) {
            newPreview.innerHTML = renderMarkdown(newText.value);
            originalPreview.innerHTML = renderMarkdown(originalText.value);
        }
    }
    
    markdownPreviewCheckbox.addEventListener('change', updateMarkdownPreview);
    newText.addEventListener('input', updatePreviews);
    originalText.addEventListener('input', updatePreviews);
    
    // Modify the LLM prompt to handle markdown
    function processTerminalCommand(input) {
        addTerminalMessage(`> ${input}`, 'user');
        
        // Handle command prefixes
        if (input.startsWith('/')) {
            const parts = input.slice(1).split(' ');
            const command = parts[0].toLowerCase();
            
            switch (command) {
                case 'help':
                    showHelp();
                    break;
                case 'models':
                    fetchModels();
                    break;
                case 'connect':
                    checkOllamaConnection();
                    break;
                case 'rewrite':
                    generateText('Rewrite the following text in a clearer, more concise way. Preserve any markdown formatting:');
                    break;
                case 'improve':
                    generateText('Improve the following text by enhancing its clarity, structure, and style. Preserve any markdown formatting:');
                    break;
                case 'summarize':
                    generateText('Summarize the following text in a few sentences. Use markdown formatting for better readability:');
                    break;
                case 'expand':
                    generateText('Expand on the following text with more details and examples. Use markdown formatting for better structure:');
                    break;
                default:
                    addTerminalMessage(`Unknown command: ${command}. Type /help for available commands.`, 'error');
            }
        } else {
            // Treat as a direct query to the AI
            if (isOllamaConnected && currentModel) {
                let processedInput = input;
                let contextText = '';
                
                // Check for /old, /new, or /both references
                if (input.includes('/both')) {
                    const originalTextContent = originalText.value.trim();
                    const newTextContent = newText.value.trim();
                    if (originalTextContent && newTextContent) {
                        contextText = `Original text:\n${originalTextContent}\n\nNew text:\n${newTextContent}`;
                        processedInput = input.replace('/both', 'both texts');
                    }
                } else if (input.includes('/old')) {
                    contextText = originalText.value.trim();
                    processedInput = input.replace('/old', 'the original text');
                } else if (input.includes('/new')) {
                    contextText = newText.value.trim();
                    processedInput = input.replace('/new', 'the new text');
                }
                
                // If we found a reference, include the text in the prompt
                if (contextText) {
                    processedInput = `${processedInput}\n\nHere is the text:\n${contextText}`;
                }
                
                // Add markdown instruction
                processedInput += "\n\nPlease use markdown formatting in your response for better readability.";
                
                callOllama({
                    text: processedInput,
                    instruction: "Answer the following question or respond to the following request. Use markdown formatting in your response:",
                    model: currentModel
                });
            } else {
                addTerminalMessage('Not connected to Ollama. Use /connect to connect first.', 'error');
            }
        }
    }
    
    // Show help
    function showHelp() {
        const helpText = `
Available commands:
/help - Show this help message
/models - List available Ollama models
/connect - Test connection to Ollama
/rewrite - Rewrite the text in the original column
/improve - Improve the text for clarity and style
/summarize - Summarize the text
/expand - Expand the text with more details

Text references in queries:
Use /old, /new, or /both in your questions to reference the respective text(s)

You can also just type a question or request directly.`;
        
        addTerminalMessage(helpText, 'system');
    }
    
    // Fetch available models
    function fetchModels() {
        addTerminalMessage('Fetching available models...', 'system');
        
        fetch('/list_models')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateModelList(data.models);
                    const modelsList = data.models.join(', ');
                    addTerminalMessage(`Available models: ${modelsList}`, 'system');
                } else {
                    addTerminalMessage(`Failed to fetch models: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                addTerminalMessage(`Error fetching models: ${error.message}`, 'error');
            });
    }
    
    // Update model list dropdown
    function updateModelList(models) {
        modelList.innerHTML = '';
        
        if (models.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No models available';
            modelList.appendChild(option);
            return;
        }
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelList.appendChild(option);
        });
        
        // Set the current model
        if (!currentModel && models.length > 0) {
            currentModel = models[0];
            modelList.value = currentModel;
        }
    }
    
    // Model selection change
    modelList.addEventListener('change', function() {
        currentModel = this.value;
        addTerminalMessage(`Switched to model: ${currentModel}`, 'system');
    });
    
    // Check Ollama connection
    function checkOllamaConnection() {
        addTerminalMessage('Testing connection to Ollama...', 'system');
        
        fetch('/list_models')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    isOllamaConnected = true;
                    addTerminalMessage('Successfully connected to Ollama!', 'system');
                    updateModelList(data.models);
                } else {
                    isOllamaConnected = false;
                    addTerminalMessage(`Failed to connect to Ollama: ${data.message}`, 'error');
                    addTerminalMessage('Make sure Ollama is running on your machine.', 'error');
                }
            })
            .catch(error => {
                isOllamaConnected = false;
                addTerminalMessage(`Error connecting to Ollama: ${error.message}`, 'error');
                addTerminalMessage('Make sure Ollama is running on your machine.', 'error');
            });
    }
    
    // Generate text with Ollama
    function generateText(instruction) {
        if (!isOllamaConnected) {
            addTerminalMessage('Not connected to Ollama. Use /connect to connect first.', 'error');
            return;
        }
        
        if (!currentModel) {
            addTerminalMessage('No model selected. Use /models to list available models.', 'error');
            return;
        }
        
        const text = originalText.value.trim();
        if (!text) {
            addTerminalMessage('Original text is empty. Please add some text first.', 'error');
            return;
        }
        
        addTerminalMessage(`Processing with ${currentModel}...`, 'system');
        
        callOllama({
            text: text,
            instruction: instruction,
            model: currentModel
        });
    }
    
    // Call Ollama API
    function callOllama(data) {
        fetch('/ollama', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                addTerminalMessage(result.response);
                // For rewrite operations, also put the result in the new text area
                if (data.instruction.includes('Rewrite') || 
                    data.instruction.includes('Improve') ||
                    data.instruction.includes('Summarize') ||
                    data.instruction.includes('Expand')) {
                    newText.value = result.response;
                }
            } else {
                addTerminalMessage(`Error: ${result.message}`, 'error');
            }
        })
        .catch(error => {
            addTerminalMessage(`Error: ${error.message}`, 'error');
        });
    }
    
    // Initialize
    checkOllamaConnection();
    showHelp();

    // Resize functionality
    const resizeHandle = document.querySelector('.resize-handle');
    const terminalResizeHandle = document.querySelector('.terminal-resize-handle');
    const container = document.querySelector('.container');
    const terminalContainer = document.querySelector('.terminal-container');
    let isResizing = false;
    let isTerminalResizing = false;
    let startX, startY, startWidth, startHeight;

    // Column resize
    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        const leftColumn = document.querySelector('.column:first-child');
        startWidth = leftColumn.offsetWidth;
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });

    // Terminal resize
    terminalResizeHandle.addEventListener('mousedown', (e) => {
        isTerminalResizing = true;
        startY = e.clientY;
        startHeight = terminalContainer.offsetHeight;
        document.body.style.cursor = 'row-resize';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (isResizing) {
            const leftColumn = document.querySelector('.column:first-child');
            const newWidth = startWidth + (e.clientX - startX);
            if (newWidth > 200) { // Minimum width check
                leftColumn.style.flex = 'none';
                leftColumn.style.width = newWidth + 'px';
            }
        }
        if (isTerminalResizing) {
            const newHeight = startHeight - (e.clientY - startY);
            if (newHeight > 100) { // Minimum height check
                terminalContainer.style.height = newHeight + 'px';
                container.style.height = `calc(100vh - ${newHeight + 60}px)`; // Adjust for header
            }
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing || isTerminalResizing) {
            isResizing = false;
            isTerminalResizing = false;
            document.body.style.cursor = 'default';
        }
    });

    // Prevent text selection while resizing
    document.addEventListener('selectstart', (e) => {
        if (isResizing || isTerminalResizing) {
            e.preventDefault();
        }
    });

    // Initialize container height
    container.style.height = `calc(100vh - ${terminalContainer.offsetHeight + 60}px)`;

    // Word count and last updated functionality
    const newWordCount = document.getElementById('newWordCount');
    const originalWordCount = document.getElementById('originalWordCount');
    const newLastUpdated = document.getElementById('newLastUpdated');
    const originalLastUpdated = document.getElementById('originalLastUpdated');
    
    let wordCountTimer;
    const WORD_COUNT_DELAY = 500; // 500ms debounce delay
    
    function updateWordCount(text, element) {
        const words = text.trim().split(/\s+/).filter(word => word.length > 0);
        element.textContent = `${words.length} words`;
    }
    
    function updateLastUpdated(element) {
        const now = new Date();
        const dateStr = now.toLocaleDateString();
        const timeStr = now.toLocaleTimeString();
        element.textContent = `updated: ${dateStr} ${timeStr}`;
    }
    
    function debounce(func, delay) {
        return function(...args) {
            clearTimeout(wordCountTimer);
            wordCountTimer = setTimeout(() => func.apply(this, args), delay);
        };
    }
    
    const debouncedUpdateWordCount = debounce((text, element) => {
        updateWordCount(text, element);
    }, WORD_COUNT_DELAY);
    
    // Update word count and last updated on text changes
    newText.addEventListener('input', () => {
        debouncedUpdateWordCount(newText.value, newWordCount);
        updateLastUpdated(newLastUpdated);
    });
    
    originalText.addEventListener('input', () => {
        debouncedUpdateWordCount(originalText.value, originalWordCount);
        updateLastUpdated(originalLastUpdated);
    });
    
    // Update word count when loading files
    const originalLoadBtn = loadBtn.cloneNode(true);
    loadBtn.parentNode.replaceChild(originalLoadBtn, loadBtn);
    
    originalLoadBtn.addEventListener('click', () => {
        const filename = filenameInput.value;
        if (!filename) {
            statusMessage.textContent = 'Please enter a filename';
            return;
        }
        
        fetch('/load', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                originalText.value = data.original_text;
                newText.value = data.new_text;
                statusMessage.textContent = `Loaded ${filename}`;
                
                // Update word counts and last updated
                updateWordCount(originalText.value, originalWordCount);
                updateWordCount(newText.value, newWordCount);
                updateLastUpdated(originalLastUpdated);
                updateLastUpdated(newLastUpdated);
            } else {
                statusMessage.textContent = data.message;
            }
        });
    });
    
    // Initialize word counts
    updateWordCount(originalText.value, originalWordCount);
    updateWordCount(newText.value, newWordCount);
});''')
    
    print("Starting enhanced server on http://127.0.0.1:5000/")
    app.run(debug=True) 