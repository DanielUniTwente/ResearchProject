// static/js/script.js

async function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    if (userInput.trim() === '') return;
    const chatbotContainer = document.getElementById('chatbot');
    const userMessage = document.createElement('div');
    userMessage.textContent = userInput;
    userMessage.className = 'user-message';
    chatbotContainer.appendChild(userMessage);
    document.getElementById('userInput').value = ''; 

    // Send message to rasa
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
    chatbotContainer.scrollTop = chatbotContainer.scrollHeight;
}

async function sendButtonMessage(payload) {
    const chatbotContainer = document.getElementById('chatbot');
    const imageContainer = document.querySelector('.image-container img');

    const userMessage = document.createElement('div');
    if (payload === '/inform{{"active_painting":"King Caspar"}}')
        userMessage.textContent = 'King Caspar';
    else if (payload === '/inform{{"active_painting":"Head of a Boy in a Turban"}}')
        userMessage.textContent = 'Head of a Boy in a Turban';
    else if (payload === '/inform{{"active_painting":"Diego Bemba, a Servant of Don Miguel de Castro"}}')
        userMessage.textContent = 'Diego Bemba, a Servant of Don Miguel de Castro';
    else if (payload === '/inform{{"active_painting":"Pedro Sunda, a Servant of Don Miguel de Castro"}}')
        userMessage.textContent = 'Pedro Sunda, a Servant of Don Miguel de Castro';
    // userMessage.textContent = payload;
    // userMessage.className = 'user-message';
    // chatbotContainer.appendChild(userMessage);
    // painting = JSON.parse(payload.substring(8))
    switch (payload) {
        case 'King Caspar':
            imageContainer.src = kingCasparImageUrl;
            break;
        case 'Head of a Boy in a Turban':
            imageContainer.src = turbanBoyImageUrl;
            break;
        case 'Diego Bemba, a Servant of Don Miguel de Castro':
            imageContainer.src = diegoBembaImageUrl;
            break;
        case 'Pedro Sunda, a Servant of Don Miguel de Castro':
            imageContainer.src = pedroSundaImageUrl;
            break;
        default:
            imageContainer.src = defaultImageUrl;
    }

    // Send message to rasa
    const response = await fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: payload })
    });
    const data = await response.json();

    // Add bot response to chat
    data.forEach((message) => {
        const botMessage = document.createElement('div');
        botMessage.textContent = message.text;
        botMessage.className = 'bot-message';
        chatbotContainer.appendChild(botMessage);
    });
    chatbotContainer.scrollTop = chatbotContainer.scrollHeight;
}

async function resetChat() {
    const chatbotContainer = document.getElementById('chatbot');
    const imageContainer = document.querySelector('.image-container img');
    chatbotContainer.innerHTML = ''; 
    imageContainer.src = defaultImageUrl;
    enableTextInput();

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

function downloadLog() {
    chat=document.getElementById('chatbot')
    const jsonChat = JSON.stringify(htmlToJson(chat.innerHTML), null, 2);
    const blob = new Blob([jsonChat], { type: 'text/plain;charset=utf-8' });
    saveAs(blob, 'chatbot.log');
}

function htmlToJson(htmlContent) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    const result = [];
    const divs = doc.querySelectorAll('div');
    divs.forEach(div => {
        const className = div.className;
        if (className === 'user-message' || className === 'bot-message') {
            result.push({
                type: className,
                content: div.textContent.trim()
            });
        } else if (className === 'buttons-container') {
            const buttons = Array.from(div.querySelectorAll('button')).map(button => button.textContent.trim());
            result.push({
                type: className,
                buttons: buttons
            });
        }
    });

    return result;
}