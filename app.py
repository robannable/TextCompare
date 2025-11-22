from flask import Flask, render_template, request, send_from_directory, jsonify, Response, stream_with_context
import os
import requests
import json
import time
from dotenv import load_dotenv
import anthropic
from functools import lru_cache

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")
DEFAULT_OLLAMA_MODEL = "llama3.1:latest"

# Anthropic configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# Initialize Anthropic client if API key is available
anthropic_client = None
if ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Cache for model lists (5 minute TTL)
model_cache = {
    'ollama': {'models': [], 'timestamp': 0},
    'anthropic': {'models': [], 'timestamp': 0}
}
CACHE_TTL = 300  # 5 minutes

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

# ============================================================================
# OLLAMA ENDPOINTS
# ============================================================================

@app.route('/ollama', methods=['POST'])
def ollama_generate():
    """Generate text using Ollama (non-streaming)"""
    try:
        data = request.json
        text = data.get('text', '')
        instruction = data.get('instruction', 'Rewrite the following text:')
        model = data.get('model', DEFAULT_OLLAMA_MODEL)

        # Format the prompt
        prompt = f"{instruction}\n\n{text}"

        # Call Ollama API with increased timeout
        response = requests.post(
            f"{OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120  # Increased timeout to 2 minutes
        )

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "response": result.get("response", "")
            })
        else:
            error_msg = f"Ollama API error: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', '')}"
            except:
                pass
            return jsonify({
                "success": False,
                "message": error_msg
            })
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request to Ollama timed out after 2 minutes. Please try again with a shorter prompt or different model."
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Could not connect to Ollama. Make sure it's running on localhost:11434"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

@app.route('/ollama/stream', methods=['POST'])
def ollama_stream():
    """Generate text using Ollama with streaming"""
    def generate():
        try:
            data = request.json
            text = data.get('text', '')
            instruction = data.get('instruction', 'Rewrite the following text:')
            model = data.get('model', DEFAULT_OLLAMA_MODEL)

            # Format the prompt
            prompt = f"{instruction}\n\n{text}"

            # Call Ollama API with streaming
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=120
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield f"data: {json.dumps({'token': chunk['response']})}\n\n"
                            if chunk.get('done', False):
                                yield f"data: {json.dumps({'done': True})}\n\n"
                        except json.JSONDecodeError:
                            continue
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/list_ollama_models')
def list_ollama_models():
    """List available Ollama models with caching"""
    try:
        # Check cache
        current_time = time.time()
        if current_time - model_cache['ollama']['timestamp'] < CACHE_TTL:
            return jsonify({
                "success": True,
                "models": model_cache['ollama']['models'],
                "cached": True
            })

        # Fetch from API
        response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=5)
        if response.status_code == 200:
            models = [model['name'] for model in response.json()['models']]
            # Update cache
            model_cache['ollama']['models'] = models
            model_cache['ollama']['timestamp'] = current_time

            return jsonify({"success": True, "models": models, "cached": False})
        else:
            error_msg = f"Could not retrieve models: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', '')}"
            except:
                pass
            return jsonify({"success": False, "message": error_msg})
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request to Ollama timed out. Please try again."
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Could not connect to Ollama. Make sure it's running on localhost:11434"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

# ============================================================================
# ANTHROPIC ENDPOINTS
# ============================================================================

@app.route('/anthropic', methods=['POST'])
def anthropic_generate():
    """Generate text using Anthropic Claude (non-streaming)"""
    if not anthropic_client:
        return jsonify({
            "success": False,
            "message": "Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env file."
        })

    try:
        data = request.json
        text = data.get('text', '')
        instruction = data.get('instruction', 'Rewrite the following text:')
        model = data.get('model', DEFAULT_ANTHROPIC_MODEL)
        max_tokens = data.get('max_tokens', 4096)
        temperature = data.get('temperature', 1.0)

        # Create the message
        message = anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": f"{instruction}\n\n{text}"
                }
            ]
        )

        # Extract the response text
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        return jsonify({
            "success": True,
            "response": response_text,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            }
        })

    except anthropic.AuthenticationError:
        return jsonify({
            "success": False,
            "message": "Invalid Anthropic API key. Please check your .env configuration."
        })
    except anthropic.RateLimitError:
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded. Please wait a moment and try again."
        })
    except anthropic.APIError as e:
        return jsonify({
            "success": False,
            "message": f"Anthropic API error: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

@app.route('/anthropic/stream', methods=['POST'])
def anthropic_stream():
    """Generate text using Anthropic Claude with streaming"""
    if not anthropic_client:
        def error_gen():
            yield f"data: {json.dumps({'error': 'Anthropic API key not configured'})}\n\n"
        return Response(stream_with_context(error_gen()), mimetype='text/event-stream')

    def generate():
        try:
            data = request.json
            text = data.get('text', '')
            instruction = data.get('instruction', 'Rewrite the following text:')
            model = data.get('model', DEFAULT_ANTHROPIC_MODEL)
            max_tokens = data.get('max_tokens', 4096)
            temperature = data.get('temperature', 1.0)

            # Stream the response
            with anthropic_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": f"{instruction}\n\n{text}"
                    }
                ]
            ) as stream:
                for text_delta in stream.text_stream:
                    yield f"data: {json.dumps({'token': text_delta})}\n\n"

                # Send completion signal with usage stats
                final_message = stream.get_final_message()
                yield f"data: {json.dumps({'done': True, 'usage': {'input_tokens': final_message.usage.input_tokens, 'output_tokens': final_message.usage.output_tokens}})}\n\n"

        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'error': 'Invalid Anthropic API key'})}\n\n"
        except anthropic.RateLimitError:
            yield f"data: {json.dumps({'error': 'Rate limit exceeded'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/list_anthropic_models')
def list_anthropic_models():
    """List available Anthropic models"""
    if not anthropic_client:
        return jsonify({
            "success": False,
            "message": "Anthropic API key not configured"
        })

    # Check cache
    current_time = time.time()
    if current_time - model_cache['anthropic']['timestamp'] < CACHE_TTL:
        return jsonify({
            "success": True,
            "models": model_cache['anthropic']['models'],
            "cached": True
        })

    # Anthropic doesn't have a models list API, so we return the known models
    models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]

    # Update cache
    model_cache['anthropic']['models'] = models
    model_cache['anthropic']['timestamp'] = current_time

    return jsonify({
        "success": True,
        "models": models,
        "cached": False
    })

# ============================================================================
# UNIFIED MODELS ENDPOINT
# ============================================================================

@app.route('/list_models')
def list_models():
    """List all available models from both providers"""
    models = {
        "anthropic": [],
        "ollama": []
    }
    errors = {}

    # Get Anthropic models
    if anthropic_client:
        anthropic_response = list_anthropic_models()
        anthropic_data = anthropic_response.get_json()
        if anthropic_data.get('success'):
            models['anthropic'] = anthropic_data.get('models', [])
        else:
            errors['anthropic'] = anthropic_data.get('message', 'Unknown error')
    else:
        errors['anthropic'] = 'API key not configured'

    # Get Ollama models
    ollama_response = list_ollama_models()
    ollama_data = ollama_response.get_json()
    if ollama_data.get('success'):
        models['ollama'] = ollama_data.get('models', [])
    else:
        errors['ollama'] = ollama_data.get('message', 'Unknown error')

    return jsonify({
        "success": True,
        "models": models,
        "errors": errors
    })

@app.route('/generate', methods=['POST'])
def generate():
    """Unified endpoint for text generation (auto-routes to appropriate provider)"""
    data = request.json
    provider = data.get('provider', 'ollama')
    stream = data.get('stream', False)

    if provider == 'anthropic':
        if stream:
            return anthropic_stream()
        else:
            return anthropic_generate()
    else:  # ollama
        if stream:
            return ollama_stream()
        else:
            return ollama_generate()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint to verify service status"""
    status = {
        "anthropic": {
            "configured": anthropic_client is not None,
            "available": False
        },
        "ollama": {
            "available": False
        }
    }

    # Check Anthropic
    if anthropic_client:
        try:
            # Quick validation - just check if client is initialized
            status["anthropic"]["available"] = True
        except:
            pass

    # Check Ollama
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=2)
        status["ollama"]["available"] = response.status_code == 200
    except:
        pass

    return jsonify(status)

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
                <select id="provider-select">
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="ollama">Ollama (Local)</option>
                </select>
                <select id="model-list">
                    <option value="">Loading models...</option>
                </select>
                <label class="stream-toggle">
                    <input type="checkbox" id="stream-toggle" checked> Stream
                </label>
                <button id="terminal-clear">Clear</button>
                <button id="terminal-toggle">▲</button>
            </div>
        </div>
        <div class="terminal-content" id="terminal-content">
            <div class="terminal-output" id="terminal-output">
                <p>Welcome to the AI Assistant Terminal.</p>
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
    height: calc(100vh - 180px);
    min-height: 0;
    overflow: hidden;
    position: relative;
}

.column {
    flex: 1;
    padding: 30px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    position: relative;
    min-width: 200px;
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
    padding: 5px;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.markdown-preview {
    display: none;
    padding: 15px;
    background: white;
    border: 1px solid #ddd;
    overflow-y: auto;
    flex: 1;
    height: 100%;
    box-sizing: border-box;
    min-height: 0;
    border-radius: 3px;
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
    padding: 15px;
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
    line-height: 1.5;
    box-sizing: border-box;
    min-height: 0;
    border-radius: 3px;
}

button {
    padding: 5px 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 3px;
}

button:hover {
    background-color: #45a049;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

input, select {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 3px;
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
    position: relative;
    min-height: 100px;
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
    align-items: center;
}

.terminal-controls button {
    background-color: #444;
    font-size: 12px;
    padding: 2px 8px;
}

.terminal-controls button:hover {
    background-color: #555;
}

.terminal-controls select {
    background-color: #444;
    color: #f0f0f0;
    border: 1px solid #555;
    font-size: 12px;
}

.stream-toggle {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #f0f0f0;
    font-size: 12px;
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

#terminal-input:disabled {
    opacity: 0.5;
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

.output-success {
    color: #4CAF50;
}

.output-info {
    color: #81C784;
}

.loading-indicator {
    color: #FFA726;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
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

/* Token usage display */
.token-usage {
    color: #888;
    font-size: 11px;
    font-style: italic;
}
''')

    print("Starting enhanced server on http://127.0.0.1:5000/")
    print(f"Anthropic configured: {anthropic_client is not None}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    app.run(debug=True)
