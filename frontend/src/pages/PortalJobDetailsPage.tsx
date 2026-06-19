import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { getStoredCandidateToken } from "../lib/portalAuthStorage";
import { JobOffer } from "../services/jobs";
import { getPublicJob, submitAuthenticatedApplication } from "../services/portal";

function splitLabel(value: string | null) {
  return value || "Non renseigné";
}

export function PortalJobDetailsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);
  const isCandidateLoggedIn = Boolean(getStoredCandidateToken());

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
          setError(getApiErrorMessage(loadError, "Impossible de charger le détail de l'offre."));
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
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Chargement de l'offre...</div>
      ) : !job ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error ?? "Offre introuvable."}</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase text-[#E8590C]">Détail de l'offre</p>
            <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">{job.title}</h1>
            <p className="mt-2 text-sm text-slate-600">
              {splitLabel(job.company_name)} - {splitLabel(job.location)} - {splitLabel(job.contract_type)}
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Expérience</p>
                <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{job.required_experience_years ?? 0}+ ans</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Diplôme</p>
                <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{splitLabel(job.education_level)}</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Statut</p>
                <p className="mt-2 text-sm font-semibold capitalize text-[#0B1F3A]">{job.status}</p>
              </div>
            </div>
            <div className="mt-6 space-y-5 text-sm leading-6 text-slate-700">
              <p>{job.description}</p>
              <p>
                <span className="font-semibold text-[#0B1F3A]">Compétences requises :</span>{" "}
                {job.required_skills.length > 0 ? job.required_skills.join(", ") : "Profil ouvert"}
              </p>
              <p>
                <span className="font-semibold text-[#0B1F3A]">Compétences souhaitées :</span>{" "}
                {job.preferred_skills.length > 0 ? job.preferred_skills.join(", ") : "Non renseigné"}
              </p>
            </div>
          </article>
          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[#0B1F3A]">Prêt à postuler ?</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Connectez-vous à votre espace candidat, vérifiez votre CV, puis postulez en un clic.
            </p>
            {isCandidateLoggedIn ? (
              <button
                className="mt-5 inline-flex w-full justify-center rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:bg-slate-400"
                disabled={isApplying}
                onClick={async () => {
                  setIsApplying(true);
                  setApplyMessage(null);
                  setError(null);
                  try {
                    const response = await submitAuthenticatedApplication(job.id);
                    setApplyMessage(response.message);
                  } catch (applyError) {
                    setError(getApiErrorMessage(applyError, "Impossible d'envoyer votre candidature. Ajoutez d'abord un CV depuis votre profil."));
                  } finally {
                    setIsApplying(false);
                  }
                }}
                type="button"
              >
                {isApplying ? "Candidature..." : "Postuler avec mon profil"}
              </button>
            ) : (
              <Link
                className="mt-5 inline-flex w-full justify-center rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08]"
                to="/portal/register"
              >
                Créer mon espace candidat
              </Link>
            )}
            <Link
              className="mt-3 inline-flex w-full justify-center rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
              to={`/portal/apply/${job.id}`}
            >
              Formulaire simple sans compte
            </Link>
            {applyMessage ? <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{applyMessage}</div> : null}
            {error ? <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
            <Link
              className="mt-3 inline-flex w-full justify-center rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
              to="/portal/jobs"
            >
              Retour aux offres
            </Link>
          </aside>
        </div>
      )}
    </main>
  );
}
