import { FormEvent, useEffect, useState } from "react";

import { getApiErrorMessage } from "../lib/errors";
import { getAdminSettings, updateAdminSettings } from "../services/admin";

export function AdminSettingsPage() {
  const [settingsText, setSettingsText] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        const response = await getAdminSettings();
        setSettingsText(JSON.stringify(response.settings, null, 2));
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Impossible de charger les paramètres."));
      }
    }
    void loadSettings();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSaving(true);
    try {
      const parsed = JSON.parse(settingsText) as Record<string, unknown>;
      const response = await updateAdminSettings(parsed);
      setSettingsText(JSON.stringify(response.settings, null, 2));
      setMessage("Paramètres enregistrés.");
    } catch (saveError) {
      setError(saveError instanceof SyntaxError ? "JSON invalide." : getApiErrorMessage(saveError, "Impossible d'enregistrer les paramètres."));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#E8590C]">Administration</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">Paramètres système</h2>
        <p className="mt-2 text-sm text-slate-600">Modifiez les paramètres applicatifs sous forme JSON clé/valeur.</p>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <form className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
        <label className="block">
          <span className="text-sm font-semibold text-slate-700">Paramètres JSON</span>
          <textarea
            className="mt-2 min-h-96 w-full rounded-lg border border-slate-300 p-4 font-mono text-sm outline-none focus:border-[#E8590C]"
            onChange={(event) => setSettingsText(event.target.value)}
            value={settingsText}
          />
        </label>
        <div className="mt-4 flex justify-end">
          <button className="rounded-lg bg-[#E8590C] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={isSaving} type="submit">
            {isSaving ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}
