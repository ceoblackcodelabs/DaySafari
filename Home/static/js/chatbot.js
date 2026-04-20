// Chatbot Functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const optionBtns = document.querySelectorAll('.chat-option-btn');
    const chatButton = document.querySelector('.chat-button');
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 80) + 'px';
    });
    
    // Send message function
    function sendMessage(message, isUser = true) {
        if (!message.trim()) return;
        
        // Add user message
        if (isUser) {
            addMessage(message, 'sent');
            chatInput.value = '';
            chatInput.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Simulate bot response after 1-2 seconds
            setTimeout(() => {
                removeTypingIndicator();
                generateBotResponse(message);
            }, 1000 + Math.random() * 1000);
        } else {
            addMessage(message, 'received');
        }
    }
    
    // Add message to chat
    function addMessage(text, type) {
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
    }
    
    // Show typing indicator
    function showTypingIndicator() {
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
    
    // Generate bot response
    function generateBotResponse(userMessage) {
        let response = getBotResponse(userMessage.toLowerCase());
        addMessage(response, 'received');
    }
    
    // Bot response logic
    function getBotResponse(message) {
        if (message.includes('book') || message.includes('booking') || message.includes('safari')) {
            return "Great! I can help you book a safari. 🦁 Please visit our booking form or provide me with your preferred destination, travel dates, and number of people. Would you like me to send you the booking link?";
        } else if (message.includes('destination') || message.includes('place') || message.includes('where')) {
            return "We offer amazing destinations including: Masai Mara (Kenya), Serengeti (Tanzania), Zanzibar Beach, Mount Kilimanjaro, Amboseli National Park, and many more! Which destination interests you? 🗺️";
        } else if (message.includes('package') || message.includes('price') || message.includes('cost')) {
            return "Our safari packages start from $649 for 3-day adventures to $1,899 for luxury experiences. Each package includes accommodation, meals, game drives, and park fees. Would you like me to share our current special offers? 💰";
        } else if (message.includes('payment') || message.includes('pay') || message.includes('credit card')) {
            return "We accept various payment methods including credit cards (Visa, Mastercard), bank transfers, and mobile money (M-Pesa). We also offer flexible payment plans with 30% deposit required to confirm booking. 💳";
        } else if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
            return "Hello! Welcome to Day Safaris Adventures! 😊 How can I assist you with your African safari adventure today?";
        } else if (message.includes('thank')) {
            return "You're very welcome! 🎉 Is there anything else I can help you with? Feel free to ask about our safari packages, destinations, or special offers!";
        } else if (message.includes('discount') || message.includes('offer') || message.includes('deal')) {
            return "We currently have a 50% off offer for first-time customers! 🎁 Also, book 3 months in advance and get an additional 10% discount. Subscribe to our newsletter for exclusive deals!";
        } else if (message.includes('group') || message.includes('family')) {
            return "We offer special group and family packages! Groups of 6+ get 15% discount, and children under 12 get 30% off. Would you like a custom quote for your group? 👨‍👩‍👧‍👦";
        } else {
            return "Thank you for your message! 📧 Our customer support team will get back to you shortly. In the meantime, feel free to check our website for safari packages, destinations, or call us at +254 700 000 000 for immediate assistance.";
        }
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Send message on button click
    sendBtn.addEventListener('click', () => {
        sendMessage(chatInput.value);
    });
    
    // Send message on Enter key (Shift+Enter for new line)
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(chatInput.value);
        }
    });
    
    // Handle option buttons
    optionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const message = btn.getAttribute('data-message');
            sendMessage(message);
        });
    });
    
    // Unread message indicator
    let unreadCount = 0;
    const chatToggle = document.getElementById('chat-toggle');
    
    function addUnreadBadge() {
        if (!chatToggle.checked) {
            unreadCount++;
            chatButton.classList.add('has-unread');
        }
    }
    
    // Remove unread badge when chat opens
    chatToggle.addEventListener('change', function() {
        if (this.checked) {
            unreadCount = 0;
            chatButton.classList.remove('has-unread');
        }
    });
    
    // Initial welcome message (only once)
    let initialMessageShown = false;
    if (!initialMessageShown) {
        setTimeout(() => {
            if (chatMessages.children.length === 1) {
                // Keep the initial welcome message
                initialMessageShown = true;
            }
        }, 100);
    }
    
    // Predefined quick responses
    const quickResponses = {
        'help': 'I can help you with:\n- Booking safaris\n- Destination information\n- Package prices\n- Payment options\n- Group discounts\nJust let me know what you need! 😊',
        'contact': 'You can reach us at:\n📞 Phone: +254 700 000 000\n📧 Email: info@daysafarisadventures.co.ke\n📍 Location: Nairobi, Kenya\nWe\'re available 24/7!',
        'hours': 'Our customer support is available:\nMonday - Friday: 8:00 AM - 8:00 PM\nSaturday: 9:00 AM - 6:00 PM\nSunday: 10:00 AM - 4:00 PM\nEmergency support available 24/7!'
    };
    
    // Add quick response keywords
    window.handleQuickResponse = function(keyword) {
        if (quickResponses[keyword]) {
            addMessage(quickResponses[keyword], 'received');
        }
    };
});