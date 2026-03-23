export function SectionCard({ title, subtitle, actions, children }) {
  return (
    <section className="section-card">
      <div className="section-card-header">
        <div>
          <p className="section-eyebrow">{title}</p>
          {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="section-actions">{actions}</div> : null}
      </div>
      <div className="section-card-body">{children}</div>
    </section>
  );
}
