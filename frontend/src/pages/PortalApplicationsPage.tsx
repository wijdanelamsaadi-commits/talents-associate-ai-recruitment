import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { PortalApplicationStatusItem, getCandidateApplications } from "../services/portal";

type DisplayApplication = PortalApplicationStatusItem & {
  contract_type?: string | null;
  location?: string | null;
};

const demoApplications: DisplayApplication[] = [
  {
    application_id: "demo-application-orange",
    job_offer_id: "demo-orange-full-stack",
    job_title: "Développeur Full Stack",
    company_name: "Orange",
    application_status: "submitted",
    current_stage: null,
    applied_at: "2026-06-18T10:00:00Z",
    cv_file_id: null,
    contract_type: "CDI",
    location: "Casablanca",
  },
  {
    application_id: "demo-application-axa",
    job_offer_id: "demo-axa-data",
    job_title: "Data Analyst",
    company_name: "AXA",
    application_status: "submitted",
    current_stage: null,
    applied_at: "2026-06-10T10:00:00Z",
    cv_file_id: null,
    contract_type: "Stage",
    location: "Rabat",
  },
  {
    application_id: "demo-application-telecom",
    job_offer_id: "demo-maroc-telecom-devops",
    job_title: "Ingénieur DevOps",
    company_name: "Maroc Telecom",
    application_status: "submitted",
    current_stage: null,
    applied_at: "2026-06-02T10:00:00Z",
    cv_file_id: null,
    contract_type: "CDI",
    location: "Casablanca",
  },
  {
    application_id: "demo-application-bmce",
    job_offer_id: "demo-bmce-recrutement",
    job_title: "Chargé(e) de Recrutement",
    company_name: "BMCE Bank",
    application_status: "submitted",
    current_stage: null,
    applied_at: "2026-05-28T10:00:00Z",
    cv_file_id: null,
    contract_type: "CDD",
    location: "Casablanca",
  },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function companyMark(companyName: string | null) {
  const name = companyName ?? "Talents Associate";
  if (name.toLowerCase().includes("orange")) {
    return { label: "orange", className: "bg-[#ff3d00] text-white text-lg" };
  }
  if (name.toLowerCase().includes("axa")) {
    return { label: "AXA", className: "bg-[#0711a8] text-white text-3xl" };
  }
  if (name.toLowerCase().includes("telecom")) {
    return { label: "Maroc\nTelecom", className: "bg-white text-[#178bd3] text-xs border border-slate-200" };
  }
  if (name.toLowerCase().includes("bmce")) {
    return { label: "BMCE\nBANK", className: "bg-white text-[#061A33] text-[10px] border border-slate-200" };
  }
  return { label: "TA", className: "bg-[#061A33] text-white text-xl" };
}

function getContract(application: DisplayApplication) {
  return application.contract_type || "Contrat non précisé";
}

function getLocation(application: DisplayApplication) {
  return application.location || "Localisation non précisée";
}

export function PortalApplicationsPage() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<DisplayApplication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

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

  const visibleApplications = error ? demoApplications : applications;
  const filteredApplications = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return visibleApplications;
    }
    return visibleApplications.filter((application) =>
      [application.job_title, application.company_name, getContract(application), getLocation(application)]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch),
    );
  }, [search, visibleApplications]);

  return (
    <main className="bg-white">
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-white to-[#fff8f4]">
        <div className="mx-auto grid max-w-[1260px] items-center gap-10 px-6 py-16 lg:grid-cols-[1fr_auto] lg:py-20">
          <div>
            <h1 className="text-4xl font-extrabold leading-tight text-[#061A33] sm:text-5xl">Mes candidatures</h1>
            <div className="mt-5 h-0.5 w-16 bg-[#ff3d00]" />
            <p className="mt-7 text-xl text-[#53627c]">Suivez l'état de vos candidatures.</p>
          </div>

          <div className="relative hidden h-40 w-80 items-center justify-center lg:flex">
            <div className="absolute right-28 h-36 w-36 rounded-full bg-[#ff3d00]/10" />
            <div className="absolute right-0 grid grid-cols-6 gap-3">
              {Array.from({ length: 30 }).map((_, index) => (
                <span className="h-1.5 w-1.5 rounded-full bg-[#ff3d00]/20" key={index} />
              ))}
            </div>
            <div className="relative flex h-24 w-24 items-center justify-center rounded-2xl border border-[#ff3d00]/40 bg-white text-5xl text-[#ff3d00] shadow-xl shadow-slate-900/5">
              □
            </div>
            <div className="relative -ml-6 mt-12 flex h-14 w-16 items-center justify-center rounded-lg bg-[#ff3d00] text-2xl text-white shadow-lg shadow-orange-500/20">
              ▣
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1260px] px-6 pb-12">
        <div className="-mt-8 rounded-xl border border-slate-100 bg-white p-5 shadow-xl shadow-slate-900/5">
          <label className="relative block max-w-3xl">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-xl text-slate-400">⌕</span>
            <input
              className="h-12 w-full rounded-lg border border-slate-200 pl-12 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-2 focus:ring-[#ff3d00]/10"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Rechercher une offre, une entreprise..."
              value={search}
            />
          </label>
        </div>

        {isLoading ? (
          <div className="mt-5 rounded-xl border border-slate-100 bg-white p-8 text-sm font-semibold text-slate-600 shadow-sm">
            Chargement des candidatures...
          </div>
        ) : filteredApplications.length === 0 ? (
          <div className="mt-5">
            <EmptyState
              title="Aucune candidature"
              description="Votre espace est prêt. Postulez à une offre pour suivre votre dossier ici."
              actionLabel="Voir les offres"
              onAction={() => navigate("/portal/jobs")}
            />
          </div>
        ) : (
          <div className="mt-5 overflow-hidden rounded-xl border border-slate-100 bg-white shadow-xl shadow-slate-900/5">
            {filteredApplications.map((application, index) => {
              const mark = companyMark(application.company_name);
              return (
                <article
                  className={index > 0 ? "border-t border-slate-100 px-8 py-7" : "px-8 py-7"}
                  key={application.application_id}
                >
                  <div className="grid items-center gap-6 md:grid-cols-[auto_1fr_280px_auto]">
                    <div className={`flex h-20 w-20 items-center justify-center whitespace-pre-line rounded-md text-center font-extrabold leading-tight ${mark.className}`}>
                      {mark.label}
                    </div>

                    <div>
                      <h2 className="text-xl font-extrabold text-[#061A33]">{application.job_title}</h2>
                      <div className="mt-4 flex flex-wrap gap-x-7 gap-y-2 text-sm font-medium text-[#061A33]">
                        <span>▣ {getContract(application)}</span>
                        <span>⌖ {getLocation(application)}</span>
                      </div>
                    </div>

                    <div className="text-sm leading-7 text-[#061A33]">
                      <p>Candidature envoyée le</p>
                      <p className="font-bold">{formatDate(application.applied_at)}</p>
                    </div>

                    <Link
                      className="inline-flex items-center justify-start gap-4 text-sm font-extrabold text-[#ff3d00] transition hover:text-[#e63600] md:justify-center"
                      to={`/portal/jobs/${application.job_offer_id}`}
                    >
                      Voir détail <span className="text-xl">›</span>
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
