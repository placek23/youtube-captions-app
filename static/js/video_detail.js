// Video Detail JavaScript

// Get video ID from URL path
function getVideoIdFromPath() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

// Load video details when page loads
document.addEventListener('DOMContentLoaded', function() {
    const videoId = getVideoIdFromPath();

    if (videoId) {
        loadVideoDetails(videoId);
    } else {
        displayError('Invalid video ID');
    }
});

// Load video details from API
async function loadVideoDetails(videoId) {
    const container = document.getElementById('videoDetailContainer');

    try {
        const response = await fetch(`/api/videos/${videoId}`);

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Video not found');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const video = await response.json();
        displayVideoDetails(video);
    } catch (error) {
        console.error('Error loading video details:', error);
        displayError(error.message || 'Failed to load video details');
    }
}

// Store current video globally for access by other functions
let currentVideo = null;

// Display video details
function displayVideoDetails(video) {
    // Store video for later use
    currentVideo = video;

    const container = document.getElementById('videoDetailContainer');

    // Create video player/thumbnail section
    let playerHTML;
    if (video.video_id) {
        playerHTML = `
            <div class="video-player-section">
                <div class="video-player">
                    <iframe
                        src="https://www.youtube.com/embed/${video.video_id}"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen
                    ></iframe>
                </div>
            </div>
        `;
    } else {
        const thumbnailUrl = video.thumbnail_url || 'https://via.placeholder.com/900x506?text=No+Thumbnail';
        playerHTML = `
            <div class="video-player-section">
                <img src="${thumbnailUrl}" alt="${escapeHtml(video.title)}" class="video-thumbnail-large">
            </div>
        `;
    }

    // Determine status
    const status = video.processing_status || 'pending';
    const statusClass = `status-${status}`;
    const statusText = status.charAt(0).toUpperCase() + status.slice(1);

    // Format date
    const publishedDate = video.published_at
        ? new Date(video.published_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })
        : 'Unknown';

    // Build video header
    const headerHTML = `
        <div class="video-header">
            <h1 class="video-title">${escapeHtml(video.title)}</h1>
            <div class="video-metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Channel:</span>
                    <span>${escapeHtml(video.channel_name)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Published:</span>
                    <span>${publishedDate}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Status:</span>
                    <span class="status-indicator ${statusClass}">${statusText}</span>
                </div>
            </div>
            <div class="video-actions">
                <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank" class="btn btn-primary">
                    Watch on YouTube
                </a>
                ${status === 'pending' || status === 'failed'
                    ? `<button onclick="processVideo()" class="btn btn-secondary">Process Video</button>`
                    : ''
                }
            </div>
            ${status === 'pending' || status === 'failed'
                ? `<div class="progress-container" id="processingProgress">
                    <div class="progress-label" id="progressText">Preparing to process...</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="progressBar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%"></div>
                    </div>
                </div>`
                : ''
            }
        </div>
    `;

    // Build summary sections
    let summaryHTML = '';

    if (video.short_summary && status === 'completed') {
        summaryHTML += `
            <div class="summary-section">
                <div class="section-header">
                    <h2 class="section-title">Short Summary</h2>
                    <button class="copy-btn" onclick="copySummary('short', this)">Copy</button>
                </div>
                <div class="summary-content" id="shortSummary">
                    ${escapeHtml(video.short_summary)}
                </div>
            </div>
        `;
    }

    if (video.detailed_summary && status === 'completed') {
        summaryHTML += `
            <div class="summary-section">
                <div class="section-header">
                    <h2 class="section-title">Detailed Summary</h2>
                    <button class="copy-btn" onclick="copySummary('detailed', this)">Copy</button>
                </div>
                <div class="summary-content" id="detailedSummary"></div>
            </div>
        `;
    }

    // Build captions section
    let captionsHTML = '';
    if (video.caption_text && status === 'completed') {
        captionsHTML = `
            <div class="captions-section">
                <div class="section-header">
                    <h2 class="section-title">
                        Original Captions
                        <button class="captions-toggle" onclick="toggleCaptions()">Show</button>
                    </h2>
                    <button class="copy-btn" onclick="copyCaptions(this)">Copy</button>
                </div>
                <div class="captions-content" id="captionsContent">${escapeHtml(video.caption_text)}</div>
            </div>
        `;
    }

    // Show message if not processed yet
    if (status !== 'completed') {
        summaryHTML = `
            <div class="summary-section">
                <h2 class="section-title">Summary Not Available</h2>
                <p style="color: #7f8c8d;">
                    ${status === 'pending'
                        ? 'This video has not been processed yet. Click "Process Video" to extract captions and generate summaries.'
                        : status === 'processing'
                        ? 'This video is currently being processed. Please check back in a few moments.'
                        : 'Processing failed for this video. You can try processing it again.'
                    }
                </p>
            </div>
        `;
    }

    // Assemble final HTML
    container.innerHTML = playerHTML + headerHTML + summaryHTML + captionsHTML;

    // Render detailed summary as markdown if available
    if (video.detailed_summary && status === 'completed') {
        const detailedSummaryDiv = document.getElementById('detailedSummary');
        if (detailedSummaryDiv && typeof marked !== 'undefined') {
            detailedSummaryDiv.innerHTML = marked.parse(video.detailed_summary);
        }
    }
}

// Toggle captions visibility
function toggleCaptions() {
    const captionsContent = document.getElementById('captionsContent');
    const toggleBtn = document.querySelector('.captions-toggle');

    if (captionsContent && toggleBtn) {
        captionsContent.classList.toggle('expanded');
        toggleBtn.textContent = captionsContent.classList.contains('expanded') ? 'Hide' : 'Show';
    }
}

// Copy summary to clipboard
async function copySummary(type, button) {
    const elementId = type === 'short' ? 'shortSummary' : 'detailedSummary';
    const element = document.getElementById(elementId);

    if (!element) return;

    const text = element.textContent || element.innerText;

    try {
        await navigator.clipboard.writeText(text);

        // Update button state
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    }
}

// Copy captions to clipboard
async function copyCaptions(button) {
    const captionsContent = document.getElementById('captionsContent');

    if (!captionsContent) return;

    const text = captionsContent.textContent || captionsContent.innerText;

    try {
        await navigator.clipboard.writeText(text);

        // Update button state
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    }
}

// Process video (extract captions and generate summaries)
async function processVideo() {
    if (!currentVideo) {
        alert('Video data not available');
        return;
    }

    const confirmed = confirm('This will extract captions and generate summaries for this video. This may take a few minutes. Continue?');

    if (!confirmed) return;

    const videoId = currentVideo.video_id; // YouTube video ID

    // Show progress bar
    const progressContainer = document.getElementById('processingProgress');
    const processBtn = document.querySelector(`button[onclick*="processVideo"]`);

    if (progressContainer) {
        progressContainer.style.display = 'block';
        updateProgress('Extracting captions...', 33);
    }

    if (processBtn) {
        processBtn.disabled = true;
        processBtn.textContent = 'Processing...';
    }

    try {
        // Start processing
        const response = await fetch(`/api/process/video/${videoId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            console.error('Processing error:', data);
            const errorMsg = data.error || 'Failed to start processing';
            updateProgress('Error: ' + errorMsg, 0);

            // Show alert for visibility
            setTimeout(() => {
                alert('Processing failed: ' + errorMsg);
            }, 500);

            if (processBtn) {
                processBtn.disabled = false;
                processBtn.textContent = 'Process Video';
            }
            return;
        }

        // Poll for status updates using the YouTube video ID
        await pollVideoStatus(videoId);

    } catch (error) {
        console.error('Error processing video:', error);
        updateProgress('Processing failed. Please try again.', 0);
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.textContent = 'Process Video';
        }
    }
}

// Poll video status for progress updates
async function pollVideoStatus(videoId) {
    const maxAttempts = 120; // 2 minutes max (120 * 1 second)
    let attempts = 0;
    let currentStep = 0;

    const steps = [
        { message: 'Extracting captions...', percentage: 33 },
        { message: 'Generating short summary...', percentage: 66 },
        { message: 'Generating detailed summary...', percentage: 90 }
    ];

    // First step is already shown, start from step 0
    const pollInterval = setInterval(async () => {
        attempts++;

        // Show simulated progress every 3 seconds
        if (attempts === 3 && currentStep === 0) {
            currentStep++;
            updateProgress(steps[currentStep].message, steps[currentStep].percentage);
        } else if (attempts === 6 && currentStep === 1) {
            currentStep++;
            updateProgress(steps[currentStep].message, steps[currentStep].percentage);
        }

        try {
            const response = await fetch(`/api/videos/${videoId}`);

            if (!response.ok) {
                throw new Error('Failed to fetch video status');
            }

            const video = await response.json();
            const status = video.processing_status || 'pending';

            // Update progress based on actual status
            if (status === 'completed') {
                updateProgress('Processing complete!', 100);
                clearInterval(pollInterval);

                // Reload page after brief delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else if (status === 'failed') {
                updateProgress('Processing failed. Please try again.', 0);
                clearInterval(pollInterval);

                // Re-enable button
                const processBtn = document.querySelector(`button[onclick*="processVideo"]`);
                if (processBtn) {
                    processBtn.disabled = false;
                    processBtn.textContent = 'Process Video';
                }
            }

            // Timeout after max attempts
            if (attempts >= maxAttempts) {
                updateProgress('Processing is taking longer than expected. Please refresh the page.', 66);
                clearInterval(pollInterval);
            }

        } catch (error) {
            console.error('Error polling status:', error);
            clearInterval(pollInterval);
            updateProgress('Error checking status. Please refresh the page.', 0);
        }
    }, 1000); // Poll every second
}

// Update progress bar
function updateProgress(message, percentage) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);

        // Remove all state classes
        progressBar.classList.remove('error', 'complete');

        // Add appropriate class based on state
        if (message.toLowerCase().includes('error') || message.toLowerCase().includes('failed')) {
            progressBar.classList.add('error');
        } else if (percentage === 100 || message.toLowerCase().includes('complete')) {
            progressBar.classList.add('complete');
        }
    }

    if (progressText) {
        progressText.textContent = message;
    }
}

// Display error state
function displayError(message) {
    const container = document.getElementById('videoDetailContainer');
    container.innerHTML = `
        <div class="error-state">
            <h2>Error</h2>
            <p>${escapeHtml(message)}</p>
            <a href="/videos" class="btn btn-primary">Back to Videos</a>
        </div>
    `;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}