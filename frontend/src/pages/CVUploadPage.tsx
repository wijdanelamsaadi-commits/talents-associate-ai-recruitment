import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ListSearch } from "../components/ListSearch";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidates } from "../services/candidates";
import { CVFile, ExtractedCVText, ParsedCV, getCVFiles, getCVText, parseCV, uploadBatchCVs, uploadCV } from "../services/cv";

const allowedExtensions = [".pdf", ".doc", ".docx", ".zip"];
const maxFileSizeBytes = 5 * 1024 * 1024;
type ProcessingStage = "idle" | "uploading" | "parsing" | "matching" | "completed";

function formatBytes(bytes: number | null) {
  if (!bytes) {
    return "-";
  }
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getParserResultLabel(parserModel: string | null | undefined) {
  if (parserModel?.startsWith("openai:")) {
    return `Résultat du parser IA (${parserModel})`;
  }
  if (parserModel === "heuristic-v1") {
    return "Résultat du parser heuristique";
  }
  return parserModel ? `Résultat du parser (${parserModel})` : "Résultat du parser";
}

function formatParsingStatus(status: string | null | undefined) {
  const labels: Record<string, string> = {
    pending: "En attente",
    processing: "En cours",
    parsing: "Analyse du CV",
    completed: "Terminé",
    parsed: "Analysé",
    failed: "Échec",
    uploaded: "Importé",
    duplicate: "Doublon",
  };
  return labels[status || ""] ?? (status ? status.replaceAll("_", " ") : "-");
}

function renderListValue(value: unknown[] | undefined) {
  if (!value || value.length === 0) {
    return <span className="text-slate-400">Information non disponible dans le CV</span>;
  }

  return (
    <ul className="space-y-2">
      {value.map((item, index) => (
        <li key={index} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {typeof item === "string" ? item : JSON.stringify(item)}
        </li>
      ))}
    </ul>
  );
}

export function CVUploadPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [cvFiles, setCVFiles] = useState<CVFile[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCVId, setSelectedCVId] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState<ExtractedCVText | null>(null);
  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null);
  const [isLoadingPage, setIsLoadingPage] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isTextLoading, setIsTextLoading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [processingStage, setProcessingStage] = useState<ProcessingStage>("idle");
  const [matchingCount, setMatchingCount] = useState<number | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const selectedCandidate = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedCandidateId),
    [candidates, selectedCandidateId],
  );

  const filteredCVFiles = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return cvFiles;
    }
    return cvFiles.filter((cvFile) => {
      const candidate = candidates.find((item) => item.id === cvFile.candidate_id);
      return [
        cvFile.original_filename,
        cvFile.mime_type,
        formatParsingStatus(cvFile.parsing_status),
        candidate?.first_name,
        candidate?.last_name,
        candidate?.email,
        candidate?.phone,
        candidate?.current_title,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [candidates, cvFiles, searchQuery]);

  const loadPageData = async () => {
    setIsLoadingPage(true);
    setError(null);
    try {
      const [candidateData, cvFileData] = await Promise.all([getCandidates(), getCVFiles()]);
      setCandidates(candidateData);
      setCVFiles(cvFileData);
      if (!selectedCandidateId && candidateData.length > 0) {
        setSelectedCandidateId(candidateData[0].id);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger les candidats ou les fichiers CV. Vérifiez que le backend FastAPI est démarré."));
    } finally {
      setIsLoadingPage(false);
    }
  };

  useEffect(() => {
    void loadPageData();
  }, []);

  const validateFile = (file: File | null) => {
    if (!file) {
      return "Sélectionnez un fichier CV PDF, DOC, DOCX ou ZIP.";
    }
    const lowerName = file.name.toLowerCase();
    if (!allowedExtensions.some((extension) => lowerName.endsWith(extension))) {
      return "Format non pris en charge. Importez un fichier PDF, DOC, DOCX ou ZIP.";
    }
    if (!lowerName.endsWith(".zip") && file.size > maxFileSizeBytes) {
      return "Le fichier dépasse 5 Mo. Le backend refusera les fichiers CV trop volumineux.";
    }
    return null;
  };

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setWarning(null);
    setMessage(null);
    setExtractedText(null);
    setParsedCV(null);
    setMatchingCount(null);

    if (!selectedFile) {
      setError("Veuillez sélectionner un fichier à importer.");
      return;
    }
    const isZip = selectedFile.name.toLowerCase().endsWith(".zip");

    const fileError = validateFile(selectedFile);
    if (fileError) {
      setError(fileError);
      return;
    }

    setIsUploading(true);
    setProcessingStage("uploading");
    setUploadProgress(0);
    try {
      if (isZip) {
        const result = await uploadBatchCVs(selectedFile as File, (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        });
        const duplicateCount = result.results.filter((item) => item.status === "duplicate").length;
        setProcessingStage("completed");
        if (duplicateCount > 0) {
          setWarning(
            `Import ZIP terminé avec ${duplicateCount} doublon(s) ignoré(s). Ce CV existe déjà dans la base de données.`,
          );
        }
        setMessage(`Import ZIP terminé. ${result.success_count} succès, ${result.error_count} erreur(s). Total analysé : ${result.total}.`);
        setSelectedFile(null);
        await loadPageData();
      } else {
        const uploaded = await uploadCV(undefined, selectedFile as File, (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
            if (progress >= 100) {
              setProcessingStage("parsing");
            }
          }
        });
        setProcessingStage("matching");
        setSelectedCVId(uploaded.id);
        setParsedCV({
          cv_file_id: uploaded.id,
          parsing_status: uploaded.processing_status,
          confidence_score: uploaded.confidence_score,
          parser_model: uploaded.parser_model,
          structured_json: uploaded.structured_json,
        });
        setMatchingCount(uploaded.matching_result_ids.length);
        if (uploaded.duplicate) {
          setProcessingStage("completed");
          setWarning(uploaded.message ?? "Ce CV existe déjà dans la base de données.");
          setSelectedFile(null);
          await loadPageData();
          await handleViewText(uploaded.id, { preserveNotice: true });
          return;
        }
        setMessage(
          uploaded.updated_existing
            ? `${uploaded.original_filename} mis à jour. L'analyse du CV et le matching IA ont été relancés.`
            : `${uploaded.original_filename} importé. Extraction du texte, analyse du CV, mise à jour du profil et matching IA terminés.`,
        );
        setSelectedFile(null);
        await loadPageData();
        await handleViewText(uploaded.id);
        setProcessingStage("completed");
        setMessage(
          uploaded.updated_existing
            ? `${uploaded.original_filename} mis à jour. Analyse du CV et ${uploaded.matching_result_ids.length} résultat(s) de matching IA actualisé(s).`
            : `${uploaded.original_filename} importé. Extraction du texte, analyse du CV, mise à jour du profil et ${uploaded.matching_result_ids.length} résultat(s) de matching IA terminé(s).`,
        );
      }
    } catch (uploadError) {
      setProcessingStage("idle");
      setError(getApiErrorMessage(uploadError, "L'import du CV a échoué. Vérifiez le format, la taille du fichier et le candidat."));
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleViewText = async (cvFileId: string, options?: { preserveNotice?: boolean }) => {
    setError(null);
    if (!options?.preserveNotice) {
      setMessage(null);
      setWarning(null);
    }
    setSelectedCVId(cvFileId);
    setParsedCV(null);
    setIsTextLoading(true);
    try {
      const data = await getCVText(cvFileId);
      setExtractedText(data);
      if (data.ai_output) {
        setParsedCV({
          cv_file_id: data.cv_file_id,
          parsing_status: data.parsing_status,
          confidence_score: data.confidence_score,
          parser_model: data.parser_model,
          structured_json: data.ai_output,
        });
      }
      if (!options?.preserveNotice) {
        setMessage("Texte extrait chargé.");
      }
    } catch (textError) {
      setExtractedText(null);
      setError(getApiErrorMessage(textError, "Impossible de charger le texte extrait pour ce CV."));
    } finally {
      setIsTextLoading(false);
    }
  };

  const handleParse = async (cvFileId: string) => {
    setError(null);
    setWarning(null);
    setMessage(null);
    setSelectedCVId(cvFileId);
    setIsParsing(true);
    try {
      const data = await parseCV(cvFileId);
      setParsedCV(data);
      setMessage("CV analysé avec succès.");
      await loadPageData();
    } catch (parseError) {
      setError(getApiErrorMessage(parseError, "L'analyse du CV a échoué. Vérifiez que le texte extrait existe pour ce fichier."));
    } finally {
      setIsParsing(false);
    }
  };

  const selectedParsedJson = parsedCV?.structured_json;
  const parserResultLabel = getParserResultLabel(parsedCV?.parser_model);
  const processingSteps: Array<{ key: ProcessingStage; label: string }> = [
    { key: "uploading", label: "Import" },
    { key: "parsing", label: "Analyse du CV" },
    { key: "matching", label: "Matching IA" },
    { key: "completed", label: "Terminé" },
  ];
  const activeStepIndex = processingSteps.findIndex((step) => step.key === processingStage);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Importer un CV candidat</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Importez un fichier PDF/DOCX ou un fichier ZIP contenant plusieurs CV. La plateforme crée ou met à jour automatiquement les profils candidats, extrait le texte, analyse les CV et lance le matching IA.
            </p>
          </div>
          <Link className="text-sm font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to="/candidates">
            Gérer les candidats
          </Link>
        </div>

        <form className="mt-6 grid gap-5 lg:grid-cols-[1fr_auto] items-end" onSubmit={handleUpload}>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Fichier CV ou lot ZIP</span>
            <input
              accept=".pdf,.doc,.docx,.zip,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/zip"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#1D6EEA] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-white"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              type="file"
            />
            <span className="mt-1 block text-xs text-slate-500">PDF, DOC, DOCX ou ZIP. Maximum 5 Mo par CV.</span>
          </label>

          <div className="flex items-end">
            <button
              className="h-10 w-full rounded-lg bg-[#1D6EEA] px-4 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
              disabled={isUploading || isLoadingPage}
              type="submit"
            >
              {isUploading ? "Analyse en cours..." : "Importer et analyser le CV"}
            </button>
          </div>
        </form>

        {(isUploading || processingStage === "completed") && processingStage !== "idle" ? (
          <div className="mt-5">
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-[#1D6EEA]" style={{ width: `${uploadProgress}%` }} />
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-4">
              {processingSteps.map((step, index) => {
                const isDone = activeStepIndex >= index;
                return (
                  <div
                    className={[
                      "rounded-lg border px-3 py-2 text-xs font-semibold",
                      isDone ? "border-[#1D6EEA] bg-[#1D6EEA]/10 text-[#1D6EEA]" : "border-slate-200 bg-white text-slate-500",
                    ].join(" ")}
                    key={step.key}
                  >
                    {step.label}
                  </div>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {processingStage === "completed"
                ? `Terminé. ${matchingCount ?? 0} résultat(s) de matching IA enregistré(s).`
                : `Étape en cours : ${processingSteps[activeStepIndex]?.label ?? "Import"}. Progression : ${uploadProgress ?? 0}%`}
            </p>
          </div>
        ) : null}

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {warning ? <p className="mt-5 rounded-lg bg-amber-50 p-3 text-sm font-medium text-amber-800">{warning}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      </section>

      {isLoadingPage ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Chargement de l'espace CV...
        </section>
      ) : null}

      {!isLoadingPage && cvFiles.length === 0 ? (
        <EmptyState
          title="Aucun CV importé"
          description="Importez un CV candidat pour afficher l'extraction, l'état d'analyse et les données structurées."
        />
      ) : null}

      {!isLoadingPage && cvFiles.length > 0 ? (
        <ListSearch
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Rechercher par fichier, candidat, email, poste ou statut..."
        />
      ) : null}

      {cvFiles.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Fichiers CV importés</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Fichier</th>
                  <th className="px-5 py-3 font-semibold">Candidat</th>
                  <th className="px-5 py-3 font-semibold">Taille</th>
                  <th className="px-5 py-3 font-semibold">Statut</th>
                  <th className="px-5 py-3 font-semibold">Importé le</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCVFiles.map((cvFile) => {
                  const candidate = candidates.find((item) => item.id === cvFile.candidate_id);
                  return (
                    <tr key={cvFile.id} className={selectedCVId === cvFile.id ? "bg-blue-50/60" : "hover:bg-slate-50"}>
                      <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">
                        {cvFile.original_filename}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                        {candidate ? `${candidate.first_name} ${candidate.last_name}` : cvFile.candidate_id}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatBytes(cvFile.file_size_bytes)}</td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <span className="rounded-full bg-[#1D6EEA]/10 px-3 py-1 text-xs font-semibold capitalize text-[#1D6EEA]">
                          {formatParsingStatus(cvFile.parsing_status)}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                        {new Date(cvFile.uploaded_at).toLocaleDateString()}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4">
                        <div className="flex gap-2">
                          <button
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                            disabled={isTextLoading}
                            onClick={() => void handleViewText(cvFile.id)}
                            type="button"
                          >
                            Voir le texte
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {!isLoadingPage && cvFiles.length > 0 && filteredCVFiles.length === 0 ? (
        <EmptyState title="Aucun CV trouvÃ©" description="Modifiez la recherche pour afficher d'autres fichiers CV." />
      ) : null}

      {cvFiles.length > 0 ? (
        <details className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <summary className="cursor-pointer text-sm font-semibold text-[#0B1F3A]">Actions de diagnostic administrateur</summary>
          <p className="mt-2 text-sm text-slate-600">
            L'analyse manuelle est conservée uniquement pour le diagnostic. Les imports de CV déclenchent déjà l'analyse et le matching IA automatiquement.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {filteredCVFiles.map((cvFile) => (
              <button
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isParsing}
                key={cvFile.id}
                onClick={() => void handleParse(cvFile.id)}
                type="button"
              >
                {isParsing && selectedCVId === cvFile.id ? "Analyse en cours..." : `Réanalyser ${cvFile.original_filename}`}
              </button>
            ))}
          </div>
        </details>
      ) : null}

      {extractedText ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Texte brut extrait</h3>
            <p className="mt-1 text-sm text-slate-600">Statut : {formatParsingStatus(extractedText.parsing_status)}</p>
          </div>
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap px-5 py-4 text-sm leading-6 text-slate-700">
            {extractedText.raw_text}
          </pre>
        </section>
      ) : null}

      {selectedParsedJson ? (
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-[#0B1F3A]">JSON structuré analysé</h3>
              <p className="mt-1 text-sm text-slate-600">{parserResultLabel} enregistré par le backend.</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
              Niveau de confiance : {parsedCV.confidence_score ?? "N/A"}
            </span>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Prénom</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.first_name || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Nom</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.last_name || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.email || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Téléphone</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.phone || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Compétences</p>
              {renderListValue(selectedParsedJson.skills)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Langues</p>
              {renderListValue(selectedParsedJson.languages)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Formation</p>
              {renderListValue(selectedParsedJson.education)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Expérience</p>
              {renderListValue(selectedParsedJson.experience)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4 lg:col-span-2">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Certifications</p>
              {renderListValue(selectedParsedJson.certifications)}
            </article>
          </div>
        </section>
      ) : null}
    </div>
  );
}
