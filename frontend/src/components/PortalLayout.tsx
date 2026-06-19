import { Link, NavLink, Outlet } from "react-router-dom";

import { getStoredCandidateToken } from "../lib/portalAuthStorage";
import { logoutCandidate } from "../services/portal";

const portalLinks = [
  { label: "Accueil", to: "/portal" },
  { label: "Offres disponibles", to: "/portal/jobs" },
  { label: "Profil candidat", to: "/portal/profile" },
  { label: "Mes candidatures", to: "/portal/applications" },
];

export function PortalLayout() {
  const isCandidateLoggedIn = Boolean(getStoredCandidateToken());

  return (
    <div className="min-h-screen bg-[#F6F8FB] text-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link to="/portal" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#E8590C] text-sm font-bold text-white">TA</span>
            <span>
              <span className="block text-sm font-semibold text-[#0B1F3A]">Talents Associate</span>
              <span className="block text-xs text-slate-500">Espace candidat</span>
            </span>
          </Link>

          <nav className="flex flex-wrap items-center gap-2">
            {portalLinks.map((item) => (
              <NavLink
                className={({ isActive }) =>
                  [
                    "rounded-lg px-3 py-2 text-sm font-semibold transition",
                    isActive ? "bg-[#E8590C]/10 text-[#E8590C]" : "text-slate-600 hover:bg-slate-100 hover:text-[#0B1F3A]",
                  ].join(" ")
                }
                end={item.to === "/portal"}
                key={item.to}
                to={item.to}
              >
                {item.label}
              </NavLink>
            ))}
            {isCandidateLoggedIn ? (
              <button
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:border-[#E8590C] hover:text-[#E8590C]"
                onClick={() => {
                  logoutCandidate();
                  window.location.href = "/portal/login";
                }}
                type="button"
              >
                Déconnexion
              </button>
            ) : (
              <>
                <Link className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 hover:text-[#0B1F3A]" to="/portal/login">
                  Connexion
                </Link>
                <Link className="rounded-lg bg-[#E8590C] px-3 py-2 text-sm font-semibold text-white hover:bg-[#c94b08]" to="/portal/register">
                  Créer un compte
                </Link>
              </>
            )}
            <Link
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:border-[#0B1F3A] hover:text-[#0B1F3A]"
              to="/login"
            >
              Espace recruteur
            </Link>
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
