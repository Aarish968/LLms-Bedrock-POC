import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  LinearProgress,
  Button,
  Alert,
} from '@mui/material';
import { Visibility, Refresh, Cancel } from '@mui/icons-material';

interface JobStatusCardProps {
  jobId: string;
  status: string;
  totalViews: number;
  processedViews: number;
  resultsCount: number;
  createdAt: string;
  errorMessage?: string;
  onViewResults: () => void;
  onRefresh: () => void;
  onCancel?: () => void;
  isLoading?: boolean;
}

const JobStatusCard: React.FC<JobStatusCardProps> = ({
  jobId,
  status,
  totalViews,
  processedViews,
  resultsCount,
  createdAt,
  errorMessage,
  onViewResults,
  onRefresh,
  onCancel,
  isLoading = false,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'warning';
      case 'RUNNING':
        return 'info';
      case 'COMPLETED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'CANCELLED':
        return 'default';
      default:
        return 'default';
    }
  };

  const getProgressValue = () => {
    if (totalViews === 0) return 0;
    return (processedViews / totalViews) * 100;
  };

  const isJobRunning = status === 'PENDING' || status === 'RUNNING';
  const isJobCompleted = status === 'COMPLETED';
  const isJobFailed = status === 'FAILED';

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6" component="div">
            Job: {jobId.slice(0, 8)}...
          </Typography>
          <Chip
            label={status}
            color={getStatusColor(status)}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Started: {new Date(createdAt).toLocaleString()}
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Progress: {processedViews} / {totalViews} views processed
        </Typography>

        {totalViews > 0 && (
          <LinearProgress
            variant="determinate"
            value={getProgressValue()}
            sx={{ mb: 2 }}
          />
        )}

        {isJobFailed && errorMessage && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errorMessage}
          </Alert>
        )}

        {isJobCompleted && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Analysis completed! Found {resultsCount} lineage relationships.
          </Alert>
        )}

        <Box display="flex" gap={1}>
          {isJobCompleted && (
            <Button
              variant="contained"
              startIcon={<Visibility />}
              onClick={onViewResults}
              size="small"
            >
              View Results
            </Button>
          )}
          
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={onRefresh}
            disabled={isLoading}
            size="small"
          >
            Refresh
          </Button>

          {isJobRunning && onCancel && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Cancel />}
              onClick={onCancel}
              size="small"
            >
              Cancel
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default JobStatusCard;