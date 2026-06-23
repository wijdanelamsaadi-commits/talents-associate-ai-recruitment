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

function formatDate(value: string | null | undefined) {
  return value ? new Date(value).toLocaleString() : "-";
}

function formatLabel(value: string | null | undefined) {
  return value ? value.replaceAll("_", " ") : "-";
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

export function CandidateDetailsPage() {
  const { candidateId } = useParams();
  const [history, setHistory] = useState<CandidateHistory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeciding, setIsDeciding] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadHistory = async () => {
    if (!candidateId) {
      setError("Candidate id is missing.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setHistory(await getCandidateHistory(candidateId));
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load candidate history."));
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

  if (isLoading) {
    return <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">Loading candidate...</section>;
  }

  if (error && !history) {
    return (
      <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p>{error}</p>
        <Link className="mt-4 inline-block font-semibold text-red-800 underline" to="/candidates">
          Back to candidates
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
        <p className="text-sm font-semibold uppercase tracking-wide text-[#E8590C]">Fiche candidat RH</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{fullName}</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
          <p>
            <span className="block font-semibold text-slate-500">Email</span>
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
            <span className="block font-semibold text-slate-500">Source</span>
            <span className="mt-1 inline-block">
              <SourceBadge source={candidate.source} />
            </span>
          </p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-5">
        <StatCard label="Statut" value={formatLabel(candidate.status)} detail={candidate.is_talent_pool ? "Présent dans le vivier candidats" : "Statut candidat"} />
        <StatCard label="Candidatures" value={String(stats.applications)} detail="Offres postulées" />
        <StatCard label="CV" value={String(stats.cvs)} detail="Fichiers conservés" />
        <StatCard label="Matching IA" value={String(stats.matches)} detail="Scores RH internes" />
        <StatCard label="Entretiens" value={String(stats.interviews)} detail={`${stats.evaluations} évaluation(s)`} />
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="text-base font-semibold text-[#0B1F3A]">Offres postulées et décisions RH</h3>
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
                      <h4 className="text-lg font-semibold text-[#0B1F3A]">{application.job_title}</h4>
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
                        className="rounded-lg border border-[#E8590C]/30 px-3 py-1.5 text-xs font-semibold text-[#E8590C] hover:bg-orange-50 disabled:opacity-50"
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
                      <span className="font-semibold capitalize text-[#0B1F3A]">{formatLabel(application.status)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Étape RH</span>
                      <span className="font-semibold capitalize text-[#0B1F3A]">{formatLabel(application.current_stage)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Score de matching</span>
                      <span className="font-semibold text-[#0B1F3A]">{formatScore(match?.score)}</span>
                    </p>
                    <p className="rounded-lg bg-slate-50 p-3">
                      <span className="block text-xs font-semibold uppercase text-slate-500">Score sémantique</span>
                      <span className="font-semibold text-[#0B1F3A]">{match?.semantic_score ?? "-"}</span>
                    </p>
                  </div>
                  {application.interviews.length > 0 || application.evaluations.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <h5 className="text-sm font-semibold text-[#0B1F3A]">Entretiens</h5>
                        <ul className="mt-2 space-y-2 text-sm text-slate-600">
                          {application.interviews.map((interview) => (
                            <li className="rounded-lg border border-slate-100 p-3" key={interview.id}>
                              {formatLabel(interview.interview_type)} - {formatLabel(interview.status)} - {formatDate(interview.scheduled_start_at)}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-[#0B1F3A]">Évaluations</h5>
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
            <h3 className="text-base font-semibold text-[#0B1F3A]">CV uploadés</h3>
          </div>
          {history.cv_files.length === 0 ? (
            <div className="p-5">
              <EmptyState title="Aucun CV" description="Aucun fichier CV n'est attaché à ce candidat." />
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {history.cv_files.map((cv) => (
                <li className="px-5 py-4 text-sm" key={cv.id}>
                  <p className="font-semibold text-[#0B1F3A]">{cv.original_filename}</p>
                  <p className="mt-1 text-slate-600">
                    Parsing {formatLabel(cv.parsing_status)} - modèle {cv.parser_model ?? "-"} - {formatDate(cv.uploaded_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Timeline RH</h3>
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
                    <p className="font-semibold text-[#0B1F3A]">{event.title}</p>
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
