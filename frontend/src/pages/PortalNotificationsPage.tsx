import { useEffect, useMemo, useState } from "react";

import { getApiErrorMessage } from "../lib/errors";
import {
  CandidateNotification,
  getCandidateNotifications,
  markCandidateNotificationRead,
} from "../services/portal";

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function typeLabel(type: CandidateNotification["type"]) {
  if (type === "interview_invitation") return "Convocation entretien";
  if (type === "accepted") return "Acceptation";
  return "Retour candidature";
}

export function PortalNotificationsPage() {
  const [notifications, setNotifications] = useState<CandidateNotification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const unreadCount = useMemo(() => notifications.filter((notification) => !notification.is_read).length, [notifications]);

  const loadNotifications = async () => {
    setIsLoading(true);
    setError(null);
    try {
      setNotifications(await getCandidateNotifications());
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Impossible de charger vos notifications."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadNotifications();
  }, []);

  const handleRead = async (notificationId: string) => {
    setError(null);
    try {
      const updated = await markCandidateNotificationRead(notificationId);
      setNotifications((current) => current.map((notification) => (notification.id === updated.id ? updated : notification)));
    } catch (readError) {
      setError(getApiErrorMessage(readError, "Impossible de marquer la notification comme lue."));
    }
  };

  return (
    <main className="bg-[#F7F8FB]">
      <section className="mx-auto max-w-[1180px] px-6 py-16 lg:px-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-[#EE6C2F]">Espace candidat</p>
            <h1 className="mt-3 text-4xl font-black text-[#24303F]">Notifications</h1>
            <p className="mt-3 max-w-2xl text-lg leading-8 text-slate-600">
              Retrouvez ici les convocations entretien et les retours importants sur vos candidatures.
            </p>
          </div>
          <span className="rounded-full bg-[#EE6C2F]/10 px-4 py-2 text-sm font-bold text-[#EE6C2F]">
            {unreadCount} non lue(s)
          </span>
        </div>

        {error ? <p className="mt-8 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-700">{error}</p> : null}

        <section className="mt-10 rounded-2xl bg-white shadow-xl shadow-slate-900/5">
          {isLoading ? (
            <p className="p-8 text-sm text-slate-600">Chargement des notifications...</p>
          ) : notifications.length === 0 ? (
            <div className="p-10 text-center">
              <h2 className="text-xl font-black text-[#24303F]">Aucune notification</h2>
              <p className="mt-2 text-slate-600">Vous recevrez ici les informations importantes de Talents Associate.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {notifications.map((notification) => (
                <article className="flex flex-col gap-4 p-6 md:flex-row md:items-start md:justify-between" key={notification.id}>
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="rounded-full bg-orange-50 px-3 py-1 text-xs font-bold text-[#EE6C2F]">
                        {typeLabel(notification.type)}
                      </span>
                      {!notification.is_read ? (
                        <span className="rounded-full bg-[#24303F] px-3 py-1 text-xs font-bold text-white">Nouveau</span>
                      ) : null}
                    </div>
                    <h2 className="mt-3 text-xl font-black text-[#24303F]">{notification.title}</h2>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{notification.message}</p>
                    <time className="mt-3 block text-xs font-semibold text-slate-400">{formatDate(notification.created_at)}</time>
                  </div>
                  {!notification.is_read ? (
                    <button
                      className="rounded-lg border border-[#EE6C2F] px-4 py-2 text-sm font-bold text-[#EE6C2F] transition hover:bg-orange-50"
                      onClick={() => void handleRead(notification.id)}
                      type="button"
                    >
                      Marquer comme lu
                    </button>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
