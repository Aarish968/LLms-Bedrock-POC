import { useMemo } from 'react'
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid'
import { Box, Chip } from '@mui/material'

interface ColumnLineageTableProps {
  searchQuery: string
}

// Sample data based on the CSV structure
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
  const columns: GridColDef[] = [
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
      return sampleData
    }

    const query = searchQuery.toLowerCase()
    return sampleData.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(query)
      )
    )
  }, [searchQuery])

  return (
    <Box sx={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={filteredData}
        columns={columns}
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
      />
    </Box>
  )
}

export default ColumnLineageTable