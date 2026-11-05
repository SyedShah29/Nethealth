type StatusCardProps = {
  label: string;
  status: "healthy" | "warning" | "critical" | "unknown" | "loading" | "unavailable";
  detail: string;
};

export function StatusCard({ label, status, detail }: StatusCardProps) {
  return (
    <article className="status-card">
      <div className="status-heading">
        <h2>{label}</h2>
        <span className={`status-label status-${status}`}>{status}</span>
      </div>
      <p className="status-detail">{detail}</p>
    </article>
  );
}
