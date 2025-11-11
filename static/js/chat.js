// chat.js - handles UI interaction and sends requests to /ask

const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const chatContainer = document.getElementById("chat-container");

function createMessageElement(text, isUser) {
  // make message wrapper if messages list not present
  let list = chatContainer.querySelector(".messages");
  if (!list) {
    list = document.createElement("div");
    list.className = "messages";
    // clear placeholder empty-state
    const empty = chatContainer.querySelector(".empty-state");
    if (empty) empty.remove();
    chatContainer.appendChild(list);
  }

  const row = document.createElement("div");
  row.className = "message-row";
  const bubble = document.createElement("div");
  bubble.className = "message-bubble " + (isUser ? "message-user" : "message-bot");

  if (isUser) {
    bubble.innerText = text;
  } else {
    // server returns HTML-safe answer with <br> for newlines; assign as innerHTML
    bubble.innerHTML = text;
  }

  row.appendChild(bubble);
  list.appendChild(row);
  // scroll to bottom
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  inputEl.focus();
  createMessageElement(text, true);
  sendBtn.disabled = true;
  sendBtn.innerText = "Sending...";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");

    // data.answer is HTML-safe (we processed on server) with <br> tags
    createMessageElement(data.answer, false);
  } catch (err) {
    console.error(err);
    createMessageElement("Sorry — an error occurred. See console for details.", false);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerText = "Send";
  }
}

sendBtn.addEventListener("click", sendMessage);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
