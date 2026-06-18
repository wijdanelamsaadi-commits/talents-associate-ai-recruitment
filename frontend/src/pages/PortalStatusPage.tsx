import { FormEvent, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { PortalApplicationStatusResponse, getPortalApplicationStatus } from "../services/portal";

function formatLabel(value: string | null) {
  return value ? value.replaceAll("_", " ") : "Application submitted";
}

export function PortalStatusPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<PortalApplicationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setStatus(null);
    try {
      const data = await getPortalApplicationStatus(email);
      setStatus(data);
    } catch (statusError) {
      setError(getApiErrorMessage(statusError, "Unable to load application status."));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Application tracking</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Check your application status</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Enter the email address used in your application form to see your submitted jobs and current stage.
        </p>

        <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
          <input
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="candidate@example.com"
            required
            type="email"
            value={email}
          />
          <button
            className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Checking..." : "Check status"}
          </button>
        </form>

        {error ? <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      </section>

      {status ? (
        <section className="mt-6">
          {status.applications.length === 0 ? (
            <EmptyState
              title="No applications found"
              description="No application is linked to this email address yet. Check the spelling or apply to an open job."
            />
          ) : (
            <div className="space-y-4">
              {status.applications.map((application) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" key={application.application_id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-semibold text-[#0B1F3A]">{application.job_title}</h2>
                      <p className="mt-1 text-sm text-slate-600">{application.company_name ?? "Talents Associate"}</p>
                    </div>
                    <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold capitalize text-[#1D6EEA]">
                      {formatLabel(application.application_status)}
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase text-slate-500">Stage</p>
                      <p className="mt-1 text-sm font-semibold capitalize text-[#0B1F3A]">{formatLabel(application.current_stage)}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase text-slate-500">Match</p>
                      <p className="mt-1 text-sm font-semibold text-[#0B1F3A]">
                        {application.best_matching_score === null ? "Pending" : `${application.best_matching_score}%`}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase text-slate-500">Applied</p>
                      <p className="mt-1 text-sm font-semibold text-[#0B1F3A]">
                        {new Date(application.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  {application.recommendation ? (
                    <p className="mt-3 text-sm capitalize text-slate-600">Recommendation: {formatLabel(application.recommendation)}</p>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </main>
  );
}
