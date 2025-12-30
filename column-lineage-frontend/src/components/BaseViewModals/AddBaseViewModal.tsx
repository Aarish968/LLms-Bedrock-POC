import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useCreateBaseView } from '../../hooks/useBaseView';

interface AddBaseViewModalProps {
  open: boolean;
  onClose: () => void;
}

export const AddBaseViewModal: React.FC<AddBaseViewModalProps> = ({ open, onClose }) => {
  const [srNo, setSrNo] = useState<string>('');
  const [tableName, setTableName] = useState<string>('');
  const [errors, setErrors] = useState<{ srNo?: string; tableName?: string }>({});

  const createMutation = useCreateBaseView();

  const validateForm = () => {
    const newErrors: { srNo?: string; tableName?: string } = {};

    if (!srNo.trim()) {
      newErrors.srNo = 'Serial number is required';
    } else if (isNaN(Number(srNo)) || Number(srNo) <= 0) {
      newErrors.srNo = 'Serial number must be a positive number';
    }

    if (!tableName.trim()) {
      newErrors.tableName = 'Table name is required';
    } else if (tableName.length > 255) {
      newErrors.tableName = 'Table name must be less than 255 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await createMutation.mutateAsync({
        sr_no: Number(srNo),
        table_name: tableName.trim(),
      });

      // Reset form and close modal on success
      setSrNo('');
      setTableName('');
      setErrors({});
      onClose();
    } catch (error) {
      // Error is handled by the mutation hook
      console.error('Create failed:', error);
    }
  };

  const handleClose = () => {
    if (!createMutation.isPending) {
      setSrNo('');
      setTableName('');
      setErrors({});
      createMutation.reset();
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Add New Record</DialogTitle>
        
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            {createMutation.error && (
              <Alert severity="error">
                {createMutation.error.message}
              </Alert>
            )}

            <TextField
              label="Serial Number"
              type="number"
              value={srNo}
              onChange={(e) => setSrNo(e.target.value)}
              error={!!errors.srNo}
              helperText={errors.srNo}
              disabled={createMutation.isPending}
              required
              fullWidth
              inputProps={{ min: 1 }}
            />

            <TextField
              label="Table Name"
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              error={!!errors.tableName}
              helperText={errors.tableName}
              disabled={createMutation.isPending}
              required
              fullWidth
              inputProps={{ maxLength: 255 }}
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button 
            onClick={handleClose} 
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={createMutation.isPending}
            startIcon={createMutation.isPending ? <CircularProgress size={20} /> : null}
          >
            {createMutation.isPending ? 'Adding...' : 'Add Record'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AddBaseViewModal;