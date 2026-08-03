import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { LockIcon } from "../components/AppIcons";
import { apiClient } from "../lib/api";
import { getApiErrorMessage } from "../lib/errors";

type ResetInfo = {
  email: string;
  full_name: string;
};

export function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [info, setInfo] = useState<ResetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const verify = async () => {
      setLoading(true);
      setTokenError(null);
      try {
        const response = await apiClient.get<ResetInfo>(`/api/auth/reset-password/${token}`);
        setInfo(response.data);
      } catch (verifyError) {
        setTokenError(getApiErrorMessage(verifyError, "Lien de réinitialisation invalide ou expiré."));
      } finally {
        setLoading(false);
      }
    };
    void verify();
  }, [token]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    setIsSubmitting(true);
    try {
      await apiClient.post(`/api/auth/reset-password/${token}`, { password });
      navigate("/login", { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Impossible de réinitialiser le mot de passe."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fff7f2] p-4">
      <div className="w-full max-w-md rounded-lg border border-orange-100 bg-white p-8 shadow-sm shadow-slate-900/5">
        <img
          alt="Talents Associate"
          className="mx-auto h-20 w-auto object-contain"
          src="/talents-associate-logo-official.png"
        />
        <h1 className="mt-5 text-center text-2xl font-extrabold text-[#24303F]">Nouveau mot de passe</h1>

        {loading ? (
          <p className="mt-6 text-center text-sm text-slate-500">Vérification du lien...</p>
        ) : tokenError ? (
          <div className="mt-6 space-y-4">
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{tokenError}</p>
            <button
              className="w-full rounded-lg bg-[#EE6C2F] px-4 py-2 text-sm font-bold text-white hover:bg-[#D9551B]"
              onClick={() => navigate("/login")}
              type="button"
            >
              Retour à la connexion
            </button>
          </div>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <p className="text-sm leading-6 text-slate-600">
              Bonjour <span className="font-semibold">{info?.full_name}</span>, choisissez un nouveau mot de passe
              pour votre compte ({info?.email}).
            </p>
            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Mot de passe</span>
              <span className="relative mt-2 block">
                <LockIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#EE6C2F]" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-lg border border-slate-300 pl-12 pr-4 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
                  minLength={8}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  type="password"
                  value={password}
                />
              </span>
            </label>
            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Confirmer le mot de passe</span>
              <span className="relative mt-2 block">
                <LockIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#EE6C2F]" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-lg border border-slate-300 pl-12 pr-4 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
                  minLength={8}
                  onChange={(event) => setConfirm(event.target.value)}
                  required
                  type="password"
                  value={confirm}
                />
              </span>
            </label>
            {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
            <button
              className="h-11 w-full rounded-lg bg-[#EE6C2F] text-sm font-bold text-white transition hover:bg-[#D9551B] disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              Réinitialiser mon mot de passe
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
