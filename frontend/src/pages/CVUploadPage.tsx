import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidates } from "../services/candidates";
import { CVFile, ExtractedCVText, ParsedCV, deleteCVFile, getCVFiles, getCVText, parseCV, uploadCV } from "../services/cv";

const allowedExtensions = [".pdf", ".doc", ".docx"];
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

function renderListValue(value: unknown[] | undefined) {
  if (!value || value.length === 0) {
    return <span className="text-slate-400">None detected</span>;
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
  const [error, setError] = useState<string | null>(null);

  const selectedCandidate = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedCandidateId),
    [candidates, selectedCandidateId],
  );

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
      setError(getApiErrorMessage(loadError, "Unable to load candidates or CV files. Check that the FastAPI backend is running on localhost:8001."));
    } finally {
      setIsLoadingPage(false);
    }
  };

  useEffect(() => {
    void loadPageData();
  }, []);

  const validateFile = (file: File | null) => {
    if (!file) {
      return "Select a PDF, DOC, or DOCX CV file.";
    }
    const lowerName = file.name.toLowerCase();
    if (!allowedExtensions.some((extension) => lowerName.endsWith(extension))) {
      return "Unsupported file format. Please upload PDF, DOC, or DOCX.";
    }
    if (file.size > maxFileSizeBytes) {
      return "File is larger than 5MB. The backend will reject oversized CV files.";
    }
    return null;
  };

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setExtractedText(null);
    setParsedCV(null);
    setMatchingCount(null);

    if (!selectedCandidateId) {
      setError("Select a candidate before uploading a CV.");
      return;
    }

    const fileError = validateFile(selectedFile);
    if (fileError) {
      setError(fileError);
      return;
    }

    setIsUploading(true);
    setProcessingStage("uploading");
    setUploadProgress(0);
    try {
      const uploaded = await uploadCV(selectedCandidateId, selectedFile as File, (progressEvent) => {
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
        structured_json: uploaded.structured_json,
      });
      setMatchingCount(uploaded.matching_result_ids.length);
      setMessage(
        `Uploaded ${uploaded.original_filename}. Text extraction, CV parsing, profile update, and automatic matching completed.`,
      );
      setSelectedFile(null);
      await loadPageData();
      await handleViewText(uploaded.id);
      setProcessingStage("completed");
      setMessage(
        `Uploaded ${uploaded.original_filename}. Text extraction, CV parsing, profile update, and ${uploaded.matching_result_ids.length} matching result(s) completed.`,
      );
    } catch (uploadError) {
      setProcessingStage("idle");
      setError(getApiErrorMessage(uploadError, "CV upload failed. Check the file format, file size, and candidate."));
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleViewText = async (cvFileId: string) => {
    setError(null);
    setMessage(null);
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
          structured_json: data.ai_output,
        });
      }
      setMessage("Extracted raw text loaded.");
    } catch (textError) {
      setExtractedText(null);
      setError(getApiErrorMessage(textError, "Unable to load extracted text for this CV."));
    } finally {
      setIsTextLoading(false);
    }
  };

  const handleParse = async (cvFileId: string) => {
    setError(null);
    setMessage(null);
    setSelectedCVId(cvFileId);
    setIsParsing(true);
    try {
      const data = await parseCV(cvFileId);
      setParsedCV(data);
      setMessage("CV parsed successfully.");
      await loadPageData();
    } catch (parseError) {
      setError(getApiErrorMessage(parseError, "CV parsing failed. Make sure extracted text exists for this file."));
    } finally {
      setIsParsing(false);
    }
  };

  const handleDeleteCV = async (cvFile: CVFile) => {
    const shouldDelete = window.confirm(`Delete CV file "${cvFile.original_filename}"?`);
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await deleteCVFile(cvFile.id);
      if (selectedCVId === cvFile.id) {
        setSelectedCVId(null);
        setExtractedText(null);
        setParsedCV(null);
      }
      setMessage("CV file deleted.");
      await loadPageData();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "CV file could not be deleted."));
    }
  };

  const selectedParsedJson = parsedCV?.structured_json;
  const processingSteps: Array<{ key: ProcessingStage; label: string }> = [
    { key: "uploading", label: "Uploading" },
    { key: "parsing", label: "Parsing" },
    { key: "matching", label: "Matching" },
    { key: "completed", label: "Completed" },
  ];
  const activeStepIndex = processingSteps.findIndex((step) => step.key === processingStage);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Upload candidate CV</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Select a candidate and upload a PDF or DOCX file. The platform extracts text, parses the CV, updates the profile,
              and runs matching automatically.
            </p>
          </div>
          <Link className="text-sm font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to="/candidates">
            Manage candidates
          </Link>
        </div>

        <form className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr_auto]" onSubmit={handleUpload}>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Candidate</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              disabled={isLoadingPage || candidates.length === 0}
              onChange={(event) => setSelectedCandidateId(event.target.value)}
              required
              value={selectedCandidateId}
            >
              {candidates.length === 0 ? <option value="">No candidates available</option> : null}
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.first_name} {candidate.last_name}
                </option>
              ))}
            </select>
            {selectedCandidate ? (
              <span className="mt-1 block text-xs text-slate-500">{selectedCandidate.email ?? "No email"}</span>
            ) : null}
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">CV file</span>
            <input
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#1D6EEA] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-white"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              type="file"
            />
            <span className="mt-1 block text-xs text-slate-500">PDF, DOC, or DOCX. Maximum 5MB.</span>
          </label>

          <div className="flex items-end">
            <button
              className="h-10 w-full rounded-lg bg-[#1D6EEA] px-4 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
              disabled={isUploading || isLoadingPage}
              type="submit"
            >
              {isUploading ? "Processing..." : "Upload and process CV"}
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
                ? `Completed. ${matchingCount ?? 0} automatic matching result(s) saved.`
                : `Current step: ${processingSteps[activeStepIndex]?.label ?? "Uploading"}. Upload progress: ${uploadProgress ?? 0}%`}
            </p>
          </div>
        ) : null}

        {message ? <p className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      </section>

      {isLoadingPage ? (
        <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Loading CV workspace...
        </section>
      ) : null}

      {!isLoadingPage && cvFiles.length === 0 ? (
        <EmptyState
          title="No CV files uploaded yet"
          description="Upload a candidate CV to see extraction, parsing status, and structured profile data here."
        />
      ) : null}

      {cvFiles.length > 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Uploaded CV files</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">File</th>
                  <th className="px-5 py-3 font-semibold">Candidate</th>
                  <th className="px-5 py-3 font-semibold">Size</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Uploaded</th>
                  <th className="px-5 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cvFiles.map((cvFile) => {
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
                          {cvFile.parsing_status.replaceAll("_", " ")}
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
                            View text
                          </button>
                          <button
                            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
                            onClick={() => void handleDeleteCV(cvFile)}
                            type="button"
                          >
                            Delete
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

      {cvFiles.length > 0 ? (
        <details className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <summary className="cursor-pointer text-sm font-semibold text-[#0B1F3A]">Admin debugging actions</summary>
          <p className="mt-2 text-sm text-slate-600">
            Manual parsing is kept only for troubleshooting. Normal CV uploads already parse and match automatically.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {cvFiles.map((cvFile) => (
              <button
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isParsing}
                key={cvFile.id}
                onClick={() => void handleParse(cvFile.id)}
                type="button"
              >
                {isParsing && selectedCVId === cvFile.id ? "Parsing..." : `Reprocess ${cvFile.original_filename}`}
              </button>
            ))}
          </div>
        </details>
      ) : null}

      {extractedText ? (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="text-base font-semibold text-[#0B1F3A]">Extracted raw text</h3>
            <p className="mt-1 text-sm text-slate-600">Status: {extractedText.parsing_status}</p>
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
              <h3 className="text-base font-semibold text-[#0B1F3A]">Structured parsed JSON</h3>
              <p className="mt-1 text-sm text-slate-600">Heuristic parser result saved by the backend.</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
              Confidence: {parsedCV.confidence_score ?? "N/A"}
            </span>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">First name</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.first_name || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Last name</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.last_name || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.email || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Phone</p>
              <p className="mt-2 text-sm font-semibold text-[#0B1F3A]">{selectedParsedJson.phone || "-"}</p>
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Skills</p>
              {renderListValue(selectedParsedJson.skills)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Languages</p>
              {renderListValue(selectedParsedJson.languages)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Education</p>
              {renderListValue(selectedParsedJson.education)}
            </article>
            <article className="rounded-lg border border-slate-200 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Experience</p>
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
