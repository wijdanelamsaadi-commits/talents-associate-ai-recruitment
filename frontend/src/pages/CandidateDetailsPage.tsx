import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidateById } from "../services/candidates";

const timelineRows = [
  { Date: "2026-06-10", Event: "CV uploaded", Owner: "Recruiter" },
  { Date: "2026-06-11", Event: "Profile parsed", Owner: "System" },
  { Date: "2026-06-12", Event: "Added to shortlist", Owner: "Recruiter" },
];

export function CandidateDetailsPage() {
  const { candidateId } = useParams();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCandidate() {
      if (!candidateId) {
        setError("Candidate id is missing.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await getCandidateById(candidateId);
        setCandidate(data);
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Unable to load candidate details. Check the candidate ID and backend connection."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadCandidate();
  }, [candidateId]);

  if (isLoading) {
    return <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">Loading candidate...</section>;
  }

  if (error || !candidate) {
    return (
      <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p>{error ?? "Candidate not found."}</p>
        <Link className="mt-4 inline-block font-semibold text-red-800 underline" to="/candidates">
          Back to candidates
        </Link>
      </section>
    );
  }

  const fullName = `${candidate.first_name} ${candidate.last_name}`;
  const timelineRowsWithCandidate = [
    { Date: new Date(candidate.created_at).toLocaleDateString(), Event: "Candidate created", Owner: candidate.source },
    ...timelineRows,
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#1D6EEA]">Candidate profile</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{fullName}</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
          <p>
            <span className="block font-semibold text-slate-500">Email</span>
            {candidate.email ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Phone</span>
            {candidate.phone ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">City</span>
            {candidate.location ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Source</span>
            {candidate.source.replaceAll("_", " ")}
          </p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Status" value={candidate.status.replaceAll("_", " ")} detail="Current recruitment pipeline stage" />
        <StatCard label="Created" value={new Date(candidate.created_at).toLocaleDateString()} detail="Backend creation date" />
        <StatCard label="Updated" value={new Date(candidate.updated_at).toLocaleDateString()} detail="Latest profile update" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          title="CV placeholder"
          description="Uploaded CV files and extracted text will appear here after frontend CV integration."
        />
        <EmptyState
          title="Skills placeholder"
          description="Parsed skills and candidate skill tags will appear here after profile enrichment."
        />
        <EmptyState
          title="Matching placeholder"
          description="Saved matching results and recommendations will appear here after matching integration."
        />
        <EmptyState
          title="History placeholder"
          description="Recruiter notes, status changes, and CRM events will appear here after timeline integration."
        />
      </section>

      <DataTable title="CRM timeline" columns={["Date", "Event", "Owner"]} rows={timelineRowsWithCandidate} />
      <EmptyState
        title="Candidate evaluations placeholder"
        description="Interview evaluations and scorecards will be connected in a later frontend step."
      />
    </div>
  );
}
