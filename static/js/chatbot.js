const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");

function appendMessage(text, who) {
  const node = document.createElement("div");
  node.className = `message ${who}`;
  node.textContent = text;
  chatLog.appendChild(node);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = new FormData(chatForm).get("question");
  appendMessage(question, "user");
  chatForm.reset();
  const response = await apiFetch("/chatbot/message", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  const payload = await response.json();
  appendMessage(payload.answer, "bot");
});
