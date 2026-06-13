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
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401 && !location.pathname.includes("register") && location.pathname !== "/") {
    localStorage.clear();
    location.href = "/";
    return null;
  }
  return response;
}

function requireAuth() {
  if (!getToken() && !["/", "/register"].includes(location.pathname)) {
    location.href = "/";
  }
}

function updateNavigation() {
  const user = getUser();
  const badge = document.querySelector("#userBadge");
  if (badge && user) {
    badge.textContent = `${user.name} · ${user.role}`;
  }
  document.querySelectorAll(".admin-only").forEach((element) => {
    element.classList.toggle("hidden", !user || user.role !== "ADMIN");
  });
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
