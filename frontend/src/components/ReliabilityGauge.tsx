type ReliabilityGaugeProps = {
  score: number | null;
};

function normalizeScore(score: number | null): number {
  if (score === null || !Number.isFinite(score)) {
    return 0;
  }

  const percentage = score <= 1 ? score * 100 : score;

  return Math.min(Math.max(percentage, 0), 100);
}

function getScoreLabel(score: number): string {
  if (score >= 90) {
    return "Excellent";
  }

  if (score >= 75) {
    return "Good";
  }

  if (score >= 60) {
    return "Needs Attention";
  }

  return "High Risk";
}

export default function ReliabilityGauge({
  score,
}: ReliabilityGaugeProps) {
  const normalizedScore = normalizeScore(score);

  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const progress =
    circumference -
    (normalizedScore / 100) * circumference;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-sm font-medium text-slate-500">
          Dataset Health
        </p>

        <h3 className="mt-1 text-lg font-semibold text-slate-950">
          Reliability Score
        </h3>
      </div>

      <div className="mt-6 flex justify-center">
        <div className="relative h-44 w-44">
          <svg
            width="176"
            height="176"
            viewBox="0 0 176 176"
            className="-rotate-90"
          >
            <circle
              cx="88"
              cy="88"
              r={radius}
              fill="none"
              strokeWidth="14"
              stroke="rgb(226 232 240)"
            />

            <circle
              cx="88"
              cy="88"
              r={radius}
              fill="none"
              strokeWidth="14"
              strokeLinecap="round"
              stroke="#2563eb"
              strokeDasharray={circumference}
              strokeDashoffset={progress}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-slate-900">
              {score === null
                ? "--"
                : `${Math.round(normalizedScore)}%`}
            </span>

            <span className="mt-1 text-sm text-slate-500">
              {score === null
                ? "Awaiting Analysis"
                : getScoreLabel(normalizedScore)}
            </span>
          </div>
        </div>
      </div>

      <p className="mt-5 text-center text-sm text-slate-500">
        Calculated from missing values,
        duplicate records,
        anomaly detection,
        and business rule validation.
      </p>
    </article>
  );
}