import { DataTable } from "../components/DataTable";
import { StatCard } from "../components/StatCard";

const activityRows = [
  { Candidate: "Sara Benali", Stage: "Parsed CV", Role: "Frontend Developer", Status: "Ready for match" },
  { Candidate: "Youssef Amrani", Stage: "Interview", Role: "Data Analyst", Status: "Evaluation pending" },
  { Candidate: "Nora Idrissi", Stage: "Shortlist", Role: "HR Assistant", Status: "Recommended" },
];

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Candidates" value="128" detail="Centralized profiles ready for review" />
        <StatCard label="CVs parsed" value="74" detail="Extracted text and structured data" />
        <StatCard label="Open jobs" value="12" detail="Active recruitment campaigns" />
        <StatCard label="Interviews" value="18" detail="Scheduled or awaiting feedback" />
      </section>

      <DataTable
        title="Recent recruitment activity"
        columns={["Candidate", "Stage", "Role", "Status"]}
        rows={activityRows}
      />
    </div>
  );
}
