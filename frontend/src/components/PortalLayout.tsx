import { Link, NavLink, Outlet } from "react-router-dom";

import { getStoredCandidateToken } from "../lib/portalAuthStorage";
import { logoutCandidate } from "../services/portal";

const portalLinks = [
  { label: "Accueil", to: "/portal" },
  { label: "Offres disponibles", to: "/portal/jobs" },
  { label: "Mes candidatures", to: "/portal/applications" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "relative px-2 py-2 text-sm font-bold transition",
    isActive
      ? "text-[#ff3d00] after:absolute after:bottom-0 after:left-2 after:h-0.5 after:w-7 after:bg-[#ff3d00]"
      : "text-[#061A33] hover:text-[#ff3d00]",
  ].join(" ");
}

export function PortalLayout() {
  const isCandidateLoggedIn = Boolean(getStoredCandidateToken());

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/95 shadow-sm shadow-slate-900/5 backdrop-blur">
        <div className="mx-auto flex h-[86px] max-w-[1400px] items-center justify-between gap-5 px-6 lg:px-12">
          <Link to="/portal" className="flex shrink-0 items-center">
            <img
              alt="Talents Associate"
              className="h-14 w-auto object-contain"
              src="/talents-associate-logo-official.png"
            />
          </Link>

          <nav className="hidden flex-1 items-center justify-center gap-9 lg:flex">
            {portalLinks.map((item) => (
              <NavLink className={navClass} end={item.to === "/portal"} key={item.to} to={item.to}>
                {item.label}
              </NavLink>
            ))}
            <a className="px-2 py-2 text-sm font-bold text-[#061A33] transition hover:text-[#ff3d00]" href="/portal#about">
              À propos
            </a>
            <a className="px-2 py-2 text-sm font-bold text-[#061A33] transition hover:text-[#ff3d00]" href="/portal#contact">
              Contact
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {isCandidateLoggedIn ? (
              <button
                className="rounded-lg border border-[#ff3d00] px-5 py-3 text-sm font-bold text-[#ff3d00] transition hover:bg-[#ff3d00]/5"
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
                <Link
                  className="hidden rounded-lg border border-[#ff3d00] px-5 py-3 text-sm font-bold text-[#ff3d00] transition hover:bg-[#ff3d00]/5 sm:inline-flex"
                  to="/portal/login"
                >
                  Se connecter
                </Link>
                <Link
                  className="rounded-lg bg-[#ff3d00] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]"
                  to="/portal/register"
                >
                  Créer un compte
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <Outlet />

      <footer id="contact" className="bg-white">
        <div className="mx-auto grid max-w-[1360px] gap-10 px-6 py-12 md:grid-cols-[1.2fr_0.8fr_0.8fr_1fr] lg:px-12">
          <div>
            <Link to="/portal" className="inline-flex items-center">
              <img
                alt="Talents Associate"
                className="h-16 w-auto object-contain"
                src="/talents-associate-logo-official.png"
              />
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-6 text-slate-600">
              Votre allié stratégique en gestion des talents et en recrutement au Maroc.
            </p>
            <div className="mt-5 flex gap-3">
              {["in", "f", "ig", "@"].map((item) => (
                <span className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-xs font-bold text-[#061A33]" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-bold text-[#061A33]">Liens rapides</h3>
            <div className="mt-4 grid gap-3 text-sm text-slate-600">
              <Link to="/portal">Accueil</Link>
              <Link to="/portal/jobs">Offres disponibles</Link>
              <Link to="/portal/applications">Mes candidatures</Link>
              <a href="/portal#about">À propos</a>
              <a href="/portal#contact">Contact</a>
            </div>
          </div>

          <div id="about">
            <h3 className="font-bold text-[#061A33]">Nos services</h3>
            <div className="mt-4 grid gap-3 text-sm text-slate-600">
              <span>Recrutement</span>
              <span>Formation & Coaching</span>
              <span>Conseil RH & organisation</span>
              <span>Team Building</span>
            </div>
          </div>

          <div>
            <h3 className="font-bold text-[#061A33]">Contact</h3>
            <div className="mt-4 grid gap-3 text-sm leading-6 text-slate-600">
              <span>+212 (0) 6 88 12 88 13</span>
              <span>contact@talentsag.ma</span>
              <span>Avenue Lalla Yacout, Résidence Calais App 17, Casablanca</span>
            </div>
          </div>
        </div>
        <div className="bg-[#061A33] px-4 py-4 text-center text-sm text-white">
          © 2026 Talents Associate. Tous droits réservés.
        </div>
      </footer>
    </div>
  );
}
