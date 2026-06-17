import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage } from "../lib/errors";

export function LoginPage() {
  const { isAuthenticated, isCheckingAuth, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/dashboard";
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
  }, [mode]);

  if (!isCheckingAuth && isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await register({ full_name: fullName, email, password });
      } else {
        await login({ email, password });
      }
      navigate(from, { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, mode === "register" ? "Registration failed." : "Login failed."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#0B1F3A] text-sm font-bold text-white">
            TA
          </div>
          <h1 className="mt-5 text-2xl font-semibold text-[#0B1F3A]">
            {mode === "register" ? "Create recruiter account" : "Recruiter login"}
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Access the recruitment workspace with your recruiter email and password.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "register" ? (
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Full name</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Recruiter name"
                required
                type="text"
                value={fullName}
              />
            </label>
          ) : null}
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="recruiter@talents-associate.com"
              required
              type="email"
              value={email}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
              minLength={mode === "register" ? 8 : 1}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              required
              type="password"
              value={password}
            />
          </label>
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}
          <button
            className="w-full rounded-lg bg-[#1D6EEA] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#165AC0] disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Please wait..." : mode === "register" ? "Create account" : "Login"}
          </button>
        </form>

        <button
          className="mt-6 w-full text-center text-sm font-semibold text-[#1D6EEA] hover:text-[#165AC0]"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          type="button"
        >
          {mode === "login" ? "Create the first recruiter account" : "I already have an account"}
        </button>
      </section>
    </main>
  );
}
