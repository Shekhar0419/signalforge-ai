import {
  CalendarDays,
  Database,
  FolderClock,
  GitBranch,
  Loader2,
  RefreshCw,
  Rows3,
} from "lucide-react";

import type {
  DatasetSummary,
} from "../services/api";

type DatasetHistoryProps = {
  datasets: DatasetSummary[];
  activeDatasetId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  onOpenDataset: (
    datasetId: string,
  ) => Promise<void>;
  onRefresh: () => Promise<void>;
};

function normalizeScore(
  score: number,
): number {
  const percentage =
    score <= 1
      ? score * 100
      : score;

  return Math.min(
    Math.max(
      percentage,
      0,
    ),
    100,
  );
}

function formatScore(
  score: number,
): string {
  return `${normalizeScore(
    score,
  ).toFixed(1)}%`;
}

function getScoreClasses(
  score: number,
): string {
  const normalized =
    normalizeScore(
      score,
    );

  if (normalized >= 90) {
    return (
      "bg-emerald-50 "
      + "text-emerald-700"
    );
  }

  if (normalized >= 75) {
    return (
      "bg-amber-50 "
      + "text-amber-700"
    );
  }

  return (
    "bg-red-50 "
    + "text-red-700"
  );
}

function formatDate(
  timestamp: string,
): string {
  const date = new Date(
    timestamp,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(
    date,
  );
}

function getVersionTypeClasses(
  versionType: string,
): string {
  const normalizedType =
    versionType.toUpperCase();

  if (
    normalizedType ===
    "CLEANED"
  ) {
    return (
      "border-violet-200 "
      + "bg-violet-50 "
      + "text-violet-700"
    );
  }

  return (
    "border-blue-200 "
    + "bg-blue-50 "
    + "text-blue-700"
  );
}

export default function DatasetHistory({
  datasets,
  activeDatasetId,
  isLoading,
  errorMessage,
  onOpenDataset,
  onRefresh,
}: DatasetHistoryProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-sky-50 p-2 text-sky-700">
            <FolderClock
              size={21}
            />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Saved analyses and versions
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Dataset history
            </h3>
          </div>
        </div>

        <button
          type="button"
          onClick={() =>
            void onRefresh()
          }
          disabled={
            isLoading
          }
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-sky-300 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2
              size={16}
              className="animate-spin"
            />
          ) : (
            <RefreshCw
              size={16}
            />
          )}

          Refresh
        </button>
      </div>

      {errorMessage && (
        <div className="mx-6 mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMessage}
        </div>
      )}

      {isLoading &&
      datasets.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Loader2
              size={19}
              className="animate-spin"
            />

            Loading dataset history...
          </div>
        </div>
      ) : datasets.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center px-6 py-10">
          <div className="max-w-md text-center">
            <Database
              size={32}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              No saved analyses yet
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Upload and analyze a CSV dataset. Saved analyses and
              cleaned versions will appear here automatically.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 p-6 lg:grid-cols-2">
          {datasets.map(
            (dataset) => {
              const isActive =
                dataset.id ===
                activeDatasetId;

              const versionNumber =
                dataset.version_number ??
                1;

              const versionType =
                dataset.version_type ??
                "ORIGINAL";

              return (
                <article
                  key={dataset.id}
                  className={[
                    "rounded-2xl border p-5 transition",
                    isActive
                      ? (
                          "border-blue-300 "
                          + "bg-blue-50/60"
                        )
                      : (
                          "border-slate-200 "
                          + "bg-white "
                          + "hover:border-sky-300 "
                          + "hover:shadow-sm"
                        ),
                  ].join(" ")}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h4 className="truncate text-base font-semibold text-slate-950">
                        {
                          dataset.filename
                        }
                      </h4>

                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
                          <GitBranch
                            size={14}
                          />

                          Version{" "}
                          {
                            versionNumber
                          }
                        </span>

                        <span
                          className={[
                            "rounded-full border px-3 py-1 text-xs font-semibold",
                            getVersionTypeClasses(
                              versionType,
                            ),
                          ].join(" ")}
                        >
                          {
                            versionType
                          }
                        </span>

                        {dataset
                          .parent_dataset_id && (
                          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-500">
                            Derived version
                          </span>
                        )}
                      </div>

                      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
                        <span className="flex items-center gap-1.5">
                          <Rows3
                            size={15}
                          />

                          {dataset
                            .row_count
                            .toLocaleString()}{" "}
                          rows
                        </span>

                        <span className="flex items-center gap-1.5">
                          <Database
                            size={15}
                          />

                          {
                            dataset
                              .column_count
                          }{" "}
                          columns
                        </span>

                        <span className="flex items-center gap-1.5">
                          <CalendarDays
                            size={15}
                          />

                          {formatDate(
                            dataset
                              .created_at,
                          )}
                        </span>
                      </div>
                    </div>

                    <span
                      className={[
                        "shrink-0 rounded-full px-3 py-1 text-xs font-semibold",
                        getScoreClasses(
                          dataset
                            .reliability_score,
                        ),
                      ].join(" ")}
                    >
                      {formatScore(
                        dataset
                          .reliability_score,
                      )}
                    </span>
                  </div>

                  <div className="mt-5 flex items-center justify-between gap-3">
                    <span className="text-xs text-slate-400">
                      {isActive
                        ? "Currently open"
                        : (
                            `ID: ${
                              dataset.id.slice(
                                0,
                                8,
                              )
                            }...`
                          )}
                    </span>

                    <button
                      type="button"
                      disabled={
                        isLoading ||
                        isActive
                      }
                      onClick={() =>
                        void onOpenDataset(
                          dataset.id,
                        )
                      }
                      className="rounded-xl bg-sky-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      {isActive
                        ? "Opened"
                        : "View analysis"}
                    </button>
                  </div>
                </article>
              );
            },
          )}
        </div>
      )}
    </section>
  );
}