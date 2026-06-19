import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { JobOffer } from "../services/jobs";
import { PortalApplicationResponse, getPublicJob, submitPortalApplication } from "../services/portal";

const supportedExtensions = [".pdf", ".docx"];

export function PortalApplyPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [processingStep, setProcessingStep] = useState<"idle" | "uploading" | "processing" | "completed">("idle");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<PortalApplicationResponse | null>(null);
  const [formState, setFormState] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    location: "",
  });
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadJob() {
      if (!jobId) {
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPublicJob(jobId);
        if (isMounted) {
          setJob(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Impossible de charger le détail de l'offre."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadJob();
    return () => {
      isMounted = false;
    };
  }, [jobId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!jobId || !file) {
      setError("Veuillez sélectionner un CV avant d'envoyer votre candidature.");
      return;
    }

    const lowerName = file.name.toLowerCase();
    if (!supportedExtensions.some((extension) => lowerName.endsWith(extension))) {
      setError("Veuillez déposer un CV au format PDF ou DOCX.");
      return;
    }

    setIsSubmitting(true);
    setProcessingStep("uploading");
    setError(null);
    setSuccess(null);
    try {
      setProcessingStep("processing");
      const response = await submitPortalApplication(jobId, { ...formState, file });
      setSuccess(response);
      setProcessingStep("completed");
    } catch (submitError) {
      setProcessingStep("idle");
      setError(getApiErrorMessage(submitError, "Envoi de la candidature impossible."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.85fr_1.15fr]">
      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Formulaire candidat</p>
        <h1 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{job?.title ?? "Postuler à cette offre"}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Déposez votre CV : la plateforme extrait le texte, prépare votre profil, calcule le score de matching et crée le suivi de candidature.
        </p>
        {isLoading ? <p className="mt-4 text-sm text-slate-500">Chargement de l'offre...</p> : null}
        {job ? (
          <Link className="mt-5 inline-flex text-sm font-semibold text-[#E8590C]" to={`/portal/jobs/${job.id}`}>
            Revoir le détail de l'offre
          </Link>
        ) : null}
      </aside>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <form className="space-y-4" onSubmit={handleSubmit}>
          {(["first_name", "last_name", "email", "phone", "location"] as const).map((field) => (
            <label className="block" key={field}>
              <span className="text-sm font-medium text-slate-700">
                {{
                  first_name: "Prénom",
                  last_name: "Nom",
                  email: "Email",
                  phone: "Téléphone",
                  location: "Ville",
                }[field]}
              </span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
                onChange={(event) => setFormState((current) => ({ ...current, [field]: event.target.value }))}
                required={field === "first_name" || field === "last_name" || field === "email"}
                type={field === "email" ? "email" : "text"}
                value={formState[field]}
              />
            </label>
          ))}

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Fichier CV</span>
            <input
              accept=".pdf,.docx"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#E8590C]/10 file:px-3 file:py-1 file:text-sm file:font-semibold file:text-[#E8590C]"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
              type="file"
            />
            <span className="mt-1 block text-xs text-slate-500">PDF ou DOCX, maximum 5 Mo.</span>
          </label>

          {processingStep !== "idle" ? (
            <div className="grid gap-2 sm:grid-cols-3">
              {[
                ["uploading", "Upload"],
                ["processing", "Parsing et matching"],
                ["completed", "Terminé"],
              ].map(([key, label]) => (
                <div
                  className={[
                    "rounded-lg border px-3 py-2 text-xs font-semibold",
                    processingStep === key || processingStep === "completed"
                      ? "border-[#E8590C] bg-[#E8590C]/10 text-[#E8590C]"
                      : "border-slate-200 text-slate-500",
                  ].join(" ")}
                  key={key}
                >
                  {label}
                </div>
              ))}
            </div>
          ) : null}

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
          {success ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {success.message} Résultats de matching : {success.matching_result_ids.length}. Score de matching :{" "}
              {success.confidence_score ?? "N/A"}.
            </div>
          ) : null}

          <button
            className="w-full rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting || isLoading || !job}
            type="submit"
          >
            {isSubmitting ? "Traitement de la candidature..." : "Envoyer ma candidature"}
          </button>
        </form>
      </section>
    </main>
  );
}
