import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { PortalApplicationResponse, getPublicJob, submitPortalApplication } from "../services/portal";

const supportedExtensions = [".pdf", ".docx"];

export function PortalApplyPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [processingStep, setProcessingStep] = useState<"idle" | "uploading" | "processing" | "completed">("idle");
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
    setProcessingStep("uploading");
    setError(null);
    setSuccess(null);
    try {
      setProcessingStep("processing");
      const response = await submitPortalApplication(jobId, { ...formState, file });
      setSuccess(response);
      setProcessingStep("completed");
    } catch (submitError) {
      setProcessingStep("idle");
      setError(getApiErrorMessage(submitError, "Application submission failed."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.85fr_1.15fr]">
      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Application form</p>
        <h1 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{job?.title ?? "Apply for this job"}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Upload your CV and the platform will automatically extract text, parse your profile, match you with the job,
          and create your application timeline.
        </p>
        {isLoading ? <p className="mt-4 text-sm text-slate-500">Loading job...</p> : null}
        {job ? (
          <Link className="mt-5 inline-flex text-sm font-semibold text-[#1D6EEA]" to={`/portal/jobs/${job.id}`}>
            Review job details
          </Link>
        ) : null}
      </aside>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <form className="space-y-4" onSubmit={handleSubmit}>
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
            <span className="mt-1 block text-xs text-slate-500">PDF or DOCX, maximum 5MB.</span>
          </label>

          {processingStep !== "idle" ? (
            <div className="grid gap-2 sm:grid-cols-3">
              {[
                ["uploading", "Upload"],
                ["processing", "Parse and match"],
                ["completed", "Completed"],
              ].map(([key, label]) => (
                <div
                  className={[
                    "rounded-lg border px-3 py-2 text-xs font-semibold",
                    processingStep === key || processingStep === "completed"
                      ? "border-[#1D6EEA] bg-[#1D6EEA]/10 text-[#1D6EEA]"
                      : "border-slate-200 text-slate-500",
                  ].join(" ")}
                  key={key}
                >
                  {label}
                </div>
              ))}
            </div>
          ) : null}

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
          {success ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {success.message} Matching results: {success.matching_result_ids.length}. Confidence:{" "}
              {success.confidence_score ?? "N/A"}.
            </div>
          ) : null}

          <button
            className="w-full rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting || isLoading || !job}
            type="submit"
          >
            {isSubmitting ? "Processing application..." : "Submit application"}
          </button>
        </form>
      </section>
    </main>
  );
}
