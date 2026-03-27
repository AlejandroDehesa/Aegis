import { EmptyState } from "./EmptyState";
import { FeedbackMessage } from "./FeedbackMessage";

export function AsyncContent({
  loading,
  error,
  isEmpty,
  loadingText = "Loading...",
  emptyTitle = "No data available",
  emptyDescription = "There is nothing to show yet.",
  children,
}) {
  if (loading) {
    return <FeedbackMessage tone="info">{loadingText}</FeedbackMessage>;
  }

  if (error) {
    return <FeedbackMessage tone="error">{error}</FeedbackMessage>;
  }

  if (isEmpty) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
      />
    );
  }

  return children;
}
