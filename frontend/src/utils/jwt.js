function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  return window.atob(padded);
}

export function readJwtExpiration(token) {
  if (!token) {
    return null;
  }

  try {
    const [, payload] = token.split(".");
    if (!payload) {
      return null;
    }

    const decoded = JSON.parse(decodeBase64Url(payload));
    return typeof decoded.exp === "number" ? decoded.exp : null;
  } catch {
    return null;
  }
}

export function isJwtExpired(token, graceSeconds = 5) {
  const expiration = readJwtExpiration(token);

  if (!expiration) {
    return false;
  }

  return Date.now() >= (expiration - graceSeconds) * 1000;
}
