import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";

const jobRows = [
  { Title: "Frontend Developer", Company: "Talents Associate", Location: "Casablanca", Status: "Open" },
  { Title: "Data Analyst", Company: "Client Partner", Location: "Remote", Status: "Open" },
  { Title: "HR Assistant", Company: "Client Partner", Location: "Rabat", Status: "Draft" },
];

export function JobOffersPage() {
  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0B1F3A]">Job offers</h2>
          <p className="mt-1 text-sm text-slate-600">Manage roles used by the matching engine.</p>
        </div>
        <button className="rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]">
          New job offer
        </button>
      </section>

      <DataTable title="Open roles" columns={["Title", "Company", "Location", "Status"]} rows={jobRows} />
      <EmptyState
        title="Job form placeholder"
        description="Create, edit, and delete actions will be wired to the FastAPI job offer endpoints later."
      />
    </div>
  );
}
