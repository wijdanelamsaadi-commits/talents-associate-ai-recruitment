import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

const recruiterPageTitles: Record<string, string> = {
  "/dashboard": "Tableau de bord",
  "/candidates": "Vivier candidats",
  "/jobs": "Offres d'emploi",
  "/matching": "Matching IA",
  "/interviews": "Entretien",
  "/evaluations": "Entretien",
};

const adminPageTitles: Record<string, string> = {
  "/cv-upload": "Import de CV",
  "/imports": "Import LinkedIn",
  "/candidates": "Vivier candidats",
  "/jobs": "Offres d'emploi",
  "/matching": "Matching IA",
  "/interviews": "Évaluation candidat",
  "/evaluations": "Évaluation candidat",
  "/admin/users": "Création profil",
};

export function Header() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const isAdmin = user?.role === "admin";
  const pageTitles = isAdmin ? adminPageTitles : recruiterPageTitles;
  const spaceLabel = isAdmin ? "Espace administrateur" : "Espace recruteur";
  const title = pageTitles[pathname] ?? (pathname.startsWith("/candidates/") ? "Détail candidat" : spaceLabel);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="sticky top-16 z-20 border-b border-slate-200 bg-white/95 backdrop-blur lg:top-0">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-[#E8590C]">{spaceLabel}</p>
          <h1 className="truncate text-xl font-semibold text-[#0B1F3A]">{title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600 sm:inline">
            {user?.full_name ?? (isAdmin ? "Administrateur" : "Recruteur")}
          </span>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
            type="button"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </header>
  );
}
