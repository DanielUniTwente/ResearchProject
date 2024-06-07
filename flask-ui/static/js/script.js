// static/js/script.js

async function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    if (userInput.trim() === '') return;

    const chatbotContainer = document.getElementById('chatbot');

    // Add user's message to the chat
    const userMessage = document.createElement('div');
    userMessage.textContent = userInput;
    userMessage.className = 'user-message';
    chatbotContainer.appendChild(userMessage);

    // Clear the input field
    document.getElementById('userInput').value = '';

    // Send the message to the Flask server
    const response = await fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    });
    const data = await response.json();

    // Add bot's response to the chat
    data.forEach((message) => {
        if (message.text) {
            const botMessage = document.createElement('div');
            botMessage.textContent = message.text;
            botMessage.className = 'bot-message';
            chatbotContainer.appendChild(botMessage);
        }

        if (message.buttons) {
            // Disable text input
            document.getElementById('userInput').disabled = true;
            const buttonsContainer = document.createElement('div');
            buttonsContainer.className = 'buttons-container';

            message.buttons.forEach(button => {
                const buttonElement = document.createElement('button');
                buttonElement.textContent = button.title;
                buttonElement.onclick = () => {
                    disableButtons(buttonsContainer);
                    sendButtonMessage(button.payload);
                    enableInput(); // Enable text input when button is clicked
                };
                buttonsContainer.appendChild(buttonElement);
            });
            chatbotContainer.appendChild(buttonsContainer);
        }
    });

    // Scroll to the bottom of the chat
    chatbotContainer.scrollTop = chatbotContainer.scrollHeight;
}

async function sendButtonMessage(payload) {
    const chatbotContainer = document.getElementById('chatbot');
    const imageContainer = document.querySelector('.image-container img');

    // Update image based on payload
    switch (payload) {
        case 'King Caspar':
            imageContainer.src = kingCasparImageUrl;
            break;
        case 'Head of a Boy in a Turban':
            imageContainer.src = turbanBoyImageUrl;
            break;
        case 'Diego Bemba':
            imageContainer.src = diegoBembaImageUrl;
            break;
        case 'Pedro Sunda':
            imageContainer.src = pedroSundaImageUrl;
            break;
        default:
            imageContainer.src = defaultImageUrl;
    }

    // Add the button payload as a user message to the chat
    const userMessage = document.createElement('div');
    userMessage.textContent = payload;
    userMessage.className = 'user-message';
    chatbotContainer.appendChild(userMessage);

    // Send the payload to the Flask server
    const response = await fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: payload })
    });
    const data = await response.json();

    // Add bot's response to the chat
    data.forEach((message) => {
        const botMessage = document.createElement('div');
        botMessage.textContent = message.text;
        botMessage.className = 'bot-message';
        chatbotContainer.appendChild(botMessage);
    });

    // Scroll to the bottom of the chat
    chatbotContainer.scrollTop = chatbotContainer.scrollHeight;
}

async function resetChat() {
    const chatbotContainer = document.getElementById('chatbot');
    const imageContainer = document.querySelector('.image-container img');
    // Clear the chat history
    chatbotContainer.innerHTML = '';

    // Reset the image to default
    imageContainer.src = defaultImageUrl;
    enableInput(); // Enable text input when chat is reset
    // Send the /restart command to Rasa server
    await fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '/restart' })
    });
}

// Function to enable text input
function enableInput() {
    document.getElementById('userInput').disabled = false;
}

function disableButtons(container) {
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = true;
    });
}
