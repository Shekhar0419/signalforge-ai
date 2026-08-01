import { BrainCircuit } from "lucide-react";

type ExecutiveSummaryProps = {
  summary: string;
};

export default function ExecutiveSummary({
  summary,
}: ExecutiveSummaryProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-violet-50 p-2 text-violet-700">
          <BrainCircuit size={20} />
        </div>

        <h3 className="text-lg font-semibold text-slate-950">
          AI executive summary
        </h3>
      </div>

      <p className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-600">
        {summary}
      </p>
    </article>
  );
}