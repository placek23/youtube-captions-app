document.addEventListener('DOMContentLoaded', () => {
    const getCaptionsBtn = document.getElementById('get-captions-btn');
    const summarizeBtn = document.getElementById('summarize-btn');
    const videoUrlInput = document.getElementById('video-url');
    const captionsOutput = document.getElementById('captions-output');
    const summaryOutput = document.getElementById('summary-output');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const copyCaptionsBtn = document.getElementById('copy-captions-btn');

    // Get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
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
                summarizeBtn.classList.remove('hidden');
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
        errorDiv.classList.add('hidden');

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
        summarizeBtn.classList.add('hidden');
        errorDiv.classList.add('hidden');
    }

    function showLoading(isLoading) {
        loadingDiv.classList.toggle('hidden', !isLoading);
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
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
