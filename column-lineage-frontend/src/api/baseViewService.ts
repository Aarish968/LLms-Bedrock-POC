import axios from 'axios';

// Types for the base view API
export interface BaseViewRecord {
  sr_no: number;
  table_name: string;
}

export interface BaseViewResponse {
  total_records: number;
  records: BaseViewRecord[];
}

export interface BaseViewParams {
  limit?: number;
  offset?: number;
  mock?: boolean;
}

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const baseViewService = {
  /**
   * Fetch base view data from the API
   */
  async getBaseViewData(params: BaseViewParams = {}): Promise<BaseViewResponse> {
    try {
      const response = await apiClient.get('/api/v1/lineage/public/base-view', {
        params: {
          limit: params.limit || 100,
          offset: params.offset || 0,
          ...(params.mock && { mock: params.mock }),
        },
      });

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || 
          error.message || 
          'Failed to fetch base view data'
        );
      }
      throw error;
    }
  },
};