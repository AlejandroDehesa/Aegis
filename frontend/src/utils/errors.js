export function getErrorMessage(error, fallback = "Error inesperado. Intentalo de nuevo.") {
  if (typeof error === "string" && error.trim()) {
    return error.trim();
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  return fallback;
}
