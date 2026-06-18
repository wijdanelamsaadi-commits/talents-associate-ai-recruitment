import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { getPublicJob } from "../services/portal";

function splitLabel(value: string | null) {
  return value || "Not specified";
}

export function PortalJobDetailsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadJob() {
      if (!jobId) {
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPublicJob(jobId);
        if (isMounted) {
          setJob(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Unable to load job details."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadJob();
    return () => {
      isMounted = false;
    };
  }, [jobId]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {isLoading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading job...</div>
      ) : !job ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error ?? "Job not found."}</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Job details</p>
            <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">{job.title}</h1>
            <p className="mt-2 text-sm text-slate-600">
              {splitLabel(job.company_name)} - {splitLabel(job.location)} - {splitLabel(job.contract_type)}
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Experience</p>
                <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{job.required_experience_years ?? 0}+ years</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Diploma</p>
                <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{splitLabel(job.education_level)}</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Status</p>
                <p className="mt-2 text-sm font-semibold capitalize text-[#0B1F3A]">{job.status}</p>
              </div>
            </div>
            <div className="mt-6 space-y-5 text-sm leading-6 text-slate-700">
              <p>{job.description}</p>
              <p>
                <span className="font-semibold text-[#0B1F3A]">Required skills:</span>{" "}
                {job.required_skills.length > 0 ? job.required_skills.join(", ") : "Open profile"}
              </p>
              <p>
                <span className="font-semibold text-[#0B1F3A]">Preferred skills:</span>{" "}
                {job.preferred_skills.length > 0 ? job.preferred_skills.join(", ") : "Not specified"}
              </p>
            </div>
          </article>
          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[#0B1F3A]">Ready to apply?</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Submit your personal information and CV. Extraction, parsing, matching, and timeline updates run automatically.
            </p>
            <Link
              className="mt-5 inline-flex w-full justify-center rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0]"
              to={`/portal/apply/${job.id}`}
            >
              Apply for this job
            </Link>
            <Link
              className="mt-3 inline-flex w-full justify-center rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-[#1D6EEA] hover:text-[#1D6EEA]"
              to="/portal/jobs"
            >
              Back to job list
            </Link>
          </aside>
        </div>
      )}
    </main>
  );
}
