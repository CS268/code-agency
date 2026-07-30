// Self-contained vanilla JS chatbot widget
// Features: floating button, chat window, message bubbles, typing indicator, localStorage history, API integration

(function() {
  // Configuration
  const config = {
    backendUrl: 'https://jcode-site-generator.onrender.com/chatbot',
    storageKey: 'jcode_chat_history',
    maxHistory: 50,
    colors: {
      primary: '#6366f1',
      secondary: '#8b5cf6',
      userBubble: '#6366f1',
      botBubble: '#f3f4f6',
      textLight: '#ffffff',
      textDark: '#1f2937'
    },
    dimensions: {
      buttonSize: '60px',
      chatWidth: '380px',
      chatHeight: '550px',
      mobileHeight: '70vh'
    }
  };

  // State management
  let chatHistory = [];
  let isOpen = false;
  let isTyping = false;
  let currentHistory = [];

  // Create DOM elements
  function createElements() {
    // Floating button
    const button = document.createElement('button');
    button.id = 'jcode-chat-button';
    button.style.position = 'fixed';
    button.style.bottom = '20px';
    button.style.right = '20px';
    button.style.width = config.dimensions.buttonSize;
    button.style.height = config.dimensions.buttonSize;
    button.style.borderRadius = '50%';
    button.style.backgroundColor = config.colors.primary;
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.cursor = 'pointer';
    button.style.zIndex = '9999';
    button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    button.style.display = 'flex';
    button.style.alignItems = 'center';
    button.style.justifyContent = 'center';
    button.style.fontSize = '24px';
    button.innerHTML = '💬';
    button.title = 'JCODE Assistant';

    // Chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'jcode-chat-window';
    chatWindow.style.position = 'fixed';
    chatWindow.style.bottom = '90px';
    chatWindow.style.right = '20px';
    chatWindow.style.width = config.dimensions.chatWidth;
    chatWindow.style.height = config.dimensions.chatHeight;
    chatWindow.style.backgroundColor = 'white';
    chatWindow.style.borderRadius = '16px';
    chatWindow.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
    chatWindow.style.display = 'none';
    chatWindow.style.flexDirection = 'column';
    chatWindow.style.overflow = 'hidden';
    chatWindow.style.zIndex = '10000';

    // Header
    const header = document.createElement('div');
    header.style.padding = '16px';
    header.style.background = `linear-gradient(135deg, ${config.colors.primary} 0%, ${config.colors.secondary} 100%)`;
    header.style.color = 'white';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';

    const title = document.createElement('h3');
    title.textContent = 'JCODE Assistant';
    title.style.margin = '0';
    title.style.fontSize = '16px';
    title.style.fontWeight = '600';

    const headerButtons = document.createElement('div');
    headerButtons.style.display = 'flex';
    headerButtons.style.gap = '8px';

    // Refresh button
    const refreshBtn = document.createElement('button');
    refreshBtn.textContent = '🔄';
    refreshBtn.style.background = 'transparent';
    refreshBtn.style.border = 'none';
    refreshBtn.style.color = 'white';
    refreshBtn.style.cursor = 'pointer';
    refreshBtn.style.fontSize = '16px';
    refreshBtn.title = 'New Chat';
    refreshBtn.addEventListener('click', () => {
      currentHistory = [];
      chatHistory = [];
      localStorage.setItem(config.storageKey, JSON.stringify([]));
      updateChatDisplay();
    });

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '✕';
    closeBtn.style.background = 'transparent';
    closeBtn.style.border = 'none';
    closeBtn.style.color = 'white';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontSize = '18px';
    closeBtn.title = 'Close';
    closeBtn.addEventListener('click', toggleChat);

    headerButtons.appendChild(refreshBtn);
    headerButtons.appendChild(closeBtn);
    header.appendChild(title);
    header.appendChild(headerButtons);

    // Message area
    const messageArea = document.createElement('div');
    messageArea.id = 'jcode-message-area';
    messageArea.style.flex = '1';
    messageArea.style.padding = '16px';
    messageArea.style.overflowY = 'auto';
    messageArea.style.display = 'flex';
    messageArea.style.flexDirection = 'column';
    messageArea.style.gap = '12px';

    // Input area
    const inputArea = document.createElement('div');
    inputArea.style.padding = '16px';
    inputArea.style.borderTop = '1px solid #e5e7eb';
    inputArea.style.display = 'flex';
    inputArea.style.gap = '8px';

    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.placeholder = 'Type your message...';
    inputField.style.flex = '1';
    inputField.style.padding = '10px 14px';
    inputField.style.border = '1px solid #d1d5db';
    inputField.style.borderRadius = '8px';
    inputField.style.outline = 'none';
    inputField.style.fontSize = '14px';

    const sendButton = document.createElement('button');
    sendButton.textContent = 'Send';
    sendButton.style.padding = '10px 20px';
    sendButton.style.backgroundColor = config.colors.primary;
    sendButton.style.color = 'white';
    sendButton.style.border = 'none';
    sendButton.style.borderRadius = '8px';
    sendButton.style.cursor = 'pointer';
    sendButton.style.fontSize = '14px';
    sendButton.style.fontWeight = '500';

    inputArea.appendChild(inputField);
    inputArea.appendChild(sendButton);

    // Assemble chat window
    chatWindow.appendChild(header);
    chatWindow.appendChild(messageArea);
    chatWindow.appendChild(inputArea);

    // Add to body
    document.body.appendChild(button);
    document.body.appendChild(chatWindow);

    // Event listeners
    button.addEventListener('click', toggleChat);
    sendButton.addEventListener('click', () => {
      const message = inputField.value.trim();
      if (message) {
        sendMessage(message);
        inputField.value = '';
      }
    });

    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const message = inputField.value.trim();
        if (message) {
          sendMessage(message);
          inputField.value = '';
        }
      }
    });

    // Load history
    loadHistory();
  }

  // Toggle chat window visibility
  function toggleChat() {
    isOpen = !isOpen;
    const chatWindow = document.getElementById('jcode-chat-window');
    const button = document.getElementById('jcode-chat-button');
    
    if (isOpen) {
      chatWindow.style.display = 'flex';
      button.style.backgroundColor = '#4f46e5';
      
      // Focus input field
      const inputField = document.querySelector('#jcode-chat-window input');
      setTimeout(() => inputField.focus(), 100);
      
      // Show welcome message if no history
      if (chatHistory.length === 0) {
        showBotMessage('Welcome to JCODE Assistant! How can I help you today?');
      }
    } else {
      chatWindow.style.display = 'none';
      button.style.backgroundColor = config.colors.primary;
    }
  }

  // Load chat history from localStorage
  function loadHistory() {
    try {
      const stored = localStorage.getItem(config.storageKey);
      if (stored) {
        chatHistory = JSON.parse(stored);
        currentHistory = [...chatHistory];
      }
    } catch (e) {
      console.error('Error loading chat history:', e);
    }
  }

  // Save chat history to localStorage
  function saveHistory() {
    try {
      // Keep only the most recent messages
      if (chatHistory.length > config.maxHistory) {
        chatHistory = chatHistory.slice(-config.maxHistory);
      }
      localStorage.setItem(config.storageKey, JSON.stringify(chatHistory));
    } catch (e) {
      console.error('Error saving chat history:', e);
    }
  }

  // Send message to backend
  function sendMessage(message) {
    const messageArea = document.getElementById('jcode-message-area');
    
    // Add user message to display
    showUserMessage(message);
    
    // Add to history
    const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString() };
    chatHistory.push(userMessage);
    currentHistory.push(userMessage);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to backend
    fetch(config.backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: message,
        history: currentHistory
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
.then(data => {
    console.log("✅ DATA RECEIVED:", data);  // AJOUTE CETTE LIGNE
    console.log("✅ DATA.REPLY:", data.reply);  // AJOUTE CETTE LIGNE
    
    removeTypingIndicator();
    
    if (data.reply) {
        console.log("✅ SHOWING BOT MESSAGE");  // AJOUTE CETTE LIGNE
        showBotMessage(data.reply);
    } else {
        console.log("❌ NO data.reply FOUND");  // AJOUTE CETTE LIGNE
    }
    
    // ... le reste du code (history, etc.)
})
    .catch(error => {
      console.error('Error:', error);
      removeTypingIndicator();
      showBotMessage('Technical issue. Contact 0466/06.22.73 or matovuruky@gmail.com');
      
      // Add error to history
      const errorMessage = { role: 'assistant', content: 'Technical issue. Contact 0466/06.22.73 or matovuruky@gmail.com', timestamp: new Date().toISOString() };
      chatHistory.push(errorMessage);
      currentHistory.push(errorMessage);
      saveHistory();
    });
  }

  // Show user message bubble
  function showUserMessage(message) {
    const messageArea = document.getElementById('jcode-message-area');
    
    const bubble = document.createElement('div');
    bubble.style.display = 'flex';
    bubble.style.justifyContent = 'flex-end';
    bubble.style.marginLeft = '60px';
    
    const bubbleInner = document.createElement('div');
    bubbleInner.textContent = message;
    bubbleInner.style.padding = '10px 14px';
    bubbleInner.style.borderRadius = '16px 16px 0 16px';
    bubbleInner.style.backgroundColor = config.colors.userBubble;
    bubbleInner.style.color = config.colors.textLight;
    bubbleInner.style.maxWidth = '80%';
    bubbleInner.style.wordWrap = 'break-word';
    bubbleInner.style.fontSize = '14px';
    
    bubble.appendChild(bubbleInner);
    messageArea.appendChild(bubble);
    messageArea.scrollTop = messageArea.scrollHeight;
  }

  // Show bot message bubble
  function showBotMessage(message) {
    const messageArea = document.getElementById('jcode-message-area');
    
    const bubble = document.createElement('div');
    bubble.style.display = 'flex';
    bubble.style.marginRight = '60px';
    
    const bubbleInner = document.createElement('div');
    bubbleInner.textContent = message;
    bubbleInner.style.padding = '10px 14px';
    bubbleInner.style.borderRadius = '16px 16px 16px 0';
    bubbleInner.style.backgroundColor = config.colors.botBubble;
    bubbleInner.style.color = config.colors.textDark;
    bubbleInner.style.maxWidth = '80%';
    bubbleInner.style.wordWrap = 'break-word';
    bubbleInner.style.fontSize = '14px';
    
    bubble.appendChild(bubbleInner);
    messageArea.appendChild(bubble);
    messageArea.scrollTop = messageArea.scrollHeight;
  }

  // Show typing indicator
  function showTypingIndicator() {
    const messageArea = document.getElementById('jcode-message-area');
    
    isTyping = true;
    
    const typingContainer = document.createElement('div');
    typingContainer.style.display = 'flex';
    typingContainer.style.marginRight = '60px';
    typingContainer.style.alignItems = 'center';
    typingContainer.style.gap = '4px';
    
    const bubble = document.createElement('div');
    bubble.style.padding = '10px 14px';
    bubble.style.borderRadius = '16px 16px 16px 0';
    bubble.style.backgroundColor = config.colors.botBubble;
    bubble.style.color = config.colors.textDark;
    bubble.style.fontSize = '14px';
    
    const dotsContainer = document.createElement('div');
    dotsContainer.style.display = 'flex';
    dotsContainer.style.gap = '3px';
    
    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('span');
      dot.textContent = '.';
      dot.style.animation = `typingAnimation 1.4s infinite ease-in-out`;
      dot.style.animationDelay = `${i * 0.2}s`;
      dotsContainer.appendChild(dot);
    }
    
    bubble.appendChild(dotsContainer);
    typingContainer.appendChild(bubble);
    messageArea.appendChild(typingContainer);
    messageArea.scrollTop = messageArea.scrollHeight;
    
    // Add animation keyframes
    const style = document.createElement('style');
    style.textContent = `
      @keyframes typingAnimation {
        0%, 60%, 100% { opacity: 0.4; }
        30% { opacity: 1; }
      }
    `;
    document.head.appendChild(style);
  }

  // Remove typing indicator
  function removeTypingIndicator() {
    const messageArea = document.getElementById('jcode-message-area');
    const lastChild = messageArea.lastChild;
    
    if (lastChild && isTyping) {
      messageArea.removeChild(lastChild);
      isTyping = false;
    }
  }

  // Update chat display with history
  function updateChatDisplay() {
    const messageArea = document.getElementById('jcode-message-area');
    messageArea.innerHTML = '';
    
    chatHistory.forEach(msg => {
      if (msg.role === 'user') {
        showUserMessage(msg.content);
      } else {
        showBotMessage(msg.content);
      }
    });
    
    messageArea.scrollTop = messageArea.scrollHeight;
  }

  // Initialize the widget
  function init() {
    // Check if already initialized
    if (document.getElementById('jcode-chat-button')) {
      return;
    }
    
    createElements();
    
    // Add mobile responsiveness
    function handleResize() {
      const chatWindow = document.getElementById('jcode-chat-window');
      if (window.innerWidth <= 768) {
        chatWindow.style.width = '100%';
        chatWindow.style.height = config.dimensions.mobileHeight;
        chatWindow.style.bottom = '0';
        chatWindow.style.right = '0';
        chatWindow.style.borderRadius = '16px 16px 0 0';
      } else {
        chatWindow.style.width = config.dimensions.chatWidth;
        chatWindow.style.height = config.dimensions.chatHeight;
        chatWindow.style.bottom = '90px';
        chatWindow.style.right = '20px';
        chatWindow.style.borderRadius = '16px';
      }
    }
    
    window.addEventListener('resize', handleResize);
    handleResize();
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();