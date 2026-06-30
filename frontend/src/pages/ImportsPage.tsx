import { FormEvent, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ListSearch } from "../components/ListSearch";
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
  const [searchQuery, setSearchQuery] = useState("");

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
      const [historyData, summaryData] = await Promise.all([getLinkedInImports(), getLinkedInImportSummary()]);
      setImports(historyData);
      setSummary(summaryData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger l'historique des imports."));
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
      setError("Veuillez sélectionner un fichier CSV LinkedIn.");
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Seuls les fichiers CSV sont pris en charge.");
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadLinkedInCSV(selectedFile);
      setLatestImport(result);
      setMessage(`Import terminé : ${result.imported_count} importé(s), ${result.updated_count} mis à jour, ${result.skipped_count} ignoré(s).`);
      setSelectedFile(null);
      await loadImports();
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "L'import CSV LinkedIn a échoué."));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Imports" value={String(summary.total_imports)} detail="Fichiers CSV traités" />
        <StatCard label="Importés" value={String(summary.total_imported)} detail="Nouveaux candidats créés" />
        <StatCard label="Mis à jour" value={String(summary.total_updated)} detail="Candidats existants actualisés" />
        <StatCard label="Ignorés" value={String(summary.total_skipped)} detail="Lignes sans identifiant requis" />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Import CSV LinkedIn</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Importez un export CSV LinkedIn. Les candidats sont dédupliqués par email ou URL LinkedIn et enregistrés avec la source Import LinkedIn.
            </p>
          </div>
        </div>

        <form className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end" onSubmit={handleUpload}>
          <label className="block flex-1">
            <span className="text-sm font-medium text-slate-700">Fichier CSV</span>
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
            {isUploading ? "Import en cours..." : "Importer le CSV"}
          </button>
        </form>

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        {latestImport?.report?.rows ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-[#0B1F3A]">Dernier rapport d'import</p>
            <p className="mt-1 text-sm text-slate-600">
              Lignes traitées : {latestImport.report.rows.length}. Consultez l'historique ci-dessous pour le rapport enregistré.
            </p>
          </div>
        ) : null}
      </section>

      {isLoading ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement de l'historique des imports...
        </section>
      ) : imports.length === 0 ? (
        <EmptyState title="Aucun import" description="Importez un export CSV LinkedIn pour créer ou mettre à jour des candidats." />
      ) : (
        <>
        <ListSearch value={searchQuery} onChange={setSearchQuery} placeholder="Rechercher par fichier, compteur ou date..." />
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Historique des imports</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Fichier</th>
                  <th className="px-5 py-3 font-semibold">Importés</th>
                  <th className="px-5 py-3 font-semibold">Mis à jour</th>
                  <th className="px-5 py-3 font-semibold">Ignorés</th>
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
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{new Date(importItem.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        {filteredImports.length === 0 ? (
          <EmptyState title="Aucun import trouvÃ©" description="Modifiez la recherche pour afficher d'autres imports LinkedIn." />
        ) : null}
        </>
      )}
    </div>
  );
}
