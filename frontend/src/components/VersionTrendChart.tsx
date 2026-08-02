import {
  Activity,
  TrendingUp,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  DatasetSummary,
} from "../services/api";

type VersionTrendChartProps = {
  datasets: DatasetSummary[];
  activeDatasetId: string | null;
};

type TrendPoint = {
  datasetId: string;
  version: number;
  label: string;
  reliability: number;
  rowCount: number;
  columnCount: number;
  versionType: string;
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

function buildTrendData(
  datasets: DatasetSummary[],
  activeDatasetId: string | null,
): TrendPoint[] {
  if (
    datasets.length === 0 ||
    !activeDatasetId
  ) {
    return [];
  }

  const activeDataset =
    datasets.find(
      (dataset) =>
        dataset.id ===
        activeDatasetId,
    );

  if (!activeDataset) {
    return [];
  }

  const rootDatasetId =
    activeDataset.parent_dataset_id ??
    activeDataset.id;

  return datasets
    .filter(
      (dataset) =>
        dataset.id ===
          rootDatasetId ||
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
    )
    .map(
      (dataset) => {
        const version =
          dataset.version_number ??
          1;

        return {
          datasetId:
            dataset.id,
          version,
          label:
            `V${version}`,
          reliability:
            Number(
              normalizeScore(
                dataset
                  .reliability_score,
              ).toFixed(2),
            ),
          rowCount:
            dataset.row_count,
          columnCount:
            dataset.column_count,
          versionType:
            dataset.version_type ??
            "ORIGINAL",
        };
      },
    );
}

type TooltipPayloadItem = {
  payload?: TrendPoint;
};

type CustomTooltipProps = {
  active?: boolean;
  payload?: TooltipPayloadItem[];
};

function CustomTooltip({
  active,
  payload,
}: CustomTooltipProps) {
  if (
    !active ||
    !payload ||
    payload.length === 0
  ) {
    return null;
  }

  const point =
    payload[0].payload;

  if (!point) {
    return null;
  }

  return (
    <div className="min-w-48 rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
      <div className="flex items-center justify-between gap-3">
        <p className="font-semibold text-slate-950">
          Version {point.version}
        </p>

        <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">
          {point.versionType}
        </span>
      </div>

      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">
            Reliability
          </dt>

          <dd className="font-semibold text-emerald-700">
            {point.reliability.toFixed(2)}%
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">
            Rows
          </dt>

          <dd className="font-semibold text-slate-800">
            {point.rowCount.toLocaleString()}
          </dd>
        </div>

        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">
            Columns
          </dt>

          <dd className="font-semibold text-slate-800">
            {point.columnCount}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export default function VersionTrendChart({
  datasets,
  activeDatasetId,
}: VersionTrendChartProps) {
  const trendData =
    buildTrendData(
      datasets,
      activeDatasetId,
    );

  if (
    trendData.length < 2
  ) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <TrendingUp size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Version analytics
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Reliability trend
            </h3>
          </div>
        </div>

        <div className="flex min-h-64 items-center justify-center px-6 py-10">
          <div className="max-w-md text-center">
            <Activity
              size={34}
              className="mx-auto text-slate-400"
            />

            <h4 className="mt-4 font-semibold text-slate-900">
              More versions are required
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Save at least one cleaned version to visualize
              reliability changes across the dataset lineage.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const firstScore =
    trendData[0].reliability;

  const latestScore =
    trendData[
      trendData.length - 1
    ].reliability;

  const scoreDifference =
    latestScore -
    firstScore;

  const minimumScore =
    Math.max(
      0,
      Math.floor(
        Math.min(
          ...trendData.map(
            (point) =>
              point.reliability,
          ),
        ) - 2,
      ),
    );

  const maximumScore =
    Math.min(
      100,
      Math.ceil(
        Math.max(
          ...trendData.map(
            (point) =>
              point.reliability,
          ),
        ) + 2,
      ),
    );

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 p-2 text-indigo-700">
            <TrendingUp size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Version analytics
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Reliability trend
            </h3>
          </div>
        </div>

        <div className="rounded-xl bg-slate-50 px-4 py-3 text-right">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Overall change
          </p>

          <p
            className={[
              "mt-1 text-lg font-bold",
              scoreDifference > 0
                ? "text-emerald-700"
                : scoreDifference < 0
                  ? "text-red-700"
                  : "text-slate-700",
            ].join(" ")}
          >
            {scoreDifference > 0
              ? "+"
              : ""}
            {scoreDifference.toFixed(2)} points
          </p>
        </div>
      </div>

      <div className="p-6">
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-500">
              Starting score
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-950">
              {firstScore.toFixed(2)}%
            </p>
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-500">
              Latest score
            </p>

            <p className="mt-2 text-2xl font-bold text-indigo-700">
              {latestScore.toFixed(2)}%
            </p>
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-500">
              Versions tracked
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-950">
              {trendData.length}
            </p>
          </article>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart
              data={trendData}
              margin={{
                top: 10,
                right: 20,
                left: 0,
                bottom: 10,
              }}
            >
              <CartesianGrid
                strokeDasharray="4 4"
                vertical={false}
              />

              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                domain={[
                  minimumScore,
                  maximumScore,
                ]}
                tickFormatter={(
                  value,
                ) =>
                  `${value}%`
                }
                tickLine={false}
                axisLine={false}
                width={55}
              />

              <Tooltip
                content={
                  <CustomTooltip />
                }
              />

              <Line
                type="monotone"
                dataKey="reliability"
                stroke="currentColor"
                strokeWidth={3}
                dot={{
                  r: 5,
                }}
                activeDot={{
                  r: 7,
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}