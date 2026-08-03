import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { SourceBadge } from "../components/SourceBadge";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import {
  CandidateHistory,
  CandidateHistoryApplication,
  acceptApplication,
  getCandidateHistory,
  reactivateApplication,
  rejectApplication,
} from "../services/candidates";
import { CandidateHistoryCVFile } from "../services/candidates";
import { downloadCVFile, uploadCV } from "../services/cv";

const allowedCVExtensions = [".pdf", ".doc", ".docx"];
const maxCVFileSizeBytes = 5 * 1024 * 1024;

function formatDate(value: string | null | undefined) {
  return value ? new Date(value).toLocaleString() : "-";
}

function formatLabel(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  const labels: Record<string, string> = {
    recruiter: "Recruteur",
    candidate_portal: "Portail candidat",
    linkedin_csv: "Import LinkedIn",
    cv_upload: "Import CV",
    manual: "Import CV",
    outlook_import: "Import CV",
    referral: "Portail candidat",
    other: "Import CV",
    pending: "En attente",
    processing: "En cours",
    completed: "Terminé",
    failed: "Échec",
    parsed: "Analysé",
    uploaded: "Importé",
    active: "Actif",
    accepted: "Acceptée",
    rejected: "Refusée",
    shortlisted: "Présélectionnée",
    hired: "Recrutée",
    interview_scheduled: "Entretien planifié",
    entretien_cabinet: "Entretien cabinet",
    entretien_client: "Entretien client",
    profil_valide: "Profil validé",
    refus_candidat: "Refus candidat",
    non_selectionne: "Non sélectionné",
    preselectionne: "Présélectionné",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatScore(value: string | number | null | undefined) {
  if (value === null || value === undefined) return "-";
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return String(value);
  return `${Math.round(numeric * 100)}%`;
}

function latestMatch(application: CandidateHistoryApplication) {
  return [...application.matching_results].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];
}

function getDateTime(value: string | null | undefined) {
  if (!value) {
    return 0;
  }
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function sortCVFilesByUploadDate(cvFiles: CandidateHistoryCVFile[]) {
  return [...cvFiles].sort((a, b) => getDateTime(b.uploaded_at) - getDateTime(a.uploaded_at));
}

type CandidateHistoryRow = {
  id: string;
  date: string | null;
  category: string;
  title: string;
  details: string;
};

export function CandidateDetailsPage() {
  const { candidateId } = useParams();
  const [history, setHistory] = useState<CandidateHistory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeciding, setIsDeciding] = useState<string | null>(null);
  const [isCvUploading, setIsCvUploading] = useState(false);
  const [isCvDownloading, setIsCvDownloading] = useState<string | null>(null);
  const [selectedCVFile, setSelectedCVFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadHistory = async () => {
    if (!candidateId) {
      setError("L'identifiant du candidat est manquant.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setHistory(await getCandidateHistory(candidateId));
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger l'historique du candidat."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, [candidateId]);

  const handleDecision = async (applicationId: string, decision: "accept" | "reject" | "reactivate") => {
    setIsDeciding(`${decision}:${applicationId}`);
    setError(null);
    setMessage(null);
    try {
      if (decision === "accept") {
        await acceptApplication(applicationId);
        setMessage("Candidature acceptée.");
      } else if (decision === "reject") {
        await rejectApplication(applicationId);
        setMessage("Candidature refusée et candidat conservé dans le vivier.");
      } else {
        await reactivateApplication(applicationId);
        setMessage("Candidature réactivée.");
      }
      await loadHistory();
    } catch (decisionError) {
      setError(getApiErrorMessage(decisionError, "La décision RH n'a pas pu être enregistrée."));
    } finally {
      setIsDeciding(null);
    }
  };

  const validateCVFile = (file: File | null) => {
    if (!file) {
      return "Veuillez sélectionner un fichier CV.";
    }
    const lowerName = file.name.toLowerCase();
    if (!allowedCVExtensions.some((extension) => lowerName.endsWith(extension))) {
      return "Format non supporté. Veuillez ajouter un CV PDF, DOC ou DOCX.";
    }
    if (file.size > maxCVFileSizeBytes) {
      return "Le fichier dépasse 5MB.";
    }
    return null;
  };

  const handleDownloadCV = async (cv: CandidateHistoryCVFile) => {
    setIsCvDownloading(cv.id);
    setError(null);
    try {
      await downloadCVFile(cv.id, cv.original_filename);
    } catch (downloadError) {
      setError(getApiErrorMessage(downloadError, "Le téléchargement du CV a échoué."));
    } finally {
      setIsCvDownloading(null);
    }
  };

  const handleUploadCandidateCV = async () => {
    if (!candidateId) {
      setError("L'identifiant du candidat est manquant.");
      return;
    }
    const validationError = validateCVFile(selectedCVFile);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsCvUploading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await uploadCV(candidateId, selectedCVFile as File);
      if (result.duplicate) {
        setMessage(result.message ?? "Ce CV existe déjà dans la base de données.");
      } else if (result.updated_existing) {
        setMessage("CV remplacé avec succès. L'analyse du CV et le matching IA ont été relancés.");
      } else {
        setMessage("CV ajouté avec succès. L'analyse du CV et le matching IA ont été lancés.");
      }
      setSelectedCVFile(null);
      await loadHistory();
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "L'ajout du CV a échoué."));
    } finally {
      setIsCvUploading(false);
    }
  };

  const stats = useMemo(() => {
    if (!history) {
      return { applications: 0, cvs: 0, matches: 0, interviews: 0, evaluations: 0 };
    }
    return {
      applications: history.applications.length,
      cvs: history.cv_files.length,
      matches: history.matching_results.length,
      interviews: history.interviews.length,
      evaluations: history.evaluations.length,
    };
  }, [history]);

  const sortedCVFiles = useMemo(() => sortCVFilesByUploadDate(history?.cv_files ?? []), [history]);

  const historyRows = useMemo<CandidateHistoryRow[]>(() => {
    if (!history) {
      return [];
    }

    const cvRows = sortedCVFiles.map((cv, index) => ({
      id: `cv-${cv.id}`,
      date: cv.uploaded_at,
      category: index === 0 ? "CV actuel" : "CV historisé",
      title: cv.original_filename,
      details: `Analyse ${formatLabel(cv.parsing_status)} - modèle ${cv.parser_model ?? "-"}`,
    }));

    const applicationRows = history.applications.map((application) => ({
      id: `application-${application.id}`,
      date: application.applied_at,
      category: "Candidature",
      title: application.job_title,
      details: `${application.company_name ?? "Entreprise non renseignée"} - statut ${formatLabel(application.status)} - Étape ${formatLabel(application.current_stage)}`,
    }));

    const preselectionRows = history.applications
      .filter((application) => application.current_stage === "preselectionne" || application.status === "shortlisted")
      .map((application) => ({
        id: `preselection-${application.id}`,
        date: application.applied_at,
        category: "Présélection CV",
        title: application.job_title,
        details: `Présélection faite sur le CV pour ${application.company_name ?? "l'offre"}.`,
      }));

    const matchingRows = history.matching_results.map((match) => ({
      id: `matching-${match.id}`,
      date: match.created_at,
      category: "Matching IA",
      title: match.job_title ?? "Offre non renseignée",
      details: `Score ${formatScore(match.score)} - recommandation ${formatLabel(match.recommendation)}`,
    }));

    const decisionRows = history.timeline_events
      .filter((event) =>
        ["application_accepted", "application_rejected", "application_reactivated", "candidate_rejected", "candidate_reactivated"].includes(event.event_type),
      )
      .map((event) => ({
        id: `decision-${event.id}`,
        date: event.created_at,
        category: "Décision RH",
        title: event.title,
        details: event.description ?? formatLabel(event.event_type),
      }));

    return [...cvRows, ...applicationRows, ...preselectionRows, ...matchingRows, ...decisionRows].sort(
      (a, b) => getDateTime(b.date) - getDateTime(a.date),
    );
  }, [history, sortedCVFiles]);

  if (isLoading) {
    return <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">Chargement du candidat...</section>;
  }

  if (error && !history) {
    return (
      <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p>{error}</p>
        <Link className="mt-4 inline-block font-semibold text-red-800 underline" to="/candidates">
          Retour aux candidats
        </Link>
      </section>
    );
  }

  if (!history) {
    return null;
  }

  const candidate = history.candidate;
  const fullName = `${candidate.first_name} ${candidate.last_name}`;

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#EE6C2F]">Fiche candidat RH</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#24303F]">{fullName}</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
          <p>
            <span className="block font-semibold text-slate-500">Nom</span>
            {candidate.last_name}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Prénom</span>
            {candidate.first_name}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Email (identifiant unique)</span>
            {candidate.email ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Téléphone</span>
            {candidate.phone ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Ville</span>
            {candidate.location ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Poste actuel</span>
            {candidate.current_title ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Secteur</span>
            {candidate.sector ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Source</span>
            <span className="mt-1 inline-block">
              <SourceBadge source={candidate.source} />
            </span>
          </p>
          {candidate.source === "linkedin_csv" && candidate.linkedin_url ? (
            <p>
              <span className="block font-semibold text-slate-500">Profil LinkedIn</span>
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="mt-1 inline-flex items-center gap-1.5 text-[#EE6C2F] hover:text-[#D9551B] font-semibold underline"
              >
                Voir le profil LinkedIn ↗
              </a>
            </p>
          ) : null}
        </div>
        {sortedCVFiles.length > 0 ? (
          <div className="mt-5 flex flex-wrap gap-3">
            {sortedCVFiles.slice(0, 1).map((cv) => (
              <button
                key={cv.id}
                className="inline-flex items-center gap-2 rounded-lg bg-[#EE6C2F] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#D9551B]"
                disabled={isCvDownloading === cv.id}
                onClick={() => void handleDownloadCV(cv)}
                type="button"
              >
                {isCvDownloading === cv.id ? "Téléchargement..." : "Télécharger le CV"}
              </button>
            ))}
          </div>
        ) : null}
      </section>

      <section className="grid gap-4 md:grid-cols-5">
        <StatCard label="Statut" value={formatLabel(candidate.status)} detail={candidate.is_talent_pool ? "Présent dans le vivier candidats" : "Statut candidat"} />
        <StatCard label="Candidatures" value={String(stats.applications)} detail="Offres postulées" />
        <StatCard label="CV" value={String(stats.cvs)} detail="Fichiers conservés" />
        <StatCard label="Matching IA" value={String(stats.matches)} detail="Scores RH internes" />
        <StatCard label="Entretiens" value={String(stats.interviews)} detail={`${stats.evaluations} évaluation(s)`} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
          <div>
            <h3 className="text-base font-semibold text-[#24303F]">Historique synthétique candidat</h3>
            <p className="mt-1 text-sm text-slate-600">
              CV envoyés ou remplacés : <span className="font-semibold text-[#24303F]">{history.cv_files.length}</span>
            </p>
          </div>
        </div>
        {historyRows.length === 0 ? (
          <div className="p-5">
            <EmptyState title="Aucun historique synthétique" description="Les CV, candidatures, matchings et décisions apparaîtront ici." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Date</th>
                  <th className="px-5 py-3 font-semibold">Type</th>
                  <th className="px-5 py-3 font-semibold">Élément</th>
                  <th className="px-5 py-3 font-semibold">Détail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {historyRows.map((row) => (
                  <tr className="hover:bg-slate-50" key={row.id}>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatDate(row.date)}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className="rounded-full bg-[#EE6C2F]/10 px-3 py-1 text-xs font-semibold text-[#EE6C2F]">{row.category}</span>
                    </td>
                    <td className="px-5 py-4 font-semibold text-[#24303F]">{row.title}</td>
                    <td className="px-5 py-4 text-slate-700">{row.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="text-base font-semibold text-[#24303F]">Offres postulées et décisions RH</h3>
          <p className="mt-1 text-sm text-slate-600">Historique des candidatures, statuts, scores de matching et actions RH.</p>
        </div>
        {history.applications.length === 0 ? (
          <div className="p-5">
            <EmptyState title="Aucune candidature" description="Ce candidat n'a pas encore postulé à une offre." />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {history.applications.map((application) => {
              const match = latestMatch(application);
              return (
                <article className="space-y-4 p-5" key={application.id}>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h4 className="text-lg font-semibold text-[#24303F]">{application.job_title}</h4>
                      <p className="mt-1 text-sm text-slate-600">
                        {application.company_name ?? "Entreprise non renseignée"} - {formatLabel(application.source)}
                      </p>
                      <p className="mt-2 text-sm text-slate-700">
                        Candidature envoyée le <span className="font-semibold">{formatDate(application.applied_at)}</span>
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
                        disabled={isDeciding !== null}
                        onClick={() => void handleDecision(application.id, "accept")}
                        type="button"
                      >
                        Accepter
                      </button>
                      <button
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                        disabled={isDeciding !== null}
                        onClick={() => void handleDecision(application.id, "reject")}
                        type="button"
                      >
                        Refuser
                      </button>
                      <button
                        className="rounded-lg border border-[#EE6C2F]/30 px-3 py-1.5 text-xs font-semibold text-[#EE6C2F] hover:bg-orange-50 disabled:opacity-50"
                        disabled={isDeciding !== null}
                        onClick={() => void handleDecision(application.id, "reactivate")}
                        type="button"
                      >
                        Réactiver
                      </button>
                    </div>
                  </div>
                  <div className="grid gap-3 text-sm md:grid-cols-4">
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Statut candidature</span>
                      <span className="font-semibold capitalize text-[#24303F]">{formatLabel(application.status)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Étape RH</span>
                      <span className="font-semibold capitalize text-[#24303F]">{formatLabel(application.current_stage)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Score de matching</span>
                      <span className="font-semibold text-[#24303F]">{formatScore(match?.score)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Score sémantique</span>
                      <span className="font-semibold text-[#24303F]">{match?.semantic_score ?? "-"}</span>
                    </p>
                  </div>
                  {application.interviews.length > 0 || application.evaluations.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <h5 className="text-sm font-semibold text-[#24303F]">Entretiens</h5>
                        <ul className="mt-2 space-y-2 text-sm text-slate-600">
                          {application.interviews.map((interview) => (
                            <li className="rounded-lg border border-slate-100 p-3" key={interview.id}>
                              {formatLabel(interview.interview_type)} - {formatLabel(interview.status)} - {formatDate(interview.scheduled_start_at)}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-[#24303F]">Évaluations</h5>
                        <ul className="mt-2 space-y-2 text-sm text-slate-600">
                          {application.evaluations.map((evaluation) => (
                            <li className="rounded-lg border border-slate-100 p-3" key={evaluation.id}>
                              Recommandation {formatLabel(evaluation.recommendation)} - Score global {evaluation.global_score ?? "-"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#24303F]">CV uploadés</h3>
          </div>
          {sortedCVFiles.length === 0 ? (
            <div className="space-y-4 p-5">
              <EmptyState title="Aucun CV" description="Aucun fichier CV n'est attaché à ce candidat." />
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
                <label className="block text-sm font-medium text-slate-700">
                  Ajouter un CV
                  <input
                    accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#EE6C2F] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-white"
                    disabled={isCvUploading}
                    onChange={(event) => setSelectedCVFile(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                </label>
                <button
                  className="mt-3 rounded-lg bg-[#EE6C2F] px-4 py-2 text-sm font-semibold text-white hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isCvUploading || !selectedCVFile}
                  onClick={() => void handleUploadCandidateCV()}
                  type="button"
                >
                  {isCvUploading ? "Ajout en cours..." : "Ajouter un CV"}
                </button>
              </div>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {sortedCVFiles.map((cv) => (
                <li className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 text-sm" key={cv.id}>
                  <div>
                    <p className="font-semibold text-[#24303F]">{cv.original_filename}</p>
                    <p className="mt-1 text-slate-600">
                      Analyse du CV {formatLabel(cv.parsing_status)} - modèle {cv.parser_model ?? "-"} - {formatDate(cv.uploaded_at)}
                    </p>
                  </div>
                  <button
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    disabled={isCvDownloading === cv.id}
                    onClick={() => void handleDownloadCV(cv)}
                    type="button"
                  >
                    {isCvDownloading === cv.id ? "Téléchargement..." : "Télécharger"}
                  </button>
                </li>
              ))}
              <li className="space-y-3 bg-slate-50 px-5 py-4 text-sm">
                <label className="block font-medium text-slate-700">
                  Remplacer CV
                  <input
                    accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#EE6C2F] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-white"
                    disabled={isCvUploading}
                    onChange={(event) => setSelectedCVFile(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                </label>
                <button
                  className="rounded-lg bg-[#EE6C2F] px-4 py-2 text-xs font-semibold text-white hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isCvUploading || !selectedCVFile}
                  onClick={() => void handleUploadCandidateCV()}
                  type="button"
                >
                  {isCvUploading ? "Remplacement en cours..." : "Remplacer CV"}
                </button>
              </li>
            </ul>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#24303F]">Timeline RH</h3>
          </div>
          {history.timeline_events.length === 0 ? (
            <div className="p-5">
              <EmptyState title="Aucun événement" description="Aucun historique RH n'est encore enregistré." />
            </div>
          ) : (
            <ol className="divide-y divide-slate-100">
              {history.timeline_events.map((event) => (
                <li className="px-5 py-4 text-sm" key={event.id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-[#24303F]">{event.title}</p>
                    <time className="text-xs text-slate-500">{formatDate(event.created_at)}</time>
                  </div>
                  <p className="mt-1 text-slate-600">{event.description ?? formatLabel(event.event_type)}</p>
                  <p className="mt-2 text-xs font-semibold uppercase text-slate-400">{formatLabel(event.event_type)}</p>
                </li>
              ))}
            </ol>
          )}
        </section>
      </section>
    </div>
  );
}
