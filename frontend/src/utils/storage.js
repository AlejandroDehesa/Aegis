import { TOKEN_STORAGE_KEY } from "../constants/storage";

export function getStoredToken() {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);

  if (!token || token === "null" || token === "undefined") {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    return null;
  }

  return token;
}

export function setStoredToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}
