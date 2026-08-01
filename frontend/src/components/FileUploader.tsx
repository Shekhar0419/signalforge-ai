import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  UploadCloud,
} from "lucide-react";
import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { uploadDataset } from "../services/api";
import type { DatasetProfileResponse } from "../services/api";

type FileUploaderProps = {
  onUploadComplete: (profile: DatasetProfileResponse) => void;
};

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

function validateFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    return "Please select a CSV file.";
  }

  if (file.size === 0) {
    return "The selected CSV file is empty.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "The selected file exceeds the 10 MB upload limit.";
  }

  return null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} bytes`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUploader({
  onUploadComplete,
}: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function selectFile(file: File): void {
    const validationError = validateFile(file);

    setErrorMessage(validationError);
    setSuccessMessage(null);

    if (validationError) {
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const file = event.target.files?.[0];

    if (file) {
      selectFile(file);
    }
  }

  function handleDragOver(
    event: DragEvent<HTMLDivElement>,
  ): void {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(
    event: DragEvent<HTMLDivElement>,
  ): void {
    event.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ): void {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      selectFile(file);
    }
  }

  async function handleUpload(): Promise<void> {
    if (!selectedFile || isUploading) {
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const profile = await uploadDataset(selectedFile);

      setSuccessMessage(
        `${selectedFile.name} was analyzed successfully.`,
      );

      onUploadComplete(profile);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The dataset could not be uploaded.";

      setErrorMessage(message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div
        className={[
          "rounded-2xl border-2 border-dashed p-6 text-center transition",
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-slate-300 bg-slate-50",
        ].join(" ")}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-white text-blue-700 shadow-sm">
          <UploadCloud size={28} />
        </div>

        <h3 className="mt-4 text-lg font-semibold text-slate-950">
          Upload a CSV dataset
        </h3>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Drag and drop a CSV here, or browse your computer.
        </p>

        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={handleInputChange}
        />

        <button
          type="button"
          className="mt-5 rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-400 hover:text-blue-700"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
        >
          Browse files
        </button>
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2 text-blue-700">
              <FileText size={20} />
            </div>

            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">
                {selectedFile.name}
              </p>

              <p className="text-xs text-slate-500">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>

          <button
            type="button"
            className="shrink-0 rounded-xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isUploading}
            onClick={handleUpload}
          >
            {isUploading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin" size={16} />
                Analyzing
              </span>
            ) : (
              "Analyze dataset"
            )}
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="mt-0.5 shrink-0" size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
}