import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { SourceBadge } from "../components/SourceBadge";
import { StatCard } from "../components/StatCard";
import { getApiErrorMessage } from "../lib/errors";
import { DashboardActivity, DashboardCount, DashboardStats, getDashboardStats } from "../services/dashboard";

const eventLabels: Record<string, string> = {
  candidate_created: "Candidate",
  candidate_updated: "Update",
  linkedin_csv_imported: "LinkedIn",
  outlook_imported: "Outlook",
  manual_cv_uploaded: "CV",
  cv_uploaded: "CV",
  cv_parsed: "CV",
  ai_match_generated: "Match",
  interview_scheduled: "Interview",
  evaluation_added: "Evaluation",
};

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function safeCounts(counts: DashboardCount[]) {
  return Array.isArray(counts) ? counts : [];
}

function ChartPanel({ title, counts }: { title: string; counts: DashboardCount[] }) {
  const rows = safeCounts(counts);
  const maxCount = Math.max(...rows.map((row) => row.count), 0);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-[#0B1F3A]">{title}</h2>
        <span className="text-xs font-medium uppercase text-slate-500">{rows.reduce((total, row) => total + row.count, 0)} total</span>
      </div>
      <div className="mt-5 space-y-4">
        {rows.length === 0 ? (
          <p className="text-sm text-slate-500">No data yet.</p>
        ) : (
          rows.map((row) => {
            const width = maxCount > 0 ? Math.max((row.count / maxCount) * 100, 6) : 0;
            return (
              <div key={row.name}>
                <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                  <span className="capitalize text-slate-700">{formatLabel(row.name)}</span>
                  <span className="font-semibold text-[#0B1F3A]">{row.count}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full bg-[#1D6EEA]" style={{ width: `${width}%` }} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

function RecentActivityFeed({ activities }: { activities: DashboardActivity[] }) {
  const activityArray = Array.isArray(activities) ? activities : [];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-[#0B1F3A]">Recent activity</h2>
        <span className="text-xs font-medium uppercase text-slate-500">CRM timeline</span>
      </div>
      {activityArray.length === 0 ? (
        <div className="mt-5">
          <EmptyState title="No recent activity" description="Candidate timeline events will appear here as the recruitment workflow moves." />
        </div>
      ) : (
        <div className="mt-5 divide-y divide-slate-100">
          {activityArray.map((activity) => (
            <article key={activity.id} className="flex gap-4 py-4 first:pt-0 last:pb-0">
              <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1D6EEA]/10 text-xs font-bold text-[#1D6EEA]">
                {eventLabels[activity.event_type]?.slice(0, 2).toUpperCase() ?? "AC"}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-[#0B1F3A]">{activity.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{activity.description ?? formatLabel(activity.event_type)}</p>
                  </div>
                  <time className="text-xs font-medium text-slate-500">{formatDate(activity.created_at)}</time>
                </div>
                <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                  <span className="rounded-full bg-slate-100 px-2 py-1 capitalize">{eventLabels[activity.event_type] ?? formatLabel(activity.event_type)}</span>
                  {typeof activity.metadata?.source === "string" ? <SourceBadge source={activity.metadata.source} /> : null}
                  {typeof activity.metadata?.candidate_source === "string" ? <SourceBadge source={activity.metadata.candidate_source} /> : null}
                  <Link className="font-semibold text-[#1D6EEA] hover:text-[#165AC0]" to={`/candidates/${activity.candidate_id}`}>
                    View candidate
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);
      try {
        const dashboardStats = await getDashboardStats();
        if (isMounted) {
          setStats(dashboardStats);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Unable to load dashboard statistics."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  const pipelineCounts = useMemo(() => safeCounts(stats?.candidate_counts ?? []), [stats?.candidate_counts]);
  const matchingBuckets = useMemo(() => safeCounts(stats?.matching_score_buckets ?? []), [stats?.matching_score_buckets]);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading dashboard statistics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!stats) {
    return <EmptyState title="Dashboard unavailable" description="No dashboard statistics were returned by the backend." />;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Candidates" value={String(stats.total_candidates)} detail="Profiles centralized in the recruitment database" />
        <StatCard label="Open jobs" value={String(stats.open_jobs)} detail={`${stats.total_jobs} total job offers tracked`} />
        <StatCard label="Interviews" value={String(stats.total_interviews)} detail={`${stats.upcoming_interviews} scheduled or rescheduled ahead`} />
        <StatCard label="Evaluations" value={String(stats.total_evaluations)} detail="Interview scorecards submitted by evaluators" />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Average match"
          value={stats.average_matching_score === null ? "N/A" : `${stats.average_matching_score.toFixed(1)}%`}
          detail="Mean score across generated matching results"
        />
        <StatCard label="Candidate statuses" value={String(pipelineCounts.length)} detail="Pipeline stages represented in the database" />
        <StatCard label="Job statuses" value={String(safeCounts(stats.job_counts).length)} detail="Draft, open, paused, closed, or archived jobs" />
        <StatCard label="Interview statuses" value={String(safeCounts(stats.interview_counts).length)} detail="Scheduling states currently represented" />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <ChartPanel title="Candidate pipeline" counts={pipelineCounts} />
        <ChartPanel title="Matching score distribution" counts={matchingBuckets} />
      </section>

      <RecentActivityFeed activities={stats.recent_activities} />
    </div>
  );
}
