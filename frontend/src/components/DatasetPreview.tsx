import { TableProperties } from "lucide-react";

import type {
  PreviewRow,
  PreviewValue,
} from "../services/api";

type DatasetPreviewProps = {
  columns: string[];
  rows: PreviewRow[];
};

function formatCellValue(
  value: PreviewValue,
): string {
  if (value === null) {
    return "Missing";
  }

  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }

  return String(value);
}

export default function DatasetPreview({
  columns,
  rows,
}: DatasetPreviewProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-50 p-2 text-cyan-700">
            <TableProperties size={20} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Record inspection
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              Dataset preview
            </h3>
          </div>
        </div>

        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          First {rows.length} rows
        </div>
      </div>

      {columns.length === 0 ? (
        <div className="flex min-h-72 items-center justify-center px-6 py-10">
          <p className="max-w-md text-center text-sm leading-6 text-slate-500">
            Upload a dataset to inspect its first records.
          </p>
        </div>
      ) : rows.length === 0 ? (
        <div className="flex min-h-72 items-center justify-center px-6 py-10">
          <p className="max-w-md text-center text-sm leading-6 text-slate-500">
            The dataset contains columns but no previewable records.
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

                {columns.map((column) => (
                  <th
                    key={column}
                    className="whitespace-nowrap border-b border-r border-slate-200 px-4 py-3 font-semibold text-slate-700 last:border-r-0"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="odd:bg-white even:bg-slate-50 hover:bg-blue-50/50"
                >
                  <td className="border-b border-r border-slate-200 px-4 py-3 font-medium text-slate-500">
                    {rowIndex + 1}
                  </td>

                  {columns.map((column) => {
                    const value =
                      row[column] ?? null;

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
                        {formatCellValue(value)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}