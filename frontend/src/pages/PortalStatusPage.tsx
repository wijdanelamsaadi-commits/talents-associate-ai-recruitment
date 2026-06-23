import { FormEvent, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { PortalApplicationStatusResponse, getPortalApplicationStatus } from "../services/portal";

function formatLabel(value: string | null) {
  return value ? value.replaceAll("_", " ") : "Candidature envoyée";
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
      setError(getApiErrorMessage(statusError, "Impossible de charger le suivi de candidature."));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Suivi de candidature</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Consulter le suivi de candidature</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Saisissez l'email utilisé dans votre candidature pour consulter vos offres et l'étape actuelle.
        </p>

        <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
          <input
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="candidat@example.com"
            required
            type="email"
            value={email}
          />
          <button
            className="rounded-lg bg-[#E8590C] px-4 py-2 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Vérification..." : "Consulter le suivi"}
          </button>
        </form>

        {error ? <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      </section>

      {status ? (
        <section className="mt-6">
          {status.applications.length === 0 ? (
            <EmptyState
              title="Aucune candidature trouvée"
              description="Aucune candidature n'est liée à cet email. Vérifiez l'adresse ou postulez à une offre ouverte."
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
                    <span className="rounded-full bg-[#E8590C]/10 px-3 py-1 text-xs font-semibold capitalize text-[#E8590C]">
                      {formatLabel(application.application_status)}
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase text-slate-500">Étape</p>
                      <p className="mt-1 text-sm font-semibold capitalize text-[#0B1F3A]">{formatLabel(application.current_stage)}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase text-slate-500">Date</p>
                      <p className="mt-1 text-sm font-semibold text-[#0B1F3A]">
                        {new Date(application.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </main>
  );
}
