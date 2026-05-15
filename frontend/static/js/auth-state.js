const AUTH_USER_KEY = "vrg_auth_username";
const authButton = document.querySelector(".auth-btn");
const topbarActions = document.querySelector(".topbar-actions");

function getAuthUser() {
  return localStorage.getItem(AUTH_USER_KEY) || "";
}

function clearAuthUser() {
  localStorage.removeItem(AUTH_USER_KEY);
  localStorage.removeItem("autovr_admin_token");
}

function renderAuthState() {
  if (!authButton || !topbarActions) return;

  const existing = document.getElementById("auth-user-inline");
  const existingLogout = document.getElementById("auth-logout-inline");
  if (existing) existing.remove();
  if (existingLogout) existingLogout.remove();

  const username = getAuthUser();
  if (!username) {
    authButton.hidden = false;
    authButton.textContent = "Регистрация / Вход";
    return;
  }

  authButton.hidden = true;

  const userBadge = document.createElement("span");
  userBadge.id = "auth-user-inline";
  userBadge.className = "auth-user";
  userBadge.textContent = username;
  topbarActions.appendChild(userBadge);

  const logoutBtn = document.createElement("button");
  logoutBtn.id = "auth-logout-inline";
  logoutBtn.className = "auth-logout-btn";
  logoutBtn.type = "button";
  logoutBtn.textContent = "Выйти";
  logoutBtn.addEventListener("click", () => {
    clearAuthUser();
    renderAuthState();
  });
  topbarActions.appendChild(logoutBtn);
}

document.addEventListener("DOMContentLoaded", renderAuthState);
