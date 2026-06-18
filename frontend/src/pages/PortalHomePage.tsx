import { Link } from "react-router-dom";

export function PortalHomePage() {
  return (
    <main>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:py-20">
          <div>
            <p className="text-sm font-semibold uppercase text-[#1D6EEA]">Candidate portal</p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight text-[#0B1F3A] sm:text-5xl">
              Find the right opportunity and apply with your CV.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
              Browse open roles, submit your profile, and let the platform extract your CV, structure your experience,
              and match you automatically with relevant job offers.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="rounded-lg bg-[#1D6EEA] px-5 py-3 text-sm font-semibold text-white hover:bg-[#165AC0]" to="/portal/jobs">
                Browse jobs
              </Link>
              <Link
                className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:border-[#1D6EEA] hover:text-[#1D6EEA]"
                to="/portal/status"
              >
                Track application
              </Link>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-lg font-semibold text-[#0B1F3A]">How it works</h2>
            <div className="mt-5 space-y-4">
              {[
                ["1", "Choose a job", "Explore public job offers without creating an account."],
                ["2", "Upload your CV", "Send your personal details and PDF or DOCX CV in one form."],
                ["3", "Automatic processing", "Extraction, parsing, matching, and CRM timeline updates run immediately."],
              ].map(([step, title, description]) => (
                <div className="flex gap-3" key={step}>
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#1D6EEA] text-sm font-bold text-white">
                    {step}
                  </span>
                  <div>
                    <p className="font-semibold text-[#0B1F3A]">{title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-4 py-10 sm:px-6 md:grid-cols-3">
        {[
          ["CV parsing", "Your CV text is extracted and converted into structured candidate data."],
          ["Smart matching", "Skills, experience, and diploma are compared against job requirements."],
          ["Status tracking", "Check submitted applications using your email address."],
        ].map(([title, description]) => (
          <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" key={title}>
            <h3 className="text-base font-semibold text-[#0B1F3A]">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
