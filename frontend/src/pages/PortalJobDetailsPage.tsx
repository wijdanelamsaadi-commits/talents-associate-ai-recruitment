import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { PortalApplicationResponse, getPublicJob, submitPortalApplication } from "../services/portal";

const supportedExtensions = [".pdf", ".docx"];

function splitLabel(value: string | null) {
  return value || "Not specified";
}

export function PortalJobDetailsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<PortalApplicationResponse | null>(null);
  const [formState, setFormState] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    location: "",
  });
  const [file, setFile] = useState<File | null>(null);

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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!jobId || !file) {
      setError("Please select a CV file before submitting.");
      return;
    }

    const lowerName = file.name.toLowerCase();
    if (!supportedExtensions.some((extension) => lowerName.endsWith(extension))) {
      setError("Please upload a PDF or DOCX CV.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await submitPortalApplication(jobId, { ...formState, file });
      setSuccess(response);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Application submission failed."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
          <Link to="/portal" className="text-sm font-semibold text-[#1D6EEA]">
            Back to jobs
          </Link>
          <Link to="/login" className="text-sm font-semibold text-slate-600">
            Recruiter login
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.1fr_0.9fr]">
        {isLoading ? (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading job...</div>
        ) : !job ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error ?? "Job not found."}</div>
        ) : (
          <>
            <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Job details</p>
              <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">{job.title}</h1>
              <p className="mt-2 text-sm text-slate-600">
                {splitLabel(job.company_name)} · {splitLabel(job.location)} · {splitLabel(job.contract_type)}
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase text-slate-500">Experience</p>
                  <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">
                    {job.required_experience_years ?? 0}+ years
                  </p>
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
              <h2 className="text-xl font-semibold text-[#0B1F3A]">Apply now</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Your CV will be extracted, parsed, and matched automatically against this job.
              </p>

              <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
                {(["first_name", "last_name", "email", "phone", "location"] as const).map((field) => (
                  <label className="block" key={field}>
                    <span className="text-sm font-medium capitalize text-slate-700">{field.replace("_", " ")}</span>
                    <input
                      className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                      onChange={(event) => setFormState((current) => ({ ...current, [field]: event.target.value }))}
                      required={field === "first_name" || field === "last_name" || field === "email"}
                      type={field === "email" ? "email" : "text"}
                      value={formState[field]}
                    />
                  </label>
                ))}

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">CV file</span>
                  <input
                    accept=".pdf,.docx"
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#1D6EEA]/10 file:px-3 file:py-1 file:text-sm file:font-semibold file:text-[#1D6EEA]"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                    required
                    type="file"
                  />
                </label>

                {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
                {success ? (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    {success.message} Matching results: {success.matching_result_ids.length}. Confidence:{" "}
                    {success.confidence_score ?? "N/A"}.
                  </div>
                ) : null}

                <button
                  className="w-full rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Submitting..." : "Submit application"}
                </button>
              </form>
            </aside>
          </>
        )}
      </section>
    </main>
  );
}
