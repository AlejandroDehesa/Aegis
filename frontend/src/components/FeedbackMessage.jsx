export function FeedbackMessage({ tone = "info", children }) {
  if (!children) {
    return null;
  }

  return <p className={`feedback-message feedback-${tone}`}>{children}</p>;
}
