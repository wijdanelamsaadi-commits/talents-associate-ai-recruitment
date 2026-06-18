import { FormEvent, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { SourceBadge } from "../components/SourceBadge";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import {
  OutlookImport,
  OutlookImportSummary,
  getOutlookImportSummary,
  getOutlookImports,
  uploadOutlookCVs,
} from "../services/imports";

const emptySummary: OutlookImportSummary = {
  total_imports: 0,
  total_imported: 0,
  total_updated: 0,
  total_skipped: 0,
  total_failed: 0,
};

function getFilesReport(importItem: OutlookImport | null) {
  const files = importItem?.report?.files;
  return Array.isArray(files) ? files : [];
}

export function OutlookImportPage() {
  const [imports, setImports] = useState<OutlookImport[]>([]);
  const [summary, setSummary] = useState<OutlookImportSummary>(emptySummary);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [latestImport, setLatestImport] = useState<OutlookImport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedFileNames = useMemo(
    () => selectedFiles.map((file) => file.name).join(", "),
    [selectedFiles],
  );

  const loadImports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [historyData, summaryData] = await Promise.all([getOutlookImports(), getOutlookImportSummary()]);
      setImports(historyData);
      setSummary(summaryData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Unable to load Outlook import history."));
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

    if (selectedFiles.length === 0) {
      setError("Select a ZIP archive or one or more PDF/DOCX CV files first.");
      return;
    }

    const invalidFile = selectedFiles.find((file) => !/\.(zip|pdf|docx)$/i.test(file.name));
    if (invalidFile) {
      setError(`${invalidFile.name} is not supported. Upload ZIP, PDF, or DOCX files.`);
      return;
    }

    setIsUploading(true);
    setMessage("Uploading Outlook CVs...");
    try {
      setMessage("Parsing CVs and running automatic matching...");
      const result = await uploadOutlookCVs(selectedFiles);
      setLatestImport(result);
      setMessage(
        `Import completed: ${result.imported_count} imported, ${result.updated_count} updated, ${result.skipped_count} skipped, ${result.failed_count} failed.`,
      );
      setSelectedFiles([]);
      await loadImports();
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Outlook CV import failed."));
      setMessage(null);
    } finally {
      setIsUploading(false);
    }
  };

  const latestFiles = getFilesReport(latestImport);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-5">
        <StatCard label="Imports" value={String(summary.total_imports)} detail="Outlook batches processed" />
        <StatCard label="Imported" value={String(summary.total_imported)} detail="New candidates created" />
        <StatCard label="Updated" value={String(summary.total_updated)} detail="Existing candidates refreshed" />
        <StatCard label="Skipped" value={String(summary.total_skipped)} detail="Unsupported or oversized files" />
        <StatCard label="Failed" value={String(summary.total_failed)} detail="Files needing review" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Outlook CV import</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Import CV attachments saved locally by the Outlook VBA macro. Upload one ZIP archive or multiple PDF/DOCX files; the platform extracts, parses, creates candidates, and runs matching automatically.
            </p>
          </div>
          <SourceBadge source="outlook_import" />
        </div>

        <form className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end" onSubmit={handleUpload}>
          <label className="block flex-1">
            <span className="text-sm font-medium text-slate-700">ZIP, PDF, or DOCX files</span>
            <input
              accept=".zip,.pdf,.docx,application/zip,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#1D6EEA]/10 file:px-3 file:py-1 file:text-sm file:font-semibold file:text-[#1D6EEA]"
              multiple
              onChange={(event) => setSelectedFiles(Array.from(event.target.files ?? []))}
              type="file"
            />
            {selectedFileNames ? <span className="mt-2 block truncate text-xs text-slate-500">{selectedFileNames}</span> : null}
          </label>
          <button
            className="rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isUploading}
            type="submit"
          >
            {isUploading ? "Processing..." : "Import Outlook CVs"}
          </button>
        </form>

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        {latestFiles.length > 0 ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-[#0B1F3A]">Latest import report</p>
            <div className="mt-3 max-h-56 overflow-y-auto rounded-lg border border-slate-200 bg-white">
              {latestFiles.map((file, index) => (
                <div className="grid gap-2 border-b border-slate-100 px-4 py-3 text-sm last:border-b-0 md:grid-cols-[1fr_auto_auto]" key={`${String(file.file)}-${index}`}>
                  <span className="font-medium text-[#0B1F3A]">{String(file.file ?? "CV file")}</span>
                  <span className="capitalize text-slate-700">{String(file.status ?? "processed")}</span>
                  <span className="text-slate-500">{file.reason ? String(file.reason) : `${String(file.matching_results ?? 0)} matches`}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading Outlook import history...
        </section>
      ) : imports.length === 0 ? (
        <EmptyState title="No Outlook imports yet" description="Upload Outlook CV attachments to create and match candidates automatically." />
      ) : (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Outlook import history</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Batch</th>
                  <th className="px-5 py-3 font-semibold">Imported</th>
                  <th className="px-5 py-3 font-semibold">Updated</th>
                  <th className="px-5 py-3 font-semibold">Skipped</th>
                  <th className="px-5 py-3 font-semibold">Failed</th>
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
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{importItem.failed_count}</td>
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
