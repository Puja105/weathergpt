const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const messagesEl = document.getElementById("messages");
const clearButton = document.getElementById("clear-chat");

const API_BASE = window.WEATHERGPT_API_URL || window.location.origin;
let history = [];

function addMessage(role, content, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "assistant" ? "W" : "Y";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = content;
  bubble.appendChild(paragraph);

  if (sources.length) {
    const sourceBox = document.createElement("div");
    sourceBox.className = "sources";
    const heading = document.createElement("strong");
    heading.textContent = "Reference material";
    sourceBox.appendChild(heading);
    sources.forEach((source) => {
      const item = document.createElement("span");
      item.className = "source-item";
      item.textContent = `${source.title}${source.similarity == null ? "" : ` · relevance ${Math.round(source.similarity * 100)}%`}`;
      sourceBox.appendChild(item);
    });
    bubble.appendChild(sourceBox);
  }

  article.append(avatar, bubble);
  messagesEl.appendChild(article);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const node = document.createElement("div");
  node.className = "typing";
  node.id = "typing-indicator";
  node.textContent = "WeatherGPT is thinking…";
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
function hideTyping() {
  document.getElementById("typing-indicator")?.remove();
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed || sendButton.disabled) return;

  addMessage("user", trimmed);
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  showTyping();

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed, history: history.slice(-12) })
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "The chatbot could not process your request.");
    }
    hideTyping();
    const answer = payload.answer || "I couldn't generate an answer. Please try again.";
    addMessage("assistant", answer, payload.sources || []);
    history.push({ role: "user", content: trimmed });
    history.push({ role: "assistant", content: answer });
  } catch (error) {
    hideTyping();
    addMessage("assistant", `Sorry, I couldn't reach WeatherGPT. ${error.message}`);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
});
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});
clearButton.addEventListener("click", () => {
  history = [];
  messagesEl.replaceChildren();
  addMessage("assistant", "New conversation started. What would you like to know about the weather?");
  input.focus();
});
