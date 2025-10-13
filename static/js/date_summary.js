document.addEventListener('DOMContentLoaded', () => {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const generateSummaryBtn = document.getElementById('generate-summary-btn');
    const loadingDiv = document.getElementById('loading');
    const loadingMessage = document.getElementById('loading-message');
    const messageContainer = document.getElementById('messageContainer');
    const statsSection = document.getElementById('statsSection');
    const summarySection = document.getElementById('summarySection');
    const summaryOutput = document.getElementById('summary-output');
    const statVideos = document.getElementById('stat-videos');
    const statChannels = document.getElementById('stat-channels');
    const statDateRange = document.getElementById('stat-date-range');

    // Set default dates (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);

    endDateInput.valueAsDate = today;
    startDateInput.valueAsDate = thirtyDaysAgo;

    // Get CSRF token from meta tag
    function getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        return token;
    }

    // Format date for display (MM/DD/YYYY)
    function formatDateDisplay(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
    }

    // Validate date range
    function validateDates() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        if (!startDate || !endDate) {
            showError('Please select both start and end dates.');
            return false;
        }

        if (new Date(startDate) > new Date(endDate)) {
            showError('Start date must be before or equal to end date.');
            return false;
        }

        return true;
    }

    generateSummaryBtn.addEventListener('click', async () => {
        if (!validateDates()) {
            return;
        }

        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        resetState();
        showLoading(true, 'Fetching videos from database...');

        try {
            // Step 1: Fetch videos in date range
            const videosResponse = await fetch('/api/videos/date-range', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate }),
            });

            const videosData = await videosResponse.json();

            if (!videosResponse.ok) {
                showError(videosData.error || 'Failed to fetch videos.');
                showLoading(false);
                return;
            }

            if (!videosData.videos || videosData.videos.length === 0) {
                showInfo('No processed videos found in the selected date range.');
                showLoading(false);
                return;
            }

            // Display stats
            displayStats(videosData.videos, startDate, endDate);

            // Step 2: Generate AI summary
            showLoading(true, 'Generating AI summary...');

            const summaryResponse = await fetch('/api/summarize/date-range', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ videos: videosData.videos }),
            });

            const summaryData = await summaryResponse.json();

            if (!summaryResponse.ok) {
                showError(summaryData.error || 'Failed to generate summary.');
                showLoading(false);
                return;
            }

            // Display summary
            displaySummary(summaryData.summary);
            showSuccess(`Successfully generated summary for ${videosData.videos.length} video(s).`);

        } catch (error) {
            showError('An unexpected error occurred. Check the console for details.');
            console.error('Error generating date range summary:', error);
        } finally {
            showLoading(false);
        }
    });

    function displayStats(videos, startDate, endDate) {
        // Count unique channels
        const uniqueChannels = new Set(videos.map(v => v.channel_name || v.channel_id).filter(Boolean));

        statVideos.textContent = videos.length;
        statChannels.textContent = uniqueChannels.size;
        statDateRange.textContent = `${formatDateDisplay(startDate)} - ${formatDateDisplay(endDate)}`;

        statsSection.classList.remove('hidden');
    }

    function displaySummary(summaryText) {
        // Use marked.parse for rendering Markdown and DOMPurify to sanitize
        const rawHtml = marked.parse(summaryText);
        const cleanHtml = DOMPurify.sanitize(rawHtml);
        summaryOutput.innerHTML = cleanHtml;
        summarySection.classList.remove('hidden');
    }

    function resetState() {
        summaryOutput.innerHTML = '';
        statsSection.classList.add('hidden');
        summarySection.classList.add('hidden');
        statVideos.textContent = '0';
        statChannels.textContent = '0';
        statDateRange.textContent = '-';
        clearMessages();
    }

    function showLoading(isLoading, message = 'Loading...') {
        loadingDiv.classList.toggle('hidden', !isLoading);
        if (loadingMessage) {
            loadingMessage.textContent = message;
        }
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

    function showInfo(message) {
        clearMessages();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message info';
        messageDiv.textContent = message;
        messageContainer.appendChild(messageDiv);
    }

    function clearMessages() {
        messageContainer.innerHTML = '';
    }
});
