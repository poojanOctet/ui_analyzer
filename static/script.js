document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const urlInput = document.getElementById('urlInput');
    const loadUrlButton = document.getElementById('loadUrlButton');
    const imagePreview = document.getElementById('imagePreview');
    const previewContainer = document.querySelector('.preview-container');
    const analyzeButton = document.getElementById('analyzeButton');
    const resultsSection = document.querySelector('.results-section');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultsContent = document.querySelector('.results-content');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    let currentFile = null; // Store the current file
    let currentUrl = null;  // Store the current URL

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const targetTab = document.getElementById(`${button.dataset.tab}-tab`);
            if (targetTab) {
                targetTab.classList.add('active');
            } else {
                console.error(`Tab content for ${button.dataset.tab} not found`);
            }
            
            resetPreview();
        });
    });

    // File Upload Handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#4F46E5';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#E5E7EB';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#E5E7EB';
        const file = e.dataTransfer.files[0];
        handleFile(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // URL Handler
    loadUrlButton.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (url) {
            await loadUrlPreview(url);
        } else {
            alert('Please enter a valid URL');
        }
    });

    // Analyze Button Handler
    analyzeButton.addEventListener('click', () => {
        if (currentFile) {
            analyzeImage(currentFile);
        } else if (currentUrl) {
            analyzeUrl(currentUrl);
        } else {
            alert('Please upload an image or enter a URL first.');
        }
    });

    function handleFile(file) {
        if (file && file.type.startsWith('image/')) {
            currentFile = file;
            currentUrl = null;
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                showPreview();
            };
            reader.readAsDataURL(file);
        } else {
            alert('Please upload an image file.');
        }
    }

    async function loadUrlPreview(url) {
        try {
            loadingSpinner.hidden = false;
            previewContainer.hidden = true;
            resultsSection.hidden = true;
            
            const response = await fetch(`/screenshot?url=${encodeURIComponent(url)}`, {
                method: 'GET',
                headers: {
                    'Accept': 'image/png'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to load screenshot');
            }
            
            const blob = await response.blob();
            const urlObject = URL.createObjectURL(blob);
            imagePreview.src = urlObject;
            currentUrl = url;
            currentFile = null;
            showPreview();
            loadingSpinner.hidden = true;
        } catch (error) {
            loadingSpinner.hidden = true;
            resultsContent.innerHTML = `
                <div class="error-message">
                    Error loading URL preview: ${error.message}
                </div>
            `;
            resultsSection.hidden = false;
        }
    }

    function showPreview() {
        dropZone.style.display = 'none';
        document.getElementById('url-tab').classList.remove('active');
        document.getElementById('file-tab').classList.remove('active');
        previewContainer.hidden = false;
        resultsSection.hidden = true;
    }

    function resetPreview() {
        currentFile = null;
        currentUrl = null;
        imagePreview.src = '';
        dropZone.style.display = 'block';
        const urlTab = document.getElementById('url-tab');
        const fileTab = document.getElementById('file-tab');
        const urlTabButton = document.querySelector('.tab-button[data-tab="url"]');
        const fileTabButton = document.querySelector('.tab-button[data-tab="file"]');
        
        if (urlTabButton.classList.contains('active')) {
            urlTab.classList.add('active');
            fileTab.classList.remove('active');
        } else {
            fileTab.classList.add('active');
            urlTab.classList.remove('active');
        }
        
        previewContainer.hidden = true;
        resultsSection.hidden = true;
        resultsContent.innerHTML = '';
    }

    async function analyzeImage(file) {
        try {
            loadingSpinner.hidden = false;
            resultsSection.hidden = false;
            resultsContent.innerHTML = '';
            analyzeButton.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/analyze-ui', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Analysis failed');
            }

            displayResults(data);
        } catch (error) {
            displayError(error);
        }
    }

    async function analyzeUrl(url) {
        try {
            loadingSpinner.hidden = false;
            resultsSection.hidden = false;
            resultsContent.innerHTML = '';
            analyzeButton.disabled = true;

            const response = await fetch(`/analyze-ui?url=${encodeURIComponent(url)}`, {
                method: 'POST'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Analysis failed');
            }

            displayResults(data);
        } catch (error) {
            displayError(error);
        }
    }

    function displayResults(data) {
        loadingSpinner.hidden = true;
        analyzeButton.disabled = false;
        const content = data.analysis.content;
        const scores = extractScores(content);
        resultsContent.innerHTML = `
            <div class="scores-container">
                <div class="score-item">Visual Design: <span>${scores.visual_design || 'N/A'}</span></div>
                <div class="score-item">User Experience: <span>${scores.ux || 'N/A'}</span></div>
                <div class="score-item">Accessibility: <span>${scores.accessibility || 'N/A'}</span></div>
            </div>
            ${formatAnalysis(content)}
        `;
    }

    function displayError(error) {
        loadingSpinner.hidden = true;
        analyzeButton.disabled = false;
        resultsContent.innerHTML = `
            <div class="error-message">
                Error: ${error.message}
            </div>
        `;
    }

    function extractScores(content) {
        const scores = {};
        const lines = content.split('\n');
        lines.forEach(line => {
            if (line.includes("visual_design:")) {
                scores.visual_design = line.split("visual_design:")[1].trim().split(' ')[0];
            } else if (line.includes("ux:")) {
                scores.ux = line.split("ux:")[1].trim().split(' ')[0];
            } else if (line.includes("accessibility:")) {
                scores.accessibility = line.split("accessibility:")[1].trim().split(' ')[0];
            }
        });
        return scores;
    }

    function formatAnalysis(content) {
        return content
            .replace(/### (.*?)\n/g, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/- (.*?)(\n|$)/g, '<li>$1</li>')
            .replace(/\n\n/g, '<br><br>');
    }
});