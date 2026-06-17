import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
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
import { Interview, getInterviews } from "../services/interviews";
import { JobOffer, getJobOffers } from "../services/jobs";

type EvaluationFormState = {
  interview_id: string;
  evaluator_name: string;
  technical_score: string;
  soft_skills_score: string;
  motivation_score: string;
  communication_score: string;
  culture_fit_score: string;
  recommendation: string;
  strengths: string;
  weaknesses: string;
  comments: string;
};

const initialFormState: EvaluationFormState = {
  interview_id: "",
  evaluator_name: "",
  technical_score: "70",
  soft_skills_score: "70",
  motivation_score: "70",
  communication_score: "70",
  culture_fit_score: "70",
  recommendation: "hold",
  strengths: "",
  weaknesses: "",
  comments: "",
};

const recommendationOptions = ["strong_yes", "yes", "hold", "no", "strong_no"];
const scoreFields: Array<keyof Pick<
  EvaluationFormState,
  "technical_score" | "soft_skills_score" | "motivation_score" | "communication_score" | "culture_fit_score"
>> = ["technical_score", "soft_skills_score", "motivation_score", "communication_score", "culture_fit_score"];

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function candidateName(candidate?: Candidate) {
  return candidate ? `${candidate.first_name} ${candidate.last_name}` : "Unknown candidate";
}

function scoreTone(score: number) {
  if (score >= 80) return "text-emerald-700 bg-emerald-50";
  if (score >= 60) return "text-[#1D6EEA] bg-[#1D6EEA]/10";
  return "text-red-700 bg-red-50";
}

function toFormState(evaluation: Evaluation): EvaluationFormState {
  return {
    interview_id: evaluation.interview_id,
    evaluator_name: evaluation.evaluator_name,
    technical_score: String(evaluation.technical_score),
    soft_skills_score: String(evaluation.soft_skills_score),
    motivation_score: String(evaluation.motivation_score),
    communication_score: String(evaluation.communication_score),
    culture_fit_score: String(evaluation.culture_fit_score),
    recommendation: evaluation.recommendation,
    strengths: evaluation.strengths ?? "",
    weaknesses: evaluation.weaknesses ?? "",
    comments: evaluation.comments ?? "",
  };
}

function toPayload(formState: EvaluationFormState, interviews: Interview[]): EvaluationPayload {
  const interview = interviews.find((item) => item.id === formState.interview_id);
  return {
    interview_id: formState.interview_id,
    candidate_id: interview?.candidate_id ?? null,
    evaluator_name: formState.evaluator_name.trim(),
    technical_score: Number(formState.technical_score),
    soft_skills_score: Number(formState.soft_skills_score),
    motivation_score: Number(formState.motivation_score),
    communication_score: Number(formState.communication_score),
    culture_fit_score: Number(formState.culture_fit_score),
    recommendation: formState.recommendation,
    strengths: formState.strengths.trim() || null,
    weaknesses: formState.weaknesses.trim() || null,
    comments: formState.comments.trim() || null,
  };
}

export function EvaluationsPage() {
  const [searchParams] = useSearchParams();
  const requestedInterviewId = searchParams.get("interviewId") ?? "";
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingEvaluation, setEditingEvaluation] = useState<Evaluation | null>(null);
  const [formState, setFormState] = useState<EvaluationFormState>(initialFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [evaluationData, interviewData, candidateData, jobData] = await Promise.all([
        getEvaluations(),
        getInterviews(),
        getCandidates(),
        getJobOffers(),
      ]);
      setEvaluations(evaluationData);
      setInterviews(interviewData);
      setCandidates(candidateData);
      setJobs(jobData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load evaluations. Check that the backend is running on localhost:8001."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (requestedInterviewId && interviews.some((interview) => interview.id === requestedInterviewId)) {
      setFormState((current) => ({ ...current, interview_id: requestedInterviewId }));
      setEditingEvaluation(null);
      setIsModalOpen(true);
    }
  }, [requestedInterviewId, interviews]);

  const stats = useMemo(() => {
    const average =
      evaluations.length === 0
        ? 0
        : Math.round(evaluations.reduce((total, evaluation) => total + evaluation.global_score, 0) / evaluations.length);
    const strong = evaluations.filter((evaluation) => evaluation.recommendation === "strong_yes").length;
    const positive = evaluations.filter((evaluation) => ["strong_yes", "yes"].includes(evaluation.recommendation)).length;
    return { average, strong, positive };
  }, [evaluations]);

  const openCreateModal = () => {
    setEditingEvaluation(null);
    setFormError(null);
    setMessage(null);
    setFormState({
      ...initialFormState,
      interview_id: requestedInterviewId || interviews[0]?.id || "",
    });
    setIsModalOpen(true);
  };

  const openEditModal = (evaluation: Evaluation) => {
    setEditingEvaluation(evaluation);
    setFormError(null);
    setMessage(null);
    setFormState(toFormState(evaluation));
    setIsModalOpen(true);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    if (!formState.interview_id) {
      setFormError("Select an interview before saving an evaluation.");
      setIsSubmitting(false);
      return;
    }

    try {
      const payload = toPayload(formState, interviews);
      if (editingEvaluation) {
        await updateEvaluation(editingEvaluation.id, payload);
        setMessage("Evaluation updated successfully.");
      } else {
        await createEvaluation(payload);
        setMessage("Evaluation created successfully.");
      }
      setIsModalOpen(false);
      setEditingEvaluation(null);
      setFormState(initialFormState);
      await loadData();
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError, "Evaluation could not be saved."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (evaluation: Evaluation) => {
    const shouldDelete = window.confirm("Delete this evaluation?");
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteEvaluation(evaluation.id);
      setMessage("Evaluation deleted.");
      await loadData();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Evaluation could not be deleted."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Evaluations" value={String(evaluations.length)} detail="Interview evaluations saved" />
        <StatCard label="Average score" value={`${stats.average}%`} detail="Mean global score" />
        <StatCard label="Positive recommendations" value={String(stats.positive)} detail="Yes or strong yes outcomes" />
      </section>

      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Evaluation management</h2>
          <p className="mt-1 text-sm text-slate-600">Create scorecards for candidate interviews and track recommendations.</p>
        </div>
        <button
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={interviews.length === 0}
          onClick={openCreateModal}
          type="button"
        >
          Create evaluation
        </button>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading evaluations...
        </section>
      ) : null}

      {!isLoading && interviews.length === 0 ? (
        <EmptyState title="No interviews available" description="Create an interview before adding an evaluation." />
      ) : null}

      {!isLoading && interviews.length > 0 && evaluations.length === 0 ? (
        <EmptyState
          title="No evaluations yet"
          description="Create the first interview evaluation to record score criteria and recommendation."
          actionLabel="Create evaluation"
          onAction={openCreateModal}
        />
      ) : null}

      {evaluations.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Evaluation scorecards</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Candidate</th>
                  <th className="px-5 py-3 font-semibold">Interview</th>
                  <th className="px-5 py-3 font-semibold">Evaluator</th>
                  <th className="px-5 py-3 font-semibold">Global score</th>
                  <th className="px-5 py-3 font-semibold">Recommendation</th>
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
                        {job?.title ?? "Interview"} {interview ? `- ${formatLabel(interview.interview_type)}` : ""}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{evaluation.evaluator_name}</td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${scoreTone(evaluation.global_score)}`}>
                          {evaluation.global_score}%
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 capitalize text-slate-700">
                        {formatLabel(evaluation.recommendation)}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <div className="flex gap-2">
                          <button
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                            onClick={() => openEditModal(evaluation)}
                            type="button"
                          >
                            Edit
                          </button>
                          <button
                            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                            onClick={() => void handleDelete(evaluation)}
                            type="button"
                          >
                            Delete
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

      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-4xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">
                {editingEvaluation ? "Edit evaluation" : "Create evaluation"}
              </h3>
              <p className="mt-1 text-sm text-slate-600">Global score is calculated automatically from the five criteria.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Interview</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, interview_id: event.target.value }))}
                    required
                    value={formState.interview_id}
                  >
                    <option value="">Select interview</option>
                    {interviews.map((interview) => {
                      const candidate = candidates.find((item) => item.id === interview.candidate_id);
                      const job = jobs.find((item) => item.id === interview.job_offer_id);
                      return (
                        <option key={interview.id} value={interview.id}>
                          {candidateName(candidate)} - {job?.title ?? "Job"} - {new Date(interview.scheduled_start_at).toLocaleDateString()}
                        </option>
                      );
                    })}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Evaluator name</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, evaluator_name: event.target.value }))}
                    required
                    value={formState.evaluator_name}
                  />
                </label>
                {scoreFields.map((field) => (
                  <label className="block" key={field}>
                    <span className="text-sm font-medium capitalize text-slate-700">{formatLabel(field)}</span>
                    <input
                      className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                      max="100"
                      min="0"
                      onChange={(event) => setFormState((current) => ({ ...current, [field]: event.target.value }))}
                      required
                      type="number"
                      value={formState[field]}
                    />
                  </label>
                ))}
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Recommendation</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, recommendation: event.target.value }))}
                    value={formState.recommendation}
                  >
                    {recommendationOptions.map((recommendation) => (
                      <option key={recommendation} value={recommendation}>
                        {formatLabel(recommendation)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Strengths</span>
                  <textarea
                    className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, strengths: event.target.value }))}
                    value={formState.strengths}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Weaknesses</span>
                  <textarea
                    className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, weaknesses: event.target.value }))}
                    value={formState.weaknesses}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Comments</span>
                  <textarea
                    className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, comments: event.target.value }))}
                    value={formState.comments}
                  />
                </label>
              </div>

              {formError ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{formError}</p> : null}

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  onClick={() => setIsModalOpen(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button
                  className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Saving..." : "Save evaluation"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
