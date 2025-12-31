import { useQuery } from '@tanstack/react-query';
import { lineageService, ViewInfo } from '@/api/lineageService';

export const useAvailableViews = (params: {
  schema_filter?: string;
  limit?: number;
  offset?: number;
} = {}) => {
  return useQuery({
    queryKey: ['available-views', params],
    queryFn: () => lineageService.getAvailableViews(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};