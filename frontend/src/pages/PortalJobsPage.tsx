import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { getPublicJobs } from "../services/portal";

function skillList(skills: string[]) {
  return skills.length > 0 ? skills.join(", ") : "Open profile";
}

export function PortalJobsPage() {
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadJobs() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPublicJobs();
        if (isMounted) {
          setJobs(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Unable to load public jobs."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadJobs();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
          <Link to="/portal" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0B1F3A] text-sm font-bold text-white">TA</span>
            <span>
              <span className="block text-sm font-semibold text-[#0B1F3A]">Talents Associate</span>
              <span className="block text-xs text-slate-500">Candidate portal</span>
            </span>
          </Link>
          <Link className="text-sm font-semibold text-[#1D6EEA]" to="/login">
            Recruiter login
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Open opportunities</p>
          <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Apply with your CV</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Submit your profile once, upload your CV, and the platform will extract, parse, and match it automatically.
          </p>
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading jobs...</div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error}</div>
        ) : jobs.length === 0 ? (
          <EmptyState title="No open jobs" description="There are no public job offers open right now." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {jobs.map((job) => (
              <article key={job.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-[#0B1F3A]">{job.title}</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      {job.company_name ?? "Talents Associate"} · {job.location ?? "Flexible"}
                    </p>
                  </div>
                  <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold text-[#1D6EEA]">
                    {job.contract_type || "Open"}
                  </span>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-600">{job.description}</p>
                <p className="mt-4 text-sm text-slate-700">
                  <span className="font-semibold">Skills:</span> {skillList(job.required_skills)}
                </p>
                <Link
                  className="mt-5 inline-flex rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
                  to={`/portal/jobs/${job.id}`}
                >
                  View and apply
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
