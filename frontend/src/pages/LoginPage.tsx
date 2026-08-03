import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { ChartIcon, LockIcon, MailIcon, TargetIcon, UsersIcon } from "../components/AppIcons";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../lib/api";
import { getApiErrorMessage } from "../lib/errors";

export function LoginPage() {
  const { isAuthenticated, isCheckingAuth, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotMessage, setForgotMessage] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [isSendingReset, setIsSendingReset] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isCheckingAuth && isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Connexion impossible."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setForgotError(null);
    setForgotMessage(null);
    setIsSendingReset(true);
    try {
      const response = await apiClient.post<{ message: string }>("/api/auth/forgot-password", {
        email: forgotEmail.trim(),
      });
      setForgotMessage(response.data.message);
    } catch (forgotPasswordError) {
      setForgotError(getApiErrorMessage(forgotPasswordError, "Impossible d'envoyer le lien de réinitialisation."));
    } finally {
      setIsSendingReset(false);
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-white text-[#24303F] lg:grid lg:grid-cols-[1fr_1fr]">
      <section className="relative flex min-h-screen flex-col justify-center px-6 py-10 sm:px-12 lg:px-20">
        <div className="mx-auto w-full max-w-xl">
          <img
            alt="Talents Associate"
            className="h-24 w-auto object-contain sm:h-28"
            src="/talents-associate-logo-official.png"
          />
          <h1 className="mt-6 text-4xl font-extrabold leading-tight text-[#24303F] sm:text-5xl">
            Bienvenue sur <span className="block text-[#EE6C2F]">Talents Associate</span>
          </h1>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-600">
            La plateforme intelligente de gestion des talents et du recrutement.
          </p>

          <div className="mt-14 grid gap-6 text-center sm:grid-cols-3">
            <div className="border-slate-200 sm:border-r sm:pr-6">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-orange-50 text-[#EE6C2F]">
                <UsersIcon className="h-7 w-7" aria-hidden="true" />
              </span>
              <p className="mt-3 text-sm font-semibold leading-5">Gérez vos candidats facilement</p>
            </div>
            <div className="border-slate-200 sm:border-r sm:px-6">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-orange-50 text-[#EE6C2F]">
                <TargetIcon className="h-7 w-7" aria-hidden="true" />
              </span>
              <p className="mt-3 text-sm font-semibold leading-5">Trouvez les meilleurs profils</p>
            </div>
            <div className="sm:pl-6">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-orange-50 text-[#EE6C2F]">
                <ChartIcon className="h-7 w-7" aria-hidden="true" />
              </span>
              <p className="mt-3 text-sm font-semibold leading-5">Pilotez vos recrutements en toute simplicité</p>
            </div>
          </div>
        </div>
        <p className="mx-auto mt-12 w-full max-w-xl text-sm text-slate-500">
          © 2026 Talents Associate. Tous droits réservés.
        </p>
      </section>

      <section className="relative flex min-h-screen items-center justify-center bg-[#fff7f2] px-6 py-10">
        <div className="pointer-events-none absolute bottom-[-9rem] right-[-8rem] h-96 w-96 rounded-full bg-[#EE6C2F]/70" />
        <div className="relative w-full max-w-xl rounded-lg border border-orange-100 bg-white p-8 shadow-xl shadow-slate-900/10 sm:p-10">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-[#24303F]">Connexion</h2>
            <p className="mt-3 text-base leading-7 text-slate-600">
              Veuillez entrer vos identifiants pour accéder à votre espace administrateur.
            </p>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Email</span>
              <span className="relative mt-2 block">
                <MailIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#EE6C2F]" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-lg border border-slate-300 pl-12 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="Entrez votre email"
                  required
                  type="email"
                  value={email}
                />
              </span>
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Mot de passe</span>
              <span className="relative mt-2 block">
                <LockIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#EE6C2F]" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-lg border border-slate-300 pl-12 pr-12 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
                  minLength={1}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Entrez votre mot de passe"
                  required
                  type={showPassword ? "text" : "password"}
                  value={password}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-sm font-bold text-slate-500 transition hover:bg-orange-50 hover:text-[#EE6C2F]"
                  onClick={() => setShowPassword((current) => !current)}
                  type="button"
                >
                  {showPassword ? "Masquer" : "Voir"}
                </button>
              </span>
            </label>

            <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
              <label className="flex items-center gap-3 text-slate-600">
                <input
                  checked={rememberMe}
                  className="h-5 w-5 rounded border-slate-300 text-[#EE6C2F] focus:ring-[#EE6C2F]"
                  onChange={(event) => setRememberMe(event.target.checked)}
                  type="checkbox"
                />
                Se souvenir de moi
              </label>
              <button
                className="font-semibold text-[#EE6C2F] hover:text-[#D9551B]"
                onClick={() => {
                  setForgotEmail(email);
                  setShowForgotPassword(true);
                  setForgotMessage(null);
                  setForgotError(null);
                }}
                type="button"
              >
                Mot de passe oublié ?
              </button>
            </div>

            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            ) : null}

            <button
              className="h-12 w-full rounded-lg bg-[#EE6C2F] px-4 text-sm font-bold text-white shadow-sm transition hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "Traitement..." : "Se connecter"}
            </button>

          </form>
        </div>
      </section>

      {showForgotPassword ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#24303F]/40 px-4">
          <form
            className="w-full max-w-md rounded-lg border border-orange-100 bg-white p-6 shadow-xl shadow-slate-900/15"
            onSubmit={handleForgotPassword}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-extrabold text-[#24303F]">Mot de passe oublié</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Entrez votre email recruteur pour recevoir un lien sécurisé de réinitialisation.
                </p>
              </div>
              <button
                className="rounded-md px-2 py-1 text-lg font-bold text-slate-500 hover:bg-orange-50 hover:text-[#EE6C2F]"
                onClick={() => setShowForgotPassword(false)}
                type="button"
              >
                ×
              </button>
            </div>
            <label className="mt-5 block">
              <span className="text-sm font-bold text-[#24303F]">Email</span>
              <span className="relative mt-2 block">
                <MailIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#EE6C2F]" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-lg border border-slate-300 pl-12 pr-4 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
                  onChange={(event) => setForgotEmail(event.target.value)}
                  placeholder="Entrez votre email"
                  required
                  type="email"
                  value={forgotEmail}
                />
              </span>
            </label>
            {forgotMessage ? <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{forgotMessage}</p> : null}
            {forgotError ? <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{forgotError}</p> : null}
            <button
              className="mt-5 h-11 w-full rounded-lg bg-[#EE6C2F] text-sm font-bold text-white transition hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSendingReset}
              type="submit"
            >
              {isSendingReset ? "Envoi..." : "Envoyer le lien"}
            </button>
          </form>
        </div>
      ) : null}
    </main>
  );
}
