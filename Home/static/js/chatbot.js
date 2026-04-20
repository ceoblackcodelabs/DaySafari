// Chatbot Functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const optionBtns = document.querySelectorAll('.chat-option-btn');
    const chatButton = document.querySelector('.chat-button');
    const chatToggle = document.getElementById('chat-toggle');
    
    // Variables
    let unreadCount = 0;
    let initialMessageShown = false;
    let isWaitingForResponse = false;
    
    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 80) + 'px';
        });
    }
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Add message to chat
    function addMessage(text, type) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (type === 'received') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-robot"></i>
                    <p>${escapeHtml(text)}</p>
                </div>
                <span class="message-time">${timeString}</span>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${escapeHtml(text)}</p>
                </div>
                <span class="message-time">${timeString}</span>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        // Add unread badge if chat is closed
        if (chatToggle && !chatToggle.checked && type === 'received') {
            addUnreadBadge();
        }
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        if (!chatMessages) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message received';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Add unread badge
    function addUnreadBadge() {
        if (chatButton && chatToggle && !chatToggle.checked) {
            unreadCount++;
            chatButton.classList.add('has-unread');
        }
    }
    
    // Remove unread badge
    function removeUnreadBadge() {
        if (chatButton) {
            unreadCount = 0;
            chatButton.classList.remove('has-unread');
        }
    }
    
    // Send message to API
    async function sendToAPI(message) {
        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                return data.response;
            } else {
                console.error('API Error:', data.error);
                return "I'm having trouble connecting to our support system. Please contact us directly at info@daysafarisadventures.co.ke or call +254 734 962 965 for assistance. 🦁";
            }
        } catch (error) {
            console.error('Network Error:', error);
            return "Network error. Please check your connection or contact us directly at info@daysafarisadventures.co.ke. We're here to help! 🦁";
        }
    }
    
    // Generate bot response using API
    async function generateBotResponse(userMessage) {
        if (isWaitingForResponse) return;
        
        isWaitingForResponse = true;
        
        // Show typing indicator
        showTypingIndicator();
        
        // Get response from API
        const response = await sendToAPI(userMessage);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        addMessage(response, 'received');
        
        isWaitingForResponse = false;
    }
    
    // Send message function
    async function sendMessage(message) {
        if (!message || !message.trim()) return;
        if (isWaitingForResponse) {
            addMessage("Please wait for my response before sending another message. 🦁", 'received');
            return;
        }
        
        // Add user message
        addMessage(message, 'sent');
        
        // Clear input
        if (chatInput) {
            chatInput.value = '';
            chatInput.style.height = 'auto';
        }
        
        // Generate bot response
        await generateBotResponse(message);
    }
    
    // Handle option buttons
    if (optionBtns && optionBtns.length > 0) {
        optionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.getAttribute('data-message');
                if (message) {
                    sendMessage(message);
                }
            });
        });
    }
    
    // Send message on button click
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            if (chatInput) {
                sendMessage(chatInput.value);
            }
        });
    }
    
    // Send message on Enter key (Shift+Enter for new line)
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(chatInput.value);
            }
        });
    }
    
    // Remove unread badge when chat opens
    if (chatToggle) {
        chatToggle.addEventListener('change', function() {
            if (this.checked) {
                removeUnreadBadge();
            }
        });
    }
    
    // Show initial welcome message if chat is empty
    if (chatMessages && chatMessages.children.length === 0 && !initialMessageShown) {
        setTimeout(() => {
            if (chatMessages.children.length === 0) {
                addMessage("Hello! Welcome to Day Safaris Adventures! 🦁 How can I help you plan your East African safari today? I can assist with destinations, packages, bookings, or any questions about our services!", 'received');
                initialMessageShown = true;
            }
        }, 500);
    }
    
    // Predefined quick responses helper
    window.handleQuickResponse = function(keyword) {
        const quickResponses = {
            'help': 'I can help you with:\n• Booking safaris\n• Destination information\n• Package prices\n• Payment options\n• Group discounts\n• Travel tips\n\nJust let me know what you need! 😊',
            'contact': 'You can reach us at:\n📞 Phone: +254 734 962 965\n📧 Email: info@daysafarisadventures.co.ke\n📍 Location: Nairobi, Kenya\n🌐 Website: daysafarisadventures.co.ke\n\nWe\'re available 24/7!',
            'hours': 'Our customer support is available:\nMonday - Friday: 8:00 AM - 8:00 PM (EAT)\nSaturday: 9:00 AM - 6:00 PM (EAT)\nSunday: 10:00 AM - 4:00 PM (EAT)\nEmergency support: 24/7 at +254 782 390 295',
            'packages': 'Our safari packages start from $649 for 3-day adventures to $1,899 for luxury experiences. Popular packages include:\n• Masai Mara Safari (4 days, $849)\n• Zanzibar Beach Holiday (6 days, $1,299)\n• Serengeti Migration (5 days, $1,499)\n• Amboseli Elephant Experience (3 days, $649)\n\nWould you like details on any specific package?',
            'destinations': 'We offer amazing destinations across East Africa:\n🇰🇪 Kenya: Masai Mara, Amboseli, Tsavo, Diani Beach\n🇹🇿 Tanzania: Serengeti, Zanzibar, Kilimanjaro, Ngorongoro\n🇺🇬 Uganda: Bwindi Gorillas, Queen Elizabeth Park\n🇷🇼 Rwanda: Kigali Cultural Tour, Lake Kivu\n\nWhich destination interests you? 🗺️'
        };
        
        if (quickResponses[keyword]) {
            addMessage(quickResponses[keyword], 'received');
        }
    };
    
    // Log that chatbot is ready
    console.log('Day Safaris Chatbot initialized successfully! 🦁');
});