import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage } from "../lib/errors";

export function LoginPage() {
  const { isAuthenticated, isCheckingAuth, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/dashboard";
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
  }, [mode]);

  if (!isCheckingAuth && isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await register({ full_name: fullName, email, password });
      } else {
        await login({ email, password });
      }
      navigate(from, { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, mode === "register" ? "Création du compte impossible." : "Connexion impossible."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F6F8FB] px-4 py-10">
      <section className="grid w-full max-w-5xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-900/10 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="bg-[#061A33] p-8 text-white sm:p-10">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#E8590C] text-sm font-bold text-white">
            TA
          </div>
          <p className="mt-8 text-sm font-semibold uppercase tracking-wide text-orange-200">Talents Associate</p>
          <h1 className="mt-3 text-3xl font-semibold leading-tight">
            {mode === "register" ? "Créer un accès recruteur" : "Espace recruteur"}
          </h1>
          <p className="mt-4 text-sm leading-6 text-slate-200">
            Connectez-vous au back-office pour gérer les candidats, les offres, le matching IA et le suivi des entretiens.
          </p>
        </div>

        <div className="p-8 sm:p-10">
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase text-[#E8590C]">
              {mode === "register" ? "Nouveau compte" : "Connexion sécurisée"}
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">
              {mode === "register" ? "Créer un compte recruteur" : "Connexion recruteur"}
            </h2>
          </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "register" ? (
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Nom complet</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Nom du recruteur"
                required
                type="text"
                value={fullName}
              />
            </label>
          ) : null}
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="recruiter@talents-associate.com"
              required
              type="email"
              value={email}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Mot de passe</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C] focus:ring-2 focus:ring-[#E8590C]/20"
              minLength={mode === "register" ? 8 : 1}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Mot de passe"
              required
              type="password"
              value={password}
            />
          </label>
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}
          <button
            className="w-full rounded-lg bg-[#E8590C] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#c94b08] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Traitement..." : mode === "register" ? "Créer le compte" : "Se connecter"}
          </button>
        </form>

        <button
          className="mt-6 w-full text-center text-sm font-semibold text-[#E8590C] hover:text-[#c94b08]"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          type="button"
        >
          {mode === "login" ? "Créer le premier compte recruteur" : "J'ai déjà un compte"}
        </button>
        </div>
      </section>
    </main>
  );
}
