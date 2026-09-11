type Status = "ready" | "ingesting" | "error" | "pending";

const STATUS_CONFIG: Record<Status, { label: string; className: string }> = {
  ready: { label: "Ready", className: "text-text/70" },
  ingesting: { label: "Ingesting", className: "text-mars" },
  error: { label: "Fault", className: "text-mars-bright" },
  pending: { label: "Standby", className: "text-text/40" },
};

export default function StatusBadge({ status }: { status: Status }) {
  const config = STATUS_CONFIG[status];
  return (
    <span className={`font-body text-xs tracking-wide ${config.className}`}>
      {status === "ingesting" && (
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-mars mr-1.5 animate-pulse" />
      )}
      {config.label}
    </span>
  );
}