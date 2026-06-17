import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";

const interviewRows = [
  { Candidate: "Youssef Amrani", Job: "Data Analyst", Date: "2026-06-21", Status: "Scheduled" },
  { Candidate: "Nora Idrissi", Job: "HR Assistant", Date: "2026-06-24", Status: "Awaiting feedback" },
];

export function InterviewsPage() {
  return (
    <div className="space-y-6">
      <DataTable title="Interview pipeline" columns={["Candidate", "Job", "Date", "Status"]} rows={interviewRows} />
      <EmptyState
        title="Interview management placeholder"
        description="Scheduling, evaluation scorecards, and recruiter feedback will be added after API integration."
        actionLabel="Schedule interview"
      />
    </div>
  );
}
