import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { lineageService, LineageAnalysisRequest, LineageAnalysisResponse, LineageAnalysisJob } from '@/api/lineageService';

export const useStartLineageAnalysis = () => {
  return useMutation({
    mutationFn: (request: LineageAnalysisRequest) => lineageService.startAnalysis(request),
    onSuccess: (data: LineageAnalysisResponse) => {
      toast.success(`Analysis started successfully! Job ID: ${data.job_id}`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to start analysis: ${error.message}`);
    },
  });
};

export const useJobStatus = (jobId: string | null, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['lineage-job-status', jobId],
    queryFn: () => {
      if (!jobId) {
        throw new Error('Job ID is required');
      }
      return lineageService.getJobStatus(jobId);
    },
    enabled: enabled && !!jobId && jobId !== 'null',
    refetchInterval: (data) => {
      // Refetch every 2 seconds if job is still running
      if (data?.status === 'PENDING' || data?.status === 'RUNNING') {
        return 2000;
      }
      return false;
    },
  });
};

export const useLineageResults = (jobId: string | null, enabled: boolean = false) => {
  return useQuery({
    queryKey: ['lineage-results', jobId],
    queryFn: () => {
      if (!jobId) {
        throw new Error('Job ID is required');
      }
      return lineageService.getResults(jobId);
    },
    enabled: enabled && !!jobId && jobId !== 'null',
  });
};

export const useLineageJobs = () => {
  return useQuery({
    queryKey: ['lineage-jobs'],
    queryFn: () => lineageService.listJobs(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

// Custom hook for managing the complete lineage analysis workflow
export const useLineageWorkflow = () => {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);

  const startAnalysisMutation = useStartLineageAnalysis();
  const jobStatusQuery = useJobStatus(currentJobId, !!currentJobId);
  const resultsQuery = useLineageResults(currentJobId, showResults);

  const startAnalysis = async (request: LineageAnalysisRequest) => {
    try {
      const response = await startAnalysisMutation.mutateAsync(request);
      setCurrentJobId(response.job_id);
      setShowResults(false);
    } catch (error) {
      console.error('Failed to start analysis:', error);
    }
  };

  const viewResults = () => {
    if (currentJobId && jobStatusQuery.data?.status === 'COMPLETED') {
      setShowResults(true);
    }
  };

  const resetWorkflow = () => {
    setCurrentJobId(null);
    setShowResults(false);
  };

  return {
    // State
    currentJobId,
    showResults,
    
    // Queries
    jobStatus: jobStatusQuery.data,
    jobStatusLoading: jobStatusQuery.isLoading,
    results: resultsQuery.data,
    resultsLoading: resultsQuery.isLoading,
    
    // Actions
    startAnalysis,
    viewResults,
    resetWorkflow,
    
    // Status checks
    isAnalysisRunning: startAnalysisMutation.isPending,
    isJobRunning: jobStatusQuery.data?.status === 'PENDING' || jobStatusQuery.data?.status === 'RUNNING',
    isJobCompleted: jobStatusQuery.data?.status === 'COMPLETED',
    isJobFailed: jobStatusQuery.data?.status === 'FAILED',
  };
};