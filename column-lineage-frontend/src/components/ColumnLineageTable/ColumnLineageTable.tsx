import { useMemo, useState } from 'react'
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid'
import { Box, Chip, Alert, CircularProgress, Switch, FormControlLabel, Typography } from '@mui/material'
import { useBaseView } from '../../hooks/useBaseView'
import { BaseViewRecord } from '../../api/baseViewService'

interface ColumnLineageTableProps {
  searchQuery: string
}

// Sample data based on the CSV structure (fallback)
const sampleData: GridRowsProp = [
  {
    id: 1,
    viewName: 'TEST_SEA_RAW_FQ',
    viewColumn: 'SUBSCRIPTION_REF_ID',
    columnType: 'DIRECT',
    sourceTable: 'CPS_DSCI_BR.SEA_BOOKINGS',
    sourceColumn: 'SUBSCRIPTION_REF_ID',
    expressionType: '',
  },
  {
    id: 2,
    viewName: 'TEST_SEA_RAW_FQ',
    viewColumn: 'FISCAL_QUARTER_ID',
    columnType: 'DIRECT',
    sourceTable: 'CPS_DSCI_BR.SEA_BOOKINGS',
    sourceColumn: 'FISCAL_QUARTER_ID',
    expressionType: '',
  },
  {
    id: 3,
    viewName: 'TEST_SEA_RAW_FQ',
    viewColumn: 'ACV',
    columnType: 'DERIVED',
    sourceTable: 'CPS_DSCI_BR.SEA_BOOKINGS',
    sourceColumn: 'ANNUAL_BOOKING_NET',
    expressionType: 'SUM',
  },
  {
    id: 4,
    viewName: 'TEST_SEA_RAW_FQ',
    viewColumn: 'CUMULATIVE_ACV',
    columnType: 'DERIVED',
    sourceTable: 'CPS_DSCI_BR.SEA_BOOKINGS',
    sourceColumn: 'ANNUAL_BOOKING_NET; FISCAL_QUARTER_ID; SUBSCRIPTION_REF_ID',
    expressionType: 'WINDOW',
  },
  {
    id: 5,
    viewName: 'TEST_SEA_RAW',
    viewColumn: 'SUBSCRIPTION_REF_ID',
    columnType: 'DIRECT',
    sourceTable: 'CPS_DSCI_BR.SEA_BOOKINGS',
    sourceColumn: 'SUBSCRIPTION_REF_ID',
    expressionType: '',
  },
]

const ColumnLineageTable = ({ searchQuery }: ColumnLineageTableProps) => {
  const [showApiData, setShowApiData] = useState(true)
  const [mockMode, setMockMode] = useState(false)

  // Fetch base view data from API
  const {
    data: apiData,
    isLoading,
    error,
    isError,
    refetch,
  } = useBaseView(
    { 
      mock: mockMode,
      limit: 100 
    },
    { enabled: showApiData }
  )

  // Transform API data to match the table structure
  const transformedApiData: GridRowsProp = useMemo(() => {
    if (!apiData?.records) return []
    
    return apiData.records.map((record: BaseViewRecord, index: number) => ({
      id: record.sr_no || index + 1,
      viewName: 'BASE_VIEW', // Since this is base view data
      viewColumn: 'TABLE_NAME', // The column we're showing
      columnType: 'DIRECT', // Base view data is direct
      sourceTable: 'PUBLIC.BASE_VIEW', // Source table
      sourceColumn: record.table_name, // The actual table name
      expressionType: '', // No expression for base view
      srNo: record.sr_no, // Additional field for display
      tableName: record.table_name, // Additional field for display
    }))
  }, [apiData])

  // Choose data source based on toggle
  const dataToUse = showApiData ? transformedApiData : sampleData

  const columns: GridColDef[] = [
    ...(showApiData ? [
      {
        field: 'srNo',
        headerName: 'Serial No.',
        width: 120,
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
        width: 250,
        renderCell: (params) => (
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem', fontWeight: 'medium' }}>
            {params.value}
          </Box>
        ),
      },
    ] : []),
    {
      field: 'viewName',
      headerName: 'View Name',
      width: 200,
      renderCell: (params) => (
        <Box sx={{ fontWeight: 'medium', color: 'primary.main' }}>
          {params.value}
        </Box>
      ),
    },
    {
      field: 'viewColumn',
      headerName: 'View Column',
      width: 180,
      renderCell: (params) => (
        <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
          {params.value}
        </Box>
      ),
    },
    {
      field: 'columnType',
      headerName: 'Column Type',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value === 'DIRECT' ? 'success' : 'warning'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'sourceTable',
      headerName: 'Source Table',
      width: 250,
      renderCell: (params) => (
        <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
          {params.value}
        </Box>
      ),
    },
    {
      field: 'sourceColumn',
      headerName: 'Source Column',
      width: 300,
      renderCell: (params) => (
        <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
          {params.value}
        </Box>
      ),
    },
    {
      field: 'expressionType',
      headerName: 'Expression Type',
      width: 140,
      renderCell: (params) => (
        params.value ? (
          <Chip
            label={params.value}
            size="small"
            color="info"
            variant="outlined"
          />
        ) : (
          <Box sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
            -
          </Box>
        )
      ),
    },
  ]

  // Filter data based on search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) {
      return dataToUse
    }

    const query = searchQuery.toLowerCase()
    return dataToUse.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(query)
      )
    )
  }, [searchQuery, dataToUse])

  // Error state
  if (showApiData && isError) {
    return (
      <Box sx={{ mb: 2 }}>
        <Alert 
          severity="error" 
          action={
            <button onClick={() => refetch()}>
              Retry
            </button>
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
      {/* Controls */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <FormControlLabel
          control={
            <Switch
              checked={showApiData}
              onChange={(e) => setShowApiData(e.target.checked)}
            />
          }
          label="Show API Data"
        />
        
        {showApiData && (
          <FormControlLabel
            control={
              <Switch
                checked={mockMode}
                onChange={(e) => setMockMode(e.target.checked)}
              />
            }
            label="Mock Mode"
          />
        )}

        {showApiData && apiData && (
          <Chip
            label={`${apiData.total_records} total records`}
            color="info"
            variant="outlined"
            size="small"
          />
        )}
      </Box>

      {/* Loading state */}
      {showApiData && isLoading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={200} mb={2}>
          <CircularProgress />
          <Typography variant="body2" sx={{ ml: 2 }}>
            Loading base view data...
          </Typography>
        </Box>
      )}

      {/* Data Grid */}
      <Box sx={{ height: 400, width: '100%' }}>
        <DataGrid
          rows={filteredData}
          columns={columns}
          loading={showApiData && isLoading}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
          }}
          pageSizeOptions={[5, 10, 25]}
          checkboxSelection
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-cell': {
              borderBottom: '1px solid #f0f0f0',
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: '#f8f9fa',
              borderBottom: '2px solid #e0e0e0',
            },
            '& .MuiDataGrid-row:hover': {
              backgroundColor: '#f5f5f5',
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
                  {searchQuery ? 'No records match your search' : 'No records found'}
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