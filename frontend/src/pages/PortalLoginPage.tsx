import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../lib/errors";
import { loginCandidate } from "../services/portal";

export function PortalLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/portal/profile";
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await loginCandidate(form);
      navigate(from);
    } catch (loginError) {
      setError(getApiErrorMessage(loginError, "Connexion impossible."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex max-w-xl px-4 py-10 sm:px-6">
      <section className="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase text-[#E8590C]">Connexion candidat</p>
        <h1 className="mt-2 text-3xl font-semibold text-[#0B1F3A]">Accédez à votre espace</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Retrouvez votre profil, votre CV et le suivi de vos candidatures Talents Associate.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
              type="email"
              value={form.email}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Mot de passe</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
              type="password"
              value={form.password}
            />
          </label>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}

          <button className="w-full rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:bg-slate-400" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          Nouveau candidat ?{" "}
          <Link className="font-semibold text-[#E8590C] hover:text-[#c94b08]" to="/portal/register">
            Créer un compte
          </Link>
        </p>
      </section>
    </main>
  );
}
