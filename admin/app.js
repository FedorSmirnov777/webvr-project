const AUTH_USER_KEY = "vrg_auth_username";
const AUTH_ACCOUNTS_KEY = "vrg_local_accounts_v1";
const ADMIN_TOKEN_KEY = "autovr_admin_token";

const modeLoginBtn = document.getElementById("mode-login");
const modeRegisterBtn = document.getElementById("mode-register");
const form = document.getElementById("auth-form");
const submitBtn = document.getElementById("submit-btn");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const messageEl = document.getElementById("auth-message");
const profileBox = document.getElementById("profile-box");
const profileNameEl = document.getElementById("profile-name");
const logoutBtn = document.getElementById("logout-btn");

let mode = "login";

function loadAccounts() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_ACCOUNTS_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveAccounts(accounts) {
  localStorage.setItem(AUTH_ACCOUNTS_KEY, JSON.stringify(accounts));
}

function setAuthUser(username) {
  localStorage.setItem(AUTH_USER_KEY, username);
}

function clearAuthUser() {
  localStorage.removeItem(AUTH_USER_KEY);
  localStorage.removeItem(ADMIN_TOKEN_KEY);
}

function getAuthUser() {
  return localStorage.getItem(AUTH_USER_KEY) || "";
}

function setMode(nextMode) {
  mode = nextMode;
  const isLogin = mode === "login";
  modeLoginBtn.classList.toggle("active", isLogin);
  modeRegisterBtn.classList.toggle("active", !isLogin);
  submitBtn.textContent = isLogin ? "Войти" : "Создать аккаунт";
  passwordInput.autocomplete = isLogin ? "current-password" : "new-password";
  showMessage("");
}

function showMessage(text, ok = false) {
  messageEl.textContent = text;
  messageEl.style.color = ok ? "#146c2e" : "#8f1d1d";
}

function showProfile(username) {
  profileNameEl.textContent = username;
  profileBox.hidden = false;
  form.hidden = true;
  modeLoginBtn.disabled = true;
  modeRegisterBtn.disabled = true;
}

function showAuthForm() {
  profileBox.hidden = true;
  form.hidden = false;
  modeLoginBtn.disabled = false;
  modeRegisterBtn.disabled = false;
}

async function tryApiLogin(username, password) {
  const emailCandidate = username.includes("@") ? username : `${username}@autovr.local`;
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: emailCandidate, password })
  });
  if (!response.ok) return null;
  const data = await response.json();
  if (data?.access_token) {
    localStorage.setItem(ADMIN_TOKEN_KEY, data.access_token);
    return data;
  }
  return null;
}

modeLoginBtn.addEventListener("click", () => setMode("login"));
modeRegisterBtn.addEventListener("click", () => setMode("register"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = String(usernameInput.value || "").trim();
  const password = String(passwordInput.value || "");

  if (!username || !password) {
    showMessage("Заполните имя пользователя и пароль.");
    return;
  }

  const accounts = loadAccounts();

  if (mode === "register") {
    if (accounts[username]) {
      showMessage("Пользователь с таким именем уже существует.");
      return;
    }
    accounts[username] = { password };
    saveAccounts(accounts);
    setAuthUser(username);
    showProfile(username);
    showMessage("Регистрация выполнена. Вы вошли в аккаунт.", true);
    return;
  }

  if (accounts[username] && accounts[username].password === password) {
    setAuthUser(username);
    showProfile(username);
    showMessage("Успешный вход.", true);
    return;
  }

  const apiResult = await tryApiLogin(username, password);
  if (apiResult) {
    setAuthUser(username);
    showProfile(username);
    showMessage("Успешный вход.", true);
    return;
  }

  showMessage("Неверное имя пользователя или пароль.");
});

logoutBtn.addEventListener("click", () => {
  clearAuthUser();
  usernameInput.value = "";
  passwordInput.value = "";
  setMode("login");
  showAuthForm();
  showMessage("Вы вышли из аккаунта.", true);
});

(function init() {
  const user = getAuthUser();
  setMode("login");
  if (user) {
    showProfile(user);
    showMessage(`Сессия восстановлена для: ${user}`, true);
  } else {
    showAuthForm();
  }
})();
