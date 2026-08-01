import {
  Activity,
  Database,
  FileCheck2,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";

import AIInsights from "./components/AIInsights";
import ColumnProfiles from "./components/ColumnProfiles";
import CopilotChat, {
  createCopilotMessage,
} from "./components/CopilotChat";
import type {
  CopilotMessage,
} from "./components/CopilotChat";
import DatasetPreview from "./components/DatasetPreview";
import ExecutiveSummary from "./components/ExecutiveSummary";
import FileUploader from "./components/FileUploader";
import Header from "./components/Header";
import MetricCard from "./components/MetricCard";
import MissingValuesChart from "./components/MissingValuesChart";
import ReliabilityGauge from "./components/ReliabilityGauge";
import { askCopilot } from "./services/api";
import type {
  ColumnMetadata,
  DatasetProfileResponse,
  PreviewRow,
  Recommendation,
} from "./services/api";

type UnknownRecord = Record<string, unknown>;

function isRecord(
  value: unknown,
): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null
  );
}

function getNumber(
  source: UnknownRecord,
  possibleKeys: string[],
): number | null {
  for (const key of possibleKeys) {
    const value = source[key];

    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
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

    if (
      typeof value === "string" &&
      value.trim().length > 0
    ) {
      return value.trim();
    }
  }

  return null;
}

function formatInteger(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function getAnomalyCount(
  profile: DatasetProfileResponse | null,
): number | null {
  if (!profile) {
    return null;
  }

  const profileRecord =
    profile as UnknownRecord;

  const directCount = getNumber(
    profileRecord,
    [
      "anomaly_count",
      "ml_anomaly_count",
      "anomalies_count",
    ],
  );

  if (directCount !== null) {
    return directCount;
  }

  const anomalies = getArray(
    profileRecord,
    [
      "ml_anomalies",
      "anomalies",
      "anomaly_records",
    ],
  );

  return anomalies.length;
}

function getQualityIssueCount(
  profile: DatasetProfileResponse | null,
): number | null {
  if (!profile) {
    return null;
  }

  const profileRecord =
    profile as UnknownRecord;

  const directCount = getNumber(
    profileRecord,
    [
      "quality_issue_count",
      "total_quality_issues",
      "issue_count",
    ],
  );

  if (directCount !== null) {
    return directCount;
  }

  const issues = getArray(
    profileRecord,
    [
      "issues",
      "quality_issues",
    ],
  );

  const missingValues =
    getNumber(
      profileRecord,
      [
        "total_missing_values",
        "missing_value_count",
        "missing_values",
      ],
    ) ?? 0;

  const duplicateRows =
    getNumber(
      profileRecord,
      [
        "duplicate_rows",
        "duplicate_count",
        "duplicate_row_count",
      ],
    ) ?? 0;

  const businessRules = getArray(
    profileRecord,
    [
      "business_rules",
      "rule_results",
      "business_rule_results",
    ],
  );

  const failedRuleCount =
    businessRules.reduce<number>(
      (count, rule) => {
        if (!isRecord(rule)) {
          return count;
        }

        const passed = rule.passed;
        const status =
          typeof rule.status === "string"
            ? rule.status.toLowerCase()
            : "";

        if (
          passed === false ||
          status === "failed" ||
          status === "fail"
        ) {
          return count + 1;
        }

        const violationCount =
          getNumber(
            rule,
            [
              "violation_count",
              "violations",
              "failed_count",
            ],
          );

        return (
          count +
          (violationCount ?? 0)
        );
      },
      0,
    );

  return (
    issues.length +
    missingValues +
    duplicateRows +
    failedRuleCount
  );
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

  const profileRecord =
    profile as UnknownRecord;

  return (
    getString(
      profileRecord,
      [
        "ai_summary",
        "executive_summary",
        "summary",
        "dataset_summary",
      ],
    ) ??
    "The dataset analysis completed successfully. Review the reliability " +
      "score, detected quality issues, anomalies, and recommendations below."
  );
}

function getRecommendationText(
  recommendation: unknown,
): string | null {
  if (
    typeof recommendation === "string"
  ) {
    return (
      recommendation.trim() ||
      null
    );
  }

  if (!isRecord(recommendation)) {
    return null;
  }

  const title = getString(
    recommendation,
    [
      "title",
      "name",
      "action",
      "category",
    ],
  );

  const description = getString(
    recommendation,
    [
      "description",
      "recommendation",
      "message",
      "reason",
    ],
  );

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

  const profileRecord =
    profile as UnknownRecord;

  return getArray(
    profileRecord,
    [
      "recommendations",
      "priority_recommendations",
      "ai_recommendations",
    ],
  );
}

function getColumnMetadata(
  profile: DatasetProfileResponse | null,
): ColumnMetadata[] {
  if (!profile) {
    return [];
  }

  if (
    Array.isArray(
      profile.column_metadata,
    )
  ) {
    return profile.column_metadata;
  }

  if (
    Array.isArray(
      profile.columns,
    )
  ) {
    return profile.columns;
  }

  return [];
}

function getPreviewColumns(
  profile: DatasetProfileResponse | null,
): string[] {
  if (!profile) {
    return [];
  }

  return Array.isArray(
    profile.preview_columns,
  )
    ? profile.preview_columns
    : [];
}

function getPreviewRows(
  profile: DatasetProfileResponse | null,
): PreviewRow[] {
  if (!profile) {
    return [];
  }

  return Array.isArray(
    profile.preview_rows,
  )
    ? profile.preview_rows
    : [];
}

function App() {
  const [
    datasetProfile,
    setDatasetProfile,
  ] =
    useState<DatasetProfileResponse | null>(
      null,
    );

  const [
    copilotMessages,
    setCopilotMessages,
  ] =
    useState<CopilotMessage[]>([]);

  const [
    isCopilotLoading,
    setIsCopilotLoading,
  ] = useState(false);

  const [
    copilotError,
    setCopilotError,
  ] =
    useState<string | null>(null);

  const qualityIssueCount =
    getQualityIssueCount(
      datasetProfile,
    );

  const anomalyCount =
    getAnomalyCount(
      datasetProfile,
    );

  const recommendations =
    getRecommendations(
      datasetProfile,
    );

  const executiveSummary =
    getExecutiveSummary(
      datasetProfile,
    );

  const columnMetadata =
    getColumnMetadata(
      datasetProfile,
    );

  const previewColumns =
    getPreviewColumns(
      datasetProfile,
    );

  const previewRows =
    getPreviewRows(
      datasetProfile,
    );

  function handleUploadComplete(
    profile: DatasetProfileResponse,
  ): void {
    setDatasetProfile(profile);
    setCopilotMessages([]);
    setCopilotError(null);
    setIsCopilotLoading(false);
  }

  async function handleCopilotQuestion(
    question: string,
  ): Promise<void> {
    if (
      !datasetProfile ||
      isCopilotLoading
    ) {
      return;
    }

    const userMessage =
      createCopilotMessage(
        "user",
        question,
      );

    setCopilotMessages(
      (currentMessages) => [
        ...currentMessages,
        userMessage,
      ],
    );

    setCopilotError(null);
    setIsCopilotLoading(true);

    try {
      const response =
        await askCopilot(
          datasetProfile.dataset_id,
          question,
        );

      const assistantMessage =
        createCopilotMessage(
          "assistant",
          response.answer,
        );

      setCopilotMessages(
        (currentMessages) => [
          ...currentMessages,
          assistantMessage,
        ],
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The AI copilot could " +
              "not answer the question."
            );

      setCopilotError(message);
    } finally {
      setIsCopilotLoading(false);
    }
  }

  function handleClearConversation(): void {
    setCopilotMessages([]);
    setCopilotError(null);
  }

  async function handleRegenerateLastAnswer(): Promise<void> {
    if (
      !datasetProfile ||
      isCopilotLoading
    ) {
      return;
    }

    const lastUserMessage =
      [...copilotMessages]
        .reverse()
        .find(
          (message) =>
            message.role === "user",
        );

    if (!lastUserMessage) {
      return;
    }

    setCopilotError(null);
    setIsCopilotLoading(true);

    try {
      const response =
        await askCopilot(
          datasetProfile.dataset_id,
          lastUserMessage.content,
        );

      const assistantMessage =
        createCopilotMessage(
          "assistant",
          response.answer,
        );

      setCopilotMessages(
        (currentMessages) => [
          ...currentMessages,
          assistantMessage,
        ],
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The AI copilot could " +
              "not regenerate the answer."
            );

      setCopilotError(message);
    } finally {
      setIsCopilotLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header
        hasCompletedAnalysis={
          datasetProfile !== null
        }
      />

      <main className="mx-auto max-w-7xl px-6 py-10">
        <section className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
              Dataset Intelligence
            </p>

            <h2 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight text-slate-950">
              Detect data-quality problems before they affect
              analytics and machine learning.
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

                <span className="text-blue-300">
                  •
                </span>

                <span>
                  ID: {datasetProfile.dataset_id}
                </span>
              </div>
            )}
          </div>

          <FileUploader
            onUploadComplete={
              handleUploadComplete
            }
          />
        </section>

        <section className="mt-10 grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
          <ReliabilityGauge
            score={
              datasetProfile
                ?.reliability_score ??
              null
            }
          />

          <div className="grid gap-5 sm:grid-cols-2">
            <MetricCard
              title="Rows analyzed"
              value={formatInteger(
                datasetProfile
                  ?.row_count ??
                  null,
              )}
              description="Total number of dataset records processed by the profiling pipeline."
              icon={
                <Database size={22} />
              }
            />

            <MetricCard
              title="Columns analyzed"
              value={formatInteger(
                datasetProfile
                  ?.column_count ??
                  null,
              )}
              description="Total number of columns included in the uploaded dataset."
              icon={
                <ShieldCheck size={22} />
              }
            />

            <MetricCard
              title="Quality issues"
              value={formatInteger(
                qualityIssueCount,
              )}
              description="Missing values, duplicate records, invalid formats, and business-rule failures."
              icon={
                <FileCheck2 size={22} />
              }
            />

            <MetricCard
              title="ML anomalies"
              value={formatInteger(
                anomalyCount,
              )}
              description="Potential unusual records detected by the Isolation Forest model."
              icon={
                <Activity size={22} />
              }
            />
          </div>
        </section>

        <section className="mt-10">
          <AIInsights
            profile={datasetProfile}
          />
        </section>

        <section className="mt-10">
          <MissingValuesChart
            columns={
              columnMetadata
            }
          />
        </section>

        <section className="mt-10">
          <DatasetPreview
            columns={
              previewColumns
            }
            rows={previewRows}
          />
        </section>

        <section className="mt-10">
          <ColumnProfiles
            columns={
              columnMetadata
            }
          />
        </section>

        <section className="mt-10">
          <CopilotChat
            datasetId={
              datasetProfile
                ?.dataset_id ??
              null
            }
            messages={
              copilotMessages
            }
            isLoading={
              isCopilotLoading
            }
            errorMessage={
              copilotError
            }
            onSendQuestion={
              handleCopilotQuestion
            }
            onClearConversation={
              handleClearConversation
            }
            onRegenerateLastAnswer={
              handleRegenerateLastAnswer
            }
          />
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-2">
          <ExecutiveSummary
            summary={
              executiveSummary
            }
          />

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
                {recommendations
                  .slice(0, 5)
                  .map(
                    (
                      item,
                      index,
                    ) => {
                      const text =
                        getRecommendationText(
                          item,
                        ) ??
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
                    },
                  )}
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