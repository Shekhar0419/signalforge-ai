const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "/api/v1";

export type TopValue = {
  value: string | number | boolean | null;
  count: number;
  ratio?: number;
};

export type ColumnMetadata = {
  column_name?: string;
  name?: string;

  logical_type?: string;
  inferred_type?: string;
  pandas_dtype?: string;

  row_count?: number;
  non_null_count?: number;

  null_count?: number;
  null_ratio?: number;

  missing_count?: number;
  missing_ratio?: number;

  unique_count?: number;
  unique_ratio?: number;

  memory_usage_bytes?: number;

  min?: number | string | boolean | null;
  max?: number | string | boolean | null;

  minimum?: number | string | boolean | null;
  maximum?: number | string | boolean | null;

  mean?: number | null;
  median?: number | null;

  std?: number | null;
  standard_deviation?: number | null;

  statistics?: Record<string, unknown>;

  top_values?:
    | TopValue[]
    | Record<string, number>;

  outlier_count?: number;
  outlier_ratio?: number;

  [key: string]: unknown;
};

export type QualityIssue = {
  severity?: string;
  code?: string;
  message?: string;
  column?: string | null;

  [key: string]: unknown;
};

export type BusinessRule = {
  column?: string;
  rule?: string;
  rule_name?: string;
  description?: string;

  passed?: boolean;
  status?: string;

  violations?: number;
  violation_count?: number;
  failed_count?: number;

  severity?: string;

  [key: string]: unknown;
};

export type Recommendation =
  | string
  | {
      title?: string;
      name?: string;
      action?: string;
      category?: string;

      description?: string;
      recommendation?: string;
      message?: string;
      reason?: string;

      priority?: string;

      [key: string]: unknown;
    };

export type MLAnomaly = {
  row_index: number;
  anomaly_score: number;

  [key: string]: unknown;
};

export type PreviewValue =
  | string
  | number
  | boolean
  | null;

export type PreviewRow = Record<
  string,
  PreviewValue
>;

export type DatasetProfileResponse = {
  dataset_id: string;
  created_at: string;

  filename: string;

  row_count: number;
  column_count: number;
  duplicate_rows: number;
  reliability_score: number;

  columns: ColumnMetadata[];
  issues: QualityIssue[];

  column_metadata: ColumnMetadata[];

  business_rules: BusinessRule[];
  recommendations: Recommendation[];
  ml_anomalies: MLAnomaly[];

  preview_columns: string[];
  preview_rows: PreviewRow[];

  ai_summary?: string;
  executive_summary?: string;
  summary?: string;
  dataset_summary?: string;

  total_missing_values?: number;
  quality_issue_count?: number;
  total_quality_issues?: number;
  issue_count?: number;

  anomaly_count?: number;
  ml_anomaly_count?: number;
  anomalies_count?: number;

  parent_dataset_id?: string | null;
  version_number?: number;
  version_type?: string;

  [key: string]: unknown;
};

export type DatasetSummary = {
  id: string;
  filename: string;
  row_count: number;
  column_count: number;
  reliability_score: number;
  created_at: string;

  parent_dataset_id?: string | null;
  version_number?: number;
  version_type?: string;
};

export type MetricComparison = {
  before: number;
  after: number;
  difference: number;
  percent_change: number | null;
  improved: boolean | null;
};

export type DatasetComparisonVersion = {
  dataset_id: string;
  filename: string;
  version_number: number;
  version_type: string;
  created_at: string;
};

export type DatasetComparisonMetrics = {
  reliability_score: MetricComparison;
  row_count: MetricComparison;
  column_count: MetricComparison;
  missing_values: MetricComparison;
  duplicate_rows: MetricComparison;
  outliers: MetricComparison;
  business_rule_violations: MetricComparison;
  ml_anomalies: MetricComparison;
};

export type DatasetComparisonResponse = {
  root_dataset_id: string;
  before: DatasetComparisonVersion;
  after: DatasetComparisonVersion;
  metrics: DatasetComparisonMetrics;
  summary: string[];
};

export type CopilotResponse = {
  dataset_id: string;
  question: string;
  answer: string;
  provider: string;
  model: string | null;
};

export type CleaningAction = {
  priority: number;
  category: string;
  column: string | null;
  title: string;
  reason: string;
  pandas_code: string;
  pyspark_code: string;
  sql_code: string;
  estimated_score_gain: number;
};

export type CleaningPlanResponse = {
  dataset_id: string;
  filename: string;
  current_reliability_score: number;
  predicted_reliability_score: number;
  estimated_score_gain: number;
  action_count: number;
  actions: CleaningAction[];
};

export type CleaningScriptFormat =
  | "pandas"
  | "pyspark"
  | "sql";

export type CleaningPreviewMetrics = {
  row_count: number;
  column_count: number;
  duplicate_rows: number;
  missing_values: number;
  quality_issue_count: number;
  reliability_score: number;
};

export type AppliedCleaningAction = {
  category: string;
  column: string | null;
  title: string;
  rows_affected: number;
  status:
    | "applied"
    | "skipped"
    | "review_required"
    | string;
  message: string;
};

export type CleaningPreviewResponse = {
  dataset_id: string;
  source_file: string;
  source_modified: boolean;
  filename: string;

  before: CleaningPreviewMetrics;
  after: CleaningPreviewMetrics;

  estimated_score_gain: number;

  applied_action_count: number;
  review_action_count: number;

  applied_actions: AppliedCleaningAction[];
  review_actions: AppliedCleaningAction[];

  preview_columns: string[];
  preview_rows: PreviewRow[];
};

export type SaveVersionResponse = {
  dataset_id: string;
  source_dataset_id: string;
  parent_dataset_id: string;
  root_dataset_id: string;

  version_number: number;
  version_type: string;

  filename: string;

  row_count: number;
  column_count: number;
  duplicate_rows: number;
  reliability_score: number;

  created_at: string;
};

type FastAPIValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type FastAPIErrorBody = {
  detail?:
    | string
    | FastAPIValidationError[];
};

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const body =
      (await response.json()) as FastAPIErrorBody;

    if (
      typeof body.detail === "string"
    ) {
      return body.detail;
    }

    if (
      Array.isArray(body.detail)
    ) {
      const messages = body.detail
        .map(
          (error) =>
            error.msg,
        )
        .filter(
          (
            message,
          ): message is string =>
            typeof message === "string" &&
            message.trim().length > 0,
        );

      if (
        messages.length > 0
      ) {
        return messages.join(", ");
      }
    }
  } catch {
    // The backend may return a non-JSON response.
  }

  if (
    response.status === 400
  ) {
    return (
      "The requested operation could not be completed."
    );
  }

  if (
    response.status === 404
  ) {
    return (
      "The requested resource could not be found."
    );
  }

  if (
    response.status === 409
  ) {
    return (
      "The dataset is not ready for this operation."
    );
  }

  if (
    response.status === 413
  ) {
    return (
      "The selected file exceeds the upload limit."
    );
  }

  if (
    response.status === 415
  ) {
    return (
      "Only CSV files are supported."
    );
  }

  if (
    response.status === 422
  ) {
    return (
      "The request could not be validated."
    );
  }

  if (
    response.status >= 500
  ) {
    return (
      "The backend encountered an unexpected error."
    );
  }

  return (
    `Request failed with status ${response.status}.`
  );
}

function validateCsvFile(
  file: File,
): void {
  if (
    !file.name
      .toLowerCase()
      .endsWith(".csv")
  ) {
    throw new Error(
      "Please select a CSV file.",
    );
  }

  if (
    file.size === 0
  ) {
    throw new Error(
      "The selected CSV file is empty.",
    );
  }
}

function validateDatasetId(
  datasetId: string,
): string {
  const cleanedDatasetId =
    datasetId.trim();

  if (
    !cleanedDatasetId
  ) {
    throw new Error(
      "Dataset ID is required.",
    );
  }

  return cleanedDatasetId;
}

function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof DOMException &&
    error.name === "AbortError"
  );
}

function throwConnectionError(
  error: unknown,
): never {
  if (
    isAbortError(error)
  ) {
    throw error;
  }

  throw new Error(
    "Unable to connect to the SignalForge backend.",
  );
}

export async function uploadDataset(
  file: File,
  signal?: AbortSignal,
): Promise<DatasetProfileResponse> {
  validateCsvFile(file);

  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/profile`,
      {
        method: "POST",
        body: formData,
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as DatasetProfileResponse;
}

export async function getDatasets(
  signal?: AbortSignal,
): Promise<DatasetSummary[]> {
  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets`,
      {
        method: "GET",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as DatasetSummary[];
}

export async function getDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<DatasetProfileResponse> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}`,
      {
        method: "GET",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as DatasetProfileResponse;
}

export async function compareDatasetVersions(
  firstDatasetId: string,
  secondDatasetId: string,
  signal?: AbortSignal,
): Promise<DatasetComparisonResponse> {
  const cleanedFirstDatasetId =
    validateDatasetId(
      firstDatasetId,
    );

  const cleanedSecondDatasetId =
    validateDatasetId(
      secondDatasetId,
    );

  if (
    cleanedFirstDatasetId ===
    cleanedSecondDatasetId
  ) {
    throw new Error(
      "Select two different dataset versions to compare.",
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedFirstDatasetId,
      )}/compare/${encodeURIComponent(
        cleanedSecondDatasetId,
      )}`,
      {
        method: "GET",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as DatasetComparisonResponse;
}

export async function askCopilot(
  datasetId: string,
  question: string,
  signal?: AbortSignal,
): Promise<CopilotResponse> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  const cleanedQuestion =
    question.trim();

  if (
    !cleanedQuestion
  ) {
    throw new Error(
      "The copilot question cannot be empty.",
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}/copilot`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          question:
            cleanedQuestion,
        }),
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as CopilotResponse;
}

export async function getCleaningPlan(
  datasetId: string,
  signal?: AbortSignal,
): Promise<CleaningPlanResponse> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}/cleaning-plan`,
      {
        method: "GET",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as CleaningPlanResponse;
}

export async function createCleaningPreview(
  datasetId: string,
  previewLimit = 20,
  signal?: AbortSignal,
): Promise<CleaningPreviewResponse> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  if (
    !Number.isInteger(
      previewLimit,
    ) ||
    previewLimit < 1 ||
    previewLimit > 100
  ) {
    throw new Error(
      "Preview limit must be between 1 and 100.",
    );
  }

  const query =
    new URLSearchParams({
      preview_limit:
        String(previewLimit),
    });

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}/cleaning-preview?${query.toString()}`,
      {
        method: "POST",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as CleaningPreviewResponse;
}

export async function saveCleanedVersion(
  datasetId: string,
  signal?: AbortSignal,
): Promise<SaveVersionResponse> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}/save-cleaned-version`,
      {
        method: "POST",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  return (
    await response.json()
  ) as SaveVersionResponse;
}

export function getCleaningScriptUrl(
  datasetId: string,
  format: CleaningScriptFormat,
): string {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  const query =
    new URLSearchParams({
      format,
    });

  return (
    `${API_BASE_URL}/datasets/${encodeURIComponent(
      cleanedDatasetId,
    )}/cleaning-script?${query.toString()}`
  );
}

export function getPdfReportUrl(
  datasetId: string,
): string {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  return (
    `${API_BASE_URL}/datasets/${encodeURIComponent(
      cleanedDatasetId,
    )}/report`
  );
}

export function getCleanedFileUrl(
  datasetId: string,
): string {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  return (
    `${API_BASE_URL}/datasets/${encodeURIComponent(
      cleanedDatasetId,
    )}/cleaned-file`
  );
}

export async function downloadCleanedFile(
  datasetId: string,
  signal?: AbortSignal,
): Promise<void> {
  const cleanedDatasetId =
    validateDatasetId(
      datasetId,
    );

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/datasets/${encodeURIComponent(
        cleanedDatasetId,
      )}/cleaned-file`,
      {
        method: "POST",
        signal,
      },
    );
  } catch (error) {
    throwConnectionError(error);
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getErrorMessage(
        response,
      ),
    );
  }

  const blob =
    await response.blob();

  const contentDisposition =
    response.headers.get(
      "Content-Disposition",
    );

  const filenameMatch =
    contentDisposition?.match(
      /filename="?([^"]+)"?/i,
    );

  const filename =
    filenameMatch?.[1] ??
    "signalforge_cleaned.csv";

  const objectUrl =
    URL.createObjectURL(
      blob,
    );

  const anchor =
    document.createElement(
      "a",
    );

  anchor.href =
    objectUrl;

  anchor.download =
    filename;

  document.body.appendChild(
    anchor,
  );

  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(
    objectUrl,
  );
}

export {
  API_BASE_URL,
};