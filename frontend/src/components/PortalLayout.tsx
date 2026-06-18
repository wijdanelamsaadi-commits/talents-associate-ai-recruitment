import { Link, NavLink, Outlet } from "react-router-dom";

const portalLinks = [
  { label: "Home", to: "/portal" },
  { label: "Jobs", to: "/portal/jobs" },
  { label: "Application status", to: "/portal/status" },
];

export function PortalLayout() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link to="/portal" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0B1F3A] text-sm font-bold text-white">TA</span>
            <span>
              <span className="block text-sm font-semibold text-[#0B1F3A]">Talents Associate</span>
              <span className="block text-xs text-slate-500">Candidate careers</span>
            </span>
          </Link>

          <nav className="flex flex-wrap items-center gap-2">
            {portalLinks.map((item) => (
              <NavLink
                className={({ isActive }) =>
                  [
                    "rounded-lg px-3 py-2 text-sm font-semibold transition",
                    isActive ? "bg-[#1D6EEA]/10 text-[#1D6EEA]" : "text-slate-600 hover:bg-slate-100 hover:text-[#0B1F3A]",
                  ].join(" ")
                }
                end={item.to === "/portal"}
                key={item.to}
                to={item.to}
              >
                {item.label}
              </NavLink>
            ))}
            <Link
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:border-[#1D6EEA] hover:text-[#1D6EEA]"
              to="/login"
            >
              Recruiter login
            </Link>
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
