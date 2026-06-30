import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { apiClient } from "../lib/api";
import { getApiErrorMessage } from "../lib/errors";

type ActivationInfo = {
  email: string;
  full_name: string;
};

export function ActivateAccountPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [info, setInfo] = useState<ActivationInfo | null>(null);
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
        const response = await apiClient.get<ActivationInfo>(`/api/auth/activate/${token}`);
        setInfo(response.data);
      } catch (verifyError) {
        setTokenError(getApiErrorMessage(verifyError, "Lien d'activation invalide ou expiré."));
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
      await apiClient.post(`/api/auth/activate/${token}`, { password });
      navigate("/login", { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Impossible d'activer le compte."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#E8590C]">Talents Associate</p>
        <h1 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">Activez votre compte</h1>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Vérification du lien…</p>
        ) : tokenError ? (
          <div className="mt-6 space-y-4">
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{tokenError}</p>
            <button
              className="text-sm font-semibold text-[#E8590C]"
              onClick={() => navigate("/login")}
              type="button"
            >
              Retour à la connexion
            </button>
          </div>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <p className="text-sm text-slate-600">
              Bonjour <span className="font-semibold">{info?.full_name}</span>, définissez votre mot de passe pour
              accéder à votre compte ({info?.email}).
            </p>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Mot de passe</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Confirmer le mot de passe</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
                minLength={8}
                onChange={(event) => setConfirm(event.target.value)}
                required
                type="password"
                value={confirm}
              />
            </div>
            {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
            <button
              className="w-full rounded-lg bg-[#E8590C] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              Activer mon compte
            </button>
          </form>
        )}
      </div>
    </div>
  );
}