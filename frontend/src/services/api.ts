const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";

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

  top_values?: TopValue[] | Record<string, number>;

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

  [key: string]: unknown;
};

export type DatasetSummary = {
  id: string;
  filename: string;
  row_count: number;
  column_count: number;
  reliability_score: number;
  created_at: string;
};

export type CopilotResponse = {
  dataset_id: string;
  question: string;
  answer: string;
  provider: string;
  model: string | null;
};

type FastAPIValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type FastAPIErrorBody = {
  detail?: string | FastAPIValidationError[];
};

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const body =
      (await response.json()) as FastAPIErrorBody;

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      const messages = body.detail
        .map((error) => error.msg)
        .filter(
          (message): message is string =>
            typeof message === "string" &&
            message.trim().length > 0,
        );

      if (messages.length > 0) {
        return messages.join(", ");
      }
    }
  } catch {
    // The backend may have returned a non-JSON response.
  }

  if (response.status === 404) {
    return "The requested resource could not be found.";
  }

  if (response.status === 413) {
    return "The selected file exceeds the upload limit.";
  }

  if (response.status === 415) {
    return "Only CSV files are supported.";
  }

  if (response.status === 422) {
    return "The request could not be validated.";
  }

  if (response.status >= 500) {
    return "The backend encountered an unexpected error.";
  }

  return `Request failed with status ${response.status}.`;
}

function validateCsvFile(file: File): void {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    throw new Error(
      "Please select a CSV file.",
    );
  }

  if (file.size === 0) {
    throw new Error(
      "The selected CSV file is empty.",
    );
  }
}

export async function uploadDataset(
  file: File,
  signal?: AbortSignal,
): Promise<DatasetProfileResponse> {
  validateCsvFile(file);

  const formData = new FormData();
  formData.append("file", file);

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
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new Error(
      "Unable to connect to the SignalForge backend.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
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
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new Error(
      "Unable to connect to the SignalForge backend.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
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
    datasetId.trim();

  if (!cleanedDatasetId) {
    throw new Error(
      "Dataset ID is required.",
    );
  }

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
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new Error(
      "Unable to connect to the SignalForge backend.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (
    await response.json()
  ) as DatasetProfileResponse;
}

export async function askCopilot(
  datasetId: string,
  question: string,
  signal?: AbortSignal,
): Promise<CopilotResponse> {
  const cleanedDatasetId =
    datasetId.trim();

  const cleanedQuestion =
    question.trim();

  if (!cleanedDatasetId) {
    throw new Error(
      "Dataset ID is required.",
    );
  }

  if (!cleanedQuestion) {
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
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: cleanedQuestion,
        }),
        signal,
      },
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new Error(
      "Unable to connect to the SignalForge backend.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (
    await response.json()
  ) as CopilotResponse;
}

export { API_BASE_URL };