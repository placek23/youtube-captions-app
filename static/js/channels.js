// Channel Management JavaScript

// Track selected channels
let selectedChannels = new Set();

// Load channels when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChannels();

    // Setup form submission
    const form = document.getElementById('addChannelForm');
    form.addEventListener('submit', handleAddChannel);

    // Setup bulk actions
    const selectAllBtn = document.getElementById('selectAllBtn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', handleSelectAll);
    }

    const bulkSyncBtn = document.getElementById('bulkSyncBtn');
    if (bulkSyncBtn) {
        bulkSyncBtn.addEventListener('click', handleBulkSync);
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

    // Show bulk actions if there are channels
    const bulkActionsContainer = document.getElementById('bulkActionsContainer');
    if (bulkActionsContainer) {
        bulkActionsContainer.style.display = channels.length > 0 ? 'flex' : 'none';
    }

    // Attach event listeners to all buttons and checkboxes
    channels.forEach(channel => {
        const checkbox = document.getElementById(`checkbox-${channel.id}`);
        const syncBtn = document.getElementById(`sync-${channel.id}`);
        const deleteBtn = document.getElementById(`delete-${channel.id}`);

        if (checkbox) {
            checkbox.addEventListener('change', (e) => handleCheckboxChange(channel.id, e.target.checked));
        }

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
            <input type="checkbox" class="channel-select-checkbox" id="checkbox-${channel.id}" />
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

// Handle checkbox change
function handleCheckboxChange(channelId, isChecked) {
    if (isChecked) {
        selectedChannels.add(channelId);
    } else {
        selectedChannels.delete(channelId);
    }

    // Update the selected card styling
    const card = document.querySelector(`[data-channel-id="${channelId}"]`);
    if (card) {
        if (isChecked) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    }

    updateSelectedCount();
}

// Update selected count display
function updateSelectedCount() {
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedChannels.size;
    }

    // Update select all button text
    const selectAllBtn = document.getElementById('selectAllBtn');
    const totalCheckboxes = document.querySelectorAll('.channel-select-checkbox').length;
    if (selectAllBtn) {
        if (selectedChannels.size === totalCheckboxes && totalCheckboxes > 0) {
            selectAllBtn.textContent = 'Deselect All';
        } else {
            selectAllBtn.textContent = 'Select All';
        }
    }
}

// Handle select all button click
function handleSelectAll() {
    const checkboxes = document.querySelectorAll('.channel-select-checkbox');
    const selectAllBtn = document.getElementById('selectAllBtn');

    // If all are selected, deselect all. Otherwise, select all.
    const shouldSelect = selectedChannels.size !== checkboxes.length;

    checkboxes.forEach(checkbox => {
        checkbox.checked = shouldSelect;
        const channelId = parseInt(checkbox.id.replace('checkbox-', ''));
        handleCheckboxChange(channelId, shouldSelect);
    });
}

// Handle bulk sync button click
async function handleBulkSync() {
    if (selectedChannels.size === 0) {
        showMessage('Please select at least one channel to sync', 'error');
        return;
    }

    const bulkSyncBtn = document.getElementById('bulkSyncBtn');
    if (!bulkSyncBtn) return;

    // Disable button during sync
    bulkSyncBtn.disabled = true;
    const originalText = bulkSyncBtn.innerHTML;
    bulkSyncBtn.innerHTML = 'Syncing...';

    try {
        const response = await fetch('/api/sync/channels/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                channel_ids: Array.from(selectedChannels),
                max_videos: 50
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message || 'Channels synced successfully!', 'success');

            // Clear selections
            selectedChannels.clear();
            document.querySelectorAll('.channel-select-checkbox').forEach(cb => {
                cb.checked = false;
            });
            document.querySelectorAll('.channel-card').forEach(card => {
                card.classList.remove('selected');
            });
            updateSelectedCount();

            // Show any failed channels
            if (data.failed_channels && data.failed_channels.length > 0) {
                console.error('Failed channels:', data.failed_channels);
            }
        } else {
            showMessage(data.error || 'Failed to sync channels', 'error');
        }
    } catch (error) {
        console.error('Error syncing channels:', error);
        showMessage('Failed to sync channels. Please try again.', 'error');
    } finally {
        bulkSyncBtn.disabled = false;
        bulkSyncBtn.innerHTML = originalText;
    }
}