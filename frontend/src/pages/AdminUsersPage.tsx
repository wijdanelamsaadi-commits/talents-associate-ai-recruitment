import { FormEvent, useEffect, useState } from "react";

import { getApiErrorMessage } from "../lib/errors";
import {
  AdminUser,
  createRecruiter,
  deleteAdminUser,
  disableAdminUser,
  enableAdminUser,
  getAdminUsers,
} from "../services/admin";

type AdminUserForm = {
  full_name: string;
  email: string;
  password: string;
  role: "recruiter" | "hiring_manager";
};

const initialForm: AdminUserForm = { full_name: "", email: "", password: "", role: "recruiter" };

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadUsers = async () => {
    setError(null);
    try {
      setUsers(await getAdminUsers());
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
      await createRecruiter(form);
      setForm(initialForm);
      setMessage("Recruteur créé avec succès.");
      await loadUsers();
    } catch (createError) {
      setError(getApiErrorMessage(createError, "Impossible de créer le recruteur."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const runAction = async (action: () => Promise<AdminUser>, successMessage: string) => {
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(successMessage);
      await loadUsers();
    } catch (actionError) {
      setError(getApiErrorMessage(actionError, "Action impossible."));
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#E8590C]">Administration</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">Utilisateurs et recruteurs</h2>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="font-semibold text-[#0B1F3A]">Créer un recruteur</h3>
        <form className="mt-4 grid gap-4 md:grid-cols-4" onSubmit={handleCreate}>
          <input
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
            onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
            placeholder="Nom complet"
            required
            value={form.full_name}
          />
          <input
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            placeholder="Email"
            required
            type="email"
            value={form.email}
          />
          <input
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
            minLength={8}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            placeholder="Mot de passe"
            required
            type="password"
            value={form.password}
          />
          <div className="flex gap-2">
            <select
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#E8590C]"
              onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as "recruiter" | "hiring_manager" }))}
              value={form.role}
            >
              <option value="recruiter">Recruteur</option>
              <option value="hiring_manager">Hiring manager</option>
            </select>
            <button className="rounded-lg bg-[#E8590C] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={isSubmitting} type="submit">
              Créer
            </button>
          </div>
        </form>
      </section>

      {message ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="font-semibold text-[#0B1F3A]">Comptes système</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-5 py-3">Nom</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">Rôle</th>
                <th className="px-5 py-3">Statut</th>
                <th className="px-5 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="whitespace-nowrap px-5 py-4 font-semibold text-[#0B1F3A]">{user.full_name}</td>
                  <td className="whitespace-nowrap px-5 py-4 text-slate-700">{user.email}</td>
                  <td className="whitespace-nowrap px-5 py-4 text-slate-700">{user.role}</td>
                  <td className="whitespace-nowrap px-5 py-4">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{user.status}</span>
                  </td>
                  <td className="whitespace-nowrap px-5 py-4">
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-semibold text-amber-700" onClick={() => void runAction(() => disableAdminUser(user.id), "Utilisateur désactivé.")} type="button">
                        Désactiver
                      </button>
                      <button className="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700" onClick={() => void runAction(() => enableAdminUser(user.id), "Utilisateur réactivé.")} type="button">
                        Réactiver
                      </button>
                      <button className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700" onClick={() => void runAction(() => deleteAdminUser(user.id), "Utilisateur supprimé en soft delete.")} type="button">
                        Soft delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
