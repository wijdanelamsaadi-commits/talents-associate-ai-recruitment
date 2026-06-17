import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#0B1F3A] text-sm font-bold text-white">
            TA
          </div>
          <h1 className="mt-5 text-2xl font-semibold text-[#0B1F3A]">Recruiter login</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Authentication will be connected in a later backend module.
          </p>
        </div>

        <form className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              placeholder="recruiter@talents-associate.com"
              type="email"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              placeholder="Password"
              type="password"
            />
          </label>
          <button
            className="w-full rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0]"
            type="button"
          >
            Continue
          </button>
        </form>

        <Link className="mt-6 block text-center text-sm font-semibold text-[#1D6EEA]" to="/dashboard">
          Open demo dashboard
        </Link>
      </section>
    </main>
  );
}
