import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { registerCandidate } from "../services/portal";

const initialForm = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  phone: "",
  location: "",
  current_title: "",
};

type RegisterField = keyof typeof initialForm;

const fields: Array<[RegisterField, string, boolean]> = [
  ["first_name", "Prénom", true],
  ["last_name", "Nom", true],
  ["email", "Email", true],
  ["password", "Mot de passe", true],
  ["phone", "Téléphone", false],
  ["location", "Ville", false],
  ["current_title", "Poste actuel", false],
];

export function PortalRegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await registerCandidate(form);
      navigate("/portal/profile");
    } catch (registerError) {
      setError(getApiErrorMessage(registerError, "Impossible de créer votre compte candidat."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto grid max-w-5xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.85fr_1.15fr]">
      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Espace candidat</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Créez votre profil Talents Associate</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Complétez vos informations principales, ajoutez votre CV, puis postulez aux opportunités publiées par nos équipes.
        </p>
        <p className="mt-5 text-sm text-slate-600">
          Déjà inscrit ?{" "}
          <Link className="font-semibold text-[#E8590C] hover:text-[#c94b08]" to="/portal/login">
            Se connecter
          </Link>
        </p>
      </aside>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
          {fields.map(([field, label, required]) => (
            <label className={field === "current_title" ? "block sm:col-span-2" : "block"} key={field}>
              <span className="text-sm font-medium text-slate-700">{label}</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
                onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
                required={Boolean(required)}
                type={field === "password" ? "password" : field === "email" ? "email" : "text"}
                value={form[field]}
              />
            </label>
          ))}

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">{error}</div> : null}

          <button
            className="rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:bg-slate-400 sm:col-span-2"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Création..." : "Créer mon compte"}
          </button>
        </form>
      </section>
    </main>
  );
}
