import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { getPublicJobs } from "../services/portal";

const demoJobs: JobOffer[] = [
  {
    id: "demo-orange-full-stack",
    title: "Développeur Full Stack",
    company_name: "Orange",
    location: "Casablanca",
    contract_type: "CDI",
    required_skills: ["React", "Node.js", "PostgreSQL", "JavaScript"],
    preferred_skills: [],
    required_experience_years: 3,
    education_level: null,
    description: "Nous recherchons un développeur Full Stack maîtrisant React, Node.js et les bases de données SQL/NoSQL pour rejoindre notre équipe tech.",
    status: "published",
    created_at: "",
    updated_at: "",
  },
  {
    id: "demo-axa-consultant",
    title: "Consultant Fonctionnel",
    company_name: "AXA",
    location: "Rabat",
    contract_type: "CDI",
    required_skills: ["Analyse", "Conduite du changement", "Processus métier"],
    preferred_skills: [],
    required_experience_years: 4,
    education_level: null,
    description: "Vous accompagnerez nos clients dans l'analyse de leurs besoins et la mise en place de solutions adaptées à leurs enjeux métiers.",
    status: "published",
    created_at: "",
    updated_at: "",
  },
  {
    id: "demo-maroc-telecom-devops",
    title: "Ingénieur DevOps",
    company_name: "Maroc Telecom",
    location: "Casablanca",
    contract_type: "CDI",
    required_skills: ["Docker", "Kubernetes", "AWS", "CI/CD"],
    preferred_skills: [],
    required_experience_years: 3,
    education_level: null,
    description: "Vous participerez à la mise en place et à l'optimisation de notre infrastructure cloud et de nos outils CI/CD.",
    status: "published",
    created_at: "",
    updated_at: "",
  },
  {
    id: "demo-recrutement-rh",
    title: "Chargé(e) de Recrutement",
    company_name: "Talents Associate",
    location: "Casablanca",
    contract_type: "CDD",
    required_skills: ["Recrutement", "Sourcing", "Entretien", "RH"],
    preferred_skills: [],
    required_experience_years: 2,
    education_level: null,
    description: "Vous prendrez en charge l'ensemble du processus de recrutement et contribuerez à attirer les meilleurs talents.",
    status: "published",
    created_at: "",
    updated_at: "",
  },
];

const experienceOptions = [
  { label: "Tous niveaux", value: "all" },
  { label: "0-1 an", value: "0-1" },
  { label: "1-3 ans", value: "1-3" },
  { label: "3-5 ans", value: "3-5" },
  { label: "5 ans et plus", value: "5+" },
];

function shortDescription(description: string) {
  if (description.length <= 155) {
    return description;
  }
  return `${description.slice(0, 152).trim()}...`;
}

function experienceLabel(years: number | null) {
  if (years === null || Number.isNaN(years)) {
    return "Tous niveaux";
  }
  if (years <= 1) {
    return "0-1 an";
  }
  if (years <= 3) {
    return "1-3 ans";
  }
  if (years <= 5) {
    return "3-5 ans";
  }
  return "5 ans et plus";
}

function matchesExperience(years: number | null, selected: string) {
  if (selected === "all") {
    return true;
  }
  const safeYears = years ?? 0;
  if (selected === "0-1") {
    return safeYears <= 1;
  }
  if (selected === "1-3") {
    return safeYears >= 1 && safeYears <= 3;
  }
  if (selected === "3-5") {
    return safeYears >= 3 && safeYears <= 5;
  }
  return safeYears >= 5;
}

function companyMark(companyName: string | null) {
  const name = companyName ?? "Talents Associate";
  if (name.toLowerCase().includes("orange")) {
    return { label: "orange", className: "bg-[#ff3d00] text-white text-sm" };
  }
  if (name.toLowerCase().includes("axa")) {
    return { label: "AXA", className: "bg-[#0711a8] text-white text-2xl" };
  }
  if (name.toLowerCase().includes("telecom")) {
    return { label: "Maroc\nTelecom", className: "bg-white text-[#178bd3] text-[10px] border border-slate-200" };
  }
  return { label: "TA", className: "bg-[#061A33] text-white text-lg" };
}

async function getPublicJobsWithTimeout() {
  return Promise.race<JobOffer[]>([
    getPublicJobs(),
    new Promise<JobOffer[]>((_, reject) => {
      window.setTimeout(() => reject(new Error("Delai de chargement depasse")), 3500);
    }),
  ]);
}

export function PortalJobsPage() {
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("all");
  const [contractType, setContractType] = useState("all");
  const [experience, setExperience] = useState("all");

  useEffect(() => {
    let isMounted = true;

    async function loadJobs() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPublicJobsWithTimeout();
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

  const visibleJobs = jobs.length > 0 ? jobs : demoJobs;

  const locations = useMemo(() => {
    const values = visibleJobs.map((job) => job.location).filter((value): value is string => Boolean(value));
    return Array.from(new Set(values));
  }, [visibleJobs]);

  const contractTypes = useMemo(() => {
    const values = visibleJobs.map((job) => job.contract_type).filter((value): value is string => Boolean(value));
    return Array.from(new Set(values));
  }, [visibleJobs]);

  const filteredJobs = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return visibleJobs.filter((job) => {
      const searchable = [job.title, job.company_name, job.description, ...job.required_skills].join(" ").toLowerCase();
      return (
        (!normalizedKeyword || searchable.includes(normalizedKeyword)) &&
        (location === "all" || job.location === location) &&
        (contractType === "all" || job.contract_type === contractType) &&
        matchesExperience(job.required_experience_years, experience)
      );
    });
  }, [contractType, experience, keyword, location, visibleJobs]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <main className="bg-white">
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-white to-[#fff6f1]">
        <div className="mx-auto grid max-w-[1360px] items-center gap-10 px-6 pb-12 pt-12 lg:grid-cols-[0.9fr_1.1fr] lg:px-12 lg:pb-20 lg:pt-16">
          <div className="relative z-10">
            <h1 className="text-4xl font-extrabold leading-tight text-[#061A33] sm:text-5xl lg:text-[56px]">Offres disponibles</h1>
            <div className="mt-5 h-0.5 w-16 bg-[#ff3d00]" />
            <p className="mt-7 max-w-lg text-lg leading-8 text-[#253858]">
              Découvrez les opportunités ouvertes et postulez avec votre profil candidat.
            </p>
            <div className="mt-9 inline-flex items-center gap-4 rounded-full bg-white px-1 py-1 text-sm font-extrabold text-[#061A33]">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-[#ff3d00]/10 text-[#ff3d00]">▣</span>
              <span>128 offres disponibles</span>
            </div>
          </div>

          <div className="relative min-h-[300px] lg:min-h-[380px]">
            <div className="absolute -left-16 top-0 hidden h-[440px] w-[440px] rounded-full bg-slate-100/60 lg:block" />
            <div className="absolute right-0 top-14 h-64 w-36 rounded-l-[4rem] bg-[#ff3d00]/10" />
            <div className="absolute left-14 top-24 z-10 hidden grid-cols-6 gap-3 lg:grid">
              {Array.from({ length: 30 }).map((_, index) => (
                <span className="h-1.5 w-1.5 rounded-full bg-[#ff3d00]" key={index} />
              ))}
            </div>
            <div className="absolute -right-20 bottom-0 hidden h-72 w-72 rounded-full border-l-4 border-[#ff3d00]/70 lg:block" />
            <img
              alt="Candidate professionnelle travaillant sur ordinateur"
              className="relative z-0 ml-auto h-[320px] w-full rounded-bl-[5rem] object-cover object-center shadow-2xl shadow-slate-900/10 lg:h-[390px] lg:w-[760px]"
              src="/portal-hero-woman.png"
            />
          </div>
        </div>
      </section>

      <section className="relative z-20 mx-auto -mt-10 max-w-[1260px] px-6">
        <form className="grid gap-5 rounded-2xl border border-slate-100 bg-white p-5 shadow-2xl shadow-slate-900/10 lg:grid-cols-[1.1fr_0.9fr_0.9fr_0.9fr_auto]" onSubmit={handleSearch}>
          <label className="block">
            <span className="flex items-center gap-2 text-sm font-bold text-[#061A33]">
              <span className="text-lg">⌕</span> Recherche par mot-clé
            </span>
            <input
              className="mt-3 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-2 focus:ring-[#ff3d00]/10"
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Ex: Développeur, Marketing..."
              value={keyword}
            />
          </label>

          <label className="block">
            <span className="flex items-center gap-2 text-sm font-bold text-[#061A33]">
              <span className="text-lg">⌖</span> Localisation
            </span>
            <select className="mt-3 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm text-slate-600 outline-none focus:border-[#ff3d00] focus:ring-2 focus:ring-[#ff3d00]/10" onChange={(event) => setLocation(event.target.value)} value={location}>
              <option value="all">Toutes les villes</option>
              {locations.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="flex items-center gap-2 text-sm font-bold text-[#061A33]">
              <span className="text-lg">▤</span> Type de contrat
            </span>
            <select className="mt-3 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm text-slate-600 outline-none focus:border-[#ff3d00] focus:ring-2 focus:ring-[#ff3d00]/10" onChange={(event) => setContractType(event.target.value)} value={contractType}>
              <option value="all">Tous les contrats</option>
              {contractTypes.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="flex items-center gap-2 text-sm font-bold text-[#061A33]">
              <span className="text-lg">▥</span> Niveau d'expérience
            </span>
            <select className="mt-3 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm text-slate-600 outline-none focus:border-[#ff3d00] focus:ring-2 focus:ring-[#ff3d00]/10" onChange={(event) => setExperience(event.target.value)} value={experience}>
              {experienceOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <button className="mt-auto h-12 rounded-lg bg-[#ff3d00] px-7 text-sm font-extrabold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]" type="submit">
            Rechercher
          </button>
        </form>
      </section>

      <section className="mx-auto max-w-[1260px] px-6 py-9">
        {isLoading ? (
          <div className="rounded-2xl border border-slate-100 bg-white p-8 text-sm font-semibold text-slate-600 shadow-xl shadow-slate-900/5">Chargement des offres...</div>
        ) : filteredJobs.length === 0 ? (
          <EmptyState title="Aucune offre ouverte" description="Aucune offre ne correspond actuellement à vos critères de recherche." />
        ) : (
          <>
            <div className="grid gap-7 lg:grid-cols-2">
              {filteredJobs.map((job) => {
                const mark = companyMark(job.company_name);
                return (
                  <article className="rounded-xl border border-slate-100 bg-white p-6 shadow-xl shadow-slate-900/8" key={job.id}>
                    <div className="flex items-start justify-between gap-5">
                      <div className="flex items-start gap-5">
                        <div className={`flex h-16 w-16 shrink-0 items-center justify-center whitespace-pre-line rounded-sm text-center font-extrabold leading-tight ${mark.className}`}>
                          {mark.label}
                        </div>
                        <div>
                          <h2 className="text-xl font-extrabold text-[#061A33]">{job.title}</h2>
                          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium text-slate-600">
                            <span>◉ {job.contract_type || "Ouvert"}</span>
                            <span>⌖ {job.location || "Flexible"}</span>
                            <span>▤ {experienceLabel(job.required_experience_years)}</span>
                          </div>
                        </div>
                      </div>
                      <button className="rounded-lg border border-slate-200 px-2 py-1 text-xl text-[#061A33] transition hover:border-[#ff3d00] hover:text-[#ff3d00]" type="button" aria-label="Sauvegarder l'offre">
                        ♡
                      </button>
                    </div>

                    <p className="mt-6 min-h-[56px] text-sm leading-7 text-slate-600">{shortDescription(job.description)}</p>

                    <div className="mt-5 flex flex-wrap gap-3">
                      {(job.required_skills.length > 0 ? job.required_skills : ["Profil ouvert"]).slice(0, 4).map((skill) => (
                        <span className="rounded-xl bg-[#eef2ff] px-4 py-2 text-xs font-bold text-[#061A33]" key={skill}>
                          {skill}
                        </span>
                      ))}
                    </div>

                    <div className="mt-6 grid gap-4 sm:grid-cols-2">
                      <Link
                        className="inline-flex h-12 items-center justify-center rounded-lg border border-[#ff3d00] text-sm font-extrabold text-[#061A33] transition hover:bg-[#ff3d00]/5 hover:text-[#ff3d00]"
                        to={`/portal/jobs/${job.id}`}
                      >
                        Voir détails
                      </Link>
                      <Link
                        className="inline-flex h-12 items-center justify-center rounded-lg bg-[#ff3d00] text-sm font-extrabold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]"
                        to={`/portal/apply/${job.id}`}
                      >
                        Postuler ↗
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}

        <div className="mt-10 flex items-center justify-center gap-4 text-sm font-bold text-[#061A33]">
          <button className="h-10 w-10 rounded-lg border border-slate-200 bg-white shadow-sm" type="button">‹</button>
          {[1, 2, 3, 4].map((page) => (
            <button className={page === 1 ? "h-10 w-10 rounded-lg bg-[#ff3d00] text-white shadow-lg shadow-orange-500/20" : "h-10 w-10 rounded-lg bg-white"} key={page} type="button">
              {page}
            </button>
          ))}
          <span>...</span>
          <button className="h-10 w-10 rounded-lg bg-white" type="button">7</button>
          <button className="h-10 w-10 rounded-lg border border-slate-200 bg-white shadow-sm" type="button">›</button>
        </div>

        <div className="mt-9 grid items-center gap-6 rounded-2xl bg-white px-8 py-8 shadow-2xl shadow-slate-900/8 md:grid-cols-[auto_1fr_auto]">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#ff3d00]/10 text-4xl text-[#ff3d00]">□</div>
          <div>
            <h2 className="text-lg font-extrabold text-[#061A33]">Vous ne trouvez pas l'offre qui vous correspond ?</h2>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-600">
              Déposez votre CV spontanément et nous vous recontacterons dès qu'une opportunité adaptée se présente.
            </p>
          </div>
          <Link
            className="inline-flex h-12 items-center justify-center rounded-lg border border-[#ff3d00] px-8 text-sm font-extrabold text-[#ff3d00] transition hover:bg-[#ff3d00]/5"
            to="/portal/profile"
          >
            Déposer mon CV
          </Link>
        </div>
      </section>
    </main>
  );
}
