import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";

import type {
  BusinessRule,
  DatasetProfileResponse,
  Recommendation,
} from "../services/api";

type AIInsightsProps = {
  profile: DatasetProfileResponse | null;
};

type RiskLevel = "Low" | "Medium" | "High";

type InsightItem = {
  label: string;
  detail: string;
};

function normalizeScore(
  score: number | undefined,
): number {
  if (
    typeof score !== "number" ||
    !Number.isFinite(score)
  ) {
    return 0;
  }

  const percentage =
    score <= 1
      ? score * 100
      : score;

  return Math.min(
    Math.max(percentage, 0),
    100,
  );
}

function getFailedBusinessRules(
  rules: BusinessRule[],
): BusinessRule[] {
  return rules.filter((rule) => {
    const status =
      typeof rule.status === "string"
        ? rule.status.toLowerCase()
        : "";

    const violations =
      typeof rule.violation_count === "number"
        ? rule.violation_count
        : typeof rule.violations === "number"
          ? rule.violations
          : typeof rule.failed_count === "number"
            ? rule.failed_count
            : 0;

    return (
      rule.passed === false ||
      status === "failed" ||
      status === "fail" ||
      violations > 0
    );
  });
}

function getMissingValueCount(
  profile: DatasetProfileResponse,
): number {
  if (
    typeof profile.total_missing_values === "number"
  ) {
    return Math.max(
      0,
      profile.total_missing_values,
    );
  }

  return profile.columns.reduce(
    (total, column) => {
      const missing =
        typeof column.missing_count === "number"
          ? column.missing_count
          : typeof column.null_count === "number"
            ? column.null_count
            : 0;

      return total + missing;
    },
    0,
  );
}

function getAnomalyCount(
  profile: DatasetProfileResponse,
): number {
  if (
    typeof profile.anomaly_count === "number"
  ) {
    return Math.max(
      0,
      profile.anomaly_count,
    );
  }

  if (
    typeof profile.ml_anomaly_count === "number"
  ) {
    return Math.max(
      0,
      profile.ml_anomaly_count,
    );
  }

  return Array.isArray(profile.ml_anomalies)
    ? profile.ml_anomalies.length
    : 0;
}

function getRecommendationText(
  recommendation: Recommendation,
): string | null {
  if (
    typeof recommendation === "string"
  ) {
    return (
      recommendation.trim() ||
      null
    );
  }

  const title =
    typeof recommendation.title === "string"
      ? recommendation.title.trim()
      : "";

  const action =
    typeof recommendation.action === "string"
      ? recommendation.action.trim()
      : "";

  const description =
    typeof recommendation.description === "string"
      ? recommendation.description.trim()
      : typeof recommendation.recommendation === "string"
        ? recommendation.recommendation.trim()
        : typeof recommendation.message === "string"
          ? recommendation.message.trim()
          : "";

  if (title && description) {
    return `${title}: ${description}`;
  }

  return (
    title ||
    action ||
    description ||
    null
  );
}

function getRiskLevel(
  profile: DatasetProfileResponse,
): RiskLevel {
  const reliabilityScore =
    normalizeScore(
      profile.reliability_score,
    );

  const failedRules =
    getFailedBusinessRules(
      profile.business_rules,
    ).length;

  const anomalies =
    getAnomalyCount(profile);

  const missingValues =
    getMissingValueCount(profile);

  if (
    reliabilityScore < 70 ||
    failedRules >= 4 ||
    anomalies >= 20 ||
    missingValues >= 100
  ) {
    return "High";
  }

  if (
    reliabilityScore < 90 ||
    failedRules > 0 ||
    anomalies > 0 ||
    missingValues > 0
  ) {
    return "Medium";
  }

  return "Low";
}

function getRiskClasses(
  risk: RiskLevel,
): string {
  if (risk === "High") {
    return "bg-red-50 text-red-700";
  }

  if (risk === "Medium") {
    return "bg-amber-50 text-amber-700";
  }

  return "bg-emerald-50 text-emerald-700";
}

function getProductionReadiness(
  profile: DatasetProfileResponse,
): {
  ready: boolean;
  label: string;
  detail: string;
} {
  const reliabilityScore =
    normalizeScore(
      profile.reliability_score,
    );

  const failedRules =
    getFailedBusinessRules(
      profile.business_rules,
    ).length;

  const anomalies =
    getAnomalyCount(profile);

  const ready =
    reliabilityScore >= 90 &&
    failedRules === 0 &&
    anomalies === 0 &&
    profile.duplicate_rows === 0;

  if (ready) {
    return {
      ready: true,
      label: "Ready for controlled use",
      detail:
        "The automated checks did not identify major blockers, but domain validation is still recommended.",
    };
  }

  return {
    ready: false,
    label: "Needs remediation",
    detail:
      "Resolve validation failures, anomalies, duplicates, and other quality findings before production use.",
  };
}

function getEstimatedCleaningTime(
  profile: DatasetProfileResponse,
): string {
  const failedRules =
    getFailedBusinessRules(
      profile.business_rules,
    ).length;

  const anomalies =
    getAnomalyCount(profile);

  const missingValues =
    getMissingValueCount(profile);

  const duplicateRows =
    profile.duplicate_rows ?? 0;

  const effortScore =
    failedRules * 3 +
    Math.ceil(anomalies / 5) +
    Math.ceil(missingValues / 25) +
    Math.ceil(duplicateRows / 10);

  if (effortScore <= 2) {
    return "5–10 minutes";
  }

  if (effortScore <= 6) {
    return "15–30 minutes";
  }

  if (effortScore <= 12) {
    return "30–60 minutes";
  }

  return "More than 1 hour";
}

function getConfidenceScore(
  profile: DatasetProfileResponse,
): number {
  const rowFactor =
    Math.min(
      profile.row_count / 500,
      1,
    ) * 20;

  const columnFactor =
    Math.min(
      profile.column_count / 20,
      1,
    ) * 15;

  const profileCoverage =
    Array.isArray(profile.columns) &&
    profile.columns.length > 0
      ? 35
      : 0;

  const ruleCoverage =
    Array.isArray(
      profile.business_rules,
    ) &&
    profile.business_rules.length > 0
      ? 15
      : 0;

  const anomalyCoverage =
    Array.isArray(
      profile.ml_anomalies,
    )
      ? 15
      : 0;

  return Math.round(
    Math.min(
      rowFactor +
        columnFactor +
        profileCoverage +
        ruleCoverage +
        anomalyCoverage,
      100,
    ),
  );
}

function buildCleaningPriorities(
  profile: DatasetProfileResponse,
): InsightItem[] {
  const items: InsightItem[] = [];

  const failedRules =
    getFailedBusinessRules(
      profile.business_rules,
    );

  const missingValues =
    getMissingValueCount(profile);

  const anomalyCount =
    getAnomalyCount(profile);

  if (failedRules.length > 0) {
    items.push({
      label: "Fix failed business rules",
      detail: `${failedRules.length} rule check${
        failedRules.length === 1
          ? ""
          : "s"
      } require attention.`,
    });
  }

  if (profile.duplicate_rows > 0) {
    items.push({
      label: "Review duplicate records",
      detail: `${profile.duplicate_rows} duplicate row${
        profile.duplicate_rows === 1
          ? ""
          : "s"
      } detected.`,
    });
  }

  if (missingValues > 0) {
    items.push({
      label: "Handle missing values",
      detail: `${missingValues} missing value${
        missingValues === 1
          ? ""
          : "s"
      } detected across the profile.`,
    });
  }

  if (anomalyCount > 0) {
    items.push({
      label: "Investigate anomalies",
      detail: `${anomalyCount} record${
        anomalyCount === 1
          ? ""
          : "s"
      } flagged by the anomaly model.`,
    });
  }

  for (const recommendation of profile.recommendations) {
    const text =
      getRecommendationText(
        recommendation,
      );

    if (
      text &&
      !items.some(
        (item) =>
          item.label === text,
      )
    ) {
      items.push({
        label: text,
        detail:
          "Recommended by the SignalForge profiling pipeline.",
      });
    }

    if (items.length >= 5) {
      break;
    }
  }

  if (items.length === 0) {
    items.push({
      label: "Continue domain validation",
      detail:
        "No major automated issues were found, but business and source-system checks are still recommended.",
    });
  }

  return items.slice(0, 5);
}

export default function AIInsights({
  profile,
}: AIInsightsProps) {
  if (!profile) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Decision intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              AI insights
            </h3>
          </div>
        </div>

        <div className="flex min-h-64 items-center justify-center text-center">
          <p className="max-w-md text-sm leading-6 text-slate-500">
            Upload and analyze a dataset to generate risk,
            readiness, effort, and cleaning-priority insights.
          </p>
        </div>
      </section>
    );
  }

  const risk =
    getRiskLevel(profile);

  const readiness =
    getProductionReadiness(profile);

  const cleaningTime =
    getEstimatedCleaningTime(
      profile,
    );

  const confidence =
    getConfidenceScore(profile);

  const priorities =
    buildCleaningPriorities(
      profile,
    );

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Decision intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              AI insights
            </h3>
          </div>
        </div>

        <span
          className={[
            "rounded-full px-3 py-1 text-xs font-semibold",
            getRiskClasses(risk),
          ].join(" ")}
        >
          {risk} overall risk
        </span>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">
              Overall risk
            </p>

            <ShieldAlert
              size={20}
              className={
                risk === "High"
                  ? "text-red-600"
                  : risk === "Medium"
                    ? "text-amber-600"
                    : "text-emerald-600"
              }
            />
          </div>

          <p className="mt-3 text-2xl font-bold text-slate-950">
            {risk}
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Based on reliability, validation failures,
            anomalies, missing values, and duplicates.
          </p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">
              Production readiness
            </p>

            {readiness.ready ? (
              <CheckCircle2
                size={20}
                className="text-emerald-600"
              />
            ) : (
              <AlertTriangle
                size={20}
                className="text-amber-600"
              />
            )}
          </div>

          <p className="mt-3 text-xl font-bold text-slate-950">
            {readiness.label}
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            {readiness.detail}
          </p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">
              Estimated cleaning time
            </p>

            <Clock3
              size={20}
              className="text-blue-600"
            />
          </div>

          <p className="mt-3 text-2xl font-bold text-slate-950">
            {cleaningTime}
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Approximation based on the number and severity of
            automated findings.
          </p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">
              Analysis confidence
            </p>

            <Target
              size={20}
              className="text-violet-600"
            />
          </div>

          <p className="mt-3 text-2xl font-bold text-slate-950">
            {confidence}%
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Reflects dataset size and the available profiling,
            rule, and anomaly coverage.
          </p>
        </article>
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 p-5">
        <h4 className="text-base font-semibold text-slate-950">
          Recommended cleaning order
        </h4>

        <ol className="mt-4 space-y-3">
          {priorities.map(
            (item, index) => (
              <li
                key={`${index}-${item.label}`}
                className="flex gap-3 rounded-xl bg-slate-50 p-4"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-700 text-sm font-bold text-white">
                  {index + 1}
                </span>

                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {item.label}
                  </p>

                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    {item.detail}
                  </p>
                </div>
              </li>
            ),
          )}
        </ol>
      </div>
    </section>
  );
}