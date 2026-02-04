import { useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { FileInputConfig } from '../../types/agent';
import { cn } from '../../lib/utils';

interface FileUploaderProps {
  fileInputs: FileInputConfig[];
  disabled?: boolean;
  onFilesChange?: (files: Record<string, File[]>) => void;
}

export default function FileUploader({
  fileInputs,
  disabled = false,
  onFilesChange,
}: FileUploaderProps) {
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, File[]>>({});

  const handleFileUpload = (fileInputId: string, files: FileList | null) => {
    if (!files) return;

    const newFiles = Array.from(files);
    setUploadedFiles((prev) => ({
      ...prev,
      [fileInputId]: newFiles,
    }));

    onFilesChange?.({
      ...uploadedFiles,
      [fileInputId]: newFiles,
    });
  };

  const handleRemoveFile = (fileInputId: string, index: number) => {
    const updatedFiles = [...uploadedFiles[fileInputId]];
    updatedFiles.splice(index, 1);

    setUploadedFiles((prev) => ({
      ...prev,
      [fileInputId]: updatedFiles,
    }));

    onFilesChange?.({
      ...uploadedFiles,
      [fileInputId]: updatedFiles,
    });
  };

  return (
    <div className="mt-3 space-y-3">
      {fileInputs.map((fileInput) => (
        <div key={fileInput.id}>
          <label
            className={cn(
              'flex items-center justify-center gap-2 p-3 border-2 border-dashed border-border-subtle rounded-lg cursor-pointer hover:border-primary/50 transition-colors',
              disabled && 'disabled:opacity-50 cursor-not-allowed'
            )}
          >
            <Upload className="w-4 h-4 text-text-muted" />
            <span className="text-sm text-text-muted">
              {fileInput.label}
              {fileInput.optional && ' (可选)'}
            </span>
            <input
              type="file"
              className="hidden"
              multiple={fileInput.multiple}
              accept={fileInput.accept}
              disabled={disabled}
              onChange={(e) => handleFileUpload(fileInput.id, e.target.files)}
            />
          </label>
          {uploadedFiles[fileInput.id] && uploadedFiles[fileInput.id].length > 0 && (
            <div className="mt-2 space-y-1">
              {uploadedFiles[fileInput.id].map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs text-text-muted bg-bg-elevated/50 rounded px-2 py-1"
                >
                  <FileText className="w-3 h-3" />
                  <span className="flex-1 truncate">{file.name}</span>
                  <span className="text-text-muted/60">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                  {!disabled && (
                    <button
                      onClick={() => handleRemoveFile(fileInput.id, idx)}
                      className="hover:text-semantic-danger transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
