const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const message = document.querySelector("#message");

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify(formToJson(loginForm)),
    });
    const payload = await response.json();
    if (!response.ok) {
      message.textContent = payload.message;
      message.className = "text-danger small";
      return;
    }
    localStorage.setItem("access_token", payload.access_token);
    localStorage.setItem("refresh_token", payload.refresh_token);
    localStorage.setItem("user", JSON.stringify(payload.user));
    location.href = "/dashboard";
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(formToJson(registerForm)),
    });
    const payload = await response.json();
    message.textContent = payload.message;
    message.className = response.ok ? "text-success small" : "text-danger small";
    if (response.ok) {
      setTimeout(() => (location.href = "/"), 900);
    }
  });
}
