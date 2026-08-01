import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ColumnMetadata } from "../services/api";

type MissingValuesChartProps = {
  columns: ColumnMetadata[];
};

type ChartRow = {
  column: string;
  missingCount: number;
  missingPercentage: number;
};

type TooltipPayloadItem = {
  payload?: ChartRow;
};

type CustomTooltipProps = {
  active?: boolean;
  payload?: TooltipPayloadItem[];
};

function getColumnName(
  column: ColumnMetadata,
): string {
  const possibleNames = [
    column.column_name,
    column.name,
  ];

  for (const value of possibleNames) {
    if (
      typeof value === "string" &&
      value.trim().length > 0
    ) {
      return value.trim();
    }
  }

  return "Unknown column";
}

function getMissingCount(
  column: ColumnMetadata,
): number {
  const possibleValues = [
    column.missing_count,
    column.null_count,
  ];

  for (const value of possibleValues) {
    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return Math.max(0, value);
    }
  }

  return 0;
}

function getRowCount(
  column: ColumnMetadata,
): number {
  if (
    typeof column.row_count === "number" &&
    Number.isFinite(column.row_count)
  ) {
    return Math.max(0, column.row_count);
  }

  return 0;
}

function getMissingPercentage(
  column: ColumnMetadata,
): number {
  const possibleRatios = [
    column.missing_ratio,
    column.null_ratio,
  ];

  for (const value of possibleRatios) {
    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      const percentage =
        value <= 1
          ? value * 100
          : value;

      return Math.min(
        Math.max(percentage, 0),
        100,
      );
    }
  }

  const missingCount =
    getMissingCount(column);

  const rowCount =
    getRowCount(column);

  if (rowCount === 0) {
    return 0;
  }

  return Math.min(
    Math.max(
      (missingCount / rowCount) * 100,
      0,
    ),
    100,
  );
}

function buildChartData(
  columns: ColumnMetadata[],
): ChartRow[] {
  return columns
    .map((column) => ({
      column: getColumnName(column),
      missingCount:
        getMissingCount(column),
      missingPercentage: Number(
        getMissingPercentage(
          column,
        ).toFixed(2),
      ),
    }))
    .sort(
      (first, second) =>
        second.missingPercentage -
        first.missingPercentage,
    )
    .slice(0, 12);
}

function getBarColor(
  missingPercentage: number,
): string {
  if (missingPercentage >= 40) {
    return "#dc2626";
  }

  if (missingPercentage >= 20) {
    return "#f59e0b";
  }

  if (missingPercentage > 0) {
    return "#2563eb";
  }

  return "#cbd5e1";
}

function CustomTooltip({
  active,
  payload,
}: CustomTooltipProps) {
  if (
    !active ||
    !payload ||
    payload.length === 0 ||
    !payload[0].payload
  ) {
    return null;
  }

  const row =
    payload[0].payload;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
      <p className="text-sm font-semibold text-slate-950">
        {row.column}
      </p>

      <p className="mt-1 text-sm text-slate-600">
        Missing values:{" "}
        <span className="font-semibold">
          {row.missingCount.toLocaleString()}
        </span>
      </p>

      <p className="text-sm text-slate-600">
        Missing percentage:{" "}
        <span className="font-semibold">
          {row.missingPercentage.toFixed(
            2,
          )}
          %
        </span>
      </p>
    </div>
  );
}

export default function MissingValuesChart({
  columns,
}: MissingValuesChartProps) {
  const chartData =
    buildChartData(columns);

  const hasMissingValues =
    chartData.some(
      (row) =>
        row.missingCount > 0 ||
        row.missingPercentage > 0,
    );

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Completeness analysis
          </p>

          <h3 className="mt-1 text-lg font-semibold text-slate-950">
            Missing values by column
          </h3>
        </div>

        <div className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          Top{" "}
          {Math.min(
            chartData.length,
            12,
          )}{" "}
          columns
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="flex h-80 items-center justify-center">
          <p className="max-w-sm text-center text-sm leading-6 text-slate-500">
            Upload a dataset to view
            missing-value percentages for
            each column.
          </p>
        </div>
      ) : !hasMissingValues ? (
        <div className="flex h-80 flex-col items-center justify-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-700">
            ✓
          </div>

          <h4 className="mt-4 font-semibold text-slate-950">
            No missing values detected
          </h4>

          <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
            Every analyzed column is
            complete for the current
            dataset.
          </p>
        </div>
      ) : (
        <div className="mt-6 h-80 w-full">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <BarChart
              data={chartData}
              margin={{
                top: 10,
                right: 10,
                left: -15,
                bottom: 45,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#e2e8f0"
              />

              <XAxis
                dataKey="column"
                axisLine={false}
                tickLine={false}
                interval={0}
                angle={-25}
                textAnchor="end"
                height={80}
                tick={{
                  fill: "#64748b",
                  fontSize: 12,
                }}
              />

              <YAxis
                domain={[0, 100]}
                axisLine={false}
                tickLine={false}
                tickFormatter={(
                  value: number,
                ) => `${value}%`}
                tick={{
                  fill: "#64748b",
                  fontSize: 12,
                }}
              />

              <Tooltip
                content={<CustomTooltip />}
                cursor={{
                  fill: "#f8fafc",
                }}
              />

              <Bar
                dataKey="missingPercentage"
                radius={[8, 8, 0, 0]}
                maxBarSize={52}
              >
                {chartData.map(
                  (row) => (
                    <Cell
                      key={row.column}
                      fill={getBarColor(
                        row.missingPercentage,
                      )}
                    />
                  ),
                )}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-4 border-t border-slate-100 pt-4 text-xs text-slate-500">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
          Below 20%
        </span>

        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
          20–39%
        </span>

        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
          40% or higher
        </span>
      </div>
    </article>
  );
}