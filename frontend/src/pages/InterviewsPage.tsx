import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StarRating } from "../components/StarRating";
import { StarRatingInput } from "../components/StarRatingInput";
import { StatCard } from "../components/StatCard";
import {
  EVALUATION_DECISION_OPTIONS,
  INTERVIEW_TYPE_OPTIONS,
  PIPELINE_STAGE_OPTIONS,
  pipelineStageLabel,
} from "../constants/pipeline";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidates } from "../services/candidates";
import {
  Evaluation,
  EvaluationPayload,
  createEvaluation,
  deleteEvaluation,
  getEvaluations,
  updateEvaluation,
} from "../services/evaluations";
import {
  Interview,
  InterviewPayload,
  createInterview,
  deleteInterview,
  getInterviews,
  updateInterview,
  updateInterviewStatus,
} from "../services/interviews";
import { JobOffer, getJobOffers } from "../services/jobs";

type InterviewFormState = {
  candidate_id: string;
  job_offer_id: string;
  interview_type: string;
  status: string;
  scheduled_start_at: string;
  notes: string;
};

type EvaluationFormState = {
  interview_id: string;
  rating: number;
  technical_score: number;
  soft_skills_score: number;
  motivation_score: number;
  recommendation: string;
  comments: string;
};

const initialInterviewForm: InterviewFormState = {
  candidate_id: "",
  job_offer_id: "",
  interview_type: "entretien_cabinet",
  status: "entretien_cabinet",
  scheduled_start_at: "",
  notes: "",
};

const initialEvaluationForm: EvaluationFormState = {
  interview_id: "",
  rating: 3,
  technical_score: 3,
  soft_skills_score: 3,
  motivation_score: 3,
  recommendation: "preselectionne",
  comments: "",
};

function candidateName(candidate?: Candidate) {
  return candidate ? `${candidate.first_name} ${candidate.last_name}` : "Candidat inconnu";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function toDatetimeLocal(value: string | null) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60_000);
  return localDate.toISOString().slice(0, 16);
}

function toApiDatetime(value: string) {
  return new Date(value).toISOString();
}

function toInterviewFormState(interview: Interview): InterviewFormState {
  return {
    candidate_id: interview.candidate_id,
    job_offer_id: interview.job_offer_id,
    interview_type: interview.interview_type,
    status: interview.status,
    scheduled_start_at: toDatetimeLocal(interview.scheduled_start_at),
    notes: interview.notes ?? "",
  };
}

function toInterviewPayload(formState: InterviewFormState): InterviewPayload {
  return {
    candidate_id: formState.candidate_id,
    job_offer_id: formState.job_offer_id,
    interview_type: formState.interview_type,
    status: formState.status,
    scheduled_start_at: toApiDatetime(formState.scheduled_start_at),
    notes: formState.notes.trim() || null,
  };
}

function toEvaluationFormState(evaluation: Evaluation): EvaluationFormState {
  return {
    interview_id: evaluation.interview_id,
    rating: evaluation.rating,
    technical_score: evaluation.technical_score,
    soft_skills_score: evaluation.soft_skills_score,
    motivation_score: evaluation.motivation_score,
    recommendation: evaluation.recommendation,
    comments: evaluation.comments ?? "",
  };
}

function toEvaluationPayload(formState: EvaluationFormState): EvaluationPayload {
  return {
    interview_id: formState.interview_id,
    rating: formState.rating,
    technical_score: formState.technical_score,
    soft_skills_score: formState.soft_skills_score,
    motivation_score: formState.motivation_score,
    recommendation: formState.recommendation,
    comments: formState.comments.trim() || null,
  };
}

export function InterviewsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") === "evaluations" ? "evaluations" : "interviews";
  const requestedInterviewId = searchParams.get("interviewId") ?? "";

  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isInterviewModalOpen, setIsInterviewModalOpen] = useState(false);
  const [isEvaluationModalOpen, setIsEvaluationModalOpen] = useState(false);
  const [editingInterview, setEditingInterview] = useState<Interview | null>(null);
  const [editingEvaluation, setEditingEvaluation] = useState<Evaluation | null>(null);
  const [interviewForm, setInterviewForm] = useState<InterviewFormState>(initialInterviewForm);
  const [evaluationForm, setEvaluationForm] = useState<EvaluationFormState>(initialEvaluationForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const interviewsArray = Array.isArray(interviews) ? interviews : [];

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [interviewData, evaluationData, candidateData, jobData] = await Promise.all([
        getInterviews(),
        getEvaluations(),
        getCandidates(),
        getJobOffers(),
      ]);
      setInterviews(Array.isArray(interviewData) ? interviewData : []);
      setEvaluations(evaluationData);
      setCandidates(candidateData);
      setJobs(jobData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger les entretiens et évaluations."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (requestedInterviewId && interviews.some((interview) => interview.id === requestedInterviewId)) {
      setEvaluationForm((current) => ({ ...current, interview_id: requestedInterviewId }));
      setEditingEvaluation(null);
      setIsEvaluationModalOpen(true);
      setSearchParams({ tab: "evaluations", interviewId: requestedInterviewId });
    }
  }, [requestedInterviewId, interviews, setSearchParams]);

  const interviewStats = useMemo(() => {
    const today = new Date().toDateString();
    const todayCount = interviewsArray.filter((interview) => new Date(interview.scheduled_start_at).toDateString() === today).length;
    const cabinetCount = interviewsArray.filter((interview) => interview.interview_type === "entretien_cabinet").length;
    const clientCount = interviewsArray.filter((interview) => interview.interview_type === "entretien_client").length;
    const validatedCount = interviewsArray.filter((interview) => interview.status === "profil_valide").length;
    return { todayCount, cabinetCount, clientCount, validatedCount };
  }, [interviewsArray]);

  const evaluationStats = useMemo(() => {
    const average =
      evaluations.length === 0
        ? 0
        : Math.round(evaluations.reduce((total, evaluation) => total + evaluation.rating, 0) / evaluations.length);
    const validated = evaluations.filter((evaluation) => evaluation.recommendation === "profil_valide").length;
    return { total: evaluations.length, average, validated };
  }, [evaluations]);

  const openCreateInterviewModal = () => {
    setEditingInterview(null);
    setFormError(null);
    setMessage(null);
    setInterviewForm({
      ...initialInterviewForm,
      candidate_id: candidates[0]?.id ?? "",
      job_offer_id: jobs[0]?.id ?? "",
    });
    setIsInterviewModalOpen(true);
  };

  const openEditInterviewModal = (interview: Interview) => {
    setEditingInterview(interview);
    setFormError(null);
    setMessage(null);
    setInterviewForm(toInterviewFormState(interview));
    setIsInterviewModalOpen(true);
  };

  const openCreateEvaluationModal = (interviewId?: string) => {
    setEditingEvaluation(null);
    setFormError(null);
    setMessage(null);
    setEvaluationForm({
      ...initialEvaluationForm,
      interview_id: interviewId ?? requestedInterviewId ?? interviews[0]?.id ?? "",
    });
    setIsEvaluationModalOpen(true);
  };

  const openEditEvaluationModal = (evaluation: Evaluation) => {
    setEditingEvaluation(evaluation);
    setFormError(null);
    setMessage(null);
    setEvaluationForm(toEvaluationFormState(evaluation));
    setIsEvaluationModalOpen(true);
  };

  const handleInterviewSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    if (!interviewForm.candidate_id || !interviewForm.job_offer_id) {
      setFormError("Sélectionnez un candidat et une offre d'emploi.");
      setIsSubmitting(false);
      return;
    }

    try {
      const payload = toInterviewPayload(interviewForm);
      if (editingInterview) {
        await updateInterview(editingInterview.id, payload);
        setMessage("Entretien mis à jour. Le statut pipeline du candidat a été synchronisé.");
      } else {
        await createInterview(payload);
        setMessage("Entretien planifié. Le statut pipeline du candidat a été mis à jour.");
      }
      setIsInterviewModalOpen(false);
      setEditingInterview(null);
      setInterviewForm(initialInterviewForm);
      await loadData();
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError, "L'entretien n'a pas pu être enregistré."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInterviewStatusChange = async (interview: Interview, status: string) => {
    setError(null);
    setMessage(null);
    try {
      await updateInterviewStatus(interview.id, status);
      setMessage(`Statut mis à jour : ${pipelineStageLabel(status)}. Pipeline candidat synchronisé.`);
      await loadData();
    } catch (statusError) {
      setError(getApiErrorMessage(statusError, "Le statut n'a pas pu être mis à jour."));
    }
  };

  const handleInterviewDelete = async (interview: Interview) => {
    if (!window.confirm("Supprimer cet entretien ?")) {
      return;
    }
    setError(null);
    try {
      await deleteInterview(interview.id);
      setMessage("Entretien supprimé.");
      await loadData();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "L'entretien n'a pas pu être supprimé."));
    }
  };

  const handleEvaluationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    if (!evaluationForm.interview_id) {
      setFormError("Sélectionnez un entretien.");
      setIsSubmitting(false);
      return;
    }

    try {
      const payload = toEvaluationPayload(evaluationForm);
      if (editingEvaluation) {
        await updateEvaluation(editingEvaluation.id, payload);
        setMessage("Évaluation mise à jour. Décision finale appliquée au pipeline.");
      } else {
        await createEvaluation(payload);
        setMessage("Évaluation enregistrée. Décision finale appliquée au pipeline.");
      }
      setIsEvaluationModalOpen(false);
      setEditingEvaluation(null);
      setEvaluationForm(initialEvaluationForm);
      await loadData();
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError, "L'évaluation n'a pas pu être enregistrée."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEvaluationDelete = async (evaluation: Evaluation) => {
    if (!window.confirm("Supprimer cette évaluation ?")) {
      return;
    }
    setError(null);
    try {
      await deleteEvaluation(evaluation.id);
      setMessage("Évaluation supprimée.");
      await loadData();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "L'évaluation n'a pas pu être supprimée."));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-2 border-b border-slate-200">
        <button
          type="button"
          className={[
            "border-b-2 px-4 py-2 text-sm font-semibold transition",
            activeTab === "interviews"
              ? "border-[#1D6EEA] text-[#1D6EEA]"
              : "border-transparent text-slate-500 hover:text-slate-700",
          ].join(" ")}
          onClick={() => setSearchParams({})}
        >
          Entretiens
        </button>
        <button
          type="button"
          className={[
            "border-b-2 px-4 py-2 text-sm font-semibold transition",
            activeTab === "evaluations"
              ? "border-[#1D6EEA] text-[#1D6EEA]"
              : "border-transparent text-slate-500 hover:text-slate-700",
          ].join(" ")}
          onClick={() => setSearchParams({ tab: "evaluations" })}
        >
          Évaluations
        </button>
      </div>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {activeTab === "interviews" ? (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <StatCard label="Aujourd'hui" value={String(interviewStats.todayCount)} detail="Entretiens planifiés aujourd'hui" />
            <StatCard label="Cabinet" value={String(interviewStats.cabinetCount)} detail="Entretiens cabinet" />
            <StatCard label="Client" value={String(interviewStats.clientCount)} detail="Entretiens client" />
            <StatCard label="Profils validés" value={String(interviewStats.validatedCount)} detail="Statut profil validé" />
          </section>

          <section className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-[#0B1F3A]">Entretiens planifiés</h2>
              <p className="mt-1 text-sm text-slate-600">
                Planifiez les entretiens et mettez à jour le statut pipeline du candidat.
              </p>
            </div>
            <button
              className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:opacity-60"
              disabled={candidates.length === 0 || jobs.length === 0}
              onClick={openCreateInterviewModal}
              type="button"
            >
              Nouvel entretien
            </button>
          </section>

          {isLoading ? (
            <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
              Chargement des entretiens...
            </section>
          ) : null}

          {!isLoading && (candidates.length === 0 || jobs.length === 0) ? (
            <EmptyState title="Candidats et offres requis" description="Créez au moins un candidat et une offre d'emploi." />
          ) : null}

          {!isLoading && interviewsArray.length === 0 && candidates.length > 0 && jobs.length > 0 ? (
            <EmptyState
              title="Aucun entretien"
              description="Planifiez le premier entretien pour un candidat."
              actionLabel="Nouvel entretien"
              onAction={openCreateInterviewModal}
            />
          ) : null}

          {interviewsArray.length > 0 ? (
            <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Candidat</th>
                      <th className="px-5 py-3 font-semibold">Poste</th>
                      <th className="px-5 py-3 font-semibold">Type</th>
                      <th className="px-5 py-3 font-semibold">Date et heure</th>
                      <th className="px-5 py-3 font-semibold">Statut</th>
                      <th className="px-5 py-3 font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {interviewsArray.map((interview) => {
                      const candidate = candidates.find((item) => item.id === interview.candidate_id);
                      const job = jobs.find((item) => item.id === interview.job_offer_id);
                      return (
                        <tr key={interview.id} className="hover:bg-slate-50">
                          <td className="whitespace-nowrap px-5 py-4">
                            <Link className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to={`/candidates/${interview.candidate_id}`}>
                              {candidateName(candidate)}
                            </Link>
                          </td>
                          <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job?.title ?? "—"}</td>
                          <td className="whitespace-nowrap px-5 py-4 text-slate-700">{pipelineStageLabel(interview.interview_type)}</td>
                          <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatDateTime(interview.scheduled_start_at)}</td>
                          <td className="whitespace-nowrap px-5 py-4">
                            <select
                              className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-700"
                              onChange={(event) => void handleInterviewStatusChange(interview, event.target.value)}
                              value={interview.status}
                            >
                              {PIPELINE_STAGE_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="whitespace-nowrap px-5 py-4">
                            <div className="flex gap-2">
                              <button
                                className="rounded-lg bg-[#1D6EEA] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#165AC0]"
                                onClick={() => {
                                  setSearchParams({ tab: "evaluations", interviewId: interview.id });
                                  openCreateEvaluationModal(interview.id);
                                }}
                                type="button"
                              >
                                Évaluer
                              </button>
                              <button
                                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                                onClick={() => openEditInterviewModal(interview)}
                                type="button"
                              >
                                Modifier
                              </button>
                              <button
                                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                                onClick={() => void handleInterviewDelete(interview)}
                                type="button"
                              >
                                Supprimer
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}
        </>
      ) : null}

      {activeTab === "evaluations" ? (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <StatCard label="Évaluations" value={String(evaluationStats.total)} detail="Évaluations enregistrées" />
            <StatCard label="Note moyenne" value={`${evaluationStats.average}/5`} detail="Note globale moyenne" />
            <StatCard label="Profils validés" value={String(evaluationStats.validated)} detail="Décisions profil validé" />
          </section>

          <section className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-[#0B1F3A]">Évaluations d&apos;entretien</h2>
              <p className="mt-1 text-sm text-slate-600">Complétez l&apos;évaluation pendant ou après l&apos;entretien.</p>
            </div>
            <button
              className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:opacity-60"
              disabled={interviews.length === 0}
              onClick={() => openCreateEvaluationModal()}
              type="button"
            >
              Nouvelle évaluation
            </button>
          </section>

          {!isLoading && interviews.length === 0 ? (
            <EmptyState title="Aucun entretien disponible" description="Planifiez un entretien avant d'ajouter une évaluation." />
          ) : null}

          {!isLoading && evaluations.length === 0 && interviews.length > 0 ? (
            <EmptyState
              title="Aucune évaluation"
              description="Enregistrez la première évaluation liée à un entretien."
              actionLabel="Nouvelle évaluation"
              onAction={() => openCreateEvaluationModal()}
            />
          ) : null}

          {evaluations.length > 0 ? (
            <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Candidat</th>
                      <th className="px-5 py-3 font-semibold">Entretien</th>
                      <th className="px-5 py-3 font-semibold">Note globale</th>
                      <th className="px-5 py-3 font-semibold">Décision finale</th>
                      <th className="px-5 py-3 font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {evaluations.map((evaluation) => {
                      const interview = interviews.find((item) => item.id === evaluation.interview_id);
                      const candidate = candidates.find((item) => item.id === evaluation.candidate_id);
                      const job = interview ? jobs.find((item) => item.id === interview.job_offer_id) : undefined;
                      return (
                        <tr key={evaluation.id} className="hover:bg-slate-50">
                          <td className="whitespace-nowrap px-5 py-4">
                            <Link className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to={`/candidates/${evaluation.candidate_id}`}>
                              {candidateName(candidate)}
                            </Link>
                          </td>
                          <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                            {job?.title ?? "Entretien"} — {interview ? formatDateTime(interview.scheduled_start_at) : ""}
                          </td>
                          <td className="whitespace-nowrap px-5 py-4">
                            <StarRating value={evaluation.rating} readOnly />
                          </td>
                          <td className="whitespace-nowrap px-5 py-4 text-slate-700">{pipelineStageLabel(evaluation.recommendation)}</td>
                          <td className="whitespace-nowrap px-5 py-4">
                            <div className="flex gap-2">
                              <button
                                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                                onClick={() => openEditEvaluationModal(evaluation)}
                                type="button"
                              >
                                Modifier
                              </button>
                              <button
                                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                                onClick={() => void handleEvaluationDelete(evaluation)}
                                type="button"
                              >
                                Supprimer
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}
        </>
      ) : null}

      {isInterviewModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">
                {editingInterview ? "Modifier l'entretien" : "Nouvel entretien"}
              </h3>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleInterviewSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Candidat</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    onChange={(event) => setInterviewForm((current) => ({ ...current, candidate_id: event.target.value }))}
                    required
                    value={interviewForm.candidate_id}
                  >
                    {candidates.map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.first_name} {candidate.last_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Poste / Offre d&apos;emploi</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    onChange={(event) => setInterviewForm((current) => ({ ...current, job_offer_id: event.target.value }))}
                    required
                    value={interviewForm.job_offer_id}
                  >
                    {jobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Type</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    onChange={(event) => setInterviewForm((current) => ({ ...current, interview_type: event.target.value }))}
                    value={interviewForm.interview_type}
                  >
                    {INTERVIEW_TYPE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Statut</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    onChange={(event) => setInterviewForm((current) => ({ ...current, status: event.target.value }))}
                    value={interviewForm.status}
                  >
                    {PIPELINE_STAGE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block sm:col-span-2">
                  <span className="text-sm font-medium text-slate-700">Date et heure</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    onChange={(event) => setInterviewForm((current) => ({ ...current, scheduled_start_at: event.target.value }))}
                    required
                    type="datetime-local"
                    value={interviewForm.scheduled_start_at}
                  />
                </label>
              </div>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Notes / Commentaires</span>
                <textarea
                  className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  onChange={(event) => setInterviewForm((current) => ({ ...current, notes: event.target.value }))}
                  value={interviewForm.notes}
                />
              </label>
              {formError ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{formError}</p> : null}
              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" onClick={() => setIsInterviewModalOpen(false)} type="button">
                  Annuler
                </button>
                <button className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={isSubmitting} type="submit">
                  {isSubmitting ? "Enregistrement..." : "Enregistrer"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}

      {isEvaluationModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-3xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">
                {editingEvaluation ? "Modifier l'évaluation" : "Nouvelle évaluation"}
              </h3>
              <p className="mt-1 text-sm text-slate-600">L&apos;évaluation est liée à un entretien et met à jour le pipeline.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleEvaluationSubmit}>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Entretien lié</span>
                <select
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  onChange={(event) => setEvaluationForm((current) => ({ ...current, interview_id: event.target.value }))}
                  required
                  value={evaluationForm.interview_id}
                >
                  <option value="">Sélectionner un entretien</option>
                  {interviews.map((interview) => {
                    const candidate = candidates.find((item) => item.id === interview.candidate_id);
                    const job = jobs.find((item) => item.id === interview.job_offer_id);
                    return (
                      <option key={interview.id} value={interview.id}>
                        {candidateName(candidate)} — {job?.title ?? "Poste"} — {formatDateTime(interview.scheduled_start_at)}
                      </option>
                    );
                  })}
                </select>
              </label>

              <StarRatingInput
                label="Note globale"
                value={evaluationForm.rating}
                onChange={(value) => setEvaluationForm((current) => ({ ...current, rating: value }))}
              />

              <div className="grid gap-4 sm:grid-cols-3">
                <StarRatingInput
                  label="Compétences techniques"
                  value={evaluationForm.technical_score}
                  onChange={(value) => setEvaluationForm((current) => ({ ...current, technical_score: value }))}
                />
                <StarRatingInput
                  label="Soft skills"
                  value={evaluationForm.soft_skills_score}
                  onChange={(value) => setEvaluationForm((current) => ({ ...current, soft_skills_score: value }))}
                />
                <StarRatingInput
                  label="Motivation"
                  value={evaluationForm.motivation_score}
                  onChange={(value) => setEvaluationForm((current) => ({ ...current, motivation_score: value }))}
                />
              </div>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">Décision finale</span>
                <select
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  onChange={(event) => setEvaluationForm((current) => ({ ...current, recommendation: event.target.value }))}
                  value={evaluationForm.recommendation}
                >
                  {EVALUATION_DECISION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">Commentaire libre</span>
                <textarea
                  className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  onChange={(event) => setEvaluationForm((current) => ({ ...current, comments: event.target.value }))}
                  value={evaluationForm.comments}
                />
              </label>

              {formError ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{formError}</p> : null}

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" onClick={() => setIsEvaluationModalOpen(false)} type="button">
                  Annuler
                </button>
                <button className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={isSubmitting} type="submit">
                  {isSubmitting ? "Enregistrement..." : "Enregistrer l'évaluation"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
