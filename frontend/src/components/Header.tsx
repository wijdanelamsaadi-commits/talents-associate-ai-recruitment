import { Link, useLocation } from "react-router-dom";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/candidates": "Candidates",
  "/cv-upload": "CV Upload",
  "/jobs": "Job Offers",
  "/matching": "AI Matching",
  "/interviews": "Interviews",
};

export function Header() {
  const { pathname } = useLocation();
  const title = pageTitles[pathname] ?? (pathname.startsWith("/candidates/") ? "Candidate Details" : "Workspace");

  return (
    <header className="sticky top-16 z-20 border-b border-slate-200 bg-white/95 backdrop-blur lg:top-0">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-[#1D6EEA]">Recruitment platform</p>
          <h1 className="truncate text-xl font-semibold text-[#0B1F3A]">{title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600 sm:inline">
            Demo mode
          </span>
          <Link
            to="/login"
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-[#1D6EEA] hover:text-[#1D6EEA]"
          >
            Login
          </Link>
        </div>
      </div>
    </header>
  );
}
