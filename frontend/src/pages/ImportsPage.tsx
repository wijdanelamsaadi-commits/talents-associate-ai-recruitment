import { FormEvent, useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { LinkedInImport, LinkedInImportSummary, getLinkedInImportSummary, getLinkedInImports, uploadLinkedInCSV } from "../services/imports";

const emptySummary: LinkedInImportSummary = {
  total_imports: 0,
  total_imported: 0,
  total_updated: 0,
  total_skipped: 0,
};

export function ImportsPage() {
  const [imports, setImports] = useState<LinkedInImport[]>([]);
  const [summary, setSummary] = useState<LinkedInImportSummary>(emptySummary);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [latestImport, setLatestImport] = useState<LinkedInImport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadImports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [historyData, summaryData] = await Promise.all([getLinkedInImports(), getLinkedInImportSummary()]);
      setImports(historyData);
      setSummary(summaryData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load import history."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadImports();
  }, []);

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLatestImport(null);

    if (!selectedFile) {
      setError("Select a LinkedIn CSV file first.");
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files are supported.");
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadLinkedInCSV(selectedFile);
      setLatestImport(result);
      setMessage(`Import completed: ${result.imported_count} imported, ${result.updated_count} updated, ${result.skipped_count} skipped.`);
      setSelectedFile(null);
      await loadImports();
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "LinkedIn CSV import failed."));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Imports" value={String(summary.total_imports)} detail="CSV files processed" />
        <StatCard label="Imported" value={String(summary.total_imported)} detail="New candidates created" />
        <StatCard label="Updated" value={String(summary.total_updated)} detail="Existing candidates refreshed" />
        <StatCard label="Skipped" value={String(summary.total_skipped)} detail="Rows missing required identifiers" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">LinkedIn CSV import</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Upload a LinkedIn export CSV. Candidates are deduplicated by email or LinkedIn URL and saved with source linkedin_csv.
            </p>
          </div>
        </div>

        <form className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end" onSubmit={handleUpload}>
          <label className="block flex-1">
            <span className="text-sm font-medium text-slate-700">CSV file</span>
            <input
              accept=".csv,text/csv"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#1D6EEA]/10 file:px-3 file:py-1 file:text-sm file:font-semibold file:text-[#1D6EEA]"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              type="file"
            />
          </label>
          <button
            className="rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isUploading}
            type="submit"
          >
            {isUploading ? "Importing..." : "Upload CSV"}
          </button>
        </form>

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        {latestImport?.report?.rows ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-[#0B1F3A]">Latest import report</p>
            <p className="mt-1 text-sm text-slate-600">
              Rows processed: {latestImport.report.rows.length}. Review import history below for the persisted report.
            </p>
          </div>
        ) : null}
      </section>

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading import history...
        </section>
      ) : imports.length === 0 ? (
        <EmptyState title="No imports yet" description="Upload a LinkedIn CSV export to create or update candidates." />
      ) : (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Import history</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">File</th>
                  <th className="px-5 py-3 font-semibold">Imported</th>
                  <th className="px-5 py-3 font-semibold">Updated</th>
                  <th className="px-5 py-3 font-semibold">Skipped</th>
                  <th className="px-5 py-3 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {imports.map((importItem) => (
                  <tr className="hover:bg-slate-50" key={importItem.id}>
                    <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{importItem.filename}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{importItem.imported_count}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{importItem.updated_count}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{importItem.skipped_count}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{new Date(importItem.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
