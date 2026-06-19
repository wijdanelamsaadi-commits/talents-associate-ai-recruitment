import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { getPublicJobs } from "../services/portal";

function skillList(skills: string[]) {
  return skills.length > 0 ? skills.join(", ") : "Profil ouvert";
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
          setError(getApiErrorMessage(loadError, "Impossible de charger les offres disponibles."));
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
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Opportunités de carrières</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Offres disponibles</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Consultez les offres publiées par Talents Associate. Connectez-vous pour postuler avec votre profil et suivre vos candidatures.
        </p>
      </div>

      {isLoading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Chargement des offres...</div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error}</div>
      ) : jobs.length === 0 ? (
        <EmptyState title="Aucune offre ouverte" description="Aucune offre publique n'est disponible pour le moment." />
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
                  {job.contract_type || "Ouvert"}
                </span>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-600">{job.description}</p>
              <p className="mt-4 text-sm text-slate-700">
                <span className="font-semibold">Compétences :</span> {skillList(job.required_skills)}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <Link
                  className="inline-flex rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
                  to={`/portal/jobs/${job.id}`}
                >
                  Voir le détail
                </Link>
                <Link
                  className="inline-flex rounded-lg bg-[#E8590C] px-4 py-2 text-sm font-semibold text-white hover:bg-[#c94b08]"
                  to={`/portal/jobs/${job.id}`}
                >
                  Postuler
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
