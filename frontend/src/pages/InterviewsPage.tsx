import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidates } from "../services/candidates";
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
  scheduled_end_at: string;
  meeting_url: string;
  location: string;
  notes: string;
};

const initialFormState: InterviewFormState = {
  candidate_id: "",
  job_offer_id: "",
  interview_type: "screening",
  status: "scheduled",
  scheduled_start_at: "",
  scheduled_end_at: "",
  meeting_url: "",
  location: "",
  notes: "",
};

const interviewTypes = ["screening", "technical", "hr", "manager", "final"];
const statusOptions = ["scheduled", "completed", "cancelled", "rescheduled", "no_show"];

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function candidateName(candidate?: Candidate) {
  return candidate ? `${candidate.first_name} ${candidate.last_name}` : "Unknown candidate";
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
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

function toFormState(interview: Interview): InterviewFormState {
  return {
    candidate_id: interview.candidate_id,
    job_offer_id: interview.job_offer_id,
    interview_type: interview.interview_type,
    status: interview.status,
    scheduled_start_at: toDatetimeLocal(interview.scheduled_start_at),
    scheduled_end_at: toDatetimeLocal(interview.scheduled_end_at),
    meeting_url: interview.meeting_url ?? "",
    location: interview.location ?? "",
    notes: interview.notes ?? "",
  };
}

function toPayload(formState: InterviewFormState): InterviewPayload {
  return {
    candidate_id: formState.candidate_id,
    job_offer_id: formState.job_offer_id,
    interview_type: formState.interview_type,
    status: formState.status,
    scheduled_start_at: toApiDatetime(formState.scheduled_start_at),
    scheduled_end_at: formState.scheduled_end_at ? toApiDatetime(formState.scheduled_end_at) : null,
    meeting_url: formState.meeting_url.trim() || null,
    location: formState.location.trim() || null,
    notes: formState.notes.trim() || null,
  };
}

export function InterviewsPage() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingInterview, setEditingInterview] = useState<Interview | null>(null);
  const [formState, setFormState] = useState<InterviewFormState>(initialFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [interviewData, candidateData, jobData] = await Promise.all([getInterviews(), getCandidates(), getJobOffers()]);
      setInterviews(interviewData);
      setCandidates(candidateData);
      setJobs(jobData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load interviews. Check that the backend is running on localhost:8001."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const stats = useMemo(() => {
    const today = new Date().toDateString();
    const todayCount = interviews.filter((interview) => new Date(interview.scheduled_start_at).toDateString() === today).length;
    const upcomingCount = interviews.filter(
      (interview) => new Date(interview.scheduled_start_at) > new Date() && interview.status === "scheduled",
    ).length;
    const completedCount = interviews.filter((interview) => interview.status === "completed").length;
    const cancelledCount = interviews.filter((interview) => ["cancelled", "no_show"].includes(interview.status)).length;
    return { todayCount, upcomingCount, completedCount, cancelledCount };
  }, [interviews]);

  const openCreateModal = () => {
    setEditingInterview(null);
    setFormError(null);
    setMessage(null);
    setFormState({
      ...initialFormState,
      candidate_id: candidates[0]?.id ?? "",
      job_offer_id: jobs[0]?.id ?? "",
    });
    setIsModalOpen(true);
  };

  const openEditModal = (interview: Interview) => {
    setEditingInterview(interview);
    setFormError(null);
    setMessage(null);
    setFormState(toFormState(interview));
    setIsModalOpen(true);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    if (!formState.candidate_id || !formState.job_offer_id) {
      setFormError("Select both a candidate and a job offer.");
      setIsSubmitting(false);
      return;
    }

    try {
      const payload = toPayload(formState);
      if (editingInterview) {
        await updateInterview(editingInterview.id, payload);
        setMessage("Interview updated successfully.");
      } else {
        await createInterview(payload);
        setMessage("Interview scheduled successfully.");
      }
      setIsModalOpen(false);
      setEditingInterview(null);
      setFormState(initialFormState);
      await loadData();
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError, "Interview could not be saved."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (interview: Interview, status: string) => {
    setError(null);
    setMessage(null);
    try {
      await updateInterviewStatus(interview.id, status);
      setMessage("Interview status updated.");
      await loadData();
    } catch (statusError) {
      setError(getApiErrorMessage(statusError, "Interview status could not be updated."));
    }
  };

  const handleDelete = async (interview: Interview) => {
    const shouldDelete = window.confirm("Delete this interview?");
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteInterview(interview.id);
      setMessage("Interview deleted.");
      await loadData();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Interview could not be deleted."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Today" value={String(stats.todayCount)} detail="Interviews scheduled today" />
        <StatCard label="Upcoming" value={String(stats.upcomingCount)} detail="Scheduled future interviews" />
        <StatCard label="Completed" value={String(stats.completedCount)} detail="Finished interview sessions" />
        <StatCard label="Cancelled" value={String(stats.cancelledCount)} detail="Cancelled or no-show sessions" />
      </section>

      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Interview management</h2>
          <p className="mt-1 text-sm text-slate-600">Schedule, update, and track candidate interviews.</p>
        </div>
        <button
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={candidates.length === 0 || jobs.length === 0}
          onClick={openCreateModal}
          type="button"
        >
          Create interview
        </button>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading interviews...
        </section>
      ) : null}

      {!isLoading && (candidates.length === 0 || jobs.length === 0) ? (
        <EmptyState
          title="Candidates and jobs are required"
          description="Create at least one candidate and one job offer before scheduling interviews."
        />
      ) : null}

      {!isLoading && interviews.length === 0 && candidates.length > 0 && jobs.length > 0 ? (
        <EmptyState
          title="No interviews scheduled"
          description="Schedule the first interview for a candidate and job offer."
          actionLabel="Create interview"
          onAction={openCreateModal}
        />
      ) : null}

      {interviews.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Interview calendar</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Candidate</th>
                  <th className="px-5 py-3 font-semibold">Job</th>
                  <th className="px-5 py-3 font-semibold">Type</th>
                  <th className="px-5 py-3 font-semibold">Schedule</th>
                  <th className="px-5 py-3 font-semibold">Location</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {interviews.map((interview) => {
                  const candidate = candidates.find((item) => item.id === interview.candidate_id);
                  const job = jobs.find((item) => item.id === interview.job_offer_id);
                  return (
                    <tr key={interview.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4">
                        <Link className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to={`/candidates/${interview.candidate_id}`}>
                          {candidateName(candidate)}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job?.title ?? interview.job_offer_id}</td>
                      <td className="whitespace-nowrap px-5 py-4 capitalize text-slate-700">{formatLabel(interview.interview_type)}</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatDateTime(interview.scheduled_start_at)}</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{interview.location || interview.meeting_url || "-"}</td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <select
                          className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-semibold capitalize text-slate-700"
                          onChange={(event) => void handleStatusChange(interview, event.target.value)}
                          value={interview.status}
                        >
                          {statusOptions.map((status) => (
                            <option key={status} value={status}>
                              {formatLabel(status)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <div className="flex gap-2">
                          <Link
                            className="rounded-lg bg-[#1D6EEA] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#165AC0]"
                            to={`/evaluations?interviewId=${interview.id}`}
                          >
                            Evaluate
                          </Link>
                          <button
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                            onClick={() => openEditModal(interview)}
                            type="button"
                          >
                            Edit
                          </button>
                          <button
                            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                            onClick={() => void handleDelete(interview)}
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
          <section className="w-full max-w-3xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">
                {editingInterview ? "Edit interview" : "Create interview"}
              </h3>
              <p className="mt-1 text-sm text-slate-600">Scheduling creates or reuses the candidate application for the selected job.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Candidate</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, candidate_id: event.target.value }))}
                    required
                    value={formState.candidate_id}
                  >
                    {candidates.map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.first_name} {candidate.last_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Job offer</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, job_offer_id: event.target.value }))}
                    required
                    value={formState.job_offer_id}
                  >
                    {jobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Interview type</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, interview_type: event.target.value }))}
                    value={formState.interview_type}
                  >
                    {interviewTypes.map((type) => (
                      <option key={type} value={type}>
                        {formatLabel(type)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Status</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm capitalize outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, status: event.target.value }))}
                    value={formState.status}
                  >
                    {statusOptions.map((status) => (
                      <option key={status} value={status}>
                        {formatLabel(status)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Start</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, scheduled_start_at: event.target.value }))}
                    required
                    type="datetime-local"
                    value={formState.scheduled_start_at}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">End</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, scheduled_end_at: event.target.value }))}
                    type="datetime-local"
                    value={formState.scheduled_end_at}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Meeting URL</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, meeting_url: event.target.value }))}
                    value={formState.meeting_url}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Location</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, location: event.target.value }))}
                    value={formState.location}
                  />
                </label>
              </div>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Notes</span>
                <textarea
                  className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                  onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
                  value={formState.notes}
                />
              </label>

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
                  {isSubmitting ? "Saving..." : "Save interview"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
