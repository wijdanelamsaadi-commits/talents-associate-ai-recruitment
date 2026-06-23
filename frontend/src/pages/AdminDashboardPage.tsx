import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { AdminDashboardStats, getAdminDashboard } from "../services/admin";

export function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        setStats(await getAdminDashboard());
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Impossible de charger le tableau de bord administrateur."));
      }
    }
    void loadStats();
  }, []);

  if (error) {
    return <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</section>;
  }

  if (!stats) {
    return <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">Chargement...</section>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#E8590C]">Espace administrateur</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">Pilotage système</h2>
        <p className="mt-2 text-sm text-slate-600">Vue globale des volumes et de l'activité plateforme.</p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Candidats" value={String(stats.candidates_count)} detail="Profils en base" />
        <StatCard label="Recruteurs" value={String(stats.recruiters_count)} detail="Comptes RH actifs ou suspendus" />
        <StatCard label="Offres" value={String(stats.jobs_count)} detail="Offres enregistrées" />
        <StatCard label="Candidatures" value={String(stats.applications_count)} detail="Applications suivies" />
        <StatCard label="Vivier candidats" value={String(stats.talent_pool_count)} detail="Candidats conservés pour recontact" />
        <StatCard
          label="Emails"
          value={`${stats.email_sent_count}/${stats.email_skipped_count}/${stats.email_failed_count}`}
          detail="Envoyés / ignorés / échoués"
        />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-[#E8590C]" to="/admin/users">
          <h3 className="font-semibold text-[#0B1F3A]">Gestion utilisateurs</h3>
          <p className="mt-2 text-sm text-slate-600">Créer, désactiver, réactiver ou supprimer soft les comptes recruteurs.</p>
        </Link>
        <Link className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-[#E8590C]" to="/admin/settings">
          <h3 className="font-semibold text-[#0B1F3A]">Paramètres système</h3>
          <p className="mt-2 text-sm text-slate-600">Gérer les paramètres applicatifs stockés côté backend.</p>
        </Link>
      </section>
    </div>
  );
}
