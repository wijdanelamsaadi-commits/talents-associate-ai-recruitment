import { FormEvent, useEffect, useMemo, useState } from "react";

import { ListSearch } from "../components/ListSearch";
import { getApiErrorMessage } from "../lib/errors";
import {
  AdminUser,
  createUser,
  deleteAdminUser,
  disableAdminUser,
  enableAdminUser,
  getAdminUsers,
} from "../services/admin";

type AdminUserForm = {
  full_name: string;
  email: string;
  role: "admin" | "recruiter";
};

const initialForm: AdminUserForm = { full_name: "", email: "", role: "recruiter" };

function formatRole(role: string) {
  const labels: Record<string, string> = {
    admin: "Administrateur",
    recruiter: "Recruteur",
  };
  return labels[role] ?? role;
}

function formatStatus(status: string) {
  const labels: Record<string, string> = {
    active: "Actif",
    invited: "En attente d'activation",
    suspended: "Désactivé",
    deleted: "Supprimé",
  };
  return labels[status] ?? status;
}

function statusClass(status: string) {
  const classes: Record<string, string> = {
    active: "border-emerald-200 bg-emerald-50 text-emerald-700",
    invited: "border-orange-200 bg-orange-50 text-[#D9551B]",
    suspended: "border-slate-200 bg-slate-100 text-slate-700",
  };
  return classes[status] ?? "border-slate-200 bg-slate-100 text-slate-700";
}

function formatDate(value: string | null) {
  if (!value) {
    return "Jamais";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionUserId, setActionUserId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const visibleUsers = useMemo(() => users.filter((user) => user.status !== "deleted"), [users]);

  const filteredUsers = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return visibleUsers;
    }
    return visibleUsers.filter((user) =>
      [
        user.full_name,
        user.email,
        formatRole(user.role),
        formatStatus(user.status),
        user.created_at,
        user.last_login_at,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [searchQuery, visibleUsers]);

  const loadUsers = async () => {
    setError(null);
    try {
      setUsers((await getAdminUsers()).filter((user) => user.status !== "deleted"));
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger les utilisateurs."));
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await createUser({
        ...form,
        full_name: form.full_name.trim(),
        email: form.email.trim(),
      });
      setForm(initialForm);
      setMessage("Invitation envoyée. L'utilisateur devra définir son mot de passe via le lien sécurisé.");
      await loadUsers();
    } catch (createError) {
      setError(getApiErrorMessage(createError, "Impossible de créer l'utilisateur."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const runAction = async (userId: string, action: () => Promise<AdminUser>, successMessage: string, remove = false) => {
    setActionUserId(userId);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(successMessage);
      if (remove) {
        setUsers((current) => current.filter((user) => user.id !== userId));
      } else {
        await loadUsers();
      }
    } catch (actionError) {
      setError(getApiErrorMessage(actionError, "Action impossible."));
    } finally {
      setActionUserId(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-orange-100 bg-white p-6 shadow-sm shadow-slate-900/5">
        <p className="text-sm font-bold uppercase tracking-wide text-[#EE6C2F]">Administration</p>
        <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-[#24303F]">Création profil</h2>
            <p className="mt-1 text-sm text-slate-500">
              Créez des accès recruteurs sans manipuler leurs mots de passe.
            </p>
          </div>
          <div className="rounded-lg border border-orange-100 bg-orange-50 px-4 py-3 text-sm font-semibold text-[#D9551B]">
            {visibleUsers.length} comptes système
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/5">
        <div className="flex flex-col gap-1">
          <h3 className="font-bold text-[#24303F]">Nouvelle invitation</h3>
          <p className="text-sm text-slate-500">
            Le recruteur recevra un lien valable 48h pour définir son mot de passe.
          </p>
        </div>
        <form className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr_220px_auto]" onSubmit={handleCreate}>
          <label className="relative block">
            <span className="mb-1 block text-sm font-semibold text-slate-700">Nom complet</span>
            <span className="pointer-events-none absolute left-3 top-9 text-sm font-bold text-[#EE6C2F]">Aa</span>
            <input
              className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
              onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
              placeholder="Nadia El Amrani"
              required
              value={form.full_name}
            />
          </label>
          <label className="relative block">
            <span className="mb-1 block text-sm font-semibold text-slate-700">Email</span>
            <span className="pointer-events-none absolute left-3 top-9 text-sm font-bold text-[#EE6C2F]">@</span>
            <input
              className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              placeholder="recruteur@talents-associate.com"
              required
              type="email"
              value={form.email}
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-semibold text-slate-700">Rôle</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/15"
              onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as "admin" | "recruiter" }))}
              value={form.role}
            >
              <option value="recruiter">Recruteur</option>
              <option value="admin">Administrateur</option>
            </select>
          </label>
          <button
            className="self-end rounded-lg bg-[#EE6C2F] px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#D9551B] disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Envoi..." : "Envoyer"}
          </button>
        </form>
      </section>

      {message ? <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {visibleUsers.length > 0 ? (
        <ListSearch
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Rechercher par nom, email, rôle ou statut..."
        />
      ) : null}

      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-900/5">
        <div className="flex flex-col gap-1 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="font-bold text-[#24303F]">Comptes système</h3>
            <p className="text-sm text-slate-500">Les comptes supprimés ne sont plus affichés dans cette liste.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-[#FBF7F4] text-xs uppercase text-slate-500">
              <tr>
                <th className="px-5 py-3">Utilisateur</th>
                <th className="px-5 py-3">Rôle</th>
                <th className="px-5 py-3">Statut</th>
                <th className="px-5 py-3">Dernière connexion</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.map((user) => {
                const isBusy = actionUserId === user.id;
                return (
                  <tr className="transition hover:bg-orange-50/40" key={user.id}>
                    <td className="whitespace-nowrap px-5 py-4">
                      <div className="font-bold text-[#24303F]">{user.full_name}</div>
                      <div className="mt-0.5 text-sm text-slate-500">{user.email}</div>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">{formatRole(user.role)}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusClass(user.status)}`}>
                        {formatStatus(user.status)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">{formatDate(user.last_login_at)}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <div className="flex justify-end gap-2">
                        {user.status !== "suspended" ? (
                          <button
                            className="rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-bold text-amber-700 transition hover:bg-amber-50 disabled:opacity-60"
                            disabled={isBusy}
                            onClick={() => void runAction(user.id, () => disableAdminUser(user.id), "Utilisateur désactivé.")}
                            type="button"
                          >
                            Désactiver
                          </button>
                        ) : (
                          <button
                            className="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-bold text-emerald-700 transition hover:bg-emerald-50 disabled:opacity-60"
                            disabled={isBusy}
                            onClick={() =>
                              void runAction(
                                user.id,
                                () => enableAdminUser(user.id),
                                "Nouvelle invitation envoyée. L'ancien lien est invalide.",
                              )
                            }
                            type="button"
                          >
                            Réactiver
                          </button>
                        )}
                        <button
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-bold text-red-700 transition hover:bg-red-50 disabled:opacity-60"
                          disabled={isBusy}
                          onClick={() => void runAction(user.id, () => deleteAdminUser(user.id), "Utilisateur retiré de la liste.", true)}
                          type="button"
                        >
                          Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      {visibleUsers.length > 0 && filteredUsers.length === 0 ? (
        <p className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
          Aucun utilisateur ne correspond à cette recherche.
        </p>
      ) : null}
    </div>
  );
}
