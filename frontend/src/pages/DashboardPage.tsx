import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import {
  DashboardPipeline,
  DashboardPipelineFilters,
  JobPipeline,
  PipelineStageCount,
  getDashboardPipeline,
} from "../services/dashboard";

const jobStatusOptions = [
  { value: "all", label: "Tous les statuts" },
  { value: "en_cours", label: "En cours" },
  { value: "cloture", label: "Clôturé" },
  { value: "annule", label: "Annulé" },
] as const;

const jobStatusLabels: Record<string, string> = {
  draft: "Brouillon",
  open: "En cours",
  paused: "En pause",
  closed: "Clôturé",
  archived: "Annulé",
};

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(value));
}

function buildCandidateLink(jobId: string, stage: string) {
  const params = new URLSearchParams({ job_id: jobId, stage });
  return `/candidates?${params.toString()}`;
}

function PipelineTable({ pipeline }: { pipeline: JobPipeline }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-[#0B1F3A]">{pipeline.title}</h3>
            <p className="mt-1 text-sm text-slate-600">
              {[pipeline.company_name, pipeline.location].filter(Boolean).join(" · ") || "Client et localisation non renseignés"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
              {jobStatusLabels[pipeline.status] ?? pipeline.status}
            </span>
            <span className="rounded-full bg-[#1D6EEA]/10 px-2.5 py-1 font-medium text-[#1D6EEA]">
              Ouvert le {formatDate(pipeline.opened_at)}
            </span>
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="px-5 py-3 font-semibold">Étape</th>
              <th className="px-5 py-3 font-semibold text-right">Nombre</th>
            </tr>
          </thead>
          <tbody>
            {pipeline.stages.map((stage: PipelineStageCount) => (
              <tr key={stage.stage} className="border-b border-slate-50 last:border-b-0">
                <td className="px-5 py-3">
                  {stage.count > 0 ? (
                    <Link
                      className="font-medium text-[#1D6EEA] hover:text-[#165AC0] hover:underline"
                      to={buildCandidateLink(pipeline.job_id, stage.stage)}
                    >
                      {stage.label}
                    </Link>
                  ) : (
                    <span className="text-slate-700">{stage.label}</span>
                  )}
                </td>
                <td className="px-5 py-3 text-right font-semibold text-[#0B1F3A]">
                  {stage.count > 0 ? (
                    <Link
                      className="text-[#1D6EEA] hover:text-[#165AC0] hover:underline"
                      to={buildCandidateLink(pipeline.job_id, stage.stage)}
                    >
                      {stage.count}
                    </Link>
                  ) : (
                    stage.count
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardPipeline | null>(null);
  const [filters, setFilters] = useState<DashboardPipelineFilters>({ job_status: "all" });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPipeline = useCallback(async (activeFilters: DashboardPipelineFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const pipelineData = await getDashboardPipeline(activeFilters);
      setData(pipelineData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger le tableau de bord."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPipeline(filters);
  }, [filters, loadPipeline]);

  function updateFilter<K extends keyof DashboardPipelineFilters>(key: K, value: DashboardPipelineFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value || undefined }));
  }

  if (isLoading && !data) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Chargement du tableau de bord...
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error}
      </div>
    );
  }

  const jobs = data?.filter_options.jobs ?? [];
  const clients = data?.filter_options.clients ?? [];
  const locations = data?.filter_options.locations ?? [];
  const pipelines = data?.pipelines ?? [];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-[#0B1F3A]">Filtres</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Poste</span>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.job_id ?? ""}
              onChange={(event) => updateFilter("job_id", event.target.value || undefined)}
            >
              <option value="">Tous les postes</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Statut du poste</span>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.job_status ?? "all"}
              onChange={(event) =>
                updateFilter("job_status", event.target.value as DashboardPipelineFilters["job_status"])
              }
            >
              {jobStatusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Client</span>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.client ?? ""}
              onChange={(event) => updateFilter("client", event.target.value || undefined)}
            >
              <option value="">Tous les clients</option>
              {clients.map((client) => (
                <option key={client} value={client}>
                  {client}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Date d&apos;ouverture (du)</span>
            <input
              type="date"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.opened_from ?? ""}
              onChange={(event) => updateFilter("opened_from", event.target.value || undefined)}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Date d&apos;ouverture (au)</span>
            <input
              type="date"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.opened_to ?? ""}
              onChange={(event) => updateFilter("opened_to", event.target.value || undefined)}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Localisation</span>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={filters.location ?? ""}
              onChange={(event) => updateFilter("location", event.target.value || undefined)}
            >
              <option value="">Toutes les localisations</option>
              {locations.map((location) => (
                <option key={location} value={location}>
                  {location}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Pipeline des candidatures par poste</h2>
          {isLoading ? <span className="text-xs text-slate-500">Mise à jour...</span> : null}
        </div>

        {error ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error}</div>
        ) : null}

        {pipelines.length === 0 ? (
          <EmptyState
            title="Aucun poste trouvé"
            description="Ajustez les filtres pour afficher le pipeline des candidatures."
          />
        ) : (
          pipelines.map((pipeline) => <PipelineTable key={pipeline.job_id} pipeline={pipeline} />)
        )}
      </section>
    </div>
  );
}
