import { Link } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";

const candidateRows = [
  { Name: "Sara Benali", Email: "sara.benali@example.com", Skills: "React, TypeScript", Status: "New" },
  { Name: "Youssef Amrani", Email: "youssef.amrani@example.com", Skills: "SQL, Power BI", Status: "Interviewing" },
  { Name: "Nora Idrissi", Email: "nora.idrissi@example.com", Skills: "HR, CRM", Status: "Shortlisted" },
];

export function CandidatesPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total candidates" value="128" detail="Profiles in the database" />
        <StatCard label="New this week" value="16" detail="Uploaded or imported profiles" />
        <StatCard label="Awaiting review" value="21" detail="Candidates needing recruiter action" />
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-[#0B1F3A]">Candidate database</h2>
        <Link
          to="/candidates/demo"
          className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
        >
          View sample profile
        </Link>
      </div>

      <DataTable title="Candidates list" columns={["Name", "Email", "Skills", "Status"]} rows={candidateRows} />
      <EmptyState
        title="LinkedIn CSV import placeholder"
        description="Bulk import and enrichment screens will be added after the backend modules are ready."
      />
    </div>
  );
}
