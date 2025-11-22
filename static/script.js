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

    // Preview elements
    const newPreview = document.getElementById('newPreview');
    const originalPreview = document.getElementById('originalPreview');

    // Terminal elements
    const terminalContent = document.getElementById('terminal-content');
    const terminalOutput = document.getElementById('terminal-output');
    const terminalInput = document.getElementById('terminal-input');
    const terminalToggle = document.getElementById('terminal-toggle');
    const terminalClear = document.getElementById('terminal-clear');
    const modelList = document.getElementById('model-list');
    const providerSelect = document.getElementById('provider-select');
    const streamToggle = document.getElementById('stream-toggle');

    // Terminal state
    let currentModel = '';
    let currentProvider = 'anthropic';
    let isProcessing = false;
    let availableModels = {
        anthropic: [],
        ollama: []
    };

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
                updateWordCount(originalText.value, originalWordCount);
                updateWordCount(newText.value, newWordCount);
                updatePreviews();
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
                    updateWordCount(originalText.value, originalWordCount);
                    updateWordCount(newText.value, newWordCount);
                    updatePreviews();
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

            if (isProcessing) {
                addTerminalMessage('Please wait for the current request to complete.', 'error');
                return;
            }

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
        if (type !== 'normal') {
            p.className = `output-${type}`;
        }
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
            updatePreviews();
        } else {
            newPreview.classList.remove('active');
            originalPreview.classList.remove('active');
            newText.style.display = 'block';
            originalText.style.display = 'block';
        }
    }

    function renderMarkdown(text) {
        if (!text) return '';
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

    // Process terminal commands
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
                case 'health':
                    checkHealth();
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
            if (!currentModel) {
                addTerminalMessage('No model selected. Use /models to list available models.', 'error');
                return;
            }

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

            callAI({
                text: processedInput,
                instruction: "Answer the following question or respond to the following request. Use markdown formatting in your response:",
                model: currentModel,
                provider: currentProvider,
                stream: streamToggle.checked
            });
        }
    }

    // Show help
    function showHelp() {
        const helpText = `
Available commands:
/help - Show this help message
/models - List available models for current provider
/health - Check service status
/rewrite - Rewrite the text in the original column
/improve - Improve the text for clarity and style
/summarize - Summarize the text
/expand - Expand the text with more details

Text references in queries:
Use /old, /new, or /both in your questions to reference the respective text(s)

Providers:
- Anthropic Claude: Cloud-based, requires API key
- Ollama: Local models, no API key needed

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
                    availableModels = data.models;
                    updateModelList(currentProvider);

                    let message = `Available models for ${currentProvider}:\n`;
                    if (data.models[currentProvider] && data.models[currentProvider].length > 0) {
                        message += data.models[currentProvider].join('\n');
                    } else {
                        message += `No models available. ${data.errors[currentProvider] || 'Unknown error'}`;
                    }
                    addTerminalMessage(message, 'system');
                } else {
                    addTerminalMessage(`Failed to fetch models`, 'error');
                }
            })
            .catch(error => {
                addTerminalMessage(`Error fetching models: ${error.message}`, 'error');
            });
    }

    // Check health status
    function checkHealth() {
        addTerminalMessage('Checking service health...', 'system');

        fetch('/health')
            .then(response => response.json())
            .then(data => {
                let message = 'Service Status:\n';
                message += `Anthropic: ${data.anthropic.configured ? (data.anthropic.available ? '✓ Available' : '✗ Configured but unavailable') : '✗ Not configured'}\n`;
                message += `Ollama: ${data.ollama.available ? '✓ Available' : '✗ Unavailable'}`;
                addTerminalMessage(message, 'info');
            })
            .catch(error => {
                addTerminalMessage(`Error checking health: ${error.message}`, 'error');
            });
    }

    // Update model list dropdown
    function updateModelList(provider) {
        modelList.innerHTML = '';

        const models = availableModels[provider] || [];

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
        if (!currentModel || !models.includes(currentModel)) {
            currentModel = models[0];
            modelList.value = currentModel;
        }
    }

    // Provider selection change
    providerSelect.addEventListener('change', function() {
        currentProvider = this.value;
        addTerminalMessage(`Switched to provider: ${currentProvider}`, 'system');
        updateModelList(currentProvider);
        fetchModels();
    });

    // Model selection change
    modelList.addEventListener('change', function() {
        currentModel = this.value;
        addTerminalMessage(`Switched to model: ${currentModel}`, 'system');
    });

    // Generate text with AI
    function generateText(instruction) {
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

        callAI({
            text: text,
            instruction: instruction,
            model: currentModel,
            provider: currentProvider,
            stream: streamToggle.checked
        });
    }

    // Call AI API (unified for both streaming and non-streaming)
    function callAI(data) {
        if (isProcessing) {
            addTerminalMessage('Another request is already in progress.', 'error');
            return;
        }

        isProcessing = true;
        terminalInput.disabled = true;

        if (data.stream) {
            callAIStream(data);
        } else {
            callAINonStream(data);
        }
    }

    // Non-streaming AI call
    function callAINonStream(data) {
        const endpoint = data.provider === 'anthropic' ? '/anthropic' : '/ollama';

        addTerminalMessage('⏳ Waiting for response...', 'loading-indicator');

        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            // Remove loading indicator
            const loadingIndicators = terminalOutput.querySelectorAll('.loading-indicator');
            loadingIndicators.forEach(el => el.remove());

            if (result.success) {
                addTerminalMessage(result.response);

                // Show token usage for Anthropic
                if (result.usage) {
                    addTerminalMessage(
                        `[Tokens: ${result.usage.input_tokens} in, ${result.usage.output_tokens} out]`,
                        'token-usage'
                    );
                }

                // For rewrite operations, also put the result in the new text area
                if (data.instruction.includes('Rewrite') ||
                    data.instruction.includes('Improve') ||
                    data.instruction.includes('Summarize') ||
                    data.instruction.includes('Expand')) {
                    newText.value = result.response;
                    updateWordCount(newText.value, newWordCount);
                    updatePreviews();
                }
            } else {
                addTerminalMessage(`Error: ${result.message}`, 'error');
            }
        })
        .catch(error => {
            // Remove loading indicator
            const loadingIndicators = terminalOutput.querySelectorAll('.loading-indicator');
            loadingIndicators.forEach(el => el.remove());

            addTerminalMessage(`Error: ${error.message}`, 'error');
        })
        .finally(() => {
            isProcessing = false;
            terminalInput.disabled = false;
            terminalInput.focus();
        });
    }

    // Streaming AI call
    function callAIStream(data) {
        const endpoint = data.provider === 'anthropic' ? '/anthropic/stream' : '/ollama/stream';

        let responseText = '';
        let responseElement = document.createElement('p');
        responseElement.className = 'streaming-response';
        terminalOutput.appendChild(responseElement);

        // Create loading indicator
        const loadingElement = document.createElement('p');
        loadingElement.className = 'loading-indicator';
        loadingElement.textContent = '⏳ Streaming response...';
        terminalOutput.appendChild(loadingElement);
        terminalOutput.scrollTop = terminalOutput.scrollHeight;

        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function read() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        loadingElement.remove();
                        isProcessing = false;
                        terminalInput.disabled = false;
                        terminalInput.focus();
                        return;
                    }

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const jsonData = JSON.parse(line.slice(6));

                                if (jsonData.error) {
                                    loadingElement.remove();
                                    addTerminalMessage(`Error: ${jsonData.error}`, 'error');
                                    isProcessing = false;
                                    terminalInput.disabled = false;
                                    return;
                                }

                                if (jsonData.token) {
                                    responseText += jsonData.token;
                                    responseElement.textContent = responseText;
                                    terminalOutput.scrollTop = terminalOutput.scrollHeight;
                                }

                                if (jsonData.done) {
                                    loadingElement.remove();

                                    // Show token usage if available
                                    if (jsonData.usage) {
                                        const usageElement = document.createElement('p');
                                        usageElement.className = 'token-usage';
                                        usageElement.textContent = `[Tokens: ${jsonData.usage.input_tokens} in, ${jsonData.usage.output_tokens} out]`;
                                        terminalOutput.appendChild(usageElement);
                                    }

                                    // For rewrite operations, update the new text area
                                    if (data.instruction.includes('Rewrite') ||
                                        data.instruction.includes('Improve') ||
                                        data.instruction.includes('Summarize') ||
                                        data.instruction.includes('Expand')) {
                                        newText.value = responseText;
                                        updateWordCount(newText.value, newWordCount);
                                        updatePreviews();
                                    }

                                    isProcessing = false;
                                    terminalInput.disabled = false;
                                    terminalInput.focus();
                                    return;
                                }
                            } catch (e) {
                                console.error('Error parsing SSE data:', e);
                            }
                        }
                    }

                    return read();
                });
            }

            return read();
        })
        .catch(error => {
            loadingElement.remove();
            addTerminalMessage(`Error: ${error.message}`, 'error');
            isProcessing = false;
            terminalInput.disabled = false;
            terminalInput.focus();
        });
    }

    // Initialize
    fetchModels();
    showHelp();
    checkHealth();

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
            if (newWidth > 200) {
                leftColumn.style.flex = 'none';
                leftColumn.style.width = newWidth + 'px';
            }
        }
        if (isTerminalResizing) {
            const newHeight = startHeight - (e.clientY - startY);
            if (newHeight > 100) {
                terminalContainer.style.height = newHeight + 'px';
                container.style.height = `calc(100vh - ${newHeight + 60}px)`;
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
    const WORD_COUNT_DELAY = 500;

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

    // Initialize word counts
    updateWordCount(originalText.value, originalWordCount);
    updateWordCount(newText.value, newWordCount);
});
