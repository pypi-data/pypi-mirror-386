/**
 * Service responsible for loading data files and directories
 * Simplified to work with backend API
 */
import { MentionContext } from './ChatContextLoaders';

export type IDatasetSchema =
  | {
      success: boolean;
      loading: false;
      fileId: string;
      fileName: string;
      filePath: string;
      fileType: string;
      extractedAt: string;
      summary: string;
      totalRows: number;
      totalColumns: number;
      columns: Array<{
        name: string;
        dataType: string;
        description: string;
      }>;
      sampleData: any[][] | object[];
      error: false;
      // Optional file modification time (seconds since epoch) from backend cache
      fileMtime?: number;
    }
  | {
      success: false;
      loading: true;
      error: false;
    }
  | {
      success: false;
      loading: false;
      error: string;
    };

// Type alias for successful schema
type ISuccessfulDatasetSchema = {
  success: true;
  loading: false;
  fileId: string;
  fileName: string;
  filePath: string;
  fileType: string;
  extractedAt: string;
  summary: string;
  totalRows: number;
  totalColumns: number;
  columns: Array<{
    name: string;
    dataType: string;
    description: string;
  }>;
  sampleData: any[][] | object[];
  error: false;
  fileMtime?: number;
};

import { FileCacheService } from '../../Services/FileCacheService';

export interface IFileInfo {
  extension: string;
  is_csv: boolean;
  is_tsv: boolean;
  is_json: boolean;
  is_parquet: boolean;
  is_pkl: boolean;
  is_text: boolean;
  is_data: boolean;
  is_binary: boolean;
  size_bytes: number;
  // Optional last modified timestamp (ISO string) from backend
  last_modified?: string;
}

export interface ICsvInfo {
  type: 'csv';
  preview_type: 'header_and_sample';
  header?: string;
  sample_rows: string[];
  estimated_columns: number;
}

export interface IJsonInfo {
  type: 'json';
  preview_type: 'structure_preview';
  structure: 'object' | 'array' | 'primitive';
  estimated_keys?: number;
  estimated_items?: number;
}

export interface IFileEntry {
  id: string;
  name: string;
  path: string;
  absolute_path: string;
  relative_path: string;
  is_directory: boolean;
  file_info?: IFileInfo;
  content_preview?: string;
  is_truncated?: boolean;
  preview_length?: number;
  csv_info?: ICsvInfo;
  json_info?: IJsonInfo;
  schema?: IDatasetSchema;
  uploaded?: boolean;
}

export interface IScanResult {
  success: boolean;
  data_path: string;
  file_count: number;
  directory_count: number;
  total_items: number;
  files: IFileEntry[];
  error?: string;
  error_type?: string;
}

/**
 * Service for loading data files using Python kernel execution
 */
export class DataLoaderService {
  private static _fileCacheService: FileCacheService;

  /**
   * Initialize the service with FileCacheService
   */
  private static getFileCacheService(): FileCacheService {
    if (!this._fileCacheService) {
      this._fileCacheService = FileCacheService.getInstance();
    }
    return this._fileCacheService;
  }

  /**
   * Load datasets from backend API
   */
  public static async loadDatasets(
    paths: string[] = ['./data']
  ): Promise<MentionContext[]> {
    const cacheService = this.getFileCacheService();

    // If cache is not initialized, wait for it to be populated
    if (!cacheService.isInitialized()) {
      console.log(
        '[DataLoaderService] Cache not initialized, waiting for FileExplorerWidget to populate...'
      );
      return [];
    }

    // Get files from cache and convert to MentionContext format
    const files = cacheService.getFiles();
    return this.convertToMentionContexts(files);
  }

  /**
   * Refresh datasets from backend API
   */
  public static async refreshDatasets(directory?: string): Promise<void> {
    // DataLoaderService no longer needs to refresh directly
    // The FileExplorerWidget handles all refreshing via polling
    console.log(
      '[DataLoaderService] Refresh requested - FileExplorerWidget handles refreshing via polling'
    );
  }

  /**
   * Convert a FileEntry to MentionContext format
   */
  public static convertFileEntryToMentionContext(
    file: IFileEntry
  ): MentionContext | null {
    try {
      // Normalize the relative path and add ./data/ prefix for id
      const normalizedRelativePath = file.relative_path.replace(/\\/g, '/');

      // Path should also include the data prefix
      const path = `./data/${normalizedRelativePath}`;

      // Get parent path with ./data/ prefix
      const parentPath = this.getParentPathFromFile(file.relative_path);
      const normalizedParentPath = parentPath
        ? `./data/${parentPath}`
        : './data';

      if (file.is_directory) {
        return {
          type: 'directory' as const,
          id: file.id,
          name: file.name,
          path: path,
          isDirectory: true,
          parentPath: normalizedParentPath
        };
      } else {
        return {
          type: 'data' as const,
          id: file.id,
          name: file.name,
          description: this.getFileDescription(file),
          content: this.formatFileContent(file),
          path: path,
          isDirectory: false,
          parentPath: normalizedParentPath
        };
      }
    } catch (error) {
      console.error('[DataLoaderService] Error converting file entry:', error);
      return null;
    }
  }

  /**
   * Convert file entries to MentionContext format
   */
  private static convertToMentionContexts(
    files: IFileEntry[]
  ): MentionContext[] {
    // Filter out any unwanted files
    return files.map((file: IFileEntry) => {
      // Normalize the relative path and add ./data/ prefix for id
      const normalizedRelativePath = file.relative_path.replace(/\\/g, '/');

      // Path should also include the data prefix
      const path = `./data/${normalizedRelativePath}`;

      // Get parent path with ./data/ prefix
      const parentPath = this.getParentPathFromFile(file.relative_path);
      const normalizedParentPath = parentPath
        ? `./data/${parentPath}`
        : './data';

      if (file.is_directory) {
        return {
          type: 'directory' as const,
          id: file.id,
          name: file.name,
          path: path,
          isDirectory: true,
          parentPath: normalizedParentPath
        };
      } else {
        return {
          type: 'data' as const,
          id: file.id,
          name: file.name,
          description: this.getFileDescription(file),
          content: this.formatFileContent(file),
          path: path,
          isDirectory: false,
          parentPath: normalizedParentPath
        };
      }
    });
  }

  /**
   * Format schema data for LLM consumption with safe truncation
   */
  private static formatSchemaForLLM(schema: IDatasetSchema): string {
    if (!schema.success) {
      return '';
    }

    // Cast to successful schema type for type safety
    const successfulSchema = schema as ISuccessfulDatasetSchema;

    // Route to appropriate formatter based on file type
    if (successfulSchema.fileType === 'xlsx') {
      return this.formatExcelSchema(successfulSchema);
    } else if (successfulSchema.fileType === 'json') {
      return this.formatJsonSchema(successfulSchema);
    } else {
      return this.formatDefaultSchema(successfulSchema);
    }
  }

  /**
   * Format Excel schema data for LLM consumption
   */
  private static formatExcelSchema(schema: ISuccessfulDatasetSchema): string {
    let schemaContent = 'Dataset Schema:\n';
    schemaContent += `File: ${schema.fileName}\n`;
    schemaContent += `Type: ${schema.fileType}\n`;
    schemaContent += `Sheet 1, Columns: ${schema.totalColumns}\n`;
    schemaContent += `Summary: ${schema.summary}\n\n`;

    // Format columns with safe truncation
    if (schema.columns && schema.columns.length > 0) {
      schemaContent += 'Sheet 1, Columns:\n';

      const maxColumns = Math.min(schema.columns.length, 20); // Limit to 20 columns

      for (let i = 0; i < maxColumns; i++) {
        const col = schema.columns[i];
        const truncatedName =
          col.name.length > 30 ? col.name.substring(0, 30) + '...' : col.name;

        schemaContent += `  ${i + 1}. ${truncatedName} (${col.dataType})\n`;
      }

      if (schema.columns.length > maxColumns) {
        schemaContent += `  ... and ${schema.columns.length - maxColumns} more columns\n`;
      }
      schemaContent += '\n';
    }

    // Format sample data with safe truncation
    if (schema.sampleData && schema.sampleData.length > 0) {
      schemaContent += 'Sheet 1, Sample Data (first 5 rows, max 10 columns):\n';

      const maxRows = Math.min(schema.sampleData.length, 5);
      const maxCols = Math.min(schema.columns?.length || 10, 10);

      for (let i = 0; i < maxRows; i++) {
        const row = schema.sampleData[i];
        if (Array.isArray(row)) {
          const truncatedRow = row.slice(0, maxCols).map(cell => {
            const cellStr = String(cell);
            return cellStr.length > 20
              ? cellStr.substring(0, 20) + '...'
              : cellStr;
          });
          schemaContent += `  Row ${i + 1}: ${truncatedRow.join(' | ')}\n`;
        } else {
          schemaContent += `  Row ${i + 1}: ${JSON.stringify(row)}\n`;
        }
      }

      if (schema.sampleData.length > maxRows) {
        schemaContent += `  ... and ${schema.sampleData.length - maxRows} more rows\n`;
      }
      schemaContent += '\n';
    }

    return schemaContent;
  }

  /**
   * Format JSON schema data for LLM consumption
   */
  private static formatJsonSchema(schema: ISuccessfulDatasetSchema): string {
    let schemaContent = 'Dataset Schema:\n';
    schemaContent += `File: ${schema.fileName}\n`;
    schemaContent += `Type: ${schema.fileType}\n`;
    schemaContent += `Attributes: ${schema.totalColumns}\n`;
    schemaContent += `Summary: ${schema.summary}\n\n`;

    // Format attributes with safe truncation
    if (schema.columns && schema.columns.length > 0) {
      schemaContent += 'Attributes:\n';

      const maxColumns = Math.min(schema.columns.length, 20); // Limit to 20 attributes

      for (let i = 0; i < maxColumns; i++) {
        const col = schema.columns[i];
        const truncatedName =
          col.name.length > 30 ? col.name.substring(0, 30) + '...' : col.name;

        schemaContent += `  ${i + 1}. ${truncatedName} (${col.dataType})\n`;
      }

      if (schema.columns.length > maxColumns) {
        schemaContent += `  ... and ${schema.columns.length - maxColumns} more attributes\n`;
      }
      schemaContent += '\n';
    }

    // Format sample data with safe truncation
    if (schema.sampleData && schema.sampleData.length > 0) {
      schemaContent += 'Sample Items (first 5 items, max 10 attributes):\n';

      const maxRows = Math.min(schema.sampleData.length, 5);
      const maxCols = Math.min(schema.columns?.length || 10, 10);

      for (let i = 0; i < maxRows; i++) {
        const row = schema.sampleData[i];
        if (Array.isArray(row)) {
          const truncatedRow = row.slice(0, maxCols).map(cell => {
            const cellStr = String(cell);
            return cellStr.length > 20
              ? cellStr.substring(0, 20) + '...'
              : cellStr;
          });
          schemaContent += `  Item ${i + 1}: ${truncatedRow.join(' | ')}\n`;
        } else {
          schemaContent += `  Item ${i + 1}: ${JSON.stringify(row)}\n`;
        }
      }

      if (schema.sampleData.length > maxRows) {
        schemaContent += `  ... and ${schema.sampleData.length - maxRows} more items\n`;
      }
      schemaContent += '\n';
    }

    return schemaContent;
  }

  /**
   * Format default schema data for LLM consumption (for non-Excel, non-JSON files)
   */
  private static formatDefaultSchema(schema: ISuccessfulDatasetSchema): string {
    let schemaContent = 'Dataset Schema:\n';
    schemaContent += `File: ${schema.fileName}\n`;
    schemaContent += `Type: ${schema.fileType}\n`;
    schemaContent += `Columns: ${schema.totalColumns}\n`;
    schemaContent += `Summary: ${schema.summary}\n\n`;

    // Format columns with safe truncation
    if (schema.columns && schema.columns.length > 0) {
      schemaContent += 'Columns:\n';

      const maxColumns = Math.min(schema.columns.length, 20); // Limit to 20 columns

      for (let i = 0; i < maxColumns; i++) {
        const col = schema.columns[i];
        const truncatedName =
          col.name.length > 30 ? col.name.substring(0, 30) + '...' : col.name;

        schemaContent += `  ${i + 1}. ${truncatedName} (${col.dataType})\n`;
      }

      if (schema.columns.length > maxColumns) {
        schemaContent += `  ... and ${schema.columns.length - maxColumns} more columns\n`;
      }
      schemaContent += '\n';
    }

    // Format sample data with safe truncation
    if (schema.sampleData && schema.sampleData.length > 0) {
      schemaContent += 'Sample Data (first 5 rows, max 10 columns):\n';

      const maxRows = Math.min(schema.sampleData.length, 5);
      const maxCols = Math.min(schema.columns?.length || 10, 10);

      for (let i = 0; i < maxRows; i++) {
        const row = schema.sampleData[i];
        if (Array.isArray(row)) {
          const truncatedRow = row.slice(0, maxCols).map(cell => {
            const cellStr = String(cell);
            return cellStr.length > 20
              ? cellStr.substring(0, 20) + '...'
              : cellStr;
          });
          schemaContent += `  Row ${i + 1}: ${truncatedRow.join(' | ')}\n`;
        } else {
          schemaContent += `  Row ${i + 1}: ${JSON.stringify(row)}\n`;
        }
      }

      if (schema.sampleData.length > maxRows) {
        schemaContent += `  ... and ${schema.sampleData.length - maxRows} more rows\n`;
      }
      schemaContent += '\n';
    }

    return schemaContent;
  }

  /**
   * Format file content for display
   */
  private static formatFileContent(file: IFileEntry): string {
    let contentWithPath = `File Path: ${file.path}\n\n`;

    if (file.schema && file.schema.success) {
      contentWithPath += this.formatSchemaForLLM(file.schema);
    } else {
      // Handle binary files
      if (file.file_info?.is_binary) {
        contentWithPath += `Binary File (${file.file_info.extension})\n\n`;
        contentWithPath += 'Content: Binary file - content not displayed';
        return contentWithPath;
      }

      // Older method of getting file content
      if (file.csv_info) {
        contentWithPath += `CSV File (${file.csv_info.estimated_columns} columns)\n`;
        if (file.csv_info.header) {
          contentWithPath += `Header: ${file.csv_info.header}\n`;
        }
        if (file.csv_info.sample_rows?.length > 0) {
          contentWithPath += `Sample Rows:\n${file.csv_info.sample_rows.join('\n')}\n`;
        } else if (file.content_preview) {
          contentWithPath += `\nContent Preview:\n${file.content_preview}`;

          if (file.is_truncated) {
            contentWithPath +=
              '\n\n[Content truncated - showing first 5000 chars or 5 lines]';
          }
        }
      } else if (file.json_info) {
        contentWithPath += `JSON File (${file.json_info.structure})\n`;
        if (file.json_info.estimated_keys) {
          contentWithPath += `Estimated Keys: ${file.json_info.estimated_keys}\n`;
        }
        if (file.json_info.estimated_items) {
          contentWithPath += `Estimated Items: ${file.json_info.estimated_items}\n`;
        }
      }
    }

    if (file.file_info && file.file_info.size_bytes) {
      contentWithPath += `\nFile Size: ${file.file_info.size_bytes} bytes`;
    }

    return contentWithPath;
  }

  /**
   * Public wrapper to get formatted file content for UI rendering
   */
  public static getFormattedFileContent(file: IFileEntry): string {
    return DataLoaderService.formatFileContent(file);
  }

  /**
   * Generate appropriate file description based on file info
   */
  private static getFileDescription(file: IFileEntry): string {
    if (!file.file_info) {
      return 'Unknown file type';
    }

    // Handle binary files first
    if (file.file_info.is_binary) {
      return `Binary file (${file.file_info.extension})`;
    }

    if (file.csv_info) {
      return `CSV file (${file.csv_info.estimated_columns} cols)`;
    } else if (file.json_info) {
      return `JSON file (${file.json_info.structure})`;
    } else if (file.file_info.is_data) {
      return `Data file (${file.file_info.extension})`;
    } else {
      return `Text file (${file.file_info.extension})`;
    }
  }

  /**
   * Get the parent path from a given path
   */
  private static getParentPath(path: string): string {
    const parts = path.split('/');
    parts.pop(); // Remove the last part
    return parts.join('/') || './data';
  }

  /**
   * Get the parent path from a file's relative path
   * Returns undefined if the file is in the root data directory
   */
  private static getParentPathFromFile(
    relativePath: string
  ): string | undefined {
    // Normalize path separators to forward slashes
    const normalizedPath = relativePath.replace(/\\/g, '/');

    // Split the path into parts
    const parts = normalizedPath.split('/');

    // If there's only one part (file in root), no parent path
    if (parts.length <= 1) {
      return undefined;
    }

    // Remove the filename (last part) to get parent directory
    parts.pop();

    // Join the remaining parts to form the parent path
    return parts.join('/');
  }
}
