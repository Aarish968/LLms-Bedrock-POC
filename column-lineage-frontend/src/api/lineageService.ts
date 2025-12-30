import { api, apiUtils, AxiosError } from './client';

// Types for lineage analysis API
export interface LineageAnalysisRequest {
  view_names?: string[];
  schema_filter?: string;
  include_system_views?: boolean;
  max_views?: number;
  async_processing?: boolean;
}

export interface LineageAnalysisResponse {
  job_id: string;
  status: string;
  message: string;
  results_url?: string;
}

export interface LineageResult {
  view_name: string;
  view_column: string;
  column_type: string;
  source_table: string;
  source_column: string;
  expression_type?: string;
  confidence_score: number;
}

export interface LineageResultsResponse {
  job_id: string;
  status: string;
  total_results: number;
  results: LineageResult[];
  summary: Record<string, any>;
}

export interface ViewInfo {
  view_name: string;
  schema_name: string;
  database_name: string;
  column_count: number;
  created_date?: string;
  last_modified?: string;
}

export const lineageService = {
  /**
   * Start lineage analysis
   */
  async startAnalysis(request: LineageAnalysisRequest): Promise<LineageAnalysisResponse> {
    try {
      const response = await api.post<LineageAnalysisResponse>('/api/v1/lineage/analyze', request);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/lineage/status/${jobId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * Get lineage results
   */
  async getResults(jobId: string, limit?: number, offset?: number): Promise<LineageResultsResponse> {
    try {
      const response = await api.get<LineageResultsResponse>(`/api/v1/lineage/results/${jobId}`, {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * List available views
   */
  async getViews(schemaFilter?: string, limit?: number, offset?: number): Promise<ViewInfo[]> {
    try {
      const response = await api.get<ViewInfo[]>('/api/v1/lineage/views', {
        params: { schema_filter: schemaFilter, limit, offset },
      });
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * Export results
   */
  async exportResults(jobId: string, format: string = 'csv', includeMetadata: boolean = true): Promise<void> {
    try {
      await api.download(`/api/v1/lineage/export/${jobId}`, `lineage_results_${jobId}.${format}`, {
        method: 'POST',
        data: {
          format,
          include_metadata: includeMetadata,
        },
      });
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * Cancel job
   */
  async cancelJob(jobId: string): Promise<{ message: string }> {
    try {
      const response = await api.delete(`/api/v1/lineage/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },

  /**
   * List jobs
   */
  async listJobs(statusFilter?: string, limit?: number, offset?: number): Promise<any[]> {
    try {
      const response = await api.get('/api/v1/lineage/jobs', {
        params: { status_filter: statusFilter, limit, offset },
      });
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(apiUtils.getErrorMessage(axiosError));
    }
  },
};