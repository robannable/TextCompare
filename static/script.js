document.addEventListener('DOMContentLoaded', function() {
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
});