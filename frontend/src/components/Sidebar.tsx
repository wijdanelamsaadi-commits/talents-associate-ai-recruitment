import { NavLink } from "react-router-dom";

type NavigationItem = {
  label: string;
  to: string;
  icon: string;
};

const navigation: NavigationItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: "D" },
  { label: "Candidates", to: "/candidates", icon: "C" },
  { label: "CV Upload", to: "/cv-upload", icon: "U" },
  { label: "Job Offers", to: "/jobs", icon: "J" },
  { label: "Matching", to: "/matching", icon: "M" },
  { label: "Interviews", to: "/interviews", icon: "I" },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-x-0 top-0 z-30 border-b border-white/10 bg-[#0B1F3A] text-white lg:inset-y-0 lg:right-auto lg:w-72 lg:border-b-0">
      <div className="flex h-16 items-center justify-between px-4 lg:h-auto lg:flex-col lg:items-stretch lg:gap-8 lg:px-6 lg:py-6">
        <NavLink to="/dashboard" className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1D6EEA] text-sm font-bold">
            TA
          </span>
          <span className="hidden min-w-0 sm:block">
            <span className="block truncate text-sm font-semibold">Talents Associate</span>
            <span className="block truncate text-xs text-slate-300">Recruitment AI</span>
          </span>
        </NavLink>

        <nav className="flex gap-1 overflow-x-auto lg:flex-col lg:gap-2 lg:overflow-visible">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex h-10 shrink-0 items-center gap-3 rounded-lg px-3 text-sm font-medium transition",
                  isActive
                    ? "bg-white text-[#0B1F3A]"
                    : "text-slate-300 hover:bg-white/10 hover:text-white",
                ].join(" ")
              }
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-current/10 text-xs font-bold">
                {item.icon}
              </span>
              <span className="hidden lg:inline">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="hidden rounded-lg border border-white/10 bg-white/5 p-4 lg:block">
          <p className="text-sm font-semibold">Recruitment workspace</p>
          <p className="mt-1 text-xs leading-5 text-slate-300">
            Centralize candidates, CV parsing, matching, and interview follow-up.
          </p>
        </div>
      </div>
    </aside>
  );
}
