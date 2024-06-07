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

    document.getElementById('userInput').value = ''; //clear input field

    // Send the message to rasa
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
            document.getElementById('userInput').disabled = true;
            const buttonsContainer = document.createElement('div');
            buttonsContainer.className = 'buttons-container';

            message.buttons.forEach(button => {
                const buttonElement = document.createElement('button');
                buttonElement.textContent = button.title;
                buttonElement.onclick = () => {
                    disablePaintingButtons(buttonsContainer);
                    sendButtonMessage(button.payload);
                    enableTextInput();
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

    // Update image based on choice
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

    // Send the painting to rasa
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
    chatbotContainer.innerHTML = ''; //clear chatbox

    imageContainer.src = defaultImageUrl;
    enableTextInput();

    // restart Rasa server
    await fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '/restart' })
    });
}

function enableTextInput() {
    document.getElementById('userInput').disabled = false;
}

function disablePaintingButtons(container) {
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = true;
    });
}
