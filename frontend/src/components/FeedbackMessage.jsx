export function FeedbackMessage({ tone = "info", children }) {
  if (!children) {
    return null;
  }

  const isError = tone === "error";

  return (
    <p
      aria-live={isError ? "assertive" : "polite"}
      className={`feedback-message feedback-${tone}`}
      role={isError ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
