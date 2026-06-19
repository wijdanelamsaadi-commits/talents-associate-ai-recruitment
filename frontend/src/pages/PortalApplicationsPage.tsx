import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { PortalApplicationStatusItem, getCandidateApplications } from "../services/portal";

function label(value: string | null) {
  return value ? value.replaceAll("_", " ") : "En cours";
}

export function PortalApplicationsPage() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<PortalApplicationStatusItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadApplications() {
      try {
        const data = await getCandidateApplications();
        if (isMounted) {
          setApplications(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Impossible de charger vos candidatures."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    loadApplications();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Mes candidatures</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Suivi candidat</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Retrouvez les offres auxquelles vous avez postulé, l’étape actuelle et les résultats de matching disponibles.
        </p>
      </div>

      {isLoading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Chargement des candidatures...</div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error}</div>
      ) : applications.length === 0 ? (
        <EmptyState
          title="Aucune candidature"
          description="Votre espace est prêt. Postulez à une offre pour suivre votre dossier ici."
          actionLabel="Voir les offres"
          onAction={() => navigate("/portal/jobs")}
        />
      ) : (
        <div className="space-y-4">
          {applications.map((application) => (
            <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" key={application.application_id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-[#0B1F3A]">{application.job_title}</h2>
                  <p className="mt-1 text-sm text-slate-600">{application.company_name ?? "Talents Associate"}</p>
                </div>
                <span className="rounded-full bg-[#E8590C]/10 px-3 py-1 text-xs font-semibold capitalize text-[#E8590C]">
                  {label(application.application_status)}
                </span>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">Étape</p>
                  <p className="mt-1 text-sm font-semibold capitalize text-[#0B1F3A]">{label(application.current_stage)}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">Score de matching</p>
                  <p className="mt-1 text-sm font-semibold text-[#0B1F3A]">
                    {application.best_matching_score === null ? "En attente" : `${application.best_matching_score}%`}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">Date</p>
                  <p className="mt-1 text-sm font-semibold text-[#0B1F3A]">{new Date(application.applied_at).toLocaleDateString()}</p>
                </div>
              </div>
              {application.recommendation ? <p className="mt-3 text-sm capitalize text-slate-600">Recommandation : {label(application.recommendation)}</p> : null}
              <Link className="mt-4 inline-flex text-sm font-semibold text-[#E8590C] hover:text-[#c94b08]" to={`/portal/jobs/${application.job_offer_id}`}>
                Revoir l’offre
              </Link>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
