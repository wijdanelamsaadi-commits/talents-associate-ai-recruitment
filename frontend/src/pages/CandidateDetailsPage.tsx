import { useParams } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";

const timelineRows = [
  { Date: "2026-06-10", Event: "CV uploaded", Owner: "Recruiter" },
  { Date: "2026-06-11", Event: "Profile parsed", Owner: "System" },
  { Date: "2026-06-12", Event: "Added to shortlist", Owner: "Recruiter" },
];

export function CandidateDetailsPage() {
  const { candidateId } = useParams();

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#1D6EEA]">Candidate profile</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">Sample Candidate</h2>
        <p className="mt-2 text-sm text-slate-600">Route id: {candidateId}</p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Match score" value="82%" detail="Example score for selected job" />
        <StatCard label="Experience" value="3 yrs" detail="Estimated from parsed CV text" />
        <StatCard label="Status" value="Shortlist" detail="Current recruitment pipeline stage" />
      </section>

      <DataTable title="CRM timeline" columns={["Date", "Event", "Owner"]} rows={timelineRows} />
      <EmptyState
        title="Structured CV profile placeholder"
        description="Skills, education, experience, evaluations, and attachments will be loaded from the API later."
      />
    </div>
  );
}
