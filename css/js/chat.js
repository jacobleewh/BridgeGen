// Initialize Socket.IO
var socket = io();

// Get current user info - try multiple methods
var currentUser = window.currentUsernameFromTemplate || document.querySelector('body').dataset.username || "";
var currentUserId = window.currentUserIdFromTemplate || parseInt(document.querySelector('body').dataset.userId) || null;
var activeUserId = null;
var activeUserName = null;

// Global variables for message operations
let currentContextMessageId = null;
let currentContextMessageElement = null;
let currentEditingMessage = null;

// Debug logging
console.log('=== CHAT INITIALIZATION ===');
console.log('Current User:', currentUser);
console.log('Current User ID:', currentUserId);
console.log('Socket.IO:', socket);

// Error checking
if (!currentUserId) {
    console.error('CRITICAL ERROR: currentUserId is not set! Chat will not work properly.');
    console.log('Body dataset:', document.querySelector('body').dataset);
    console.log('Window variables:', {
        currentUserIdFromTemplate: window.currentUserIdFromTemplate,
        currentUsernameFromTemplate: window.currentUsernameFromTemplate
    });
}

// Join user's personal room
if (currentUser) {
    socket.emit('join', { username: currentUser });
    console.log('Emitted join event with username:', currentUser);
} else {
    console.error('Cannot join room - no username');
}

// ============================================================
// TIMESTAMP FORMATTING FUNCTIONS (SINGAPORE STANDARD TIME)
// ============================================================

// Singapore timezone constant
const SST_TZ = 'Asia/Singapore'; // Singapore Standard Time (GMT+8)

/**
 * Format time for display in chat (Singapore Standard Time - SST/GMT+8)
 * Handles both message timestamps and contact list timestamps
 * @param {string|Date} dateString - The timestamp to format
 * @returns {string} Formatted time string
 */
function formatTime(dateString) {
    // Handle invalid input
    if (!dateString) return '';
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        console.error('Invalid date:', dateString);
        return '';
    }
    
    // Get current time
    const now = new Date();
    
    // Create formatter for Singapore timezone
    const sstFormatter = new Intl.DateTimeFormat('en-SG', {
        timeZone: SST_TZ,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
    
    // Get dates in Singapore timezone for comparison
    const dateInSST = sstFormatter.format(date);
    const todayInSST = sstFormatter.format(now);
    
    // Calculate yesterday in Singapore timezone
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayInSST = sstFormatter.format(yesterday);
    
    // Same day - show time only (HH:MM in Singapore time)
    if (dateInSST === todayInSST) {
        return date.toLocaleTimeString('en-SG', {
            timeZone: SST_TZ,
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    }
    
    // Yesterday
    if (dateInSST === yesterdayInSST) {
        return 'Yesterday';
    }
    
    // Within the last 7 days - show day name
    const weekAgo = new Date(now);
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    if (date > weekAgo) {
        return date.toLocaleDateString('en-SG', {
            timeZone: SST_TZ,
            weekday: 'short'
        });
    }
    
    // Older than a week - show date (DD/MM format)
    return date.toLocaleDateString('en-SG', {
        timeZone: SST_TZ,
        day: '2-digit',
        month: '2-digit'
    });
}

/**
 * Format message time - shows exact time for message bubbles (Singapore Standard Time - SST/GMT+8)
 * @param {string|Date} dateString - The timestamp to format
 * @returns {string} Formatted time string (HH:MM)
 */
function formatMessageTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        console.error('Invalid date:', dateString);
        return '';
    }
    
    // Format time in Singapore timezone (HH:MM format, 24-hour)
    return date.toLocaleTimeString('en-SG', {
        timeZone: SST_TZ,
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

/**
 * Format date for date separators in chat (Singapore Standard Time - SST/GMT+8)
 * @param {string} dateString - The date to format
 * @returns {string} Formatted date string
 */
function formatDateSeparator(dateString) {
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) {
        return '';
    }
    
    const now = new Date();
    
    // Create formatter for Singapore timezone
    const sstFormatter = new Intl.DateTimeFormat('en-SG', {
        timeZone: SST_TZ,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
    
    const dateInSST = sstFormatter.format(date);
    const todayInSST = sstFormatter.format(now);
    
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayInSST = sstFormatter.format(yesterday);
    
    // Check if today (in Singapore time)
    if (dateInSST === todayInSST) {
        return 'Today';
    }
    
    // Check if yesterday (in Singapore time)
    if (dateInSST === yesterdayInSST) {
        return 'Yesterday';
    }
    
    // Otherwise show full date (in Singapore time)
    return date.toLocaleDateString('en-SG', {
        timeZone: SST_TZ,
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

/**
 * Update all contact timestamps periodically
 */
function updateAllContactTimestamps() {
    document.querySelectorAll('[id^="last-time-"]').forEach(timeEl => {
        const timestamp = timeEl.dataset.timestamp;
        if (timestamp) {
            timeEl.textContent = formatTime(timestamp);
        }
    });
}

// ============================================================
// SOCKET.IO EVENT HANDLERS
// ============================================================

// Handle incoming messages
socket.on('receive_message', function(data) {
    console.log('Received message:', data);
    console.log('Active user ID:', activeUserId);
    console.log('Message involves:', data.sender_id, 'and', data.receiver_id);
    
    // Update last message in contact list
    const displayMessage = data.message || (data.attachment_url ? '📎 Attachment' : '');
    updateContactLastMessage(data.sender_id, data.receiver_id, displayMessage, data.timestamp);
    
    // Check if this message is part of the active conversation
    const isActiveChat = (data.sender_id === currentUserId && data.receiver_id === activeUserId) ||
                         (data.sender_id === activeUserId && data.receiver_id === currentUserId);
    
    if (isActiveChat) {
        console.log('Displaying message in active chat');
        appendMessage(data);
    } else {
        console.log('Message not for active chat, showing badge');
        if (data.sender_id !== currentUserId) {
            incrementUnreadCount(data.sender_id);
        }
    }
});

// Handle message edited by other user
socket.on('message_edited', function(data) {
    console.log('Message edited event:', data);
    
    const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
    if (messageElement) {
        const messageBubble = messageElement.querySelector('.message-bubble');
        const messageData = JSON.parse(messageElement.dataset.message || '{}');
        
        messageBubble.innerHTML = `
            <p class="message-text">${escapeHtml(data.new_text)}<span class="message-edited">(edited)</span></p>
            <div class="message-time">${formatMessageTime(messageData.timestamp)}</div>
        `;
        
        messageData.message = data.new_text;
        messageData.edited = true;
        messageElement.dataset.message = JSON.stringify(messageData);
    }
});

// Handle message deleted by other user
socket.on('message_deleted', function(data) {
    console.log('Message deleted event:', data);
    
    const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
    if (messageElement) {
        messageElement.remove();
    }
});

// Handle typing indicator
socket.on('user_typing', function(data) {
    if (data.user_id === activeUserId) {
        showTypingIndicator();
    }
});

socket.on('user_stop_typing', function(data) {
    if (data.user_id === activeUserId) {
        hideTypingIndicator();
    }
});

// ============================================================
// CHAT FUNCTIONS
// ============================================================

// Open chat with a user
function openChat(userId, username, avatar) {
    console.log('=== OPENING CHAT ===');
    console.log('User ID:', userId, 'Username:', username);
    
    activeUserId = userId;
    activeUserName = username;
    window.activeUserId = userId;
    window.activeUserName = username;
    
    // Hide empty state, show active chat
    const chatEmpty = document.querySelector('.chat-empty');
    const chatActive = document.getElementById('chatActive');
    
    if (chatEmpty) chatEmpty.style.display = 'none';
    if (chatActive) chatActive.style.display = 'flex';
    
    // Update chat header
    const avatarEl = document.getElementById('activeUserAvatar');
    const nameEl = document.getElementById('activeUserName');
    
    if (avatarEl) avatarEl.src = avatar;
    if (nameEl) nameEl.textContent = username;
    
    // Highlight active contact
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeContact = document.querySelector(`[data-user-id="${userId}"]`);
    if (activeContact) {
        activeContact.classList.add('active');
    }
    
    // Clear unread badge
    const unreadBadge = document.getElementById(`unread-${userId}`);
    if (unreadBadge) {
        unreadBadge.style.display = 'none';
        unreadBadge.textContent = '0';
    }
    
    // Load chat history
    loadChatHistory(userId);
}

// Load chat history from server
function loadChatHistory(userId) {
    fetch(`/chat/history/${userId}`)
        .then(response => response.json())
        .then(data => {
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML = '';
            
            let lastDate = null;
            data.messages.forEach(msg => {
                const msgDate = new Date(msg.timestamp).toDateString();
                if (msgDate !== lastDate) {
                    addDateSeparator(msg.timestamp);
                    lastDate = msgDate;
                }
                
                appendMessage(msg, false);
            });
            
            if (data.messages.length > 0) {
                const lastMsg = data.messages[data.messages.length - 1];
                const displayMessage = lastMsg.message || (lastMsg.attachment_url ? '📎 Attachment' : '');
                updateContactLastMessage(lastMsg.sender_id, lastMsg.receiver_id, displayMessage, lastMsg.timestamp);
            }
            
            scrollToBottom();
        })
        .catch(error => console.error('Error loading chat history:', error));
}

// ============================================================
// MESSAGE SENDING FUNCTIONS
// ============================================================

/**
 * Main send message function
 */
function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!activeUserId) {
        console.error('No active user selected');
        alert('Please select a chat first');
        return;
    }
    
    // Check if we have a file attachment
    if (window.selectedFile) {
        sendMessageWithFile(message);
        return;
    }
    
    // Send text message only
    if (message === '') return;
    
    const messageData = {
        receiver_id: activeUserId,
        message: message,
        timestamp: new Date().toISOString()
    };
    
    socket.emit('send_message', messageData);
    input.value = '';
}

/**
 * Send message with file attachment
 */
function sendMessageWithFile(message) {
    const formData = new FormData();
    formData.append('file', window.selectedFile);
    formData.append('receiver_id', activeUserId);
    
    if (message) {
        formData.append('message', message);
    }
    
    const input = document.getElementById('messageInput');
    const originalPlaceholder = input.placeholder;
    input.placeholder = 'Sending file...';
    input.disabled = true;
    
    fetch('/chat/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            input.value = '';
            input.placeholder = originalPlaceholder;
            input.disabled = false;
            removeFile();
            
            if (data.message) {
                appendMessage(data.message);
            }
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        alert('Failed to send file: ' + error.message);
        input.placeholder = originalPlaceholder;
        input.disabled = false;
    });
}

// ============================================================
// MESSAGE DISPLAY FUNCTIONS
// ============================================================

/**
 * Append message to chat window with edit/delete options
 */
function appendMessage(data, scroll = true) {
    const messagesDiv = document.getElementById('chatMessages');
    const isSent = data.sender_id === currentUserId;
    
    const messageWrapper = document.createElement('div');
    messageWrapper.className = `message-wrapper ${isSent ? 'sent' : 'received'}`;
    messageWrapper.dataset.messageId = data.id;
    messageWrapper.dataset.message = JSON.stringify(data);
    
    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';
    messageBubble.style.position = 'relative';
    
    // Add attachment if exists
    if (data.attachment_url) {
        const attachment = createAttachmentElement(data);
        messageBubble.appendChild(attachment);
    }
    
    // Add text if exists
    if (data.message) {
        const messageText = document.createElement('p');
        messageText.className = 'message-text';
        messageText.textContent = data.message;
        
        if (data.edited) {
            const editedSpan = document.createElement('span');
            editedSpan.className = 'message-edited';
            editedSpan.textContent = '(edited)';
            messageText.appendChild(editedSpan);
        }
        
        messageBubble.appendChild(messageText);
    }
    
    // Add timestamp
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatMessageTime(data.timestamp);
    messageBubble.appendChild(messageTime);
    
    // Add options button for sent messages
    if (isSent) {
        const optionsBtn = document.createElement('div');
        optionsBtn.className = 'message-options';
        optionsBtn.innerHTML = `
            <button class="message-options-btn" onclick="showMessageContextMenu(event, ${data.id}, this.closest('.message-wrapper'))">
                <i class="fas fa-ellipsis-v"></i>
            </button>
        `;
        messageBubble.appendChild(optionsBtn);
    }
    
    messageWrapper.appendChild(messageBubble);
    messagesDiv.appendChild(messageWrapper);
    
    if (scroll) {
        scrollToBottom();
    }
}

/**
 * Create attachment element for message
 */
function createAttachmentElement(data) {
    const fileType = data.attachment_type || 'application/octet-stream';
    
    // Handle images
    if (fileType.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = data.attachment_url;
        img.className = 'message-image';
        img.alt = data.attachment_name || 'Image';
        img.onclick = () => window.open(data.attachment_url, '_blank');
        return img;
    }
    
    // Handle other files
    const attachmentDiv = document.createElement('div');
    attachmentDiv.className = 'message-attachment';
    
    const icon = document.createElement('i');
    icon.className = `${getFileIcon(fileType)} message-attachment-icon`;
    
    const info = document.createElement('div');
    info.className = 'message-attachment-info';
    
    const name = document.createElement('div');
    name.className = 'message-attachment-name';
    name.textContent = data.attachment_name || 'File';
    
    const size = document.createElement('div');
    size.className = 'message-attachment-size';
    size.textContent = data.attachment_size ? formatFileSize(data.attachment_size) : '';
    
    info.appendChild(name);
    info.appendChild(size);
    
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'message-attachment-download';
    downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
    downloadBtn.onclick = () => {
        const link = document.createElement('a');
        link.href = data.attachment_url;
        link.download = data.attachment_name || 'file';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
    
    attachmentDiv.appendChild(icon);
    attachmentDiv.appendChild(info);
    attachmentDiv.appendChild(downloadBtn);
    
    return attachmentDiv;
}

// ============================================================
// FILE HANDLING FUNCTIONS
// ============================================================

function getFileIcon(fileType) {
    if (!fileType) return 'fas fa-file';
    const type = fileType.toLowerCase();
    if (type.startsWith('image/')) return 'fas fa-image';
    if (type.includes('pdf')) return 'fas fa-file-pdf';
    if (type.includes('word') || type.includes('document')) return 'fas fa-file-word';
    if (type.includes('text')) return 'fas fa-file-alt';
    if (type.includes('excel') || type.includes('sheet')) return 'fas fa-file-excel';
    if (type.includes('powerpoint') || type.includes('presentation')) return 'fas fa-file-powerpoint';
    if (type.includes('zip') || type.includes('rar')) return 'fas fa-file-archive';
    if (type.includes('audio')) return 'fas fa-file-audio';
    if (type.includes('video')) return 'fas fa-file-video';
    return 'fas fa-file';
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
        alert('File size must be less than 10MB');
        event.target.value = '';
        return;
    }
    
    window.selectedFile = file;
    
    const previewArea = document.getElementById('filePreviewArea');
    const fileSize = formatFileSize(file.size);
    const icon = getFileIcon(file.type);
    
    previewArea.innerHTML = `
        <div class="file-preview">
            <i class="${icon} file-preview-icon"></i>
            <div class="file-preview-info">
                <div class="file-preview-name">${escapeHtml(file.name)}</div>
                <div class="file-preview-size">${fileSize}</div>
            </div>
            <button class="file-preview-remove" onclick="removeFile()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
}

function removeFile() {
    window.selectedFile = null;
    const previewArea = document.getElementById('filePreviewArea');
    if (previewArea) previewArea.innerHTML = '';
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.value = '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// MESSAGE CONTEXT MENU FUNCTIONS
// ============================================================

function showMessageContextMenu(e, messageId, messageElement) {
    e.preventDefault();
    e.stopPropagation();
    
    const menu = document.getElementById('messageContextMenu');
    const messageData = JSON.parse(messageElement.dataset.message || '{}');
    
    currentContextMessageId = messageId;
    currentContextMessageElement = messageElement;
    
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.classList.add('active');
    
    // Hide edit option if message has attachment
    const editItem = menu.querySelector('.context-menu-item:nth-child(1)');
    if (messageData.attachment_url) {
        editItem.style.display = 'none';
    } else {
        editItem.style.display = 'flex';
    }
    
    setTimeout(() => {
        document.addEventListener('click', closeContextMenuOutside);
    }, 0);
}

function closeContextMenuOutside(e) {
    const menu = document.getElementById('messageContextMenu');
    if (!menu.contains(e.target)) {
        closeContextMenu();
    }
}

function closeContextMenu() {
    const menu = document.getElementById('messageContextMenu');
    menu.classList.remove('active');
    document.removeEventListener('click', closeContextMenuOutside);
}

// ============================================================
// MESSAGE EDIT FUNCTIONALITY
// ============================================================

function editMessage() {
    closeContextMenu();
    
    if (!currentContextMessageElement) return;
    
    const messageBubble = currentContextMessageElement.querySelector('.message-bubble');
    const messageText = currentContextMessageElement.querySelector('.message-text');
    
    if (!messageText) {
        alert('Cannot edit messages with attachments');
        return;
    }
    
    const originalText = messageText.textContent.replace('(edited)', '').trim();
    currentEditingMessage = {
        id: currentContextMessageId,
        element: currentContextMessageElement,
        originalText: originalText
    };
    
    const editHTML = `
        <textarea class="message-edit-input" rows="3">${escapeHtml(originalText)}</textarea>
        <div class="message-edit-actions">
            <button class="btn-edit-cancel" onclick="cancelEdit()">Cancel</button>
            <button class="btn-edit-save" onclick="saveEdit()">Save</button>
        </div>
    `;
    
    messageBubble.innerHTML = editHTML;
    messageBubble.classList.add('message-editing');
    
    const textarea = messageBubble.querySelector('.message-edit-input');
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            saveEdit();
        }
        if (e.key === 'Escape') {
            cancelEdit();
        }
    });
}

function saveEdit() {
    if (!currentEditingMessage) return;
    
    const textarea = currentEditingMessage.element.querySelector('.message-edit-input');
    const newText = textarea.value.trim();
    
    if (!newText) {
        alert('Message cannot be empty');
        return;
    }
    
    if (newText === currentEditingMessage.originalText) {
        cancelEdit();
        return;
    }
    
    fetch(`/chat/message/${currentEditingMessage.id}/edit`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: newText })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const messageBubble = currentEditingMessage.element.querySelector('.message-bubble');
            const messageData = JSON.parse(currentEditingMessage.element.dataset.message || '{}');
            
            messageBubble.innerHTML = `
                <p class="message-text">${escapeHtml(newText)}<span class="message-edited">(edited)</span></p>
                <div class="message-time">${formatMessageTime(messageData.timestamp)}</div>
                <div class="message-options">
                    <button class="message-options-btn" onclick="showMessageContextMenu(event, ${currentEditingMessage.id}, this.closest('.message-wrapper'))">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            `;
            messageBubble.classList.remove('message-editing');
            
            messageData.message = newText;
            messageData.edited = true;
            currentEditingMessage.element.dataset.message = JSON.stringify(messageData);
            
            socket.emit('message_edited', {
                message_id: currentEditingMessage.id,
                new_text: newText,
                receiver_id: activeUserId
            });
            
            currentEditingMessage = null;
        } else {
            alert('Failed to edit message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error editing message:', error);
        alert('Failed to edit message');
    });
}

function cancelEdit() {
    if (!currentEditingMessage) return;
    
    const messageBubble = currentEditingMessage.element.querySelector('.message-bubble');
    const messageData = JSON.parse(currentEditingMessage.element.dataset.message || '{}');
    
    messageBubble.innerHTML = `
        <p class="message-text">${escapeHtml(currentEditingMessage.originalText)}${messageData.edited ? '<span class="message-edited">(edited)</span>' : ''}</p>
        <div class="message-time">${formatMessageTime(messageData.timestamp)}</div>
        <div class="message-options">
            <button class="message-options-btn" onclick="showMessageContextMenu(event, ${messageData.id}, this.closest('.message-wrapper'))">
                <i class="fas fa-ellipsis-v"></i>
            </button>
        </div>
    `;
    messageBubble.classList.remove('message-editing');
    
    currentEditingMessage = null;
}

// ============================================================
// MESSAGE COPY/DELETE FUNCTIONALITY
// ============================================================

function copyMessage() {
    closeContextMenu();
    
    if (!currentContextMessageElement) return;
    
    const messageText = currentContextMessageElement.querySelector('.message-text');
    if (!messageText) {
        alert('No text to copy');
        return;
    }
    
    const text = messageText.textContent.replace('(edited)', '').trim();
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Message copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy message:', err);
        alert('Failed to copy message');
    });
}

function confirmDeleteMessage() {
    closeContextMenu();
    showConfirmation(
        'Delete Message',
        'Are you sure you want to delete this message? This action cannot be undone.',
        deleteMessageConfirmed
    );
}

function deleteMessageConfirmed() {
    if (!currentContextMessageId || !currentContextMessageElement) return;
    
    fetch(`/chat/message/${currentContextMessageId}/delete`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentContextMessageElement.remove();
            
            socket.emit('message_deleted', {
                message_id: currentContextMessageId,
                receiver_id: activeUserId
            });
            
            showNotification('Message deleted');
        } else {
            alert('Failed to delete message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error deleting message:', error);
        alert('Failed to delete message');
    });
}

// ============================================================
// CONFIRMATION MODAL FUNCTIONS
// ============================================================

function showConfirmation(title, message, onConfirm) {
    const modal = document.getElementById('confirmationModal');
    const titleEl = document.getElementById('confirmationTitle');
    const messageEl = document.getElementById('confirmationMessage');
    const confirmBtn = document.getElementById('confirmButton');
    
    titleEl.textContent = title;
    messageEl.textContent = message;
    modal.classList.add('active');
    
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', () => {
        onConfirm();
        closeConfirmationModal();
    });
}

function closeConfirmationModal() {
    const modal = document.getElementById('confirmationModal');
    modal.classList.remove('active');
}

// ============================================================
// HEADER MENU AND FRIEND REMOVAL
// ============================================================

function toggleHeaderMenu() {
    const menu = document.getElementById('headerMenu');
    menu.classList.toggle('active');
    
    if (menu.classList.contains('active')) {
        setTimeout(() => {
            document.addEventListener('click', closeHeaderMenuOutside);
        }, 0);
    }
}

function closeHeaderMenuOutside(e) {
    const menu = document.getElementById('headerMenu');
    if (!menu.contains(e.target) && !e.target.closest('.btn-icon')) {
        menu.classList.remove('active');
        document.removeEventListener('click', closeHeaderMenuOutside);
    }
}

function closeHeaderMenu() {
    document.getElementById('headerMenu').classList.remove('active');
}

function viewProfile() {
    if (window.activeUserId) {
        window.location.href = `/profile/${window.activeUserId}`;
    }
    closeHeaderMenu();
}

function clearChat() {
    showConfirmation(
        'Clear Chat History',
        'Are you sure you want to delete all messages with this user? This action cannot be undone.',
        clearChatConfirmed
    );
    closeHeaderMenu();
}

function clearChatConfirmed() {
    if (!window.activeUserId) return;
    
    fetch(`/chat/clear/${window.activeUserId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('chatMessages').innerHTML = '';
            showNotification('Chat history cleared');
        } else {
            alert('Failed to clear chat: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error clearing chat:', error);
        alert('Failed to clear chat');
    });
}

function confirmRemoveFriend() {
    showConfirmation(
        'Remove Friend',
        `Are you sure you want to remove ${window.activeUserName} from your friends? You won't be able to message each other anymore.`,
        removeFriendConfirmed
    );
    closeHeaderMenu();
}

function removeFriendConfirmed() {
    if (!window.activeUserId) return;
    
    fetch(`/remove_friend/${window.activeUserId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const contactItem = document.querySelector(`[data-user-id="${window.activeUserId}"]`);
            if (contactItem) {
                contactItem.remove();
            }
            
            document.getElementById('chatActive').style.display = 'none';
            document.querySelector('.chat-empty').style.display = 'flex';
            
            showNotification('Friend removed');
        } else {
            alert('Failed to remove friend: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error removing friend:', error);
        alert('Failed to remove friend');
    });
}

// ============================================================
// UI HELPER FUNCTIONS
// ============================================================

function addDateSeparator(dateString) {
    const messagesDiv = document.getElementById('chatMessages');
    const separator = document.createElement('div');
    separator.className = 'date-separator';
    separator.textContent = formatDateSeparator(dateString);
    messagesDiv.appendChild(separator);
}

function updateContactLastMessage(senderId, receiverId, message, timestamp) {
    const contactUserId = (senderId === currentUserId) ? receiverId : senderId;
    
    const lastMsgEl = document.getElementById(`last-msg-${contactUserId}`);
    const lastTimeEl = document.getElementById(`last-time-${contactUserId}`);
    
    if (lastMsgEl && message) {
        const displayMsg = message.length > 40 ? message.substring(0, 40) + '...' : message;
        lastMsgEl.textContent = displayMsg;
    }
    
    if (lastTimeEl && timestamp) {
        lastTimeEl.dataset.timestamp = timestamp;
        lastTimeEl.textContent = formatTime(timestamp);
    }
    
    const contactItem = document.querySelector(`[data-user-id="${contactUserId}"]`);
    if (contactItem) {
        const contactList = document.getElementById('contactList');
        if (contactList.firstChild !== contactItem) {
            contactList.insertBefore(contactItem, contactList.firstChild);
        }
    }
}

function incrementUnreadCount(userId) {
    const unreadBadge = document.getElementById(`unread-${userId}`);
    if (unreadBadge) {
        const currentCount = parseInt(unreadBadge.textContent) || 0;
        unreadBadge.textContent = currentCount + 1;
        unreadBadge.style.display = 'inline-block';
    }
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('chatMessages');
    if (messagesDiv) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: #4A90E2;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 3000;
        opacity: 0;
        transform: translateX(400px);
        transition: all 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================================
// TYPING INDICATOR
// ============================================================

let typingTimeout;
const messageInput = document.getElementById('messageInput');

if (messageInput) {
    messageInput.addEventListener('input', function() {
        if (activeUserId) {
            socket.emit('typing', { user_id: activeUserId });
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                socket.emit('stop_typing', { user_id: activeUserId });
            }, 1000);
        }
    });
}

function showTypingIndicator() {
    const messagesDiv = document.getElementById('chatMessages');
    const existingIndicator = messagesDiv.querySelector('.typing-indicator');
    
    if (!existingIndicator) {
        const indicator = document.createElement('div');
        indicator.className = 'message-wrapper received';
        indicator.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesDiv.appendChild(indicator);
        scrollToBottom();
    }
}

function hideTypingIndicator() {
    const indicator = document.querySelector('.typing-indicator');
    if (indicator) {
        indicator.parentElement.remove();
    }
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// ============================================================
// TAB SWITCHING & SEARCH
// ============================================================

document.querySelectorAll('.chat-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
    });
});

const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        document.querySelectorAll('.contact-item').forEach(contact => {
            const name = contact.querySelector('.contact-name').textContent.toLowerCase();
            const message = contact.querySelector('.contact-message').textContent.toLowerCase();
            
            if (name.includes(searchTerm) || message.includes(searchTerm)) {
                contact.style.display = 'flex';
            } else {
                contact.style.display = 'none';
            }
        });
    });
}

// ============================================================
// NEW CHAT MODAL
// ============================================================

function showNewChatModal() {
    const modal = document.getElementById('newChatModal');
    if (modal) modal.style.display = 'flex';
}

function closeNewChatModal() {
    const modal = document.getElementById('newChatModal');
    if (modal) modal.style.display = 'none';
}

function startNewChat(userId, username, avatar) {
    closeNewChatModal();
    openChat(userId, username, avatar);
}

// ============================================================
// AUTO-SCROLL ON NEW MESSAGES
// ============================================================

const observer = new MutationObserver(() => {
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return;
    
    const isScrolledToBottom = messagesDiv.scrollHeight - messagesDiv.clientHeight <= messagesDiv.scrollTop + 50;
    if (isScrolledToBottom) scrollToBottom();
});

const chatMessagesDiv = document.getElementById('chatMessages');
if (chatMessagesDiv) {
    observer.observe(chatMessagesDiv, { childList: true });
}

// ============================================================
// EVENT LISTENERS & INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, attaching contact click handlers...');
    
    document.querySelectorAll('.contact-item').forEach(item => {
        item.addEventListener('click', function() {
            const userId = parseInt(this.dataset.userId);
            const username = this.dataset.username;
            const avatar = this.dataset.avatar;
            openChat(userId, username, avatar);
        });
    });
    
    document.querySelectorAll('.friend-item').forEach(item => {
        item.addEventListener('click', function() {
            const userId = parseInt(this.dataset.userId);
            const username = this.dataset.username;
            const avatar = this.dataset.avatar;
            startNewChat(userId, username, avatar);
        });
    });
    
    // Close confirmation modal when clicking outside
    const modal = document.getElementById('confirmationModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeConfirmationModal();
            }
        });
    }
    
    console.log('Contact handlers attached. Total contacts:', document.querySelectorAll('.contact-item').length);
});

// Auto-update timestamps every minute
setInterval(updateAllContactTimestamps, 60000);

// ============================================================
// DEBUGGING HELPERS
// ============================================================

function testTimestamps() {
    const now = new Date();
    console.log('=== TIMESTAMP TESTS (Singapore Time - GMT+8) ===');
    console.log('Browser local time:', now.toString());
    console.log('Singapore time:', now.toLocaleString('en-SG', { timeZone: SST_TZ }));
}

console.log('✅ Chat.js loaded with all features');
console.log('✅ Singapore Standard Time (GMT+8)');
console.log('✅ File attachments enabled');
console.log('✅ Edit/Delete messages enabled');
console.log('✅ Remove friend enabled');