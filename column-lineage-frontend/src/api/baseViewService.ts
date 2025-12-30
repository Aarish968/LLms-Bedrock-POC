import { api, apiUtils, AxiosError } from './client';

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

export const baseViewService = {
  /**
   * Fetch base view data from the API
   */
  async getBaseViewData(params: BaseViewParams = {}): Promise<BaseViewResponse> {
    try {
      const response = await api.get<BaseViewResponse>('/api/v1/lineage/public/base-view', {
        params: {
          limit: params.limit || 100,
          offset: params.offset || 0,
          ...(params.mock && { mock: params.mock }),
        },
      });

      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      
      // Use utility functions for better error handling
      if (apiUtils.isNetworkError(axiosError)) {
        throw new Error('Network error - please check your connection');
      }
      
      if (apiUtils.isTimeoutError(axiosError)) {
        throw new Error('Request timeout - please try again');
      }
      
      if (apiUtils.isServerError(axiosError)) {
        throw new Error('Server error - please try again later');
      }
      
      // Use the utility function to get error message
      const errorMessage = apiUtils.getErrorMessage(axiosError);
      throw new Error(errorMessage || 'Failed to fetch base view data');
    }
  },
};