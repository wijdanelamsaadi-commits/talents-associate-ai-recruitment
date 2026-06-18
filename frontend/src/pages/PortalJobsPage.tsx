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
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Open opportunities</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Browse job offers</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Find a role, read the details, and submit your application with a CV. No candidate login is required.
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
                    {job.company_name ?? "Talents Associate"} - {job.location ?? "Flexible"}
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
              <div className="mt-5 flex flex-wrap gap-2">
                <Link
                  className="inline-flex rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-[#1D6EEA] hover:text-[#1D6EEA]"
                  to={`/portal/jobs/${job.id}`}
                >
                  View details
                </Link>
                <Link
                  className="inline-flex rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
                  to={`/portal/apply/${job.id}`}
                >
                  Apply
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
