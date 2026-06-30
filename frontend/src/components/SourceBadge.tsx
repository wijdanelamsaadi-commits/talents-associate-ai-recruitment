const sourceStyles: Record<string, string> = {
  cv_upload: "bg-sky-50 text-sky-700 ring-sky-200",
  linkedin_csv: "bg-blue-50 text-blue-700 ring-blue-200",
  candidate_portal: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export function formatSource(source: string | null | undefined) {
  const labels: Record<string, string> = {
    all: "Toutes les sources",
    cv_upload: "Import CV",
    linkedin_csv: "Import LinkedIn",
    candidate_portal: "Portail candidat",
  };
  return labels[source || ""] ?? "Import CV";
}

export function SourceBadge({ source }: { source: string | null | undefined }) {
  const style = sourceStyles[source || ""] ?? "bg-slate-100 text-slate-700 ring-slate-200";
  return (
    <span className={["inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ring-1", style].join(" ")}>
      {formatSource(source)}
    </span>
  );
}
