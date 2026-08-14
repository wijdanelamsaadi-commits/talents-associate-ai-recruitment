import { NavLink } from "react-router-dom";
import type { ReactElement, SVGProps } from "react";

import {
  BriefcaseIcon,
  ChartIcon,
  FileCVIcon,
  LinkedinIcon,
  StarIcon,
  TargetIcon,
  UserPlusIcon,
  UsersIcon,
} from "./AppIcons";
import { useAuth } from "../contexts/AuthContext";

type NavigationItem = {
  label: string;
  to: string;
  icon: (props: SVGProps<SVGSVGElement>) => ReactElement;
};

const recruiterNavigation: NavigationItem[] = [
  { label: "Vivier candidats", to: "/candidates", icon: UsersIcon },
  { label: "Offres d'emploi", to: "/jobs", icon: BriefcaseIcon },
  { label: "Matching IA", to: "/matching", icon: TargetIcon },
  { label: "Entretien", to: "/interviews", icon: StarIcon },
  { label: "Tableau de bord", to: "/dashboard", icon: ChartIcon },
];

const adminNavigation: NavigationItem[] = [
  { label: "Import de CV", to: "/cv-upload", icon: FileCVIcon },
  { label: "Import LinkedIn", to: "/imports", icon: LinkedinIcon },
  { label: "Vivier candidats", to: "/candidates", icon: UsersIcon },
  { label: "Offres d'emploi", to: "/jobs", icon: BriefcaseIcon },
  { label: "Matching IA", to: "/matching", icon: TargetIcon },
  { label: "Évaluation candidat", to: "/interviews", icon: StarIcon },
  { label: "Création profil", to: "/admin/users", icon: UserPlusIcon },
  { label: "Tableau de bord", to: "/dashboard", icon: ChartIcon },
];

export function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const visibleNavigation = isAdmin ? adminNavigation : recruiterNavigation;
  const homePath = "/dashboard";
  const spaceLabel = isAdmin ? "Espace administrateur" : "Espace recruteur";

  return (
    <aside className="fixed inset-x-0 top-0 z-30 border-b border-[#EE6C2F]/30 bg-[var(--color-sidebar)] text-[var(--color-text-light)] shadow-lg shadow-slate-950/10 lg:inset-y-0 lg:right-auto lg:w-72 lg:border-b-0 lg:border-r lg:border-[#EE6C2F]/20">
      <div className="flex h-16 items-center justify-between px-4 lg:h-full lg:flex-col lg:items-stretch lg:justify-start lg:gap-8 lg:px-6 lg:py-7">
        <NavLink to={homePath} className="flex min-w-0 items-center gap-3 lg:flex-col lg:items-start">
          <span className="rounded-xl bg-white px-3 py-2 shadow-sm lg:px-4 lg:py-3">
            <img
              alt="Talents Associate"
              className="h-9 w-auto object-contain lg:h-20"
              src="/talents-associate-logo-official.png"
            />
          </span>
          <span className="hidden min-w-0 lg:block">
            <span className="block truncate text-xs font-semibold uppercase tracking-wide text-[#EE6C2F]">{spaceLabel}</span>
          </span>
        </NavLink>

        <nav className="flex gap-1 overflow-x-auto lg:flex-col lg:gap-2 lg:overflow-visible">
          {visibleNavigation.map((item) => {
            const Icon = item.icon;
            return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex h-11 shrink-0 items-center gap-3 rounded-lg border-l-4 px-3 text-sm font-bold transition",
                  isActive
                    ? "border-[#EE6C2F] bg-[var(--color-sidebar-active)] text-white shadow-sm"
                    : "border-transparent text-white/85 hover:border-[#EE6C2F]/70 hover:bg-white/10 hover:text-white",
                ].join(" ")
              }
            >
              <span className="flex h-8 min-w-8 items-center justify-center rounded-md bg-[#EE6C2F]/15 text-[#EE6C2F]">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="hidden lg:inline">{item.label}</span>
            </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
