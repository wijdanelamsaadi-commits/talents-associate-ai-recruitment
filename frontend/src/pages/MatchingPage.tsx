import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";

const matchRows = [
  { Candidate: "Sara Benali", Job: "Frontend Developer", Score: "88", Recommendation: "Strong match" },
  { Candidate: "Youssef Amrani", Job: "Data Analyst", Score: "76", Recommendation: "Good match" },
  { Candidate: "Nora Idrissi", Job: "HR Assistant", Score: "69", Recommendation: "Average match" },
];

export function MatchingPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Average score" value="78%" detail="Across latest matching results" />
        <StatCard label="Strong matches" value="9" detail="Candidates above shortlist threshold" />
        <StatCard label="Missing skills" value="24" detail="Detected across active jobs" />
      </section>

      <DataTable
        title="Matching results"
        columns={["Candidate", "Job", "Score", "Recommendation"]}
        rows={matchRows}
      />
      <EmptyState
        title="Run matching placeholder"
        description="Candidate and job selectors will call the matching endpoint during the integration phase."
        actionLabel="Run sample match"
      />
    </div>
  );
}
