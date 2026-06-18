import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidates } from "../services/candidates";
import { JobOffer, getJobOffers } from "../services/jobs";
import { MatchingResult, deleteMatchingResult, getMatchingResults, runMatching } from "../services/matching";

function findCandidate(candidates: Candidate[], candidateId: string) {
  return candidates.find((candidate) => candidate.id === candidateId);
}

function findJob(jobs: JobOffer[], jobId: string) {
  return jobs.find((job) => job.id === jobId);
}

function candidateName(candidate?: Candidate) {
  return candidate ? `${candidate.first_name} ${candidate.last_name}` : "Unknown candidate";
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
  return value ? value.replaceAll("_", " ") : "No recommendation";
}

function DetailedScores({ scores }: { scores: MatchingResult["detailed_scores"] }) {
  if (!scores) {
    return <p className="text-sm text-slate-500">No detailed scores available.</p>;
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
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [currentResult, setCurrentResult] = useState<MatchingResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      if (!selectedJobId && jobData.length > 0) {
        setSelectedJobId(jobData[0].id);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load matching workspace. Check that the backend is running on localhost:8001."));
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
  const selectedJob = findJob(jobs, selectedJobId);
  const matchedSkills = skillList(currentResult?.matched_skills ?? null);
  const missingSkills = skillList(currentResult?.missing_skills ?? null);

  const handleRunMatching = async () => {
    setError(null);
    setMessage(null);

    if (!selectedCandidateId || !selectedJobId) {
      setError("Select both a candidate and a job offer before running matching.");
      return;
    }

    setIsRunning(true);
    try {
      const result = await runMatching(selectedCandidateId, selectedJobId);
      setCurrentResult(result);
      setMessage("Matching result generated and saved.");
      const updatedResults = await getMatchingResults();
      setResults(updatedResults);
    } catch (matchingError) {
      setError(
        getApiErrorMessage(
          matchingError,
          "Matching failed. Make sure the candidate has a parsed CV and the selected job offer exists.",
        ),
      );
    } finally {
      setIsRunning(false);
    }
  };

  const handleDeleteResult = async (result: MatchingResult) => {
    const shouldDelete = window.confirm(`Delete matching result with score ${result.score}%?`);
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
      setMessage("Matching result deleted.");
      setResults(await getMatchingResults());
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Matching result could not be deleted."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Average score" value={`${averageScore}%`} detail="Across saved matching results" />
        <StatCard label="Strong matches" value={String(strongMatches)} detail="Candidates scoring 80% or higher" />
        <StatCard label="Saved results" value={String(results.length)} detail="Created automatically after CV processing" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Automatic matching results</h2>
            <p className="mt-1 text-sm text-slate-600">
              Matching is generated automatically after recruiter CV upload or candidate portal application.
            </p>
          </div>
          <div className="flex gap-3 text-sm font-semibold">
            <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/cv-upload">
              Upload CV
            </Link>
            <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/jobs">
              Manage jobs
            </Link>
          </div>
        </div>
      </section>

      <details className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-[#0B1F3A]">Admin debugging actions</summary>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="mt-5 text-lg font-semibold text-[#0B1F3A]">Manual candidate matching</h2>
            <p className="mt-1 text-sm text-slate-600">
              Use this only to troubleshoot or regenerate a specific candidate/job comparison. Normal matching runs automatically.
            </p>
          </div>
          <div className="flex gap-3 text-sm font-semibold">
            <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/cv-upload">
              Upload CV
            </Link>
            <Link className="text-[#1D6EEA] hover:text-[#165AC0]" to="/jobs">
              Manage jobs
            </Link>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Candidate</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              disabled={isLoading || candidates.length === 0}
              onChange={(event) => setSelectedCandidateId(event.target.value)}
              value={selectedCandidateId}
            >
              {candidates.length === 0 ? <option value="">No candidates available</option> : null}
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.first_name} {candidate.last_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Job offer</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              disabled={isLoading || jobs.length === 0}
              onChange={(event) => setSelectedJobId(event.target.value)}
              value={selectedJobId}
            >
              {jobs.length === 0 ? <option value="">No jobs available</option> : null}
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
              disabled={isLoading || isRunning || !selectedCandidateId || !selectedJobId}
              onClick={() => void handleRunMatching()}
              type="button"
            >
              {isRunning ? "Running..." : "Run matching"}
            </button>
          </div>
        </div>

        {selectedCandidate || selectedJob ? (
          <p className="mt-4 text-sm text-slate-600">
            Current selection: <span className="font-semibold">{candidateName(selectedCandidate)}</span> for{" "}
            <span className="font-semibold">{selectedJob?.title ?? "no job selected"}</span>.
          </p>
        ) : null}
      </details>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {currentResult ? (
        <section className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-[#0B1F3A]">Latest matching result</h3>
              <p className="mt-1 text-sm text-slate-600">{currentResult.explanation ?? "No explanation provided."}</p>
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
              <p className="text-sm font-semibold text-[#0B1F3A]">Matched skills</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {matchedSkills.length > 0 ? (
                  matchedSkills.map((skill) => (
                    <span key={skill} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">No matched skills detected.</span>
                )}
              </div>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-sm font-semibold text-[#0B1F3A]">Missing skills</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {missingSkills.length > 0 ? (
                  missingSkills.map((skill) => (
                    <span key={skill} className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">No missing skills detected.</span>
                )}
              </div>
            </article>
          </div>
        </section>
      ) : null}

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading matching results...
        </section>
      ) : null}

      {!isLoading && results.length === 0 ? (
        <EmptyState
          title="No matching results yet"
          description="Upload a CV or submit a portal application to generate matching results automatically."
        />
      ) : null}

      {results.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Previous matching results</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Candidate</th>
                  <th className="px-5 py-3 font-semibold">Job</th>
                  <th className="px-5 py-3 font-semibold">Score</th>
                  <th className="px-5 py-3 font-semibold">Recommendation</th>
                  <th className="px-5 py-3 font-semibold">Created</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((result) => {
                  const candidate = findCandidate(candidates, result.candidate_id);
                  const job = findJob(jobs, result.job_offer_id);
                  return (
                    <tr key={result.id} className="hover:bg-slate-50">
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{candidateName(candidate)}</td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{job?.title ?? result.job_offer_id}</td>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{result.score}%</td>
                      <td className="whitespace-nowrap px-5 py-4 capitalize text-slate-700">
                        {formatRecommendation(result.recommendation)}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                        {new Date(result.created_at).toLocaleDateString()}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <button
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                          onClick={() => void handleDeleteResult(result)}
                          type="button"
                        >
                          Delete
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
    </div>
  );
}
