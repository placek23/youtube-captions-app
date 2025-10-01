// Channel Management JavaScript

// Load channels when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChannels();
    loadPendingCount();

    // Setup form submission
    const form = document.getElementById('addChannelForm');
    form.addEventListener('submit', handleAddChannel);

    // Setup process pending button
    const processPendingBtn = document.getElementById('processPendingBtn');
    if (processPendingBtn) {
        processPendingBtn.addEventListener('click', handleProcessPending);
    }
});

// Load all channels from API
async function loadChannels() {
    const container = document.getElementById('channelsContainer');

    try {
        const response = await fetch('/api/channels');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.channels && data.channels.length > 0) {
            displayChannels(data.channels);
        } else {
            displayEmptyState();
        }
    } catch (error) {
        console.error('Error loading channels:', error);
        container.innerHTML = `
            <div class="message error">
                Failed to load channels. Please try refreshing the page.
            </div>
        `;
    }
}

// Display channels in grid
function displayChannels(channels) {
    const container = document.getElementById('channelsContainer');

    const gridHTML = `
        <div class="channels-grid">
            ${channels.map(channel => createChannelCard(channel)).join('')}
        </div>
    `;

    container.innerHTML = gridHTML;

    // Attach event listeners to all buttons
    channels.forEach(channel => {
        const syncBtn = document.getElementById(`sync-${channel.id}`);
        const deleteBtn = document.getElementById(`delete-${channel.id}`);

        if (syncBtn) {
            syncBtn.addEventListener('click', () => handleSyncChannel(channel.id));
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => handleDeleteChannel(channel.id, channel.channel_name));
        }
    });
}

// Create HTML for a single channel card
function createChannelCard(channel) {
    const thumbnailUrl = channel.thumbnail_url || 'https://via.placeholder.com/300x150?text=No+Thumbnail';
    const createdDate = new Date(channel.created_at).toLocaleDateString();

    return `
        <div class="channel-card" data-channel-id="${channel.id}">
            <img src="${thumbnailUrl}" alt="${channel.channel_name}" class="channel-thumbnail">
            <div class="channel-info">
                <div class="channel-name">${escapeHtml(channel.channel_name)}</div>
                <div class="channel-meta">Added: ${createdDate}</div>
                <div class="channel-actions">
                    <button class="btn-sync" id="sync-${channel.id}">Sync Videos</button>
                    <button class="btn-delete" id="delete-${channel.id}">Delete</button>
                </div>
            </div>
        </div>
    `;
}

// Display empty state when no channels
function displayEmptyState() {
    const container = document.getElementById('channelsContainer');
    container.innerHTML = `
        <div class="empty-state">
            <h3>No Channels Yet</h3>
            <p>Add your first YouTube channel using the form above to get started.</p>
        </div>
    `;
}

// Handle add channel form submission
async function handleAddChannel(event) {
    event.preventDefault();

    const form = event.target;
    const urlInput = document.getElementById('channelUrl');
    const submitBtn = document.getElementById('addChannelBtn');
    const channelUrl = urlInput.value.trim();

    if (!channelUrl) {
        showMessage('Please enter a YouTube channel URL', 'error');
        return;
    }

    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';

    try {
        const response = await fetch('/api/channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel_url: channelUrl })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message || 'Channel added successfully!', 'success');
            urlInput.value = '';
            // Reload channels list
            setTimeout(() => loadChannels(), 500);
        } else {
            showMessage(data.error || 'Failed to add channel', 'error');
        }
    } catch (error) {
        console.error('Error adding channel:', error);
        showMessage('Failed to add channel. Please try again.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add Channel';
    }
}

// Handle sync channel button click
async function handleSyncChannel(channelId) {
    const syncBtn = document.getElementById(`sync-${channelId}`);

    if (!syncBtn) return;

    // Disable button during sync
    syncBtn.disabled = true;
    const originalText = syncBtn.textContent;
    syncBtn.textContent = 'Syncing...';

    try {
        const response = await fetch(`/api/sync/channel/${channelId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message || 'Channel synced successfully!', 'success');
            // Reload pending count after successful sync
            await loadPendingCount();
        } else {
            showMessage(data.error || 'Failed to sync channel', 'error');
        }
    } catch (error) {
        console.error('Error syncing channel:', error);
        showMessage('Failed to sync channel. Please try again.', 'error');
    } finally {
        syncBtn.disabled = false;
        syncBtn.textContent = originalText;
    }
}

// Handle delete channel button click
async function handleDeleteChannel(channelId, channelName) {
    // Confirm deletion
    const confirmed = confirm(`Are you sure you want to delete "${channelName}"? This will also delete all associated videos and summaries.`);

    if (!confirmed) return;

    const deleteBtn = document.getElementById(`delete-${channelId}`);

    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.textContent = 'Deleting...';
    }

    try {
        const response = await fetch(`/api/channels/${channelId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message || 'Channel deleted successfully!', 'success');
            // Remove card from UI
            const card = document.querySelector(`[data-channel-id="${channelId}"]`);
            if (card) {
                card.style.transition = 'opacity 0.3s';
                card.style.opacity = '0';
                setTimeout(() => {
                    card.remove();
                    // Check if we need to show empty state
                    const remainingCards = document.querySelectorAll('.channel-card');
                    if (remainingCards.length === 0) {
                        displayEmptyState();
                    }
                }, 300);
            }
        } else {
            showMessage(data.error || 'Failed to delete channel', 'error');
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.textContent = 'Delete';
            }
        }
    } catch (error) {
        console.error('Error deleting channel:', error);
        showMessage('Failed to delete channel. Please try again.', 'error');
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.textContent = 'Delete';
        }
    }
}

// Show message to user
function showMessage(text, type) {
    const container = document.getElementById('messageContainer');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;

    container.appendChild(messageDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.transition = 'opacity 0.3s';
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load pending videos count from API
async function loadPendingCount() {
    try {
        const response = await fetch('/api/stats');

        if (!response.ok) {
            console.error('Failed to load pending count:', response.status);
            return;
        }

        const data = await response.json();
        const pendingCount = data.pending_processing || 0;

        // Update the count display
        const countElement = document.getElementById('pendingCount');
        if (countElement) {
            countElement.textContent = pendingCount;
        }

        // Show or hide the processing section based on pending count
        const processingSection = document.getElementById('processPendingSection');
        if (processingSection) {
            processingSection.style.display = pendingCount > 0 ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error loading pending count:', error);
    }
}

// Handle process pending videos button click
async function handleProcessPending() {
    const processPendingBtn = document.getElementById('processPendingBtn');
    const progressDiv = document.getElementById('processingProgress');
    const statusText = document.getElementById('processingStatus');

    if (!processPendingBtn || !progressDiv || !statusText) return;

    // Disable button and show progress
    processPendingBtn.disabled = true;
    progressDiv.style.display = 'block';
    statusText.textContent = 'Processing videos...';

    try {
        const response = await fetch('/api/process/pending', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ batch_size: 5 })
        });

        const data = await response.json();

        if (response.ok) {
            const processed = data.processed || 0;
            const failed = data.failed || 0;
            const remaining = data.remaining || 0;

            let message = `Processed ${processed} video(s)`;
            if (failed > 0) {
                message += `, ${failed} failed`;
            }
            if (remaining > 0) {
                message += `. ${remaining} video(s) remaining.`;
            } else {
                message += '. All videos processed!';
            }

            showMessage(message, 'success');

            // Reload pending count
            await loadPendingCount();

            // If there are still videos remaining, suggest processing again
            if (remaining > 0) {
                statusText.textContent = `${remaining} video(s) still pending. Click again to continue processing.`;
            }
        } else {
            showMessage(data.error || 'Failed to process videos', 'error');
        }
    } catch (error) {
        console.error('Error processing pending videos:', error);
        showMessage('Failed to process videos. Please try again.', 'error');
    } finally {
        processPendingBtn.disabled = false;
        // Hide progress indicator after a short delay if no more videos
        setTimeout(() => {
            const countElement = document.getElementById('pendingCount');
            const count = parseInt(countElement?.textContent || '0');
            if (count === 0) {
                progressDiv.style.display = 'none';
            }
        }, 2000);
    }
}