import { BrainCircuit } from "lucide-react";

type HeaderProps = {
  hasCompletedAnalysis: boolean;
};

export default function Header({
  hasCompletedAnalysis,
}: HeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-700 p-2 text-white">
            <BrainCircuit size={24} />
          </div>

          <div>
            <h1 className="text-lg font-bold text-slate-950">
              SignalForge AI
            </h1>

            <p className="text-xs text-slate-500">
              AI Data Reliability Assistant
            </p>
          </div>
        </div>

        <div
          className={[
            "rounded-full px-3 py-1 text-sm font-medium",
            hasCompletedAnalysis
              ? "bg-blue-50 text-blue-700"
              : "bg-emerald-50 text-emerald-700",
          ].join(" ")}
        >
          {hasCompletedAnalysis
            ? "Analysis complete"
            : "System ready"}
        </div>
      </div>
    </header>
  );
}