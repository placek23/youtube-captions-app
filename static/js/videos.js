// Video List JavaScript

// State management
let currentPage = 1;
let currentChannelFilter = '';
let currentSortOrder = 'published_at_desc';
let totalPages = 1;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Parse URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    currentPage = parseInt(urlParams.get('page')) || 1;
    currentChannelFilter = urlParams.get('channel_id') || '';
    currentSortOrder = urlParams.get('order_by') || 'published_at_desc';

    // Set filter values from URL
    const sortSelect = document.getElementById('sortOrder');
    if (sortSelect) {
        sortSelect.value = currentSortOrder;
        sortSelect.addEventListener('change', handleSortChange);
    }

    // Load channels for filter dropdown
    loadChannelsFilter();

    // Load videos
    loadVideos();
});

// Load channels for filter dropdown
async function loadChannelsFilter() {
    const channelFilter = document.getElementById('channelFilter');

    if (!channelFilter) return;

    try {
        const response = await fetch('/api/channels');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.channels && data.channels.length > 0) {
            data.channels.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.id;
                option.textContent = channel.channel_name;
                channelFilter.appendChild(option);
            });

            // Set current filter value
            if (currentChannelFilter) {
                channelFilter.value = currentChannelFilter;
            }

            // Add event listener
            channelFilter.addEventListener('change', handleChannelFilterChange);
        }
    } catch (error) {
        console.error('Error loading channels filter:', error);
    }
}

// Load videos from API
async function loadVideos() {
    const container = document.getElementById('videosContainer');

    // Show loading state
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading videos...</p>
        </div>
    `;

    try {
        // Build API URL with query parameters
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20
        });

        if (currentChannelFilter) {
            params.append('channel_id', currentChannelFilter);
        }

        if (currentSortOrder) {
            params.append('order_by', currentSortOrder);
        }

        const response = await fetch(`/api/videos?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.videos && data.videos.length > 0) {
            displayVideos(data.videos);
            displayPagination(data.pagination);
        } else {
            displayEmptyState();
        }
    } catch (error) {
        console.error('Error loading videos:', error);
        container.innerHTML = `
            <div class="message error">
                Failed to load videos. Please try refreshing the page.
            </div>
        `;
    }
}

// Display videos in grid
function displayVideos(videos) {
    const container = document.getElementById('videosContainer');

    const gridHTML = `
        <div class="videos-grid">
            ${videos.map(video => createVideoCard(video)).join('')}
        </div>
    `;

    container.innerHTML = gridHTML;
}

// Create HTML for a single video card
function createVideoCard(video) {
    const thumbnailUrl = video.thumbnail_url || `https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`;
    const publishedDate = new Date(video.published_at).toLocaleDateString();
    const shortSummary = video.short_summary || 'No summary available yet';
    const processingStatus = video.processing_status || 'pending';

    // Status badge
    let statusBadge = '';
    if (processingStatus === 'pending') {
        statusBadge = '<span class="status-badge status-pending">Pending</span>';
    } else if (processingStatus === 'processing') {
        statusBadge = '<span class="status-badge status-processing">Processing</span>';
    } else if (processingStatus === 'failed') {
        statusBadge = '<span class="status-badge status-failed">Failed</span>';
    }

    return `
        <div class="video-card" onclick="navigateToVideo('${video.video_id}')">
            <div class="video-thumbnail-wrapper">
                <img src="${thumbnailUrl}" alt="${escapeHtml(video.title)}" class="video-thumbnail">
                ${statusBadge}
            </div>
            <div class="video-info">
                <h3 class="video-title">${escapeHtml(video.title)}</h3>
                <div class="video-meta">
                    <span class="channel-name">${escapeHtml(video.channel_name)}</span>
                    <span class="separator">•</span>
                    <span class="published-date">${publishedDate}</span>
                </div>
                <p class="video-summary">${escapeHtml(shortSummary)}</p>
            </div>
        </div>
    `;
}

// Navigate to video detail page
function navigateToVideo(videoId) {
    window.location.href = `/video/${videoId}`;
}

// Display pagination controls
function displayPagination(pagination) {
    const container = document.getElementById('paginationContainer');

    if (!pagination || pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }

    totalPages = pagination.total_pages;
    currentPage = pagination.page;

    let paginationHTML = '<div class="pagination">';

    // Previous button
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage - 1})">Previous</button>`;
    } else {
        paginationHTML += `<button class="page-btn" disabled>Previous</button>`;
    }

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="page-btn active">${i}</button>`;
        } else {
            paginationHTML += `<button class="page-btn" onclick="goToPage(${i})">${i}</button>`;
        }
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage + 1})">Next</button>`;
    } else {
        paginationHTML += `<button class="page-btn" disabled>Next</button>`;
    }

    paginationHTML += '</div>';

    // Page info
    paginationHTML += `
        <div class="page-info">
            Page ${currentPage} of ${totalPages} (${pagination.total_count} total videos)
        </div>
    `;

    container.innerHTML = paginationHTML;
}

// Navigate to specific page
function goToPage(page) {
    currentPage = page;
    updateURL();
    loadVideos();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Handle channel filter change
function handleChannelFilterChange(event) {
    currentChannelFilter = event.target.value;
    currentPage = 1; // Reset to first page
    updateURL();
    loadVideos();
}

// Handle sort order change
function handleSortChange(event) {
    currentSortOrder = event.target.value;
    currentPage = 1; // Reset to first page
    updateURL();
    loadVideos();
}

// Update URL with current filters
function updateURL() {
    const params = new URLSearchParams();

    if (currentPage > 1) {
        params.append('page', currentPage);
    }

    if (currentChannelFilter) {
        params.append('channel_id', currentChannelFilter);
    }

    if (currentSortOrder && currentSortOrder !== 'published_at_desc') {
        params.append('order_by', currentSortOrder);
    }

    const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
    window.history.pushState({}, '', newURL);
}

// Display empty state
function displayEmptyState() {
    const container = document.getElementById('videosContainer');
    container.innerHTML = `
        <div class="empty-state">
            <h3>No Videos Found</h3>
            <p>Add some channels and sync their videos to get started.</p>
            <a href="/channels" class="btn-primary">Go to Channels</a>
        </div>
    `;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}