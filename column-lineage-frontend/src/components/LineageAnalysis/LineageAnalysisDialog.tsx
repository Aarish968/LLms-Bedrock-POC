import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  Divider,
} from '@mui/material';
import { PlayArrow, Cancel, Visibility, Refresh } from '@mui/icons-material';
import { useLineageWorkflow } from '@/hooks/lineage/useLineageAnalysis';
import { useAvailableViews } from '@/hooks/lineage/useAvailableViews';
import DatabaseSchemaSelector from './DatabaseSchemaSelector';
import DebugInfo from './DebugInfo';

interface LineageAnalysisDialogProps {
  open: boolean;
  onClose: () => void;
}

const LineageAnalysisDialog: React.FC<LineageAnalysisDialogProps> = ({ open, onClose }) => {
  const [selectedDatabase, setSelectedDatabase] = useState('');
  const [selectedSchema, setSelectedSchema] = useState('');
  const [asyncProcessing, setAsyncProcessing] = useState(true);
  const [includeMetadata, setIncludeMetadata] = useState(true);

  const {
    currentJobId,
    showResults,
    jobStatus,
    jobStatusLoading,
    results,
    resultsLoading,
    startAnalysis,
    viewResults,
    resetWorkflow,
    isAnalysisRunning,
    isJobRunning,
    isJobCompleted,
    isJobFailed,
  } = useLineageWorkflow();

  const { data: availableViews, isLoading: viewsLoading } = useAvailableViews(
    selectedDatabase, 
    selectedSchema
  );

  const handleStartAnalysis = async () => {
    await startAnalysis({
      database_filter: selectedDatabase,
      schema_filter: selectedSchema,
      async_processing: asyncProcessing,
      include_metadata: includeMetadata,
    });
  };

  const handleClose = () => {
    resetWorkflow();
    setSelectedDatabase('');
    setSelectedSchema('');
    onClose();
  };

  const canStartAnalysis = selectedDatabase && selectedSchema && !isAnalysisRunning && !viewsLoading;

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
    if (!jobStatus) return 0;
    if (jobStatus.total_views === 0) return 0;
    return (jobStatus.processed_views / jobStatus.total_views) * 100;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Column Lineage Analysis</Typography>
          {currentJobId && (
            <Chip
              label={`Job: ${currentJobId.slice(0, 8)}...`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Debug Info - Remove this in production */}
        <DebugInfo
          currentJobId={currentJobId}
          jobStatus={jobStatus}
          isAnalysisRunning={isAnalysisRunning}
          isJobRunning={isJobRunning}
          isJobCompleted={isJobCompleted}
        />

        {!currentJobId ? (
          // Configuration Phase
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure and start column lineage analysis for your database views.
            </Typography>

            <DatabaseSchemaSelector
              selectedDatabase={selectedDatabase}
              selectedSchema={selectedSchema}
              onDatabaseChange={setSelectedDatabase}
              onSchemaChange={setSelectedSchema}
              disabled={isAnalysisRunning}
            />

            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={asyncProcessing}
                    onChange={(e) => setAsyncProcessing(e.target.checked)}
                  />
                }
                label="Async Processing"
              />
              <Typography variant="caption" display="block" color="text.secondary">
                Run analysis in background (recommended for large datasets)
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                  />
                }
                label="Include Metadata"
              />
              <Typography variant="caption" display="block" color="text.secondary">
                Include additional metadata in analysis results
              </Typography>
            </Box>

            {/* Available Views Preview */}
            {selectedDatabase && selectedSchema && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Available Views Preview
                </Typography>
                {viewsLoading ? (
                  <Typography variant="body2" color="text.secondary">
                    Loading views...
                  </Typography>
                ) : availableViews && availableViews.length > 0 ? (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Found {availableViews.length} views in {selectedDatabase}.{selectedSchema}
                    </Typography>
                    <Box sx={{ maxHeight: 100, overflow: 'auto' }}>
                      {availableViews.slice(0, 10).map((view, index) => (
                        <Chip
                          key={index}
                          label={view.view_name}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                      {availableViews.length > 10 && (
                        <Typography variant="caption" color="text.secondary">
                          ... and {availableViews.length - 10} more
                        </Typography>
                      )}
                    </Box>
                  </Box>
                ) : (
                  <Alert severity="warning">
                    No views found in {selectedDatabase}.{selectedSchema}
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        ) : (
          // Job Status Phase
          <Box>
            <Box sx={{ mb: 3 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                <Typography variant="subtitle1">Analysis Status</Typography>
                <Chip
                  label={jobStatus?.status || 'Unknown'}
                  color={getStatusColor(jobStatus?.status || '')}
                  size="small"
                />
              </Box>

              {jobStatus && (
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Progress: {jobStatus.processed_views} / {jobStatus.total_views} views processed
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={getProgressValue()}
                    sx={{ mb: 2 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Started: {new Date(jobStatus.created_at).toLocaleString()}
                  </Typography>
                </Box>
              )}

              {isJobFailed && jobStatus?.error_message && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {jobStatus.error_message}
                </Alert>
              )}

              {isJobCompleted && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Analysis completed successfully! Found {jobStatus?.results_count} lineage relationships.
                </Alert>
              )}
            </Box>

            {/* Results Preview */}
            {showResults && results && (
              <Box>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Analysis Results
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Total Results: {results.total_results}
                </Typography>
                
                {results.results.slice(0, 5).map((result, index) => (
                  <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2">
                      <strong>{result.view_name}.{result.view_column}</strong> ← {result.source_table}.{result.source_column}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Confidence: {(result.confidence_score * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                ))}
                
                {results.results.length > 5 && (
                  <Typography variant="caption" color="text.secondary">
                    ... and {results.results.length - 5} more results
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          Close
        </Button>

        {!currentJobId ? (
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handleStartAnalysis}
            disabled={!canStartAnalysis}
          >
            {isAnalysisRunning ? 'Starting...' : 'Start Analysis'}
          </Button>
        ) : (
          <Box>
            {isJobCompleted && !showResults && (
              <Button
                variant="contained"
                startIcon={<Visibility />}
                onClick={viewResults}
                disabled={resultsLoading}
                sx={{ mr: 1 }}
              >
                {resultsLoading ? 'Loading...' : 'View Results'}
              </Button>
            )}
            
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={resetWorkflow}
              disabled={isJobRunning}
            >
              New Analysis
            </Button>
          </Box>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default LineageAnalysisDialog;