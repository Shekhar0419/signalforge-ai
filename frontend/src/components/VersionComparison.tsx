import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  GitCompareArrows,
  Loader2,
  Minus,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  compareDatasetVersions,
} from "../services/api";
import type {
  DatasetComparisonResponse,
  DatasetSummary,
  MetricComparison,
} from "../services/api";

type VersionComparisonProps = {
  datasets: DatasetSummary[];
  activeDatasetId: string | null;
};

type MetricCardProps = {
  label: string;
  metric: MetricComparison;
  valueType?: "integer" | "score";
  lowerIsBetter?: boolean;
};

function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits: 2,
    },
  ).format(value);
}

function formatMetricValue(
  value: number,
  valueType: "integer" | "score",
): string {
  if (valueType === "score") {
    return `${value.toFixed(2)}%`;
  }

  return formatNumber(value);
}

function formatDifference(
  value: number,
  valueType: "integer" | "score",
): string {
  const sign =
    value > 0
      ? "+"
      : "";

  if (valueType === "score") {
    return `${sign}${value.toFixed(2)} points`;
  }

  return `${sign}${formatNumber(value)}`;
}

function MetricCard({
  label,
  metric,
  valueType = "integer",
  lowerIsBetter = false,
}: MetricCardProps) {
  const improved =
    metric.improved === true;

  const declined =
    metric.improved === false;

  const unchanged =
    metric.difference === 0;

  const Icon =
    unchanged
      ? Minus
      : improved
        ? TrendingUp
        : declined
          ? TrendingDown
          : ArrowRight;

  const statusLabel =
    unchanged
      ? "No change"
      : improved
        ? "Improved"
        : declined
          ? "Declined"
          : "Changed";

  const statusClasses =
    unchanged
      ? "bg-slate-100 text-slate-600"
      : improved
        ? "bg-emerald-50 text-emerald-700"
        : declined
          ? "bg-red-50 text-red-700"
          : "bg-blue-50 text-blue-700";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {label}
          </p>

          <div className="mt-4 flex items-center gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Before
              </p>

              <p className="mt-1 text-2xl font-bold text-slate-950">
                {formatMetricValue(
                  metric.before,
                  valueType,
                )}
              </p>
            </div>

            <ArrowRight
              size={20}
              className="shrink-0 text-slate-400"
            />

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                After
              </p>

              <p
                className={[
                  "mt-1 text-2xl font-bold",
                  improved
                    ? "text-emerald-700"
                    : declined
                      ? "text-red-700"
                      : "text-blue-700",
                ].join(" ")}
              >
                {formatMetricValue(
                  metric.after,
                  valueType,
                )}
              </p>
            </div>
          </div>
        </div>

        <div
          className={[
            "rounded-xl p-2",
            statusClasses,
          ].join(" ")}
        >
          <Icon size={20} />
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <span
          className={[
            "rounded-full px-3 py-1 text-xs font-semibold",
            statusClasses,
          ].join(" ")}
        >
          {statusLabel}
        </span>

        <div className="text-right">
          <p className="text-sm font-semibold text-slate-700">
            {formatDifference(
              metric.difference,
              valueType,
            )}
          </p>

          {metric.percent_change !== null && (
            <p className="mt-1 text-xs text-slate-400">
              {metric.percent_change > 0
                ? "+"
                : ""}
              {metric.percent_change.toFixed(2)}%
            </p>
          )}
        </div>
      </div>

      {lowerIsBetter && (
        <p className="mt-3 text-xs text-slate-400">
          Lower values generally indicate better data quality.
        </p>
      )}
    </article>
  );
}

export default function VersionComparison({
  datasets,
  activeDatasetId,
}: VersionComparisonProps) {
  const [
    firstDatasetId,
    setFirstDatasetId,
  ] = useState("");

  const [
    secondDatasetId,
    setSecondDatasetId,
  ] = useState("");

  const [
    comparison,
    setComparison,
  ] =
    useState<DatasetComparisonResponse | null>(
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

  const lineageDatasets =
    useMemo(() => {
      if (
        !activeDatasetId ||
        datasets.length === 0
      ) {
        return datasets;
      }

      const activeDataset =
        datasets.find(
          (dataset) =>
            dataset.id ===
            activeDatasetId,
        );

      if (!activeDataset) {
        return datasets;
      }

      const rootDatasetId =
        activeDataset.parent_dataset_id ??
        activeDataset.id;

      return datasets
        .filter(
          (dataset) =>
            dataset.id === rootDatasetId ||
            dataset.parent_dataset_id ===
              rootDatasetId,
        )
        .sort(
          (first, second) =>
            (
              first.version_number ??
              1
            ) -
            (
              second.version_number ??
              1
            ),
        );
    }, [
      activeDatasetId,
      datasets,
    ]);

  useEffect(() => {
    if (
      lineageDatasets.length < 2
    ) {
      setFirstDatasetId("");
      setSecondDatasetId("");
      setComparison(null);
      return;
    }

    const original =
      lineageDatasets.find(
        (dataset) =>
          (
            dataset.version_type ??
            "ORIGINAL"
          ).toUpperCase() ===
          "ORIGINAL",
      ) ??
      lineageDatasets[0];

    const latest =
      lineageDatasets[
        lineageDatasets.length - 1
      ];

    setFirstDatasetId(
      original.id,
    );

    setSecondDatasetId(
      latest.id,
    );

    setComparison(null);
    setErrorMessage(null);
  }, [lineageDatasets]);

  async function handleCompare(): Promise<void> {
    if (
      !firstDatasetId ||
      !secondDatasetId ||
      firstDatasetId ===
        secondDatasetId ||
      isLoading
    ) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result =
        await compareDatasetVersions(
          firstDatasetId,
          secondDatasetId,
        );

      setComparison(result);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The selected dataset versions " +
              "could not be compared."
            );

      setErrorMessage(message);
      setComparison(null);
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset(): void {
    setComparison(null);
    setErrorMessage(null);
  }

  if (
    lineageDatasets.length < 2
  ) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <GitCompareArrows
              size={21}
            />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Version intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Compare dataset versions
            </h3>
          </div>
        </div>

        <div className="flex min-h-64 items-center justify-center px-6 py-10">
          <div className="max-w-md text-center">
            <BarChart3
              size={34}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              Two versions are required
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Save at least one cleaned version before comparing
              dataset quality changes.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <GitCompareArrows
              size={21}
            />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Version intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Compare dataset versions
            </h3>
          </div>
        </div>

        {comparison && (
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700"
          >
            <X size={16} />
            Clear comparison
          </button>
        )}
      </div>

      <div className="p-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr_auto] lg:items-end">
          <label>
            <span className="text-sm font-medium text-slate-600">
              Before version
            </span>

            <select
              value={firstDatasetId}
              onChange={(event) => {
                setFirstDatasetId(
                  event.target.value,
                );
                setComparison(null);
                setErrorMessage(null);
              }}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100"
            >
              {lineageDatasets.map(
                (dataset) => (
                  <option
                    key={dataset.id}
                    value={dataset.id}
                  >
                    Version{" "}
                    {dataset.version_number ??
                      1}{" "}
                    ·{" "}
                    {dataset.version_type ??
                      "ORIGINAL"}
                  </option>
                ),
              )}
            </select>
          </label>

          <div className="hidden pb-3 text-slate-400 lg:block">
            <ArrowRight size={22} />
          </div>

          <label>
            <span className="text-sm font-medium text-slate-600">
              After version
            </span>

            <select
              value={secondDatasetId}
              onChange={(event) => {
                setSecondDatasetId(
                  event.target.value,
                );
                setComparison(null);
                setErrorMessage(null);
              }}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100"
            >
              {lineageDatasets.map(
                (dataset) => (
                  <option
                    key={dataset.id}
                    value={dataset.id}
                  >
                    Version{" "}
                    {dataset.version_number ??
                      1}{" "}
                    ·{" "}
                    {dataset.version_type ??
                      "ORIGINAL"}
                  </option>
                ),
              )}
            </select>
          </label>

          <button
            type="button"
            onClick={() =>
              void handleCompare()
            }
            disabled={
              !firstDatasetId ||
              !secondDatasetId ||
              firstDatasetId ===
                secondDatasetId ||
              isLoading
            }
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-indigo-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isLoading ? (
              <Loader2
                size={17}
                className="animate-spin"
              />
            ) : (
              <GitCompareArrows
                size={17}
              />
            )}

            Compare versions
          </button>
        </div>

        {firstDatasetId ===
          secondDatasetId && (
          <p className="mt-3 text-sm text-amber-700">
            Select two different versions.
          </p>
        )}

        {errorMessage && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {!comparison &&
          !isLoading &&
          !errorMessage && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
            <GitCompareArrows
              size={32}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              Select two versions to compare
            </h4>

            <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
              Compare reliability, row counts, missing values,
              duplicates, outliers, rule violations, and ML
              anomalies across the same dataset lineage.
            </p>
          </div>
        )}

        {isLoading && (
          <div className="mt-6 flex min-h-64 items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <Loader2
                size={20}
                className="animate-spin"
              />

              Comparing dataset versions...
            </div>
          </div>
        )}

        {comparison && (
          <div className="mt-8 space-y-8">
            <div className="grid gap-4 rounded-2xl border border-indigo-100 bg-indigo-50 p-5 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-500">
                  Before
                </p>

                <p className="mt-2 text-lg font-bold text-slate-950">
                  Version{" "}
                  {
                    comparison.before
                      .version_number
                  }
                </p>

                <p className="mt-1 truncate text-sm text-slate-500">
                  {
                    comparison.before
                      .filename
                  }
                </p>
              </div>

              <ArrowRight
                size={24}
                className="hidden text-indigo-400 lg:block"
              />

              <div className="lg:text-right">
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-500">
                  After
                </p>

                <p className="mt-2 text-lg font-bold text-slate-950">
                  Version{" "}
                  {
                    comparison.after
                      .version_number
                  }
                </p>

                <p className="mt-1 truncate text-sm text-slate-500">
                  {
                    comparison.after
                      .filename
                  }
                </p>
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Reliability score"
                metric={
                  comparison.metrics
                    .reliability_score
                }
                valueType="score"
              />

              <MetricCard
                label="Rows"
                metric={
                  comparison.metrics
                    .row_count
                }
              />

              <MetricCard
                label="Missing values"
                metric={
                  comparison.metrics
                    .missing_values
                }
                lowerIsBetter
              />

              <MetricCard
                label="Duplicate rows"
                metric={
                  comparison.metrics
                    .duplicate_rows
                }
                lowerIsBetter
              />

              <MetricCard
                label="Columns"
                metric={
                  comparison.metrics
                    .column_count
                }
              />

              <MetricCard
                label="Statistical outliers"
                metric={
                  comparison.metrics
                    .outliers
                }
                lowerIsBetter
              />

              <MetricCard
                label="Rule violations"
                metric={
                  comparison.metrics
                    .business_rule_violations
                }
                lowerIsBetter
              />

              <MetricCard
                label="ML anomalies"
                metric={
                  comparison.metrics
                    .ml_anomalies
                }
                lowerIsBetter
              />
            </div>

            <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
              <div className="flex items-start gap-3">
                <div className="rounded-xl bg-white p-2 text-emerald-700">
                  <CheckCircle2
                    size={20}
                  />
                </div>

                <div>
                  <p className="text-sm font-medium text-emerald-700">
                    Comparison summary
                  </p>

                  <h4 className="mt-1 text-lg font-semibold text-emerald-950">
                    What changed between these versions
                  </h4>
                </div>
              </div>

              <ul className="mt-5 space-y-3">
                {comparison.summary.map(
                  (
                    item,
                    index,
                  ) => (
                    <li
                      key={`${index}-${item}`}
                      className="flex gap-3 rounded-xl border border-emerald-100 bg-white/70 px-4 py-3 text-sm leading-6 text-emerald-900"
                    >
                      <CheckCircle2
                        size={17}
                        className="mt-1 shrink-0 text-emerald-600"
                      />

                      <span>
                        {item}
                      </span>
                    </li>
                  ),
                )}
              </ul>
            </article>
          </div>
        )}
      </div>
    </section>
  );
}