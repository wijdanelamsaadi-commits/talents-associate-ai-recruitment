import { FormEvent, useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { JobOffer, JobOfferPayload, createJobOffer, deleteJobOffer, getJobOffers, updateJobOffer } from "../services/jobs";

type JobFormState = {
  title: string;
  company_name: string;
  location: string;
  contract_type: string;
  required_skills: string;
  preferred_skills: string;
  required_experience_years: string;
  education_level: string;
  description: string;
  status: string;
};

const initialFormState: JobFormState = {
  title: "",
  company_name: "",
  location: "",
  contract_type: "",
  required_skills: "",
  preferred_skills: "",
  required_experience_years: "",
  education_level: "",
  description: "",
  status: "open",
};

const statusOptions = ["draft", "open", "paused", "closed", "archived"];

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function splitSkills(value: string) {
  return value
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);
}

function joinSkills(value: string[]) {
  return value.join(", ");
}

function toFormState(job: JobOffer): JobFormState {
  return {
    title: job.title,
    company_name: job.company_name ?? "",
    location: job.location ?? "",
    contract_type: job.contract_type ?? "",
    required_skills: joinSkills(job.required_skills),
    preferred_skills: joinSkills(job.preferred_skills),
    required_experience_years: job.required_experience_years?.toString() ?? "",
    education_level: job.education_level ?? "",
    description: job.description,
    status: job.status,
  };
}

function toPayload(formState: JobFormState): JobOfferPayload {
  return {
    title: formState.title.trim(),
    company_name: formState.company_name.trim() || null,
    location: formState.location.trim() || null,
    contract_type: formState.contract_type.trim() || null,
    required_skills: splitSkills(formState.required_skills),
    preferred_skills: splitSkills(formState.preferred_skills),
    required_experience_years: formState.required_experience_years ? Number(formState.required_experience_years) : null,
    education_level: formState.education_level.trim() || null,
    description: formState.description.trim(),
    status: formState.status,
  };
}

export function JobOffersPage() {
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingJob, setEditingJob] = useState<JobOffer | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formState, setFormState] = useState<JobFormState>(initialFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getJobOffers();
      setJobs(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load job offers. Check that the backend is running on localhost:8001."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  const openCreateModal = () => {
    setEditingJob(null);
    setFormState(initialFormState);
    setError(null);
    setMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (job: JobOffer) => {
    setEditingJob(job);
    setFormState(toFormState(job));
    setError(null);
    setMessage(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const payload = toPayload(formState);
      if (editingJob) {
        await updateJobOffer(editingJob.id, payload);
        setMessage("Job offer updated successfully.");
      } else {
        await createJobOffer(payload);
        setMessage("Job offer created successfully.");
      }
      setIsModalOpen(false);
      setEditingJob(null);
      setFormState(initialFormState);
      await loadJobs();
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Job offer could not be saved. Verify required fields."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (job: JobOffer) => {
    const shouldDelete = window.confirm(`Delete job offer "${job.title}"?`);
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteJobOffer(job.id);
      setMessage("Job offer deleted.");
      await loadJobs();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Job offer could not be deleted."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Job offers</h2>
          <p className="mt-1 text-sm text-slate-600">Manage roles used by the matching engine.</p>
        </div>
        <button
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
          onClick={openCreateModal}
          type="button"
        >
          New job offer
        </button>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading job offers...
        </section>
      ) : null}

      {!isLoading && jobs.length === 0 ? (
        <EmptyState
          title="No job offers yet"
          description="Create the first job offer to start matching parsed candidate CVs."
          actionLabel="Create job offer"
          onAction={openCreateModal}
        />
      ) : null}

      {!isLoading && jobs.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Active job offers</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Title</th>
                  <th className="px-5 py-3 font-semibold">Company</th>
                  <th className="px-5 py-3 font-semibold">Location</th>
                  <th className="px-5 py-3 font-semibold">Required skills</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{job.title}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.company_name ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.location ?? "-"}</td>
                    <td className="max-w-sm px-5 py-4 text-slate-700">{job.required_skills.join(", ") || "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold capitalize text-[#1D6EEA]">
                        {formatLabel(job.status)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <div className="flex gap-2">
                        <button
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          onClick={() => openEditModal(job)}
                          type="button"
                        >
                          Edit
                        </button>
                        <button
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                          onClick={() => void handleDelete(job)}
                          type="button"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
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
                {editingJob ? "Edit job offer" : "Create job offer"}
              </h3>
              <p className="mt-1 text-sm text-slate-600">Skills can be entered as comma-separated values.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Title</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
                    required
                    value={formState.title}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Company</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, company_name: event.target.value }))}
                    value={formState.company_name}
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
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Contract type</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, contract_type: event.target.value }))}
                    placeholder="Full-time, internship, freelance"
                    value={formState.contract_type}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Required skills</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, required_skills: event.target.value }))}
                    placeholder="React, TypeScript, FastAPI"
                    value={formState.required_skills}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Preferred skills</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, preferred_skills: event.target.value }))}
                    placeholder="PostgreSQL, Tailwind"
                    value={formState.preferred_skills}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Experience years</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    min="0"
                    onChange={(event) =>
                      setFormState((current) => ({ ...current, required_experience_years: event.target.value }))
                    }
                    type="number"
                    value={formState.required_experience_years}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Education level</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, education_level: event.target.value }))}
                    value={formState.education_level}
                  />
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
              </div>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Description</span>
                <textarea
                  className="mt-2 min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                  onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))}
                  required
                  value={formState.description}
                />
              </label>

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
                  {isSubmitting ? "Saving..." : "Save job offer"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
