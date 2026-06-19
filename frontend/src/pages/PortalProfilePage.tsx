import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import {
  CandidateProfile,
  getCandidateProfile,
  replaceCandidateCv,
  updateCandidateProfile,
} from "../services/portal";

export function PortalProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    location: "",
    linkedin_url: "",
    portfolio_url: "",
    current_title: "",
  });
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadProfile() {
      try {
        const data = await getCandidateProfile();
        if (isMounted) {
          setProfile(data);
          setForm({
            first_name: data.first_name,
            last_name: data.last_name,
            phone: data.phone ?? "",
            location: data.location ?? "",
            linkedin_url: data.linkedin_url ?? "",
            portfolio_url: data.portfolio_url ?? "",
            current_title: data.current_title ?? "",
          });
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Impossible de charger votre profil."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    loadProfile();
    return () => {
      isMounted = false;
    };
  }, []);

  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await updateCandidateProfile(form);
      setProfile(updated);
      setMessage("Profil enregistré.");
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Impossible de mettre à jour votre profil."));
    } finally {
      setIsSaving(false);
    }
  };

  const uploadCv = async () => {
    if (!file) {
      setError("Sélectionnez un CV PDF ou DOCX.");
      return;
    }
    setIsSaving(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await replaceCandidateCv(file);
      setProfile(updated);
      setFile(null);
      setMessage("CV mis à jour et analysé.");
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Impossible de déposer votre CV."));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <main className="mx-auto max-w-5xl px-4 py-8 text-sm text-slate-600 sm:px-6">Chargement du profil...</main>;
  }

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.15fr_0.85fr]">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Profil candidat</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Informations candidat</h1>
        <p className="mt-2 text-sm text-slate-600">{profile?.email}</p>

        <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={saveProfile}>
          {[
            ["first_name", "Prénom"],
            ["last_name", "Nom"],
            ["phone", "Téléphone"],
            ["location", "Ville"],
            ["current_title", "Poste actuel"],
            ["linkedin_url", "LinkedIn"],
            ["portfolio_url", "Portfolio"],
          ].map(([field, label]) => (
            <label className={field === "portfolio_url" ? "block sm:col-span-2" : "block"} key={field}>
              <span className="text-sm font-medium text-slate-700">{label}</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
                onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
                required={field === "first_name" || field === "last_name"}
                value={form[field as keyof typeof form]}
              />
            </label>
          ))}

          <button className="rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:bg-slate-400 sm:col-span-2" disabled={isSaving} type="submit">
            {isSaving ? "Enregistrement..." : "Enregistrer mon profil"}
          </button>
        </form>
      </section>

      <aside className="space-y-6">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[#0B1F3A]">Mon CV</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {profile?.latest_cv_filename ? `CV actuel : ${profile.latest_cv_filename}` : "Ajoutez votre CV pour postuler rapidement."}
          </p>
          <input
            accept=".pdf,.docx"
            className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-[#E8590C]/10 file:px-3 file:py-1 file:text-sm file:font-semibold file:text-[#E8590C]"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            type="file"
          />
          <button className="mt-4 w-full rounded-lg bg-[#0B1F3A] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#102b50] disabled:bg-slate-400" disabled={isSaving || !file} onClick={() => void uploadCv()} type="button">
            {profile?.latest_cv_filename ? "Remplacer mon CV" : "Déposer mon CV"}
          </button>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[#0B1F3A]">Prochaine étape</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Consultez les opportunités et postulez avec votre CV déjà enregistré.</p>
          <Link className="mt-4 inline-flex w-full justify-center rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08]" to="/portal/jobs">
            Voir les offres
          </Link>
        </section>

        {(message || error) && (
          <div className={message ? "rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800" : "rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"}>
            {message || error}
          </div>
        )}
      </aside>
    </main>
  );
}
