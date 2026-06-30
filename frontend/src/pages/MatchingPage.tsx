import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ListSearch } from "../components/ListSearch";
import { StatCard } from "../components/StatCard";
import { EDUCATION_LEVELS, EXPERIENCE_LEVELS, SECTORS } from "../constants/sectors";
import { getCvDownloadUrl } from "../lib/cv";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, VivierSearchResult, getCandidates, searchCandidatesVivier } from "../services/candidates";
import { JobOffer, getJobOffers } from "../services/jobs";
import { MatchingResult, deleteMatchingResult, getMatchingResults, runMatching } from "../services/matching";

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

function DetailedScores({ scores }: { scores: MatchingResult["detailed_scores"] }) {
  if (!scores) {
    return <p className="text-sm text-slate-500">Aucun score détaillé disponible.</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {Object.entries(scores).map(([label, value]) => (
        <article key={label} className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label.replaceAll("_", " ")}</p>
          <p className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{Number(value).toFixed(0)}%</p>
        </article>
      ))}
    </div>
  );
}

export function MatchingPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [results, setResults] = useState<MatchingResult[]>([]);
  const [vivierResults, setVivierResults] = useState<VivierSearchResult[]>([]);
  const [searchForm, setSearchForm] = useState<VivierSearchForm>(initialSearchForm);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [selectedDebugJobId, setSelectedDebugJobId] = useState("");
  const [currentResult, setCurrentResult] = useState<MatchingResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vivierSearchQuery, setVivierSearchQuery] = useState("");
  const [historySearchQuery, setHistorySearchQuery] = useState("");

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [candidateData, jobData, resultData] = await Promise.all([getCandidates(), getJobOffers(), getMatchingResults()]);
      setCandidates(candidateData);
      setJobs(jobData);
      setResults(resultData);
      if (!selectedCandidateId && candidateData.length > 0) {
        setSelectedCandidateId(candidateData[0].id);
      }
      if (!selectedDebugJobId && jobData.length > 0) {
        setSelectedDebugJobId(jobData[0].id);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger le moteur de matching. Vérifiez que le backend est démarré."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const averageScore = useMemo(() => {
    if (results.length === 0) {
      return 0;
    }
    return Math.round(results.reduce((total, result) => total + result.score, 0) / results.length);
  }, [results]);

  const strongMatches = useMemo(() => results.filter((result) => result.score >= 80).length, [results]);

  const selectedCandidate = findCandidate(candidates, selectedCandidateId);
  const selectedDebugJob = findJob(jobs, selectedDebugJobId);
  const matchedSkills = skillList(currentResult?.matched_skills ?? null);
  const missingSkills = skillList(currentResult?.missing_skills ?? null);

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

  const handleRunMatching = async () => {
    setError(null);
    setMessage(null);

    if (!selectedCandidateId || !selectedDebugJobId) {
      setError("Sélectionnez un candidat et une offre avant de lancer le matching.");
      return;
    }

    setIsRunning(true);
    try {
      const result = await runMatching(selectedCandidateId, selectedDebugJobId);
      setCurrentResult(result);
      setMessage("Résultat de matching généré et enregistré.");
      const updatedResults = await getMatchingResults();
      setResults(updatedResults);
    } catch (matchingError) {
      setError(
        getApiErrorMessage(
          matchingError,
          "Le matching a échoué. Vérifiez que le candidat possède un CV parsé et que l'offre existe.",
        ),
      );
    } finally {
      setIsRunning(false);
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
      if (currentResult?.id === result.id) {
        setCurrentResult(null);
      }
      setMessage("Résultat de matching supprimé.");
      setResults(await getMatchingResults());
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Le résultat n'a pas pu être supprimé."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Score moyen" value={`${averageScore}%`} detail="Sur les résultats enregistrés" />
        <StatCard label="Fortes correspondances" value={String(strongMatches)} detail="Candidats avec un score ≥ 80%" />
        <StatCard label="Résultats enregistrés" value={String(results.length)} detail="Générés après traitement des CV" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Recherche dans le vivier</h2>
          <p className="mt-1 text-sm text-slate-600">
            Filtrez les candidats par critères métier. Avec CV : matching sur compétences, expérience, formation et
            intitulé. Sans CV : matching sur poste, secteur et entreprise.
          </p>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleVivierSearch}>
          <div className="grid gap-4 lg:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Poste (intitulé)</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                list="job-titles"
                onChange={(event) => setSearchForm((current) => ({ ...current, poste: event.target.value }))}
                placeholder="Saisie libre ou sélection depuis les offres"
                value={searchForm.poste}
              />
              <datalist id="job-titles">
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
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
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, technical_skills: event.target.value }))}
                placeholder="Python; SQL; React"
                value={searchForm.technical_skills}
              />
              <span className="mt-1 block text-xs text-slate-500">Séparées par des points-virgules</span>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Compétences comportementales</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, soft_skills: event.target.value }))}
                placeholder="Communication; Leadership"
                value={searchForm.soft_skills}
              />
              <span className="mt-1 block text-xs text-slate-500">Séparées par des points-virgules</span>
            </label>

            <label className="block lg:col-span-2">
              <span className="text-sm font-medium text-slate-700">Langues</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                onChange={(event) => setSearchForm((current) => ({ ...current, langues: event.target.value }))}
                placeholder="Français; Anglais"
                value={searchForm.langues}
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-lg bg-[#1D6EEA] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60"
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
            placeholder="Rechercher par candidat, email, poste, secteur ou score..."
          />
        ) : null}
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Résultats du vivier</h3>
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
                    <th className="px-5 py-3 font-semibold">Secteur</th>
                    <th className="px-5 py-3 font-semibold">Score</th>
                    <th className="px-5 py-3 font-semibold">CV</th>
                    <th className="px-5 py-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredVivierResults.map((result) => (
                    <tr key={result.candidate.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4">
                        <Link
                          className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]"
                          to={`/candidates/${result.candidate.id}`}
                        >
                          {result.candidate.first_name} {result.candidate.last_name}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{result.candidate.email ?? "-"}</td>
                      <td className="px-5 py-4 text-slate-700">{result.candidate.current_title ?? "-"}</td>
                      <td className="px-5 py-4 text-slate-700">{result.candidate.sector ?? "-"}</td>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{Math.round(result.score)}%</td>
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
                            <a
                              className="rounded-lg border border-[#1D6EEA]/30 px-3 py-1.5 text-xs font-semibold text-[#1D6EEA] hover:bg-blue-50"
                              download
                              href={getCvDownloadUrl(result.cv_file_id)}
                              rel="noreferrer"
                              target="_blank"
                            >
                              Télécharger CV
                            </a>
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

      <details className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-[#0B1F3A]">Actions de débogage admin</summary>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="mt-5 text-lg font-semibold text-[#0B1F3A]">Matching manuel candidat / offre</h2>
            <p className="mt-1 text-sm text-slate-600">
              Utilisez ceci uniquement pour tester ou régénérer une comparaison spécifique.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Candidat</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              disabled={isLoading || candidates.length === 0}
              onChange={(event) => setSelectedCandidateId(event.target.value)}
              value={selectedCandidateId}
            >
              {candidates.length === 0 ? <option value="">Aucun candidat disponible</option> : null}
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.first_name} {candidate.last_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Offre d&apos;emploi</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              disabled={isLoading || jobs.length === 0}
              onChange={(event) => setSelectedDebugJobId(event.target.value)}
              value={selectedDebugJobId}
            >
              {jobs.length === 0 ? <option value="">Aucune offre disponible</option> : null}
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} {job.company_name ? `- ${job.company_name}` : ""}
                </option>
              ))}
            </select>
          </label>

          <div className="flex items-end">
            <button
              className="h-10 w-full rounded-lg bg-[#1D6EEA] px-4 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
              disabled={isLoading || isRunning || !selectedCandidateId || !selectedDebugJobId}
              onClick={() => void handleRunMatching()}
              type="button"
            >
              {isRunning ? "En cours..." : "Lancer le matching"}
            </button>
          </div>
        </div>

        {selectedCandidate || selectedDebugJob ? (
          <p className="mt-4 text-sm text-slate-600">
            Sélection actuelle : <span className="font-semibold">{candidateName(selectedCandidate)}</span> pour{" "}
            <span className="font-semibold">{selectedDebugJob?.title ?? "aucune offre"}</span>.
          </p>
        ) : null}
      </details>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {currentResult ? (
        <section className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-[#0B1F3A]">Dernier résultat de matching</h3>
              <p className="mt-1 text-sm text-slate-600">{currentResult.explanation ?? "Aucune explication fournie."}</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-semibold text-[#0B1F3A]">{currentResult.score}%</p>
              <p className="text-sm font-semibold capitalize text-[#1D6EEA]">
                {formatRecommendation(currentResult.recommendation)}
              </p>
            </div>
          </div>

          <DetailedScores scores={currentResult.detailed_scores} />

          <div className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm font-semibold text-[#0B1F3A]">Compétences correspondantes</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {matchedSkills.length > 0 ? (
                  matchedSkills.map((skill) => (
                    <span key={skill} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">Aucune compétence correspondante détectée.</span>
                )}
              </div>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm font-semibold text-[#0B1F3A]">Compétences manquantes</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {missingSkills.length > 0 ? (
                  missingSkills.map((skill) => (
                    <span key={skill} className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">Aucune compétence manquante détectée.</span>
                )}
              </div>
            </article>
          </div>
        </section>
      ) : null}

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
          placeholder="Rechercher par candidat, offre, score, recommandation ou compÃ©tence..."
        />
      ) : null}

      {results.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Historique des matchings</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Candidat</th>
                  <th className="px-5 py-3 font-semibold">Offre</th>
                  <th className="px-5 py-3 font-semibold">Score</th>
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
                  return (
                    <tr key={result.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{displayCandidateName}</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{displayJobTitle}</td>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{result.score}%</td>
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
        <EmptyState title="Aucun matching trouvÃ©" description="Modifiez la recherche pour afficher d'autres rÃ©sultats." />
      ) : null}
    </div>
  );
}
