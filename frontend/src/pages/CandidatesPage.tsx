import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { Candidate, createCandidate, getCandidates } from "../services/candidates";

type CandidateFormState = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  city: string;
  source: string;
};

const initialFormState: CandidateFormState = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  city: "",
  source: "manual",
};

const sourceOptions = ["manual", "cv_upload", "linkedin_csv", "candidate_portal", "referral", "other"];

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

export function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formState, setFormState] = useState<CandidateFormState>(initialFormState);
  const [formError, setFormError] = useState<string | null>(null);

  const loadCandidates = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCandidates();
      setCandidates(data);
    } catch {
      setError("Unable to load candidates. Check that the FastAPI backend is running on localhost:8000.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadCandidates();
  }, []);

  const stats = useMemo(() => {
    const activeCount = candidates.filter((candidate) => candidate.status === "active").length;
    const interviewingCount = candidates.filter((candidate) => candidate.status === "interviewing").length;
    return {
      total: candidates.length,
      active: activeCount,
      interviewing: interviewingCount,
    };
  }, [candidates]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      await createCandidate({
        first_name: formState.first_name.trim(),
        last_name: formState.last_name.trim(),
        email: formState.email.trim() || null,
        phone: formState.phone.trim() || null,
        location: formState.city.trim() || null,
        source: formState.source,
      });
      setFormState(initialFormState);
      setIsModalOpen(false);
      await loadCandidates();
    } catch {
      setFormError("Candidate could not be created. Verify required fields and duplicate email.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total candidates" value={String(stats.total)} detail="Profiles loaded from the backend" />
        <StatCard label="Active candidates" value={String(stats.active)} detail="Profiles currently marked active" />
        <StatCard label="Interviewing" value={String(stats.interviewing)} detail="Candidates in interview stage" />
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Candidate database</h2>
          <p className="mt-1 text-sm text-slate-600">Live candidate records from the FastAPI backend.</p>
        </div>
        <button
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
          onClick={() => setIsModalOpen(true)}
          type="button"
        >
          Create candidate
        </button>
      </div>

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading candidates...
        </section>
      ) : null}

      {error ? (
        <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</section>
      ) : null}

      {!isLoading && !error && candidates.length === 0 ? (
        <EmptyState
          title="No candidates yet"
          description="Create the first candidate profile to start building the recruitment database."
          actionLabel="Create candidate"
          onAction={() => setIsModalOpen(true)}
        />
      ) : null}

      {!isLoading && !error && candidates.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Candidates list</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Name</th>
                  <th className="px-5 py-3 font-semibold">Email</th>
                  <th className="px-5 py-3 font-semibold">Phone</th>
                  <th className="px-5 py-3 font-semibold">City</th>
                  <th className="px-5 py-3 font-semibold">Source</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {candidates.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-5 py-4">
                      <Link className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to={`/candidates/${candidate.id}`}>
                        {candidate.first_name} {candidate.last_name}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.email ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.phone ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidate.location ?? "-"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatStatus(candidate.source)}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold capitalize text-[#1D6EEA]">
                        {formatStatus(candidate.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <EmptyState
        title="LinkedIn CSV import placeholder"
        description="Bulk import and enrichment screens will be added after the backend modules are ready."
      />

      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">Create candidate</h3>
              <p className="mt-1 text-sm text-slate-600">Add a manual profile to the backend candidate database.</p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">First name</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, first_name: event.target.value }))}
                    required
                    value={formState.first_name}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Last name</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, last_name: event.target.value }))}
                    required
                    value={formState.last_name}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Email</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, email: event.target.value }))}
                    type="email"
                    value={formState.email}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Phone</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, phone: event.target.value }))}
                    value={formState.phone}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">City</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, city: event.target.value }))}
                    value={formState.city}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Source</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, source: event.target.value }))}
                    value={formState.source}
                  >
                    {sourceOptions.map((source) => (
                      <option key={source} value={source}>
                        {formatStatus(source)}
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
                  Cancel
                </button>
                <button
                  className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Creating..." : "Create candidate"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
