document.addEventListener('DOMContentLoaded', () => {
    const getCaptionsBtn = document.getElementById('get-captions-btn');
    const summarizeBtn = document.getElementById('summarize-btn');
    const saveToDbBtn = document.getElementById('save-to-db-btn');
    const videoUrlInput = document.getElementById('video-url');
    const captionsOutput = document.getElementById('captions-output');
    const summaryOutput = document.getElementById('summary-output');
    const loadingDiv = document.getElementById('loading');
    const messageContainer = document.getElementById('messageContainer');
    const captionsSection = document.getElementById('captionsSection');
    const summarySection = document.getElementById('summarySection');
    const copyCaptionsBtn = document.getElementById('copy-captions-btn');

    // Store video data for saving
    let videoData = {
        video_id: '',
        title: '',
        video_url: '',
        caption_text: '',
        short_summary: '',
        detailed_summary: ''
    };

    // Get CSRF token from meta tag (returns empty string if not present for serverless)
    function getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        return token;
    }

    // Extract video ID from YouTube URL
    function extractVideoId(url) {
        const urlObj = new URL(url);
        if (urlObj.hostname.includes('youtube.com')) {
            return urlObj.searchParams.get('v');
        } else if (urlObj.hostname.includes('youtu.be')) {
            return urlObj.pathname.substring(1);
        }
        return null;
    }

    getCaptionsBtn.addEventListener('click', async () => {
        const videoUrl = videoUrlInput.value.trim();
        if (!videoUrl) {
            showError('Please enter a YouTube video URL.');
            return;
        }

        resetState();
        showLoading(true);

        try {
            const response = await fetch('/get_captions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ video_url: videoUrl }),
            });

            const data = await response.json();

            if (response.ok) {
                captionsOutput.value = data.captions;
                captionsSection.classList.remove('hidden');

                // Store video data
                videoData.video_url = videoUrl;
                videoData.video_id = data.video_id || extractVideoId(videoUrl);
                videoData.title = data.title || 'YouTube Video';
                videoData.caption_text = data.captions;
            } else {
                showError(data.error || 'An unknown error occurred.');
            }
        } catch (error) {
            showError('Failed to fetch captions. Check the console for details.');
            console.error('Error fetching captions:', error);
        } finally {
            showLoading(false);
        }
    });

    summarizeBtn.addEventListener('click', async () => {
        const captionText = captionsOutput.value;
        if (!captionText) {
            showError('There are no captions to summarize.');
            return;
        }

        showLoading(true);
        summaryOutput.innerHTML = '';
        clearMessages();

        try {
            const response = await fetch('/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ caption_text: captionText }),
            });

            const data = await response.json();

            if (response.ok) {
                // Use marked.parse for rendering Markdown and DOMPurify to sanitize
                const rawHtml = marked.parse(data.summary);
                const cleanHtml = DOMPurify.sanitize(rawHtml);
                summaryOutput.innerHTML = cleanHtml;
                summarySection.classList.remove('hidden');

                // Store summary data (treat the summary as detailed_summary)
                videoData.detailed_summary = data.summary;
                videoData.short_summary = data.summary.substring(0, 500) + '...'; // First 500 chars as short

                // Show save button
                if (saveToDbBtn) {
                    saveToDbBtn.classList.remove('hidden');
                }
            } else {
                showError(data.error || 'An unknown error occurred during summarization.');
            }
        } catch (error) {
            showError('Failed to generate summary. Check the console for details.');
            console.error('Error generating summary:', error);
        } finally {
            showLoading(false);
        }
    });

    if (saveToDbBtn) {
        saveToDbBtn.addEventListener('click', async () => {
            // Validate that we have all required data
            if (!videoData.video_id || !videoData.title || !videoData.video_url) {
                showError('Missing video information. Please fetch captions first.');
                return;
            }

            showLoading(true);
            clearMessages();

            try {
                const response = await fetch('/api/save_video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify(videoData),
                });

                const data = await response.json();

                if (response.ok) {
                    // Redirect to video detail page
                    window.location.href = `/video/${videoData.video_id}`;
                } else if (response.status === 409) {
                    // Video already exists
                    showError('This video is already in the database.');
                    // Optionally redirect to the existing video
                    setTimeout(() => {
                        window.location.href = `/video/${videoData.video_id}`;
                    }, 2000);
                } else {
                    showError(data.error || 'Failed to save video to database.');
                }
            } catch (error) {
                showError('Failed to save video. Check the console for details.');
                console.error('Error saving video:', error);
            } finally {
                showLoading(false);
            }
        });
    }

    if (copyCaptionsBtn) {
        copyCaptionsBtn.addEventListener('click', () => {
            const captionText = captionsOutput.value;
            if (captionText) {
                navigator.clipboard.writeText(captionText)
                    .then(() => {
                        const originalText = copyCaptionsBtn.textContent;
                        copyCaptionsBtn.textContent = 'Copied!';
                        setTimeout(() => {
                            copyCaptionsBtn.textContent = originalText;
                        }, 2000); // Revert text after 2 seconds
                    })
                    .catch(err => {
                        console.error('Failed to copy captions: ', err);
                        showError('Failed to copy captions. See console for details.');
                    });
            } else {
                showError('No captions to copy.');
            }
        });
    }

    function resetState() {
        captionsOutput.value = '';
        summaryOutput.innerHTML = '';
        captionsSection.classList.add('hidden');
        summarySection.classList.add('hidden');
        summarizeBtn.classList.add('hidden');
        if (saveToDbBtn) {
            saveToDbBtn.classList.add('hidden');
        }
        clearMessages();
        // Reset video data
        videoData = {
            video_id: '',
            title: '',
            video_url: '',
            caption_text: '',
            short_summary: '',
            detailed_summary: ''
        };
    }

    function showLoading(isLoading) {
        loadingDiv.classList.toggle('hidden', !isLoading);
    }

    function showError(message) {
        clearMessages();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message error';
        messageDiv.textContent = message;
        messageContainer.appendChild(messageDiv);
    }

    function showSuccess(message) {
        clearMessages();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message success';
        messageDiv.textContent = message;
        messageContainer.appendChild(messageDiv);
    }

    function clearMessages() {
        messageContainer.innerHTML = '';
    }

    // The formatSummary function is not strictly necessary if marked.js is handling all formatting.
    // It can be removed or kept if specific pre-processing for marked.js is needed later.
    // For now, let's keep it to ensure the replacement content matches the intended 'good' part of the script.
    function formatSummary(text) {
        // Replace markdown-like formatting with HTML tags for display
        let html = text.replace(/\n/g, '<br>'); // Newlines
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');     // Italics
        html = html.replace(/^- (.*)/gm, '<ul><li>$1</li></ul>'); // Basic list items
        // Consolidate multiple <ul> tags
        html = html.replace(/<\/ul>\s*<ul>/g, '');
        return html;
    }
});
