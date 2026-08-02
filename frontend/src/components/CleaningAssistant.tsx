import {
  AlertCircle,
  ArrowRight,
  Check,
  Clipboard,
  Code2,
  Download,
  FileCode2,
  Loader2,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCleaningPlan,
  getCleaningScriptUrl,
} from "../services/api";
import type {
  CleaningAction,
  CleaningPlanResponse,
  CleaningScriptFormat,
} from "../services/api";

type CleaningAssistantProps = {
  datasetId: string | null;
};

type CodeTab = CleaningScriptFormat;

const CODE_TABS: Array<{
  value: CodeTab;
  label: string;
}> = [
  {
    value: "pandas",
    label: "Pandas",
  },
  {
    value: "pyspark",
    label: "PySpark",
  },
  {
    value: "sql",
    label: "SQL",
  },
];

function normalizeScore(
  score: number,
): number {
  const normalized =
    score <= 1
      ? score * 100
      : score;

  return Math.min(
    Math.max(normalized, 0),
    100,
  );
}

function formatScore(
  score: number,
): string {
  return `${normalizeScore(
    score,
  ).toFixed(2)}%`;
}

function formatGain(
  gain: number,
): string {
  const normalized =
    Number.isFinite(gain)
      ? gain
      : 0;

  return `+${
    normalized.toFixed(2)
  }`;
}

function formatCategory(
  category: string,
): string {
  return category
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}

function getPriorityClasses(
  priority: number,
): string {
  if (priority === 1) {
    return (
      "bg-red-50 text-red-700 " +
      "border-red-200"
    );
  }

  if (priority === 2) {
    return (
      "bg-amber-50 text-amber-700 " +
      "border-amber-200"
    );
  }

  return (
    "bg-blue-50 text-blue-700 " +
    "border-blue-200"
  );
}

function getActionCode(
  action: CleaningAction,
  tab: CodeTab,
): string {
  if (tab === "pandas") {
    return action.pandas_code;
  }

  if (tab === "pyspark") {
    return action.pyspark_code;
  }

  return action.sql_code;
}

function buildCombinedCode(
  actions: CleaningAction[],
  tab: CodeTab,
): string {
  if (actions.length === 0) {
    return (
      tab === "sql"
        ? "-- No cleaning actions were generated."
        : "# No cleaning actions were generated."
    );
  }

  const commentPrefix =
    tab === "sql"
      ? "--"
      : "#";

  return actions
    .map(
      (
        action,
        index,
      ) => {
        const code =
          getActionCode(
            action,
            tab,
          );

        return [
          `${commentPrefix} Action ${
            index + 1
          }: ${action.title}`,
          `${commentPrefix} Reason: ${
            action.reason
          }`,
          code,
        ].join("\n");
      },
    )
    .join("\n\n");
}

function downloadFromUrl(
  url: string,
): void {
  const anchor =
    document.createElement("a");

  anchor.href = url;
  anchor.rel = "noopener";
  anchor.target = "_blank";

  document.body.appendChild(
    anchor,
  );

  anchor.click();
  anchor.remove();
}

function CleaningActionCard({
  action,
  index,
}: {
  action: CleaningAction;
  index: number;
}) {
  const [
    activeTab,
    setActiveTab,
  ] =
    useState<CodeTab>("pandas");

  const [
    copied,
    setCopied,
  ] =
    useState(false);

  const activeCode =
    getActionCode(
      action,
      activeTab,
    );

  async function handleCopy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(
        activeCode,
      );

      setCopied(true);

      window.setTimeout(
        () => {
          setCopied(false);
        },
        1500,
      );
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-700 text-sm font-bold text-white">
              {index + 1}
            </div>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={[
                    "rounded-full border px-2.5 py-1 text-xs font-semibold",
                    getPriorityClasses(
                      action.priority,
                    ),
                  ].join(" ")}
                >
                  Priority {
                    action.priority
                  }
                </span>

                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                  {formatCategory(
                    action.category,
                  )}
                </span>
              </div>

              <h4 className="mt-3 text-base font-semibold text-slate-950">
                {action.title}
              </h4>

              {action.column && (
                <p className="mt-1 text-sm font-medium text-indigo-700">
                  Column: {
                    action.column
                  }
                </p>
              )}

              <p className="mt-2 text-sm leading-6 text-slate-500">
                {action.reason}
              </p>
            </div>
          </div>

          <div className="shrink-0 rounded-xl bg-emerald-50 px-3 py-2 text-right">
            <p className="text-xs font-medium text-emerald-700">
              Estimated gain
            </p>

            <p className="mt-1 text-lg font-bold text-emerald-800">
              +{
                action.estimated_score_gain.toFixed(
                  2,
                )
              }
            </p>
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex rounded-xl bg-slate-100 p-1">
            {CODE_TABS.map(
              (tab) => (
                <button
                  key={tab.value}
                  type="button"
                  onClick={() =>
                    setActiveTab(
                      tab.value,
                    )
                  }
                  className={[
                    "rounded-lg px-3 py-2 text-xs font-semibold transition",
                    activeTab ===
                    tab.value
                      ? "bg-white text-indigo-700 shadow-sm"
                      : "text-slate-500 hover:text-slate-800",
                  ].join(" ")}
                >
                  {tab.label}
                </button>
              ),
            )}
          </div>

          <button
            type="button"
            onClick={() =>
              void handleCopy()
            }
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700"
          >
            {copied ? (
              <>
                <Check size={14} />
                Copied
              </>
            ) : (
              <>
                <Clipboard
                  size={14}
                />
                Copy code
              </>
            )}
          </button>
        </div>

        <pre className="mt-4 max-h-80 overflow-auto rounded-2xl bg-slate-950 p-5 text-xs leading-6 text-slate-100">
          <code>
            {activeCode}
          </code>
        </pre>

        <div className="mt-3 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
          Review this generated code before applying it to production
          data. Business-rule corrections may require domain-specific
          logic.
        </div>
      </div>
    </article>
  );
}

export default function CleaningAssistant({
  datasetId,
}: CleaningAssistantProps) {
  const [
    cleaningPlan,
    setCleaningPlan,
  ] =
    useState<CleaningPlanResponse | null>(
      null,
    );

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] =
    useState<string | null>(null);

  const [
    combinedCodeTab,
    setCombinedCodeTab,
  ] =
    useState<CodeTab>("pandas");

  const [
    copiedCombinedCode,
    setCopiedCombinedCode,
  ] = useState(false);

  async function loadCleaningPlan(): Promise<void> {
    if (!datasetId) {
      setCleaningPlan(null);
      setErrorMessage(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const plan =
        await getCleaningPlan(
          datasetId,
        );

      setCleaningPlan(plan);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The cleaning plan could " +
              "not be loaded."
            );

      setErrorMessage(message);
      setCleaningPlan(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadCleaningPlan();
  }, [datasetId]);

  const combinedCode =
    useMemo(
      () =>
        buildCombinedCode(
          cleaningPlan?.actions ??
            [],
          combinedCodeTab,
        ),
      [
        cleaningPlan,
        combinedCodeTab,
      ],
    );

  async function handleCopyCombinedCode(): Promise<void> {
    try {
      await navigator.clipboard.writeText(
        combinedCode,
      );

      setCopiedCombinedCode(true);

      window.setTimeout(
        () => {
          setCopiedCombinedCode(
            false,
          );
        },
        1500,
      );
    } catch {
      setCopiedCombinedCode(false);
    }
  }

  function handleDownload(
    format: CleaningScriptFormat,
  ): void {
    if (!datasetId) {
      return;
    }

    const url =
      getCleaningScriptUrl(
        datasetId,
        format,
      );

    downloadFromUrl(url);
  }

  if (!datasetId) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Automated remediation
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              AI Data Cleaning Assistant
            </h3>
          </div>
        </div>

        <div className="flex min-h-72 items-center justify-center text-center">
          <div className="max-w-md">
            <FileCode2
              size={34}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              No dataset connected
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Upload or open a saved dataset to generate a prioritized
              cleaning plan and ready-to-review Pandas, PySpark, and SQL
              scripts.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Automated remediation
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              AI Data Cleaning Assistant
            </h3>
          </div>
        </div>

        <button
          type="button"
          onClick={() =>
            void loadCleaningPlan()
          }
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-emerald-300 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2
              size={16}
              className="animate-spin"
            />
          ) : (
            <RefreshCw size={16} />
          )}

          Regenerate plan
        </button>
      </div>

      {errorMessage && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle
            size={18}
            className="mt-0.5 shrink-0"
          />

          <span>
            {errorMessage}
          </span>
        </div>
      )}

      {isLoading &&
      !cleaningPlan ? (
        <div className="flex min-h-80 items-center justify-center">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Loader2
              size={20}
              className="animate-spin"
            />

            Generating cleaning plan...
          </div>
        </div>
      ) : cleaningPlan ? (
        <>
          <div className="mt-6 grid gap-5 md:grid-cols-3">
            <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-medium text-slate-500">
                Current reliability
              </p>

              <p className="mt-3 text-3xl font-bold text-slate-950">
                {formatScore(
                  cleaningPlan.current_reliability_score,
                )}
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Reliability before applying the recommended cleaning
                actions.
              </p>
            </article>

            <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
              <p className="text-sm font-medium text-emerald-700">
                Predicted reliability
              </p>

              <div className="mt-3 flex items-center gap-3">
                <p className="text-3xl font-bold text-emerald-900">
                  {formatScore(
                    cleaningPlan.predicted_reliability_score,
                  )}
                </p>

                <TrendingUp
                  size={24}
                  className="text-emerald-700"
                />
              </div>

              <p className="mt-2 text-sm leading-6 text-emerald-700">
                Estimated outcome if the generated recommendations are
                validated and implemented.
              </p>
            </article>

            <article className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5">
              <p className="text-sm font-medium text-indigo-700">
                Estimated score gain
              </p>

              <div className="mt-3 flex items-center gap-3">
                <p className="text-3xl font-bold text-indigo-900">
                  {formatGain(
                    cleaningPlan.estimated_score_gain,
                  )}
                </p>

                <ArrowRight
                  size={23}
                  className="text-indigo-700"
                />
              </div>

              <p className="mt-2 text-sm leading-6 text-indigo-700">
                Based on {
                  cleaningPlan.action_count
                } generated cleaning action
                {cleaningPlan.action_count ===
                1
                  ? ""
                  : "s"}.
              </p>
            </article>
          </div>

          <div className="mt-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-base font-semibold text-slate-950">
                  Recommended cleaning actions
                </h4>

                <p className="mt-1 text-sm text-slate-500">
                  Actions are ordered by operational priority and expected
                  data-quality impact.
                </p>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                {
                  cleaningPlan.action_count
                } actions
              </span>
            </div>

            {cleaningPlan.actions.length ===
            0 ? (
              <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-center">
                <Check
                  size={30}
                  className="mx-auto text-emerald-700"
                />

                <h5 className="mt-3 font-semibold text-emerald-900">
                  No automated cleaning actions required
                </h5>

                <p className="mt-2 text-sm leading-6 text-emerald-700">
                  The current automated checks did not identify any
                  remediation actions. Continue with domain-specific
                  validation before production use.
                </p>
              </div>
            ) : (
              <div className="mt-5 space-y-5">
                {cleaningPlan.actions.map(
                  (
                    action,
                    index,
                  ) => (
                    <CleaningActionCard
                      key={`${action.category}-${action.column ?? "dataset"}-${index}`}
                      action={
                        action
                      }
                      index={
                        index
                      }
                    />
                  ),
                )}
              </div>
            )}
          </div>

          <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <Code2
                    size={19}
                    className="text-indigo-700"
                  />

                  <h4 className="text-base font-semibold text-slate-950">
                    Combined cleaning script
                  </h4>
                </div>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Review all generated actions together or download a full
                  executable starter script.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() =>
                    handleDownload(
                      "pandas",
                    )
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-800"
                >
                  <Download
                    size={16}
                  />
                  Pandas
                </button>

                <button
                  type="button"
                  onClick={() =>
                    handleDownload(
                      "pyspark",
                    )
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-sky-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-800"
                >
                  <Download
                    size={16}
                  />
                  PySpark
                </button>

                <button
                  type="button"
                  onClick={() =>
                    handleDownload(
                      "sql",
                    )
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-900"
                >
                  <Download
                    size={16}
                  />
                  SQL
                </button>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
              <div className="flex rounded-xl bg-white p-1 shadow-sm">
                {CODE_TABS.map(
                  (tab) => (
                    <button
                      key={
                        tab.value
                      }
                      type="button"
                      onClick={() =>
                        setCombinedCodeTab(
                          tab.value,
                        )
                      }
                      className={[
                        "rounded-lg px-4 py-2 text-xs font-semibold transition",
                        combinedCodeTab ===
                        tab.value
                          ? "bg-indigo-700 text-white"
                          : "text-slate-500 hover:text-slate-900",
                      ].join(" ")}
                    >
                      {tab.label}
                    </button>
                  ),
                )}
              </div>

              <button
                type="button"
                onClick={() =>
                  void handleCopyCombinedCode()
                }
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700"
              >
                {copiedCombinedCode ? (
                  <>
                    <Check
                      size={14}
                    />
                    Copied
                  </>
                ) : (
                  <>
                    <Clipboard
                      size={14}
                    />
                    Copy full script
                  </>
                )}
              </button>
            </div>

            <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl bg-slate-950 p-5 text-xs leading-6 text-slate-100">
              <code>
                {combinedCode}
              </code>
            </pre>
          </div>
        </>
      ) : null}
    </section>
  );
}