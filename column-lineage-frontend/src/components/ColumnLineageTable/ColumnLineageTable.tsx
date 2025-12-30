import { useMemo, useState } from 'react'
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid'
import { Box, Chip, Alert, CircularProgress, Typography, TextField, Button, Stack } from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Search as SearchIcon } from '@mui/icons-material'
import { useBaseView } from '../../hooks/useBaseView'
import { BaseViewRecord } from '../../api/baseViewService'

interface ColumnLineageTableProps {
  searchQuery: string
}

const ColumnLineageTable = ({ searchQuery }: ColumnLineageTableProps) => {
  const [localSearchQuery, setLocalSearchQuery] = useState('')

  // Fetch base view data from API (always enabled, no mock mode)
  const {
    data: apiData,
    isLoading,
    error,
    isError,
    refetch,
  } = useBaseView({
    mock: false,
    limit: 100 
  })

  // Transform API data to match the simplified table structure
  const transformedApiData: GridRowsProp = useMemo(() => {
    if (!apiData?.records) return []
    
    return apiData.records.map((record: BaseViewRecord) => ({
      id: record.sr_no,
      srNo: record.sr_no,
      tableName: record.table_name,
    }))
  }, [apiData])

  // Use API data
  const dataToUse = transformedApiData

  // Simplified columns - only Serial No. and Table Name
  const columns: GridColDef[] = [
    {
      field: 'srNo',
      headerName: 'Serial No.',
      width: 150,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color="primary"
          variant="outlined"
        />
      ),
    },
    {
      field: 'tableName',
      headerName: 'Table Name',
      flex: 1,
      minWidth: 300,
      renderCell: (params) => (
        <Box sx={{ 
          fontFamily: 'monospace', 
          fontSize: '0.875rem', 
          fontWeight: 'medium',
          color: 'text.primary'
        }}>
          {params.value}
        </Box>
      ),
    },
  ]

  // Filter data based on both search queries (prop and local)
  const filteredData = useMemo(() => {
    const combinedQuery = (searchQuery + ' ' + localSearchQuery).trim().toLowerCase()
    
    if (!combinedQuery) {
      return dataToUse
    }

    return dataToUse.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(combinedQuery)
      )
    )
  }, [searchQuery, localSearchQuery, dataToUse])

  // Handle button clicks
  const handleAdd = () => {
    console.log('Add button clicked')
    // Add your add functionality here
  }

  const handleEdit = () => {
    console.log('Edit button clicked')
    // Add your edit functionality here
  }

  // Error state
  if (isError) {
    return (
      <Box sx={{ mb: 2 }}>
        <Alert 
          severity="error" 
          action={
            <Button onClick={() => refetch()} size="small">
              Retry
            </Button>
          }
        >
          <Typography variant="h6" gutterBottom>
            Failed to load base view data
          </Typography>
          <Typography variant="body2">
            {error?.message || 'An unexpected error occurred'}
          </Typography>
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      {/* Header with title and controls on same line */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 2,
        flexWrap: 'wrap',
        gap: 2
      }}>
        <Typography variant="h6" component="h2">
          Source Column and Table Mapping
        </Typography>
        
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            placeholder="Search by serial number or table name..."
            value={localSearchQuery}
            onChange={(e) => setLocalSearchQuery(e.target.value)}
            size="small"
            sx={{ minWidth: 300 }}
            slotProps={{
              input: {
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              },
            }}
          />
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
            size="small"
          >
            Add
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={handleEdit}
            size="small"
          >
            Edit
          </Button>
        </Stack>
      </Box>

      {/* Loading state */}
      {isLoading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={200} mb={2}>
          <CircularProgress />
          <Typography variant="body2" sx={{ ml: 2 }}>
            Loading table data...
          </Typography>
        </Box>
      )}

      {/* Data Grid */}
      <Box sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={filteredData}
          columns={columns}
          loading={isLoading}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
          }}
          pageSizeOptions={[5, 10, 25, 50]}
          checkboxSelection
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-cell': {
              borderBottom: '1px solid #f0f0f0',
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: '#f8f9fa',
              borderBottom: '2px solid #e0e0e0',
              fontWeight: 600,
            },
            '& .MuiDataGrid-row:hover': {
              backgroundColor: '#f5f5f5',
            },
            '& .MuiDataGrid-root': {
              border: '1px solid #e0e0e0',
            },
          }}
          slots={{
            noRowsOverlay: () => (
              <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                height="100%"
              >
                <Typography variant="h6" color="text.secondary">
                  No data available
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {localSearchQuery || searchQuery ? 'No records match your search' : 'No records found'}
                </Typography>
              </Box>
            ),
          }}
        />
      </Box>
    </Box>
  )
}

export default ColumnLineageTable