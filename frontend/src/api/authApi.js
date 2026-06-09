import { apiRequest } from "./http";

export function loginUser(credentials) {
  return apiRequest("/login", {
    method: "POST",
    body: credentials,
    ignoreUnauthorized: true,
  });
}

export function signupUser(payload) {
  return apiRequest("/signup", {
    method: "POST",
    body: payload,
  });
}

export function getCurrentUser(options = {}) {
  return apiRequest("/me", options);
}

export function logoutUser() {
  return apiRequest("/logout", {
    method: "POST",
    ignoreUnauthorized: true,
  });
}
