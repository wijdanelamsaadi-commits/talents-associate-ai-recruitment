import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { Candidate, getCandidateById } from "../services/candidates";
import { TimelineEvent, getCandidateTimeline } from "../services/timeline";

type TimelineFilter = "all" | "cv" | "matching" | "interview" | "evaluation";

const filters: Array<{ label: string; value: TimelineFilter }> = [
  { label: "All", value: "all" },
  { label: "CV", value: "cv" },
  { label: "Matching", value: "matching" },
  { label: "Interview", value: "interview" },
  { label: "Evaluation", value: "evaluation" },
];

const filterEventTypes: Record<Exclude<TimelineFilter, "all">, string[]> = {
  cv: ["cv_uploaded", "cv_parsed"],
  matching: ["ai_match_generated"],
  interview: ["interview_scheduled"],
  evaluation: ["evaluation_added"],
};

function eventIcon(eventType: string) {
  if (eventType.startsWith("cv_")) return "CV";
  if (eventType === "ai_match_generated") return "AI";
  if (eventType === "interview_scheduled") return "IN";
  if (eventType === "evaluation_added") return "EV";
  if (eventType.startsWith("candidate_")) return "CA";
  return "NO";
}

function formatEventType(eventType: string) {
  return eventType.replaceAll("_", " ");
}

export function CandidateDetailsPage() {
  const { candidateId } = useParams();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [activeFilter, setActiveFilter] = useState<TimelineFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCandidate() {
      if (!candidateId) {
        setError("Candidate id is missing.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const [candidateData, timelineData] = await Promise.all([
          getCandidateById(candidateId),
          getCandidateTimeline(candidateId),
        ]);
        setCandidate(candidateData);
        setTimeline(timelineData);
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Unable to load candidate details. Check the candidate ID and backend connection."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadCandidate();
  }, [candidateId]);

  const filteredTimeline = useMemo(() => {
    if (activeFilter === "all") {
      return timeline;
    }
    return timeline.filter((event) => filterEventTypes[activeFilter].includes(event.event_type));
  }, [activeFilter, timeline]);

  if (isLoading) {
    return <section className="rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">Loading candidate...</section>;
  }

  if (error || !candidate) {
    return (
      <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p>{error ?? "Candidate not found."}</p>
        <Link className="mt-4 inline-block font-semibold text-red-800 underline" to="/candidates">
          Back to candidates
        </Link>
      </section>
    );
  }

  const fullName = `${candidate.first_name} ${candidate.last_name}`;

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#1D6EEA]">Candidate profile</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#0B1F3A]">{fullName}</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
          <p>
            <span className="block font-semibold text-slate-500">Email</span>
            {candidate.email ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Phone</span>
            {candidate.phone ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">City</span>
            {candidate.location ?? "-"}
          </p>
          <p>
            <span className="block font-semibold text-slate-500">Source</span>
            {candidate.source.replaceAll("_", " ")}
          </p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Status" value={candidate.status.replaceAll("_", " ")} detail="Current recruitment pipeline stage" />
        <StatCard label="Created" value={new Date(candidate.created_at).toLocaleDateString()} detail="Backend creation date" />
        <StatCard label="Timeline events" value={String(timeline.length)} detail="CRM history entries" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          title="CV profile summary"
          description="Uploaded CV files, extracted text, and parsed profile data are tracked in the CRM timeline."
        />
        <EmptyState
          title="Recruitment activity"
          description="Matching, interviews, evaluations, and manual notes appear below as candidate history."
        />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
          <div>
            <h3 className="text-base font-semibold text-[#0B1F3A]">CRM timeline</h3>
            <p className="mt-1 text-sm text-slate-600">Chronological candidate history and recruitment activity.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <button
                className={[
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                  activeFilter === filter.value
                    ? "bg-[#1D6EEA] text-white"
                    : "border border-slate-300 text-slate-700 hover:bg-slate-50",
                ].join(" ")}
                key={filter.value}
                onClick={() => setActiveFilter(filter.value)}
                type="button"
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {filteredTimeline.length === 0 ? (
          <div className="p-5">
            <EmptyState title="No timeline events" description="No CRM history entries match this filter yet." />
          </div>
        ) : (
          <ol className="divide-y divide-slate-100">
            {filteredTimeline.map((event) => (
              <li className="flex gap-4 px-5 py-5" key={event.id}>
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1D6EEA]/10 text-xs font-bold text-[#1D6EEA]">
                  {eventIcon(event.event_type)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h4 className="font-semibold text-[#0B1F3A]">{event.title}</h4>
                    <time className="text-xs font-medium text-slate-500">{new Date(event.created_at).toLocaleString()}</time>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{event.description ?? formatEventType(event.event_type)}</p>
                  <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {formatEventType(event.event_type)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
