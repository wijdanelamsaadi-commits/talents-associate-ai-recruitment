import { FormEvent, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ListSearch } from "../components/ListSearch";
import {
  CONTRACT_TYPES,
  EDUCATION_LEVELS,
  EXPERIENCE_LEVELS,
  SECTORS,
} from "../constants/sectors";
import {
  EXPERIENCE_LEVEL_TO_YEARS,
  JOB_POSITIONS,
  JobLanguage,
  LANGUAGE_LEVELS,
  LANGUAGE_OPTIONS,
  yearsToExperienceLevel,
} from "../constants/jobOffers";
import { getApiErrorMessage } from "../lib/errors";
import { JobOffer, JobOfferPayload, createJobOffer, deleteJobOffer, getJobOffers, updateJobOffer } from "../services/jobs";

type JobFormState = {
  title: string;
  company_name: string;
  location: string;
  sector: string;
  contract_type: string;
  required_skills: string;
  soft_skills: string;
  experience_level: string;
  education_level: string;
  description: string;
  status: string;
  languages: JobLanguage[];
};

const initialFormState: JobFormState = {
  title: "",
  company_name: "",
  location: "",
  sector: "",
  contract_type: "",
  required_skills: "",
  soft_skills: "",
  experience_level: "",
  education_level: "",
  description: "",
  status: "open",
  languages: [{ language: "Français", level: "Courant" }],
};

const statusOptions = [
  { value: "draft", label: "Brouillon" },
  { value: "open", label: "En cours" },
  { value: "paused", label: "En pause" },
  { value: "closed", label: "Clôturé" },
  { value: "archived", label: "Annulé" },
];

function splitSemicolonList(value: string) {
  return value
    .split(";")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinSemicolonList(value: string[]) {
  return value.join("; ");
}

function toFormState(job: JobOffer): JobFormState {
  return {
    title: job.title,
    company_name: job.company_name ?? "",
    location: job.location ?? "",
    sector: job.sector ?? "",
    contract_type: job.contract_type ?? "",
    required_skills: joinSemicolonList(job.required_skills),
    soft_skills: joinSemicolonList(job.soft_skills),
    experience_level: yearsToExperienceLevel(job.required_experience_years),
    education_level: job.education_level ?? "",
    description: job.description,
    status: job.status,
    languages: job.languages.length > 0 ? job.languages : [{ language: "Français", level: "Courant" }],
  };
}

function toPayload(formState: JobFormState): JobOfferPayload {
  return {
    title: formState.title.trim(),
    company_name: formState.company_name.trim() || null,
    location: formState.location.trim() || null,
    sector: formState.sector.trim() || null,
    contract_type: formState.contract_type.trim() || null,
    required_skills: splitSemicolonList(formState.required_skills),
    soft_skills: splitSemicolonList(formState.soft_skills),
    languages: formState.languages.filter((entry) => entry.language && entry.level),
    required_experience_years: formState.experience_level
      ? EXPERIENCE_LEVEL_TO_YEARS[formState.experience_level] ?? null
      : null,
    education_level: formState.education_level.trim() || null,
    description: formState.description.trim(),
    status: formState.status,
  };
}

export function JobOffersPage() {
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingJob, setEditingJob] = useState<JobOffer | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formState, setFormState] = useState<JobFormState>(initialFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredJobs = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return jobs;
    }
    return jobs.filter((job) =>
      [
        job.title,
        job.company_name,
        job.location,
        job.sector,
        job.contract_type,
        job.status,
        statusOptions.find((option) => option.value === job.status)?.label,
        job.description,
        ...job.required_skills,
        ...job.soft_skills,
        ...job.languages.map((entry) => `${entry.language} ${entry.level}`),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [jobs, searchQuery]);

  const loadJobs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getJobOffers();
      setJobs(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger les offres d'emploi."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  const openCreateModal = () => {
    setEditingJob(null);
    setFormState(initialFormState);
    setError(null);
    setMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (job: JobOffer) => {
    setEditingJob(job);
    setFormState(toFormState(job));
    setError(null);
    setMessage(null);
    setIsModalOpen(true);
  };

  const updateLanguage = (index: number, field: keyof JobLanguage, value: string) => {
    setFormState((current) => ({
      ...current,
      languages: current.languages.map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, [field]: value } : entry,
      ),
    }));
  };

  const addLanguage = () => {
    setFormState((current) => ({
      ...current,
      languages: [...current.languages, { language: "Français", level: "Intermédiaire" }],
    }));
  };

  const removeLanguage = (index: number) => {
    setFormState((current) => ({
      ...current,
      languages: current.languages.filter((_, entryIndex) => entryIndex !== index),
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const payload = toPayload(formState);
      if (editingJob) {
        await updateJobOffer(editingJob.id, payload);
        setMessage("Offre d'emploi mise à jour.");
      } else {
        await createJobOffer(payload);
        setMessage("Offre d'emploi créée.");
      }
      setIsModalOpen(false);
      setEditingJob(null);
      setFormState(initialFormState);
      await loadJobs();
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "L'offre d'emploi n'a pas pu être enregistrée."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (job: JobOffer) => {
    const shouldDelete = window.confirm(`Supprimer l'offre « ${job.title} » ?`);
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteJobOffer(job.id);
      setMessage("Offre d'emploi supprimée.");
      await loadJobs();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "L'offre d'emploi n'a pas pu être supprimée."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Offres d&apos;emploi</h2>
          <p className="mt-1 text-sm text-slate-600">Gérez les postes utilisés par le moteur de matching.</p>
        </div>
        <button
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
          onClick={openCreateModal}
          type="button"
        >
          Nouvelle offre
        </button>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement des offres d&apos;emploi...
        </section>
      ) : null}

      {!isLoading && jobs.length === 0 ? (
        <EmptyState
          title="Aucune offre d'emploi"
          description="Créez la première offre pour lancer le matching des CV."
          actionLabel="Créer une offre"
          onAction={openCreateModal}
        />
      ) : null}

      {!isLoading && jobs.length > 0 ? (
        <ListSearch
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Rechercher par poste, client, secteur, statut ou compétence..."
        />
      ) : null}

      {!isLoading && jobs.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Offres actives</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Poste</th>
                  <th className="px-5 py-3 font-semibold">Client</th>
                  <th className="px-5 py-3 font-semibold">Secteur</th>
                  <th className="px-5 py-3 font-semibold">Localisation</th>
                  <th className="px-5 py-3 font-semibold">Contrat</th>
                  <th className="px-5 py-3 font-semibold">Statut</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{job.title}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.company_name ?? "—"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.sector ?? "—"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.location ?? "—"}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job.contract_type ?? "—"}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold text-[#1D6EEA]">
                        {statusOptions.find((option) => option.value === job.status)?.label ?? job.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <div className="flex gap-2">
                        <button
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          onClick={() => openEditModal(job)}
                          type="button"
                        >
                          Modifier
                        </button>
                        <button
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                          onClick={() => void handleDelete(job)}
                          type="button"
                        >
                          Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {!isLoading && jobs.length > 0 && filteredJobs.length === 0 ? (
        <EmptyState title="Aucune offre trouvÃ©e" description="Modifiez la recherche pour afficher d'autres offres." />
      ) : null}

      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0B1F3A]/40 px-4 py-6">
          <section className="w-full max-w-4xl rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B1F3A]">
                {editingJob ? "Modifier l'offre d'emploi" : "Créer une offre d'emploi"}
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Séparez les compétences par des points-virgules (;).
              </p>
            </div>
            <form className="space-y-5 p-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Poste</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
                    required
                    value={formState.title}
                  >
                    <option value="">Sélectionner un poste</option>
                    {JOB_POSITIONS.map((position) => (
                      <option key={position} value={position}>
                        {position}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Client</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, company_name: event.target.value }))}
                    value={formState.company_name}
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Secteur d&apos;activité</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, sector: event.target.value }))}
                    value={formState.sector}
                  >
                    <option value="">Sélectionner un secteur</option>
                    {SECTORS.map((sector) => (
                      <option key={sector} value={sector}>
                        {sector}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Localisation</span>
                  <input
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, location: event.target.value }))}
                    value={formState.location}
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Type de contrat</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, contract_type: event.target.value }))}
                    value={formState.contract_type}
                  >
                    <option value="">Sélectionner un type</option>
                    {CONTRACT_TYPES.map((contractType) => (
                      <option key={contractType} value={contractType}>
                        {contractType}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Niveau d&apos;expérience</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, experience_level: event.target.value }))}
                    value={formState.experience_level}
                  >
                    <option value="">Sélectionner un niveau</option>
                    {EXPERIENCE_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Niveau d&apos;études</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, education_level: event.target.value }))}
                    value={formState.education_level}
                  >
                    <option value="">Sélectionner un niveau</option>
                    {EDUCATION_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Statut</span>
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                    onChange={(event) => setFormState((current) => ({ ...current, status: event.target.value }))}
                    value={formState.status}
                  >
                    {statusOptions.map((status) => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">Compétences techniques</span>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                  onChange={(event) => setFormState((current) => ({ ...current, required_skills: event.target.value }))}
                  placeholder="React; TypeScript; FastAPI"
                  value={formState.required_skills}
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">Compétences comportementales</span>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                  onChange={(event) => setFormState((current) => ({ ...current, soft_skills: event.target.value }))}
                  placeholder="Communication; Esprit d'équipe; Autonomie"
                  value={formState.soft_skills}
                />
              </label>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">Langues</span>
                  <button
                    className="text-sm font-semibold text-[#1D6EEA] hover:text-[#165AC0]"
                    onClick={addLanguage}
                    type="button"
                  >
                    Ajouter une langue
                  </button>
                </div>
                {formState.languages.map((entry, index) => (
                  <div key={`${entry.language}-${index}`} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
                    <select
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                      onChange={(event) => updateLanguage(index, "language", event.target.value)}
                      value={entry.language}
                    >
                      {LANGUAGE_OPTIONS.map((language) => (
                        <option key={language} value={language}>
                          {language}
                        </option>
                      ))}
                    </select>
                    <select
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                      onChange={(event) => updateLanguage(index, "level", event.target.value)}
                      value={entry.level}
                    >
                      {LANGUAGE_LEVELS.map((level) => (
                        <option key={level} value={level}>
                          {level}
                        </option>
                      ))}
                    </select>
                    <button
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                      disabled={formState.languages.length === 1}
                      onClick={() => removeLanguage(index)}
                      type="button"
                    >
                      Retirer
                    </button>
                  </div>
                ))}
              </div>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">Description</span>
                <textarea
                  className="mt-2 min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                  onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))}
                  required
                  value={formState.description}
                />
              </label>

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  onClick={() => setIsModalOpen(false)}
                  type="button"
                >
                  Annuler
                </button>
                <button
                  className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Enregistrement..." : "Enregistrer"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
