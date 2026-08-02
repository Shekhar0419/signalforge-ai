import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Database,
  Download,
  Eye,
  FileWarning,
  Loader2,
  RefreshCw,
  Rows3,
  Save,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import {
  createCleaningPreview,
  downloadCleanedFile,
  saveCleanedVersion,
} from "../services/api";
import type {
  AppliedCleaningAction,
  CleaningPreviewResponse,
  PreviewRow,
  PreviewValue,
  SaveVersionResponse,
} from "../services/api";

type CleaningPreviewProps = {
  datasetId: string | null;
  onVersionSaved: (
    savedVersion: SaveVersionResponse,
  ) => Promise<void> | void;
};

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

function formatInteger(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function formatCellValue(
  value: PreviewValue,
): string {
  if (value === null) {
    return "Missing";
  }

  if (
    typeof value === "number"
  ) {
    if (
      Number.isInteger(value)
    ) {
      return value.toLocaleString();
    }

    return value.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 2,
      },
    );
  }

  if (
    typeof value === "boolean"
  ) {
    return value
      ? "True"
      : "False";
  }

  return String(value);
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

function ComparisonMetric({
  title,
  before,
  after,
  icon,
  lowerIsBetter = false,
}: {
  title: string;
  before: string;
  after: string;
  icon: React.ReactNode;
  lowerIsBetter?: boolean;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">
          {title}
        </p>

        <div className="rounded-xl bg-slate-100 p-2 text-slate-600">
          {icon}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Before
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-950">
            {before}
          </p>
        </div>

        <ArrowRight
          size={22}
          className="shrink-0 text-slate-400"
        />

        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            After
          </p>

          <p
            className={[
              "mt-2 text-2xl font-bold",
              lowerIsBetter
                ? "text-emerald-700"
                : "text-blue-700",
            ].join(" ")}
          >
            {after}
          </p>
        </div>
      </div>
    </article>
  );
}

function ActionList({
  title,
  description,
  actions,
  type,
}: {
  title: string;
  description: string;
  actions: AppliedCleaningAction[];
  type: "applied" | "review";
}) {
  const isApplied =
    type === "applied";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div
          className={[
            "rounded-xl p-2",
            isApplied
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700",
          ].join(" ")}
        >
          {isApplied ? (
            <CheckCircle2 size={20} />
          ) : (
            <AlertTriangle size={20} />
          )}
        </div>

        <div>
          <h4 className="text-base font-semibold text-slate-950">
            {title}
          </h4>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            {description}
          </p>
        </div>
      </div>

      {actions.length === 0 ? (
        <div
          className={[
            "mt-5 rounded-xl border px-4 py-4 text-sm",
            isApplied
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-slate-200 bg-slate-50 text-slate-500",
          ].join(" ")}
        >
          {isApplied
            ? "No automatic cleaning actions were required."
            : "No manual-review actions were generated."}
        </div>
      ) : (
        <div className="mt-5 space-y-3">
          {actions.map(
            (
              action,
              index,
            ) => (
              <div
                key={`${action.category}-${action.column ?? "dataset"}-${index}`}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={[
                          "rounded-full px-2.5 py-1 text-xs font-semibold",
                          isApplied
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-amber-100 text-amber-700",
                        ].join(" ")}
                      >
                        {isApplied
                          ? "Applied"
                          : "Review required"}
                      </span>

                      <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                        {formatCategory(
                          action.category,
                        )}
                      </span>
                    </div>

                    <h5 className="mt-3 text-sm font-semibold text-slate-900">
                      {action.title}
                    </h5>

                    {action.column && (
                      <p className="mt-1 text-xs font-medium text-blue-700">
                        Column: {action.column}
                      </p>
                    )}

                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      {action.message}
                    </p>
                  </div>

                  <div className="rounded-xl bg-white px-3 py-2 text-right">
                    <p className="text-xs font-medium text-slate-500">
                      Rows affected
                    </p>

                    <p className="mt-1 text-lg font-bold text-slate-900">
                      {formatInteger(
                        action.rows_affected,
                      )}
                    </p>
                  </div>
                </div>
              </div>
            ),
          )}
        </div>
      )}
    </article>
  );
}

function CleanedPreviewTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: PreviewRow[];
}) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-50 p-2 text-cyan-700">
            <Eye size={20} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Simulated output
            </p>

            <h4 className="mt-1 text-lg font-semibold text-slate-950">
              Cleaned dataset preview
            </h4>
          </div>
        </div>

        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          First {rows.length} rows
        </span>
      </div>

      {columns.length === 0 ||
      rows.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center px-6 py-10">
          <p className="max-w-md text-center text-sm leading-6 text-slate-500">
            No cleaned preview rows are available.
          </p>
        </div>
      ) : (
        <div className="max-h-[520px] overflow-auto">
          <table className="min-w-max border-collapse text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-100">
              <tr>
                <th className="border-b border-r border-slate-200 px-4 py-3 font-semibold text-slate-700">
                  Row
                </th>

                {columns.map(
                  (column) => (
                    <th
                      key={column}
                      className="whitespace-nowrap border-b border-r border-slate-200 px-4 py-3 font-semibold text-slate-700 last:border-r-0"
                    >
                      {column}
                    </th>
                  ),
                )}
              </tr>
            </thead>

            <tbody>
              {rows.map(
                (
                  row,
                  rowIndex,
                ) => (
                  <tr
                    key={rowIndex}
                    className="odd:bg-white even:bg-slate-50 hover:bg-blue-50/50"
                  >
                    <td className="border-b border-r border-slate-200 px-4 py-3 font-medium text-slate-500">
                      {rowIndex + 1}
                    </td>

                    {columns.map(
                      (column) => {
                        const value =
                          row[column] ??
                          null;

                        const isMissing =
                          value === null;

                        return (
                          <td
                            key={`${rowIndex}-${column}`}
                            className={[
                              "max-w-xs whitespace-nowrap border-b border-r border-slate-200 px-4 py-3 last:border-r-0",
                              isMissing
                                ? "bg-red-50 font-medium text-red-700"
                                : "text-slate-700",
                            ].join(" ")}
                          >
                            {formatCellValue(
                              value,
                            )}
                          </td>
                        );
                      },
                    )}
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

export default function CleaningPreview({
  datasetId,
  onVersionSaved,
}: CleaningPreviewProps) {
  const [
    preview,
    setPreview,
  ] =
    useState<CleaningPreviewResponse | null>(
      null,
    );

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    isDownloading,
    setIsDownloading,
  ] = useState(false);

  const [
    isSavingVersion,
    setIsSavingVersion,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] =
    useState<string | null>(null);

  const [
    actionError,
    setActionError,
  ] =
    useState<string | null>(null);

  const [
    successMessage,
    setSuccessMessage,
  ] =
    useState<string | null>(null);

  async function generatePreview(): Promise<void> {
    if (
      !datasetId ||
      isLoading
    ) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setActionError(null);
    setSuccessMessage(null);

    try {
      const result =
        await createCleaningPreview(
          datasetId,
          20,
        );

      setPreview(result);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The cleaning preview could " +
              "not be generated."
            );

      setErrorMessage(message);
      setPreview(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDownloadCleanedFile(): Promise<void> {
    if (
      !datasetId ||
      !preview ||
      isDownloading
    ) {
      return;
    }

    setIsDownloading(true);
    setActionError(null);
    setSuccessMessage(null);

    try {
      await downloadCleanedFile(
        datasetId,
      );

      setSuccessMessage(
        "The safely cleaned CSV file was downloaded successfully.",
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The cleaned CSV file could " +
              "not be downloaded."
            );

      setActionError(message);
    } finally {
      setIsDownloading(false);
    }
  }

  async function handleSaveCleanedVersion(): Promise<void> {
    if (
      !datasetId ||
      !preview ||
      isSavingVersion
    ) {
      return;
    }

    setIsSavingVersion(true);
    setActionError(null);
    setSuccessMessage(null);

    try {
      const savedVersion =
        await saveCleanedVersion(
          datasetId,
        );

      setSuccessMessage(
        `Cleaned dataset saved successfully as Version ${savedVersion.version_number}.`,
      );

      await onVersionSaved(
        savedVersion,
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : (
              "The cleaned dataset version could " +
              "not be saved."
            );

      setActionError(message);
    } finally {
      setIsSavingVersion(false);
    }
  }

  useEffect(() => {
    setPreview(null);
    setErrorMessage(null);
    setActionError(null);
    setSuccessMessage(null);
  }, [datasetId]);

  if (!datasetId) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-50 p-2 text-blue-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Safe transformation preview
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Before and after cleaning
            </h3>
          </div>
        </div>

        <div className="flex min-h-72 items-center justify-center px-6 py-10">
          <div className="max-w-md text-center">
            <Database
              size={34}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              No dataset connected
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Upload or open a saved dataset to simulate safe cleaning
              operations.
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
          <div className="rounded-xl bg-blue-50 p-2 text-blue-700">
            <Sparkles size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Safe transformation preview
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Before and after cleaning
            </h3>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() =>
              void generatePreview()
            }
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2
                size={16}
                className="animate-spin"
              />
            ) : preview ? (
              <RefreshCw size={16} />
            ) : (
              <Eye size={16} />
            )}

            {preview
              ? "Regenerate preview"
              : "Generate preview"}
          </button>

          <button
            type="button"
            onClick={() =>
              void handleDownloadCleanedFile()
            }
            disabled={
              !preview ||
              isDownloading ||
              isSavingVersion
            }
            className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isDownloading ? (
              <Loader2
                size={16}
                className="animate-spin"
              />
            ) : (
              <Download size={16} />
            )}

            Download cleaned CSV
          </button>

          <button
            type="button"
            onClick={() =>
              void handleSaveCleanedVersion()
            }
            disabled={
              !preview ||
              isSavingVersion ||
              isDownloading
            }
            className="inline-flex items-center gap-2 rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSavingVersion ? (
              <Loader2
                size={16}
                className="animate-spin"
              />
            ) : (
              <Save size={16} />
            )}

            Save cleaned version
          </button>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-800">
        Generate the preview first. After reviewing the simulated
        changes, you can download the cleaned CSV or save it as a new
        dataset version. The original source file is never modified.
      </div>

      {errorMessage && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <FileWarning
            size={18}
            className="mt-0.5 shrink-0"
          />

          <span>
            {errorMessage}
          </span>
        </div>
      )}

      {actionError && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <FileWarning
            size={18}
            className="mt-0.5 shrink-0"
          />

          <span>
            {actionError}
          </span>
        </div>
      )}

      {successMessage && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2
            size={18}
            className="mt-0.5 shrink-0"
          />

          <span>
            {successMessage}
          </span>
        </div>
      )}

      {isLoading &&
      !preview ? (
        <div className="flex min-h-72 items-center justify-center">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Loader2
              size={20}
              className="animate-spin"
            />

            Simulating safe cleaning operations...
          </div>
        </div>
      ) : !preview ? (
        <div className="flex min-h-72 items-center justify-center px-6 py-10">
          <div className="max-w-md text-center">
            <Eye
              size={34}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              Preview has not been generated
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Click Generate preview to compare dataset quality before
              and after safe cleaning operations.
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-6 space-y-8">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <div>
              <p className="text-sm font-medium text-emerald-700">
                Estimated reliability improvement
              </p>

              <p className="mt-2 text-3xl font-bold text-emerald-900">
                +{preview.estimated_score_gain.toFixed(
                  2,
                )}
              </p>
            </div>

            <div className="text-right">
              <p className="text-sm font-medium text-emerald-700">
                Source file modified
              </p>

              <p className="mt-2 text-lg font-bold text-emerald-900">
                {preview.source_modified
                  ? "Yes"
                  : "No"}
              </p>
            </div>
          </div>

          {preview.applied_action_count ===
            0 &&
            preview.review_action_count >
              0 && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                <div className="flex items-start gap-3">
                  <AlertTriangle
                    size={20}
                    className="mt-0.5 shrink-0 text-amber-700"
                  />

                  <div>
                    <h4 className="font-semibold text-amber-900">
                      No automatic changes were applied
                    </h4>

                    <p className="mt-2 text-sm leading-6 text-amber-800">
                      The remaining findings involve business-rule
                      violations or statistical outliers. SignalForge
                      preserved those records because safe correction
                      requires domain review.
                    </p>
                  </div>
                </div>
              </div>
            )}

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <ComparisonMetric
              title="Reliability score"
              before={formatScore(
                preview.before.reliability_score,
              )}
              after={formatScore(
                preview.after.reliability_score,
              )}
              icon={
                <ShieldCheck size={20} />
              }
            />

            <ComparisonMetric
              title="Rows"
              before={formatInteger(
                preview.before.row_count,
              )}
              after={formatInteger(
                preview.after.row_count,
              )}
              icon={
                <Rows3 size={20} />
              }
              lowerIsBetter
            />

            <ComparisonMetric
              title="Missing values"
              before={formatInteger(
                preview.before.missing_values,
              )}
              after={formatInteger(
                preview.after.missing_values,
              )}
              icon={
                <FileWarning size={20} />
              }
              lowerIsBetter
            />

            <ComparisonMetric
              title="Duplicate rows"
              before={formatInteger(
                preview.before.duplicate_rows,
              )}
              after={formatInteger(
                preview.after.duplicate_rows,
              )}
              icon={
                <Database size={20} />
              }
              lowerIsBetter
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <ActionList
              title="Automatically applied"
              description={`${preview.applied_action_count} safe action${
                preview.applied_action_count === 1
                  ? ""
                  : "s"
              } were simulated.`}
              actions={
                preview.applied_actions
              }
              type="applied"
            />

            <ActionList
              title="Manual review required"
              description={`${preview.review_action_count} finding${
                preview.review_action_count === 1
                  ? ""
                  : "s"
              } were preserved for domain review.`}
              actions={
                preview.review_actions
              }
              type="review"
            />
          </div>

          <CleanedPreviewTable
            columns={
              preview.preview_columns
            }
            rows={
              preview.preview_rows
            }
          />
        </div>
      )}
    </section>
  );
}