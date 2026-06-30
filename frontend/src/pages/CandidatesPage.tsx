import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { SourceBadge, formatSource } from "../components/SourceBadge";
import { StatCard } from "../components/StatCard";
import { SECTORS } from "../constants/sectors";
import { getApiErrorMessage } from "../lib/errors";
import {
  Candidate,
  getCandidatesPaginated,
  reactivateCandidate,
  updateCandidate,
} from "../services/candidates";

const PAGE_SIZE = 50;

type CandidateFormState = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  city: string;
  current_title: string;
  sector: string;
  source: string;
  status: string;
};

const initialFormState: CandidateFormState = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  city: "",
  current_title: "",
  sector: "",
  source: "cv_upload",
  status: "new",
};

const sourceOptions = ["cv_upload", "linkedin_csv", "candidate_portal"];
const statusOptions = [
  "new",
  "active",
  "shortlisted",
  "interviewing",
  "offered",
  "hired",
  "rejected",
  "archived",
  "talent_pool",
  "preselectionne",
  "non_selectionne",
  "entretien_cabinet",
  "entretien_client",
  "profil_valide",
  "refus_candidat",
];

const pipelineStageLabels: Record<string, string> = {
  recu: "Candidatures reçues",
  preselectionne: "Présélectionnées",
  non_selectionne: "Non sélectionnées",
  entretien_cabinet: "Entretien cabinet",
  entretien_client: "Entretien client",
  profil_valide: "Profil validé",
  refus_candidat: "Refus candidat",
};
const candidateFilterOptions = [
  { label: "Vivier des candidats", value: "all" },
] as const;

type CandidateFilter = (typeof candidateFilterOptions)[number]["value"];

function formatStatus(status: string) {
  const labels: Record<string, string> = {
    new: "nouveau",
    active: "actif",
    shortlisted: "présélectionné",
    interviewing: "entretien",
    offered: "offre envoyée",
    hired: "recruté",
    rejected: "refusé",
    archived: "archivé",
    talent_pool: "vivier candidats",
    preselectionne: "présélectionné",
    non_selectionne: "non sélectionné",
    entretien_cabinet: "entretien cabinet",
    entretien_client: "entretien client",
    profil_valide: "profil validé",
    refus_candidat: "refus candidat",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}

function formatCurrentPosition(candidate: Candidate) {
  const title = candidate.current_title?.trim();
  const company = candidate.current_company?.trim();
  if (title && company) {
    return `${title} — ${company}`;
  }
  return title || company || "-";
}

function toFormState(candidate: Candidate): CandidateFormState {
  return {
    first_name: candidate.first_name,
    last_name: candidate.last_name,
    email: candidate.email ?? "",
    phone: candidate.phone ?? "",
    city: candidate.location ?? "",
    current_title: candidate.current_title ?? "",
    sector: candidate.sector ?? "",
    source: candidate.source,
    status: candidate.status,
  };
}

export function CandidatesPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const pipelineJobId = searchParams.get("job_id") ?? undefined;
  const pipelineStage = searchParams.get("stage") ?? undefined;
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [page, setPage] = useState(1);
  const [totalCandidates, setTotalCandidates] = useState(0);
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCandidate, setEditingCandidate] = useState<Candidate | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formState, setFormState] = useState<CandidateFormState>(initialFormState);
  const [formError, setFormError] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [candidateFilter, setCandidateFilter] = useState<CandidateFilter>("all");

  const totalPages = Math.max(1, Math.ceil(totalCandidates / PAGE_SIZE));

  const loadCandidates = async (pageNumber = page, cursor: string | null = page === 1 ? null : cursorHistory[page - 2] ?? null) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getCandidatesPaginated({
        skip: 0,
        limit: PAGE_SIZE,
        after_id: pageNumber === 1 ? null : cursor,
        filter: candidateFilter,
        job_offer_id: pipelineJobId,
        pipeline_stage: pipelineStage,
      });
      setCandidates(response.items);
      setTotalCandidates(response.total);
      setNextCursor(response.next_cursor);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger les candidats. Vérifiez que le backend est démarré sur localhost:8001."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const cursor = page === 1 ? null : cursorHistory[page - 2] ?? null;
    void loadCandidates(page, cursor);
  }, [page, candidateFilter, pipelineJobId, pipelineStage]);

  const stats = useMemo(() => {
    const activeCount = candidates.filter((candidate) => candidate.status === "active").length;
    const interviewingCount = candidates.filter((candidate) => candidate.status === "interviewing").length;
    return {
      total: totalCandidates,
      active: activeCount,
      interviewing: interviewingCount,
    };
  }, [candidates, totalCandidates]);

  const goToNextPage = () => {
    if (page >= totalPages || !nextCursor) {
      return;
    }
    setCursorHistory((current) => {
      const updated = [...current];
      updated[page - 1] = nextCursor;
      return updated;
    });
    setPage((current) => current + 1);
  };

  const goToPreviousPage = () => {
    if (page > 1) {
      setPage((current) => current - 1);
    }
  };

  const filteredCandidates = useMemo(() => {
    if (sourceFilter === "all") {
      return candidates;
    }
    return candidates.filter((candidate) => candidate.source === sourceFilter);
  }, [candidates, sourceFilter]);

  const openEditModal = (candidate: Candidate) => {
    setEditingCandidate(candidate);
    setFormState(toFormState(candidate));
    setFormError(null);
    setMessage(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingCandidate) {
      return;
    }

    setFormError(null);
    setIsSubmitting(true);

    const payload = {
      first_name: formState.first_name.trim(),
      last_name: formState.last_name.trim(),
      email: formState.email.trim() || null,
      phone: formState.phone.trim() || null,
      location: formState.city.trim() || null,
      current_title: formState.current_title.trim() || null,
      sector: formState.sector.trim() || null,
      source: formState.source,
      status: formState.status,
    };

    try {
      await updateCandidate(editingCandidate.id, payload);
      setMessage("Candidat mis à jour avec succès.");
      setFormState(initialFormState);
      setEditingCandidate(null);
      setIsModalOpen(false);
      await loadCandidates(page, page === 1 ? null : cursorHistory[page - 2] ?? null);
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError, "Le candidat n'a pas pu être enregistré."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetPagination = () => {
    setCursorHistory([]);
    setNextCursor(null);
    setPage(1);
  };

  const handleReactivate = async (candidate: Candidate) => {
    setError(null);
    setMessage(null);
    try {
      await reactivateCandidate(candidate.id);
      setMessage("Candidat réactivé.");
      await loadCandidates(page, page === 1 ? null : cursorHistory[page - 2] ?? null);
    } catch (reactivateError) {
      setError(getApiErrorMessage(reactivateError, "Le candidat n'a pas pu être réactivé."));
    }
  };

  return (
    <div className="space-y-6">
      {pipelineJobId || pipelineStage ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[#1D6EEA]/20 bg-[#1D6EEA]/5 px-4 py-3 text-sm">
          <p className="text-slate-700">
            Filtre pipeline actif
            {pipelineStage ? ` — ${pipelineStageLabels[pipelineStage] ?? pipelineStage}` : ""}
          </p>
          <button
            type="button"
            className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]"
            onClick={() => setSearchParams({})}
          >
            Effacer le filtre
          </button>
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total candidats" value={String(stats.total)} detail="Profils chargés depuis le backend" />
        <StatCard label="Candidats actifs" value={String(stats.active)} detail="Profils actuellement actifs" />
        <StatCard label="En entretien" value={String(stats.interviewing)} detail="Candidats en phase d'entretien" />
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Vivier des candidats</h2>
          <p className="mt-1 text-sm text-slate-600">
            Les candidats sont ajoutés via l&apos;import de CV, l&apos;import LinkedIn ou le profilage manuel.
          </p>
        </div>
        <div className="flex gap-3 text-sm font-semibold">
          <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/cv-upload">
            Import de CV
          </Link>
          <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/imports">
            Import LinkedIn
          </Link>
        </div>
      </div>

      <section className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <span className="text-sm font-medium text-slate-700">Filtrer les candidats</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {candidateFilterOptions.map((option) => (
              <button
                className={`rounded-full border px-4 py-2 text-sm font-semibold transition ${
                  candidateFilter === option.value
                    ? "border-[#FF3D00] bg-[#FF3D00] text-white"
                    : "border-slate-200 bg-white text-slate-700 hover:border-[#FF3D00]/60 hover:text-[#FF3D00]"
                }`}
                key={option.value}
                onClick={() => {
                  setCandidateFilter(option.value);
                  resetPagination();
                }}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <label className="block w-full lg:w-64">
          <span className="text-sm font-medium text-slate-700">Source</span>
          <select
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
            onChange={(event) => {
              setSourceFilter(event.target.value);
              setPage(1);
            }}
            value={sourceFilter}
          >
            <option value="all">Toutes les sources</option>
            {sourceOptions.map((source) => (
              <option key={source} value={source}>
                {formatSource(source)}
              </option>
            ))}
          </select>
        </label>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</section> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement des candidats...
        </section>
      ) : null}

      {!isLoading && !error && candidates.length === 0 ? (
        <EmptyState
          title="Aucun candidat"
          description="Les candidats sont ajoutés via l'import de CV, l'import LinkedIn ou le profilage manuel."
        />
      ) : null}

      {!isLoading && !error && candidates.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Liste des candidats</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Nom</th>
                  <th className="px-5 py-3 font-semibold">Prénom</th>
                  <th className="px-5 py-3 font-semibold">Email</th>
                  <th className="px-5 py-3 font-semibold">Téléphone</th>
                  <th className="px-5 py-3 font-semibold">Ville</th>
                  <th className="px-5 py-3 font-semibold">Poste actuel</th>
                  <th className="px-5 py-3 font-semibold">Secteur</th>
                  <th className="px-5 py-3 font-semibold">Source</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCandidates.map((candidate) => (
                  <tr
                    key={candidate.id}
                    className="hover:bg-slate-50 cursor-pointer"
                    onClick={() => navigate(`/candidates/${candidate.id}`)}
                  >
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#1D6EEA] hover:text-[#165AC0]">
                      {candidate.last_name}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.first_name}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.email ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.phone ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.location ?? "-"}</td>
                    <td className="px-5 py-4 text-slate-700">{formatCurrentPosition(candidate)}</td>
                    <td className="px-5 py-4 text-slate-700">{candidate.sector ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <SourceBadge source={candidate.source} />
                    </td>
                    <td className="whitespace-nowrap px-5 py-4" onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-2">
                        <button
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          onClick={(e) => {
                            e.stopPropagation();
                            openEditModal(candidate);
                          }}
                          type="button"
                        >
                          Modifier
                        </button>
                        {candidate.status === "archived" || candidate.status === "rejected" || candidate.is_talent_pool ? (
                          <button
                            className="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
                            onClick={(e) => {
                              e.stopPropagation();
                              void handleReactivate(candidate);
                            }}
                            type="button"
                          >
                            Réactiver
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4">
            <p className="text-sm text-slate-600">
              Page {page} sur {totalPages} — {totalCandidates} candidat(s)
            </p>
            <div className="flex gap-2">
              <button
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={page <= 1 || isLoading}
                onClick={goToPreviousPage}
                type="button"
              >
                Précédent
              </button>
              <button
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={page >= totalPages || isLoading || !nextCursor}
                onClick={goToNextPage}
                type="button"
              >
                Suivant
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {!isLoading && !error && candidates.length > 0 && filteredCandidates.length === 0 ? (
        <EmptyState title="Aucun candidat pour cette source" description="Modifiez le filtre source pour afficher d'autres profils." />
      ) : null}

      {isModalOpen && editingCandidate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">Modifier le candidat</h3>
              <p className="mt-1 text-sm text-slate-600">L&apos;email est l&apos;identifiant unique du candidat.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Prénom</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, first_name: event.target.value }))}
                    required
                    value={formState.first_name}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Nom</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, last_name: event.target.value }))}
                    required
                    value={formState.last_name}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Email (identifiant unique)</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, email: event.target.value }))}
                    required
                    type="email"
                    value={formState.email}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Téléphone</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, phone: event.target.value }))}
                    value={formState.phone}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Ville</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, city: event.target.value }))}
                    value={formState.city}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Poste actuel</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, current_title: event.target.value }))}
                    value={formState.current_title}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Secteur</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, sector: event.target.value }))}
                    value={formState.sector}
                  >
                    <option value="">—</option>
                    {SECTORS.map((sector) => (
                      <option key={sector} value={sector}>
                        {sector}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Source</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, source: event.target.value }))}
                    value={formState.source}
                  >
                    {sourceOptions.map((source) => (
                      <option key={source} value={source}>
                        {formatSource(source)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Statut</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, status: event.target.value }))}
                    value={formState.status}
                  >
                    {statusOptions.map((status) => (
                      <option key={status} value={status}>
                        {formatStatus(status)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {formError ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{formError}</p> : null}

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  onClick={() => setIsModalOpen(false)}
                  type="button"
                >
                  Annuler
                </button>
                <button
                  className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Enregistrement..." : "Enregistrer"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
