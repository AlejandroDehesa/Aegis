export function EmptyState({ title, description }) {
  return (
    <div aria-live="polite" className="empty-state" role="status">
      <p className="empty-title">{title}</p>
      <p className="empty-description">{description}</p>
    </div>
  );
}
