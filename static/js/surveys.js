const surveyForm = document.querySelector("#surveyForm");
const surveyMessage = document.querySelector("#surveyMessage");

surveyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await apiFetch("/surveys", {
    method: "POST",
    body: JSON.stringify(formToJson(surveyForm)),
  });
  const payload = await response.json();
  surveyMessage.textContent = payload.message;
  surveyMessage.className = response.ok ? "text-success" : "text-danger";
  if (response.ok) surveyForm.reset();
});
