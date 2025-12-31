import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import { Add, Refresh } from '@mui/icons-material';
import { useLineageJobs, useJobStatus, useLineageResults } from '@/hooks/lineage/useLineageAnalysis';
import JobStatusCard from './JobStatusCard';
import ResultsViewer from './ResultsViewer';

interface JobsDashboardProps {
  onNewAnalysis: () => void;
}

const JobsDashboard: React.FC<JobsDashboardProps> = ({ onNewAnalysis }) => {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);

  const { data: jobs, isLoading: jobsLoading, refetch: refetchJobs } = useLineageJobs();
  const { data: selectedJobStatus, refetch: refetchJobStatus } = useJobStatus(
    selectedJobId, 
    !!selectedJobId
  );
  const { data: resultsData, isLoading: resultsLoading } = useLineageResults(
    selectedJobId,
    showResults
  );

  const handleViewResults = (jobId: string) => {
    setSelectedJobId(jobId);
    setShowResults(true);
  };

  const handleRefreshJob = (jobId: string) => {
    setSelectedJobId(jobId);
    refetchJobStatus();
  };

  const handleCloseResults = () => {
    setShowResults(false);
    setSelectedJobId(null);
  };

  const handleRefreshAll = () => {
    refetchJobs();
  };

  if (jobsLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <Typography>Loading jobs...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="between" sx={{ mb: 3 }}>
        <Typography variant="h5" component="h1">
          Column Lineage Jobs
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefreshAll}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={onNewAnalysis}
          >
            New Analysis
          </Button>
        </Box>
      </Box>

      {!jobs || jobs.length === 0 ? (
        <Alert severity="info">
          No analysis jobs found. Start your first analysis!
        </Alert>
      ) : (
        <Box>
          {jobs.map((job) => (
            <JobStatusCard
              key={job.job_id}
              jobId={job.job_id}
              status={job.status}
              totalViews={job.total_views}
              processedViews={job.processed_views}
              resultsCount={job.results_count}
              createdAt={job.created_at}
              errorMessage={job.error_message}
              onViewResults={() => handleViewResults(job.job_id)}
              onRefresh={() => handleRefreshJob(job.job_id)}
            />
          ))}
        </Box>
      )}

      {/* Results Dialog */}
      <Dialog
        open={showResults}
        onClose={handleCloseResults}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Analysis Results - Job {selectedJobId?.slice(0, 8)}...
        </DialogTitle>
        <DialogContent>
          {resultsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <Typography>Loading results...</Typography>
            </Box>
          ) : resultsData ? (
            <ResultsViewer
              results={resultsData.results}
              summary={resultsData.summary}
              totalResults={resultsData.total_results}
            />
          ) : (
            <Alert severity="error">
              Failed to load results
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseResults}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default JobsDashboard;