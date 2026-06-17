import { EmptyState } from "../components/EmptyState";

const uploadSteps = ["Select PDF or DOCX", "Extract raw text", "Run heuristic parser", "Review candidate profile"];

export function CVUploadPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-[#0B1F3A]">Upload candidate CV</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This placeholder mirrors the backend upload flow without sending files yet.
        </p>
        <div className="mt-6 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">
          <p className="text-sm font-semibold text-[#0B1F3A]">Drop CV file here</p>
          <p className="mt-2 text-sm text-slate-500">PDF and DOCX support is available in the backend API.</p>
          <button className="mt-5 rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]">
            Choose file
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {uploadSteps.map((step, index) => (
          <article key={step} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold text-[#1D6EEA]">Step {index + 1}</p>
            <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{step}</p>
          </article>
        ))}
      </section>

      <EmptyState
        title="No recent frontend uploads"
        description="The API endpoint is ready, and this screen will be connected during the integration phase."
      />
    </div>
  );
}
