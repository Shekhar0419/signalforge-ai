const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type TopValue = {
  value: string | number | boolean | null;
  count: number;
};

export type ColumnMetadata = {
  column_name?: string;
  logical_type?: string;
  pandas_dtype?: string;
  row_count?: number;
  null_count?: number;
  null_ratio?: number;
  unique_count?: number;
  unique_ratio?: number;
  memory_usage_bytes?: number;
  minimum?: number | string | null;
  maximum?: number | string | null;
  mean?: number | null;
  median?: number | null;
  standard_deviation?: number | null;
  top_values?: TopValue[];
  [key: string]: unknown;
};

export type BusinessRule = {
  column?: string;
  rule?: string;
  description?: string;
  passed?: boolean;
  violation_count?: number;
  severity?: string;
  [key: string]: unknown;
};

export type Recommendation = {
  title?: string;
  description?: string;
  priority?: string;
  category?: string;
  [key: string]: unknown;
};

export type MLAnomaly = {
  row_index: number;
  anomaly_score: number;
};

export type DatasetProfileResponse = {
  dataset_id: string;
  created_at: string;
  filename?: string;
  row_count: number;
  column_count: number;
  reliability_score: number;
  duplicate_rows?: number;
  total_missing_values?: number;
  column_metadata?: ColumnMetadata[];
  business_rules?: BusinessRule[];
  recommendations?: Recommendation[];
  ml_anomalies?: MLAnomaly[];
  ai_summary?: string;
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

type FastAPIErrorBody = {
  detail?: string | Array<{
    loc?: Array<string | number>;
    msg?: string;
    type?: string;
  }>;
};

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as FastAPIErrorBody;

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      return body.detail
        .map((error) => error.msg ?? "Validation error")
        .join(", ");
    }
  } catch {
    // The server may have returned plain text or an empty response.
  }

  return `Request failed with status ${response.status}.`;
}

export async function uploadDataset(
  file: File,
  signal?: AbortSignal,
): Promise<DatasetProfileResponse> {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    throw new Error("Please select a CSV file.");
  }

  if (file.size === 0) {
    throw new Error("The selected CSV file is empty.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/datasets/profile`,
    {
      method: "POST",
      body: formData,
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as DatasetProfileResponse;
}

export async function getDatasets(
  signal?: AbortSignal,
): Promise<DatasetSummary[]> {
  const response = await fetch(`${API_BASE_URL}/datasets`, {
    method: "GET",
    signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as DatasetSummary[];
}

export async function getDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<DatasetProfileResponse> {
  const cleanedDatasetId = datasetId.trim();

  if (!cleanedDatasetId) {
    throw new Error("Dataset ID is required.");
  }

  const response = await fetch(
    `${API_BASE_URL}/datasets/${encodeURIComponent(cleanedDatasetId)}`,
    {
      method: "GET",
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as DatasetProfileResponse;
}