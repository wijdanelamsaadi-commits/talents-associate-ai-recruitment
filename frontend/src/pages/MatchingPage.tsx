import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { JobTitleAutocomplete } from "../components/JobTitleAutocomplete";
import { ListSearch } from "../components/ListSearch";
import { StatCard } from "../components/StatCard";
import { EDUCATION_LEVELS, EXPERIENCE_LEVELS, SECTORS } from "../constants/sectors";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, VivierSearchResult, getCandidates, searchCandidatesVivier } from "../services/candidates";
import { downloadCVFile } from "../services/cv";
import { JobOffer, getJobOffers } from "../services/jobs";
import { MatchingResult, deleteMatchingResult, getMatchingResults } from "../services/matching";
import { getJobReferenceTitles } from "../services/references";

type VivierSearchForm = {
  poste: string;
  secteur: string;
  experience_level: string;
  education_level: string;
  technical_skills: string;
  soft_skills: string;
  langues: string;
};

const initialSearchForm: VivierSearchForm = {
  poste: "",
  secteur: "",
  experience_level: "",
  education_level: "",
  technical_skills: "",
  soft_skills: "",
  langues: "",
};

function findCandidate(candidates: Candidate[], candidateId: string) {
  return candidates.find((candidate) => candidate.id === candidateId);
}

function findJob(jobs: JobOffer[], jobId: string) {
  return jobs.find((job) => job.id === jobId);
}

function candidateName(candidate?: Candidate) {
  return candidate ? `${candidate.first_name} ${candidate.last_name}` : "Candidat inconnu";
}

function skillList(value: MatchingResult["matched_skills"]) {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.map(String);
  }
  return Object.values(value).map((item) => String(item));
}

function formatRecommendation(value: string | null) {
  return value ? value.replaceAll("_", " ") : "Aucune recommandation";
}

function getScoreValue(scores: MatchingResult["detailed_scores"], key: string) {
  const value = scores?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getBusinessScore(scores: MatchingResult["detailed_scores"]) {
  const skillScore = getScoreValue(scores, "skill_score");
  const experienceScore = getScoreValue(scores, "experience_score");
  const educationScore = getScoreValue(scores, "education_score");
  const languageScore = getScoreValue(scores, "language_score");

  if (skillScore === null || experienceScore === null || educationScore === null || languageScore === null) {
    return null;
  }

  return Math.round((skillScore * 0.4) + (experienceScore * 0.3) + (educationScore * 0.25) + (languageScore * 0.05));
}

function formatScore(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value)}%` : "-";
}

export function MatchingPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [results, setResults] = useState<MatchingResult[]>([]);
  const [vivierResults, setVivierResults] = useState<VivierSearchResult[]>([]);
  const [jobReferenceTitles, setJobReferenceTitles] = useState<string[]>([]);
  const [searchForm, setSearchForm] = useState<VivierSearchForm>(initialSearchForm);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vivierSearchQuery, setVivierSearchQuery] = useState("");
  const [historySearchQuery, setHistorySearchQuery] = useState("");
  const [downloadingCvId, setDownloadingCvId] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [candidateData, jobData, resultData] = await Promise.all([
        getCandidates(),
        getJobOffers(),
        getMatchingResults(),
      ]);
      setCandidates(candidateData);
      setJobs(jobData);
      setResults(resultData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger le moteur de matching. Vérifiez que le backend est démarré."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadJobReferenceTitles = async () => {
      try {
        const referenceTitles = await getJobReferenceTitles();
        if (isMounted) {
          setJobReferenceTitles(referenceTitles);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Impossible de charger la liste officielle des postes."));
        }
      }
    };

    void loadJobReferenceTitles();

    return () => {
      isMounted = false;
    };
  }, []);

  const averageScore = useMemo(() => {
    if (results.length === 0) {
      return 0;
    }
    return Math.round(results.reduce((total, result) => total + result.score, 0) / results.length);
  }, [results]);

  const strongMatches = useMemo(() => results.filter((result) => result.score >= 80).length, [results]);

  const filteredVivierResults = useMemo(() => {
    const normalizedQuery = vivierSearchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return vivierResults;
    }
    return vivierResults.filter((result) =>
      [
        result.candidate.first_name,
        result.candidate.last_name,
        result.candidate.email,
        result.candidate.current_title,
        result.candidate.identified_job_profile,
        result.candidate.current_company,
        result.candidate.sector,
        result.score,
        result.has_cv ? "cv" : "sans cv",
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [vivierResults, vivierSearchQuery]);

  const filteredResults = useMemo(() => {
    const normalizedQuery = historySearchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return results;
    }
    return results.filter((result) => {
      const candidate = findCandidate(candidates, result.candidate_id);
      const job = findJob(jobs, result.job_offer_id);
      return [
        result.candidate_name,
        candidateName(candidate),
        candidate?.email,
        result.job_title,
        job?.title,
        job?.company_name,
        result.score,
        formatRecommendation(result.recommendation),
        new Date(result.created_at).toLocaleDateString("fr-FR"),
        ...skillList(result.matched_skills),
        ...skillList(result.missing_skills),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [candidates, historySearchQuery, jobs, results]);

  const handleJobSelect = (jobId: string) => {
    setSelectedJobId(jobId);
    const job = findJob(jobs, jobId);
    if (job) {
      setSearchForm((current) => ({
        ...current,
        poste: job.title,
        education_level: job.education_level ?? current.education_level,
        technical_skills: job.required_skills.join("; "),
      }));
    }
  };

  const handleVivierSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSearching(true);
    setHasSearched(true);

    const params = Object.fromEntries(
      Object.entries(searchForm).filter(([, value]) => value.trim() !== ""),
    ) as VivierSearchForm;
    if (Object.keys(params).length === 0) {
      setVivierResults([]);
      setMessage("Saisissez au moins un critère pour calculer une pertinence vivier.");
      setIsSearching(false);
      return;
    }

    try {
      const data = await searchCandidatesVivier(params);
      setVivierResults(data);
      setMessage(`${data.length} candidat(s) trouvé(s).`);
    } catch (searchError) {
      setError(getApiErrorMessage(searchError, "La recherche dans le vivier a échoué."));
      setVivierResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleDeleteResult = async (result: MatchingResult) => {
    const shouldDelete = window.confirm(`Supprimer le résultat de matching avec un score de ${result.score}% ?`);
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteMatchingResult(result.id);
      setMessage("Résultat de matching supprimé.");
      setResults(await getMatchingResults());
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Le résultat n'a pas pu être supprimé."));
    }
  };

  const handleDownloadCV = async (cvFileId: string, candidate: Candidate) => {
    setError(null);
    setDownloadingCvId(cvFileId);
    try {
      const fallbackFilename = `${candidate.first_name}-${candidate.last_name}-CV.pdf`.replaceAll(" ", "-");
      await downloadCVFile(cvFileId, fallbackFilename);
    } catch (downloadError) {
      setError(getApiErrorMessage(downloadError, "Le téléchargement du CV a échoué."));
    } finally {
      setDownloadingCvId(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Score moyen Matching IA" value={`${averageScore}%`} detail="Sur les résultats enregistrés" />
        <StatCard label="Fortes correspondances" value={String(strongMatches)} detail="Candidats avec un score ≥ 80%" />
        <StatCard label="Résultats enregistrés" value={String(results.length)} detail="Générés après traitement des CV" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-lg font-semibold text-[#24303F]">Recherche dans le vivier</h2>
          <p className="mt-1 text-sm text-slate-600">
            Filtrez les candidats par critères métier. Avec CV : matching sur compétences, expérience, formation et
            intitulé. Sans CV : matching sur poste, secteur et entreprise.
          </p>
          <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800">
            Score temporaire calculé à partir des critères de recherche. Ce score n’est pas le Matching IA final.
          </p>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleVivierSearch}>
          <div className="grid gap-4 lg:grid-cols-2">
            <JobTitleAutocomplete
              label="Poste (intitule)"
              onChange={(poste) => setSearchForm((current) => ({ ...current, poste }))}
              options={jobReferenceTitles}
              placeholder="Saisie libre ou selection depuis la liste officielle"
              value={searchForm.poste}
            />
            <label className="hidden">
              <span className="text-sm font-medium text-slate-700">Poste (intitulé)</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                list="job-titles"
                onChange={(event) => setSearchForm((current) => ({ ...current, poste: event.target.value }))}
                placeholder="Saisie libre ou sélection depuis les offres"
                value={searchForm.poste}
              />
              <datalist id="job-titles">
                {jobReferenceTitles.map((title) => (
                  <option key={`reference-${title}`} value={title} />
                ))}
                {jobs.map((job) => (
                  <option key={job.id} value={job.title}>
                    {job.company_name ? `${job.title} — ${job.company_name}` : job.title}
                  </option>
                ))}
              </datalist>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Offre existante (optionnel)</span>
              <select
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => handleJobSelect(event.target.value)}
                value={selectedJobId}
              >
                <option value="">— Sélectionner une offre —</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} {job.company_name ? `— ${job.company_name}` : ""}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Secteur d&apos;activité</span>
              <select
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, secteur: event.target.value }))}
                value={searchForm.secteur}
              >
                <option value="">— Tous les secteurs —</option>
                {SECTORS.map((sector) => (
                  <option key={sector} value={sector}>
                    {sector}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Niveau d&apos;expérience</span>
              <select
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, experience_level: event.target.value }))}
                value={searchForm.experience_level}
              >
                <option value="">—</option>
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, education_level: event.target.value }))}
                value={searchForm.education_level}
              >
                <option value="">—</option>
                {EDUCATION_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Compétences techniques</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, technical_skills: event.target.value }))}
                placeholder="Python; SQL; React"
                value={searchForm.technical_skills}
              />
              <span className="mt-1 block text-xs text-slate-500">Séparées par des points-virgules</span>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Compétences comportementales</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, soft_skills: event.target.value }))}
                placeholder="Communication; Leadership"
                value={searchForm.soft_skills}
              />
              <span className="mt-1 block text-xs text-slate-500">Séparées par des points-virgules</span>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Langues</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, langues: event.target.value }))}
                placeholder="Français; Anglais"
                value={searchForm.langues}
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-lg bg-[#EE6C2F] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSearching}
              type="submit"
            >
              {isSearching ? "Recherche en cours..." : "Rechercher dans le vivier"}
            </button>
            <button
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              onClick={() => {
                setSearchForm(initialSearchForm);
                setSelectedJobId("");
                setVivierResults([]);
                setHasSearched(false);
                setMessage(null);
              }}
              type="button"
            >
              Réinitialiser
            </button>
          </div>
        </form>
      </section>

      {hasSearched ? (
        <>
        {vivierResults.length > 0 ? (
          <ListSearch
            value={vivierSearchQuery}
            onChange={setVivierSearchQuery}
            placeholder="Rechercher par candidat, email, poste, secteur ou pertinence..."
          />
        ) : null}
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#24303F]">Résultats du vivier</h3>
            <p className="mt-1 text-sm text-slate-600">{filteredVivierResults.length} candidat(s) correspondant(s)</p>
          </div>
          {filteredVivierResults.length === 0 ? (
            <div className="p-5">
              <EmptyState title="Aucun candidat trouvé" description="Affinez vos critères de recherche." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3 font-semibold">Candidat</th>
                    <th className="px-5 py-3 font-semibold">Email</th>
                    <th className="px-5 py-3 font-semibold">Poste actuel</th>
                    <th className="px-5 py-3 font-semibold">Profil identifié</th>
                    <th className="px-5 py-3 font-semibold">Secteur</th>
                    <th className="px-5 py-3 font-semibold">Pertinence vivier</th>
                    <th className="px-5 py-3 font-semibold">CV</th>
                    <th className="px-5 py-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredVivierResults.map((result) => (
                    <tr key={result.candidate.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4">
                        <Link
                          className="font-semibold text-[#EE6C2F] hover:text-[#D9551B]"
                          to={`/candidates/${result.candidate.id}`}
                        >
                          {result.candidate.first_name} {result.candidate.last_name}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{result.candidate.email ?? "-"}</td>
                      <td className="px-5 py-4 text-slate-700">{result.candidate.current_title ?? "-"}</td>
                      <td className="px-5 py-4 text-slate-700">
                        {result.candidate.identified_job_profile ? (
                          <>
                            {result.candidate.identified_job_profile}
                            {typeof result.candidate.job_profile_confidence === "number" ? (
                              <span className="mt-1 block text-xs text-slate-500">
                                {Math.round(result.candidate.job_profile_confidence * 100)} %
                              </span>
                            ) : null}
                          </>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="px-5 py-4 text-slate-700">{result.candidate.sector ?? "-"}</td>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#24303F]">{Math.round(result.score)}%</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                        {result.has_cv ? "Oui" : "Non"}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <div className="flex gap-2">
                          <Link
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                            to={`/candidates/${result.candidate.id}`}
                          >
                            Voir le profil
                          </Link>
                          {result.cv_file_id ? (
                            <button
                              className="rounded-lg border border-[#EE6C2F]/30 px-3 py-1.5 text-xs font-semibold text-[#EE6C2F] hover:bg-orange-50"
                              disabled={downloadingCvId === result.cv_file_id}
                              onClick={() => void handleDownloadCV(result.cv_file_id as string, result.candidate)}
                              type="button"
                            >
                              Télécharger CV
                            </button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        </>
      ) : null}

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement des résultats de matching...
        </section>
      ) : null}

      {!isLoading && results.length === 0 ? (
        <EmptyState
          title="Aucun résultat de matching"
          description="Importez un CV ou soumettez une candidature via le portail pour générer des résultats automatiquement."
        />
      ) : null}

      {!isLoading && results.length > 0 ? (
        <ListSearch
          value={historySearchQuery}
          onChange={setHistorySearchQuery}
          placeholder="Rechercher par candidat, offre, score, recommandation ou compétence..."
        />
      ) : null}

      {results.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#24303F]">Historique des matchings</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Candidat</th>
                  <th className="px-5 py-3 font-semibold">Offre</th>
                  <th className="px-5 py-3 font-semibold">Score de Matching IA</th>
                  <th className="px-5 py-3 font-semibold">Détails</th>
                  <th className="px-5 py-3 font-semibold">Recommandation</th>
                  <th className="px-5 py-3 font-semibold">Date</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredResults.map((result) => {
                  const candidate = findCandidate(candidates, result.candidate_id);
                  const job = findJob(jobs, result.job_offer_id);
                  const displayCandidateName = result.candidate_name ?? candidateName(candidate);
                  const displayJobTitle = result.job_title ?? job?.title ?? result.job_offer_id;
                  const businessScore = getBusinessScore(result.detailed_scores);
                  const semanticScore = result.semantic_score ?? getScoreValue(result.detailed_scores, "semantic_score");
                  return (
                    <tr key={result.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{displayCandidateName}</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{displayJobTitle}</td>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#24303F]">{result.score}%</td>
                      <td className="min-w-[260px] px-5 py-4 text-xs text-slate-600">
                        <div className="flex flex-wrap gap-x-3 gap-y-1">
                          <span>Métier {formatScore(businessScore)}</span>
                          <span>Sémantique {formatScore(semanticScore)}</span>
                          <span>Compétences {formatScore(getScoreValue(result.detailed_scores, "skill_score"))}</span>
                          <span>Expérience {formatScore(getScoreValue(result.detailed_scores, "experience_score"))}</span>
                          <span>Formation {formatScore(getScoreValue(result.detailed_scores, "education_score"))}</span>
                          <span>Langues {formatScore(getScoreValue(result.detailed_scores, "language_score"))}</span>
                        </div>
                        <p className="mt-1 text-slate-500">
                          Embedding : {result.embedding_version ?? (result.used_semantic_embedding ? "text-embedding-3-small" : "Non utilisé")}
                        </p>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 capitalize text-slate-700">
                        {formatRecommendation(result.recommendation)}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                        {new Date(result.created_at).toLocaleDateString("fr-FR")}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <button
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                          onClick={() => void handleDeleteResult(result)}
                          type="button"
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {!isLoading && results.length > 0 && filteredResults.length === 0 ? (
        <EmptyState title="Aucun matching trouvé" description="Modifiez la recherche pour afficher d'autres résultats." />
      ) : null}
    </div>
  );
}
