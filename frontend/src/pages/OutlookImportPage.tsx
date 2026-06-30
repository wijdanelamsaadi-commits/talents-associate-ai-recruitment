import { FormEvent, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ListSearch } from "../components/ListSearch";
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

function formatImportStatus(status: unknown) {
  const labels: Record<string, string> = {
    imported: "Importé",
    updated: "Mis à jour",
    skipped: "Ignoré",
    failed: "Échec",
    processed: "Traité",
  };
  return labels[String(status ?? "processed")] ?? String(status ?? "Traité");
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
  const [searchQuery, setSearchQuery] = useState("");

  const selectedFileNames = useMemo(
    () => selectedFiles.map((file) => file.name).join(", "),
    [selectedFiles],
  );

  const filteredImports = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return imports;
    }
    return imports.filter((importItem) =>
      [
        importItem.filename,
        importItem.imported_count,
        importItem.updated_count,
        importItem.skipped_count,
        importItem.failed_count,
        new Date(importItem.created_at).toLocaleString(),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [imports, searchQuery]);

  const loadImports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [historyData, summaryData] = await Promise.all([getOutlookImports(), getOutlookImportSummary()]);
      setImports(historyData);
      setSummary(summaryData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger l'historique des imports de CV."));
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
      setError("Veuillez sélectionner une archive ZIP ou un ou plusieurs CV PDF/DOCX.");
      return;
    }

    const invalidFile = selectedFiles.find((file) => !/\.(zip|pdf|docx)$/i.test(file.name));
    if (invalidFile) {
      setError(`${invalidFile.name} n'est pas pris en charge. Importez des fichiers ZIP, PDF ou DOCX.`);
      return;
    }

    setIsUploading(true);
    setMessage("Import des CV en cours...");
    try {
      setMessage("Analyse des CV et matching IA en cours...");
      const result = await uploadOutlookCVs(selectedFiles);
      setLatestImport(result);
      setMessage(
        `Import terminé : ${result.imported_count} importé(s), ${result.updated_count} mis à jour, ${result.skipped_count} ignoré(s), ${result.failed_count} en échec.`,
      );
      setSelectedFiles([]);
      await loadImports();
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "L'import des CV a échoué."));
      setMessage(null);
    } finally {
      setIsUploading(false);
    }
  };

  const latestFiles = getFilesReport(latestImport);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-5">
        <StatCard label="Imports" value={String(summary.total_imports)} detail="Lots de CV traités" />
        <StatCard label="Importés" value={String(summary.total_imported)} detail="Nouveaux candidats créés" />
        <StatCard label="Mis à jour" value={String(summary.total_updated)} detail="Candidats existants actualisés" />
        <StatCard label="Ignorés" value={String(summary.total_skipped)} detail="Fichiers non pris en charge ou trop volumineux" />
        <StatCard label="Échecs" value={String(summary.total_failed)} detail="Fichiers à vérifier" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Import local de CV</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Importez une archive ZIP ou plusieurs fichiers PDF/DOCX. La plateforme extrait le texte, analyse les CV, crée ou met à jour les candidats et lance le matching IA automatiquement.
            </p>
          </div>
          <SourceBadge source="cv_upload" />
        </div>

        <form className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end" onSubmit={handleUpload}>
          <label className="block flex-1">
            <span className="text-sm font-medium text-slate-700">Fichiers ZIP, PDF ou DOCX</span>
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
            {isUploading ? "Traitement en cours..." : "Importer les CV"}
          </button>
        </form>

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        {latestFiles.length > 0 ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-[#0B1F3A]">Dernier rapport d'import</p>
            <div className="mt-3 max-h-56 overflow-y-auto rounded-lg border border-slate-200 bg-white">
              {latestFiles.map((file, index) => (
                <div className="grid gap-2 border-b border-slate-100 px-4 py-3 text-sm last:border-b-0 md:grid-cols-[1fr_auto_auto]" key={`${String(file.file)}-${index}`}>
                  <span className="font-medium text-[#0B1F3A]">{String(file.file ?? "Fichier CV")}</span>
                  <span className="capitalize text-slate-700">{formatImportStatus(file.status)}</span>
                  <span className="text-slate-500">{file.reason ? String(file.reason) : `${String(file.matching_results ?? 0)} résultat(s) de matching IA`}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement de l'historique des imports de CV...
        </section>
      ) : imports.length === 0 ? (
        <EmptyState title="Aucun import de CV" description="Importez des CV pour créer ou mettre à jour les candidats et lancer le matching IA automatiquement." />
      ) : (
        <>
        <ListSearch value={searchQuery} onChange={setSearchQuery} placeholder="Rechercher par lot, compteur ou date..." />
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Historique des imports de CV</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Lot</th>
                  <th className="px-5 py-3 font-semibold">Importés</th>
                  <th className="px-5 py-3 font-semibold">Mis à jour</th>
                  <th className="px-5 py-3 font-semibold">Ignorés</th>
                  <th className="px-5 py-3 font-semibold">Échecs</th>
                  <th className="px-5 py-3 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredImports.map((importItem) => (
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
        {filteredImports.length === 0 ? (
          <EmptyState title="Aucun import de CV trouvÃ©" description="Modifiez la recherche pour afficher d'autres lots." />
        ) : null}
        </>
      )}
    </div>
  );
}
