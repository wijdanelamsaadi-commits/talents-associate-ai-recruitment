import { NavLink } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

type NavigationItem = {
  label: string;
  to: string;
  icon: string;
};

const recruiterNavigation: NavigationItem[] = [
  { label: "Tableau de bord", to: "/dashboard", icon: "T" },
  { label: "Vivier candidats", to: "/candidates", icon: "C" },
  { label: "Offres d'emploi", to: "/jobs", icon: "O" },
  { label: "Matching IA", to: "/matching", icon: "M" },
  { label: "Entretien", to: "/interviews", icon: "E" },
];

const adminNavigation: NavigationItem[] = [
  { label: "Import de CV", to: "/cv-upload", icon: "CV" },
  { label: "Import LinkedIn", to: "/imports", icon: "LI" },
  { label: "Vivier candidats", to: "/candidates", icon: "C" },
  { label: "Offres d'emploi", to: "/jobs", icon: "O" },
  { label: "Matching IA", to: "/matching", icon: "M" },
  { label: "Évaluation candidat", to: "/interviews", icon: "E" },
  { label: "Création profil", to: "/admin/users", icon: "U" },
];

export function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const visibleNavigation = isAdmin ? adminNavigation : recruiterNavigation;
  const homePath = isAdmin ? "/cv-upload" : "/dashboard";
  const spaceLabel = isAdmin ? "Espace administrateur" : "Espace recruteur";

  return (
    <aside className="fixed inset-x-0 top-0 z-30 border-b border-white/10 bg-[#061A33] text-white shadow-xl shadow-slate-950/10 lg:inset-y-0 lg:right-auto lg:w-72 lg:border-b-0">
      <div className="flex h-16 items-center justify-between px-4 lg:h-auto lg:flex-col lg:items-stretch lg:gap-8 lg:px-6 lg:py-6">
        <NavLink to={homePath} className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#E8590C] text-sm font-bold shadow-sm">
            TA
          </span>
          <span className="hidden min-w-0 sm:block">
            <span className="block truncate text-sm font-semibold">Talents Associate</span>
            <span className="block truncate text-xs text-slate-300">{spaceLabel}</span>
          </span>
        </NavLink>

        <nav className="flex gap-1 overflow-x-auto lg:flex-col lg:gap-2 lg:overflow-visible">
          {visibleNavigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex h-10 shrink-0 items-center gap-3 rounded-lg px-3 text-sm font-medium transition",
                  isActive
                    ? "bg-white text-[#061A33] shadow-sm"
                    : "text-slate-300 hover:bg-white/10 hover:text-white",
                ].join(" ")
              }
            >
              <span className="flex h-6 min-w-6 items-center justify-center rounded-md bg-[#E8590C]/15 px-1 text-[11px] font-bold text-[#F97316]">
                {item.icon}
              </span>
              <span className="hidden lg:inline">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="hidden rounded-lg border border-white/10 bg-white/5 p-4 lg:block">
          <p className="text-sm font-semibold">{spaceLabel}</p>
          <p className="mt-1 text-xs leading-5 text-slate-300">
            {isAdmin
              ? "Gérez les imports, le vivier, le matching et la création des profils."
              : "Suivez le pipeline, les offres, le matching et les entretiens."}
          </p>
        </div>
      </div>
    </aside>
  );
}
