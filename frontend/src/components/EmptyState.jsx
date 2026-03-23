export function EmptyState({ title, description }) {
  return (
    <div className="empty-state">
      <p className="empty-title">{title}</p>
      <p className="empty-description">{description}</p>
    </div>
  );
}
