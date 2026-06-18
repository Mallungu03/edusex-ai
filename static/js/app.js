function getToken() {
  return localStorage.getItem("access_token");
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    return null;
  }
}

async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return await fetch(url, { ...options, headers });
}

function requireAuth() {
  return true;
}

function updateNavigation() {
  const user = getUser();
  const badge = document.querySelector("#userBadge");
  if (badge) {
    badge.textContent = user ? `${user.name} · ${user.role}` : "";
  }
  const logout = document.querySelector("#logoutBtn");
  if (logout) {
    logout.addEventListener("click", async () => {
      await apiFetch("/auth/logout", { method: "POST", body: "{}" });
      localStorage.clear();
      location.href = "/";
    });
  }
}

function formToJson(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  form.querySelectorAll("input[type='checkbox']").forEach((input) => {
    data[input.name] = input.checked;
  });
  return data;
}

function renderJson(element, payload) {
  element.textContent = JSON.stringify(payload, null, 2);
}

requireAuth();
document.addEventListener("DOMContentLoaded", updateNavigation);
