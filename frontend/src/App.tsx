import {
  Activity,
  BrainCircuit,
  Database,
  FileCheck2,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";

import FileUploader from "./components/FileUploader";
import type {
  DatasetProfileResponse,
  Recommendation,
} from "./services/api";

type MetricCardProps = {
  title: string;
  value: string;
  description: string;
  icon: ReactNode;
};

type UnknownRecord = Record<string, unknown>;

function MetricCard({
  title,
  value,
  description,
  icon,
}: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
        </div>

        <div className="rounded-xl bg-blue-50 p-3 text-blue-700">
          {icon}
        </div>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-500">
        {description}
      </p>
    </article>
  );
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function getNumber(
  source: UnknownRecord,
  possibleKeys: string[],
): number | null {
  for (const key of possibleKeys) {
    const value = source[key];

    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
  }

  return null;
}

function getArray(
  source: UnknownRecord,
  possibleKeys: string[],
): unknown[] {
  for (const key of possibleKeys) {
    const value = source[key];

    if (Array.isArray(value)) {
      return value;
    }
  }

  return [];
}

function getString(
  source: UnknownRecord,
  possibleKeys: string[],
): string | null {
  for (const key of possibleKeys) {
    const value = source[key];

    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return null;
}

function formatInteger(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat("en-US").format(value);
}

function formatReliabilityScore(
  profile: DatasetProfileResponse | null,
): string {
  if (!profile) {
    return "—";
  }

  const rawScore = Number(profile.reliability_score);

  if (!Number.isFinite(rawScore)) {
    return "—";
  }

  const percentage = rawScore <= 1 ? rawScore * 100 : rawScore;

  return `${Math.round(percentage)}%`;
}

function getAnomalyCount(
  profile: DatasetProfileResponse | null,
): number | null {
  if (!profile) {
    return null;
  }

  const profileRecord = profile as UnknownRecord;

  const directCount = getNumber(profileRecord, [
    "anomaly_count",
    "ml_anomaly_count",
    "anomalies_count",
  ]);

  if (directCount !== null) {
    return directCount;
  }

  const anomalies = getArray(profileRecord, [
    "ml_anomalies",
    "anomalies",
    "anomaly_records",
  ]);

  return anomalies.length;
}

function getQualityIssueCount(
  profile: DatasetProfileResponse | null,
): number | null {
  if (!profile) {
    return null;
  }

  const profileRecord = profile as UnknownRecord;

  const directCount = getNumber(profileRecord, [
    "quality_issue_count",
    "total_quality_issues",
    "issue_count",
  ]);

  if (directCount !== null) {
    return directCount;
  }

  const missingValues =
    getNumber(profileRecord, [
      "total_missing_values",
      "missing_value_count",
      "missing_values",
    ]) ?? 0;

  const duplicateRows =
    getNumber(profileRecord, [
      "duplicate_rows",
      "duplicate_count",
      "duplicate_row_count",
    ]) ?? 0;

  const businessRules = getArray(profileRecord, [
    "business_rules",
    "rule_results",
    "business_rule_results",
  ]);

  const failedRuleCount = businessRules.reduce<number>(
  (count, rule) => {
    if (!isRecord(rule)) {
      return count;
    }

    const passed = rule.passed;
    const status = rule.status;

    if (
      passed === false ||
      status === "failed" ||
      status === "fail"
    ) {
      return count + 1;
    }

    const violationCount = getNumber(rule, [
      "violation_count",
      "violations",
      "failed_count",
    ]);

    return count + (violationCount ?? 0);
  },
  0,
);

  return missingValues + duplicateRows + failedRuleCount;
}

function getExecutiveSummary(
  profile: DatasetProfileResponse | null,
): string {
  if (!profile) {
    return (
      "Upload a dataset to generate a concise explanation of its " +
      "reliability, key risks, likely root causes, and recommended actions."
    );
  }

  const profileRecord = profile as UnknownRecord;

  return (
    getString(profileRecord, [
      "ai_summary",
      "executive_summary",
      "summary",
      "dataset_summary",
    ]) ??
    "The dataset analysis completed successfully. Review the reliability " +
      "score, detected quality issues, anomalies, and recommendations below."
  );
}

function getRecommendationText(
  recommendation: unknown,
): string | null {
  if (typeof recommendation === "string") {
    return recommendation.trim() || null;
  }

  if (!isRecord(recommendation)) {
    return null;
  }

  const title = getString(recommendation, [
    "title",
    "name",
    "action",
    "category",
  ]);

  const description = getString(recommendation, [
    "description",
    "recommendation",
    "message",
    "reason",
  ]);

  if (title && description) {
    return `${title}: ${description}`;
  }

  return title ?? description;
}

function getRecommendations(
  profile: DatasetProfileResponse | null,
): Recommendation[] | unknown[] {
  if (!profile) {
    return [];
  }

  const profileRecord = profile as UnknownRecord;

  return getArray(profileRecord, [
    "recommendations",
    "priority_recommendations",
    "ai_recommendations",
  ]);
}

function App() {
  const [datasetProfile, setDatasetProfile] =
    useState<DatasetProfileResponse | null>(null);

  const qualityIssueCount = getQualityIssueCount(datasetProfile);
  const anomalyCount = getAnomalyCount(datasetProfile);
  const recommendations = getRecommendations(datasetProfile);

  function handleUploadComplete(
    profile: DatasetProfileResponse,
  ): void {
    setDatasetProfile(profile);
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-700 p-2 text-white">
              <BrainCircuit size={24} />
            </div>

            <div>
              <h1 className="text-lg font-bold text-slate-950">
                SignalForge AI
              </h1>

              <p className="text-xs text-slate-500">
                AI Data Reliability Assistant
              </p>
            </div>
          </div>

          <div
            className={[
              "rounded-full px-3 py-1 text-sm font-medium",
              datasetProfile
                ? "bg-blue-50 text-blue-700"
                : "bg-emerald-50 text-emerald-700",
            ].join(" ")}
          >
            {datasetProfile ? "Analysis complete" : "System ready"}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-10">
        <section className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
              Dataset Intelligence
            </p>

            <h2 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight text-slate-950">
              Detect data-quality problems before they affect analytics
              and machine learning.
            </h2>

            <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
              Upload a CSV dataset to generate reliability metrics,
              business-rule validation, anomaly detection,
              recommendations, and AI-generated insights.
            </p>

            {datasetProfile && (
              <div className="mt-6 inline-flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
                <span className="font-semibold">
                  Dataset analyzed
                </span>

                <span className="text-blue-300">•</span>

                <span>ID: {datasetProfile.dataset_id}</span>
              </div>
            )}
          </div>

          <FileUploader onUploadComplete={handleUploadComplete} />
        </section>

        <section className="mt-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Reliability score"
            value={formatReliabilityScore(datasetProfile)}
            description="Overall quality score calculated from missing data, duplicates, and detected issues."
            icon={<ShieldCheck size={22} />}
          />

          <MetricCard
            title="Rows analyzed"
            value={formatInteger(
              datasetProfile?.row_count ?? null,
            )}
            description="Total number of dataset records processed by the profiling pipeline."
            icon={<Database size={22} />}
          />

          <MetricCard
            title="Quality issues"
            value={formatInteger(qualityIssueCount)}
            description="Missing values, duplicate records, invalid formats, and business-rule failures."
            icon={<FileCheck2 size={22} />}
          />

          <MetricCard
            title="ML anomalies"
            value={formatInteger(anomalyCount)}
            description="Potential unusual records detected by the Isolation Forest model."
            icon={<Activity size={22} />}
          />
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-violet-50 p-2 text-violet-700">
                <BrainCircuit size={20} />
              </div>

              <h3 className="text-lg font-semibold text-slate-950">
                AI executive summary
              </h3>
            </div>

            <p className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-600">
              {getExecutiveSummary(datasetProfile)}
            </p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-amber-50 p-2 text-amber-700">
                <FileCheck2 size={20} />
              </div>

              <h3 className="text-lg font-semibold text-slate-950">
                Priority recommendations
              </h3>
            </div>

            {recommendations.length > 0 ? (
              <ol className="mt-4 space-y-3">
                {recommendations.slice(0, 5).map((item, index) => {
                  const text =
                    getRecommendationText(item) ??
                    "Review this detected data-quality issue.";

                  return (
                    <li
                      key={`${index}-${text}`}
                      className="flex gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4"
                    >
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-700 text-xs font-bold text-white">
                        {index + 1}
                      </span>

                      <p className="text-sm leading-6 text-slate-600">
                        {text}
                      </p>
                    </li>
                  );
                })}
              </ol>
            ) : (
              <p className="mt-4 text-sm leading-7 text-slate-500">
                Upload a dataset to receive prioritized data-cleaning,
                validation, and risk-reduction recommendations.
              </p>
            )}
          </article>
        </section>
      </main>
    </div>
  );
}

export default App;