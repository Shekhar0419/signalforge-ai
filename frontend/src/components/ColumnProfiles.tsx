import {
  AlertTriangle,
  BarChart3,
  Braces,
  ChevronDown,
  ChevronUp,
  Database,
} from "lucide-react";
import { useMemo, useState } from "react";

import type { ColumnMetadata } from "../services/api";

type ColumnProfilesProps = {
  columns: ColumnMetadata[];
};

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function getString(
  source: ColumnMetadata,
  keys: string[],
): string | null {
  for (const key of keys) {
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

function getNumber(
  source: ColumnMetadata,
  keys: string[],
): number | null {
  for (const key of keys) {
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

function getStatistics(
  column: ColumnMetadata,
): UnknownRecord {
  return isRecord(column.statistics)
    ? column.statistics
    : {};
}

function getStatistic(
  column: ColumnMetadata,
  keys: string[],
): number | null {
  const directValue = getNumber(
    column,
    keys,
  );

  if (directValue !== null) {
    return directValue;
  }

  const statistics =
    getStatistics(column);

  for (const key of keys) {
    const value =
      statistics[key];

    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return value;
    }
  }

  return null;
}

function getColumnName(
  column: ColumnMetadata,
): string {
  return (
    getString(
      column,
      [
        "column_name",
        "name",
      ],
    ) ??
    "Unnamed column"
  );
}

function getColumnType(
  column: ColumnMetadata,
): string {
  return (
    getString(
      column,
      [
        "logical_type",
        "inferred_type",
        "pandas_dtype",
      ],
    ) ??
    "Unknown"
  );
}

function getMissingRatio(
  column: ColumnMetadata,
): number {
  const ratio = getNumber(
    column,
    [
      "missing_ratio",
      "null_ratio",
    ],
  );

  if (ratio === null) {
    return 0;
  }

  return ratio <= 1
    ? ratio * 100
    : ratio;
}

function getUniqueRatio(
  column: ColumnMetadata,
): number {
  const ratio = getNumber(
    column,
    [
      "unique_ratio",
    ],
  );

  if (ratio === null) {
    return 0;
  }

  return ratio <= 1
    ? ratio * 100
    : ratio;
}

function formatNumber(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  if (Number.isInteger(value)) {
    return value.toLocaleString();
  }

  return value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 2,
    },
  );
}

function formatPercentage(
  value: number,
): string {
  return `${value.toFixed(1)}%`;
}

function getRiskLabel(
  missingRatio: number,
  outlierRatio: number,
): {
  label: string;
  className: string;
} {
  if (
    missingRatio >= 40 ||
    outlierRatio >= 20
  ) {
    return {
      label: "High risk",
      className:
        "bg-red-50 text-red-700",
    };
  }

  if (
    missingRatio >= 20 ||
    outlierRatio >= 10
  ) {
    return {
      label: "Needs review",
      className:
        "bg-amber-50 text-amber-700",
    };
  }

  return {
    label: "Healthy",
    className:
      "bg-emerald-50 text-emerald-700",
  };
}

function ColumnProfileCard({
  column,
}: {
  column: ColumnMetadata;
}) {
  const [isExpanded, setIsExpanded] =
    useState(false);

  const columnName =
    getColumnName(column);

  const columnType =
    getColumnType(column);

  const missingRatio =
    getMissingRatio(column);

  const uniqueRatio =
    getUniqueRatio(column);

  const outlierRatioRaw =
    getNumber(
      column,
      [
        "outlier_ratio",
      ],
    ) ?? 0;

  const outlierRatio =
    outlierRatioRaw <= 1
      ? outlierRatioRaw * 100
      : outlierRatioRaw;

  const risk =
    getRiskLabel(
      missingRatio,
      outlierRatio,
    );

  const missingCount =
    getNumber(
      column,
      [
        "missing_count",
        "null_count",
      ],
    );

  const uniqueCount =
    getNumber(
      column,
      [
        "unique_count",
      ],
    );

  const outlierCount =
    getNumber(
      column,
      [
        "outlier_count",
      ],
    );

  const mean =
    getStatistic(
      column,
      ["mean"],
    );

  const median =
    getStatistic(
      column,
      ["median"],
    );

  const minimum =
    getStatistic(
      column,
      [
        "minimum",
        "min",
      ],
    );

  const maximum =
    getStatistic(
      column,
      [
        "maximum",
        "max",
      ],
    );

  const standardDeviation =
    getStatistic(
      column,
      [
        "standard_deviation",
        "std",
      ],
    );

  return (
    <article className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-start justify-between gap-4 p-5 text-left"
        onClick={() =>
          setIsExpanded(
            (current) => !current,
          )
        }
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="truncate text-base font-semibold text-slate-950">
              {columnName}
            </h4>

            <span
              className={[
                "rounded-full px-2.5 py-1 text-xs font-semibold",
                risk.className,
              ].join(" ")}
            >
              {risk.label}
            </span>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-500">
            <span className="flex items-center gap-1.5">
              <Braces size={15} />
              {columnType}
            </span>

            <span>
              Missing{" "}
              {formatPercentage(
                missingRatio,
              )}
            </span>

            <span>
              Unique{" "}
              {formatPercentage(
                uniqueRatio,
              )}
            </span>
          </div>
        </div>

        <span className="rounded-lg bg-slate-100 p-2 text-slate-600">
          {isExpanded ? (
            <ChevronUp size={18} />
          ) : (
            <ChevronDown size={18} />
          )}
        </span>
      </button>

      {isExpanded && (
        <div className="border-t border-slate-200 p-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Missing values
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(
                  missingCount,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Unique values
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(
                  uniqueCount,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Outliers
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(
                  outlierCount,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Mean
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(mean)}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Median
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(median)}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Standard deviation
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(
                  standardDeviation,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Minimum
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(minimum)}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Maximum
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatNumber(maximum)}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Outlier ratio
              </p>

              <p className="mt-2 text-xl font-semibold text-slate-950">
                {formatPercentage(
                  outlierRatio,
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

export default function ColumnProfiles({
  columns,
}: ColumnProfilesProps) {
  const sortedColumns = useMemo(
    () =>
      [...columns].sort(
        (first, second) =>
          getMissingRatio(second) -
          getMissingRatio(first),
      ),
    [columns],
  );

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <BarChart3 size={20} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Schema intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Column profiles
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          <Database size={14} />
          {columns.length} columns
        </div>
      </div>

      {columns.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center">
          <div className="max-w-md text-center">
            <AlertTriangle
              className="mx-auto text-slate-400"
              size={30}
            />

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Upload a dataset to inspect detailed column statistics.
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {sortedColumns.map(
            (column, index) => (
              <ColumnProfileCard
                key={`${getColumnName(
                  column,
                )}-${index}`}
                column={column}
              />
            ),
          )}
        </div>
      )}
    </section>
  );
}