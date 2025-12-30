import { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  InputAdornment,
  Chip,
} from '@mui/material'
import { Search, PlayArrow, Person } from '@mui/icons-material'

import ColumnLineageTable from '../components/ColumnLineageTable/ColumnLineageTable'
import useUserContext from '@/hooks/users/useUserContext'

const DashboardPage = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const user = useUserContext()

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }

  const handleStartAnalysis = () => {
    // TODO: Implement view to column lineage analysis
    console.log('Starting view to column lineage analysis...')
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="body1" color="text.secondary">
            Database View Column Lineage Analysis System
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Person fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary">
              Welcome, {user.email}
            </Typography>
            {user.isAdmin && (
              <Chip label="Admin" size="small" color="primary" variant="outlined" />
            )}
            {user.isAnalyst && (
              <Chip label="Analyst" size="small" color="secondary" variant="outlined" />
            )}
          </Box>
        </Box>
      </Box>

      {/* Controls Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Search Box */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <TextField
                fullWidth
                placeholder="Search views, tables, or columns..."
                value={searchQuery}
                onChange={handleSearch}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                Search functionality will be implemented later
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Start Analysis Button */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%'
            }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrow />}
                onClick={handleStartAnalysis}
                sx={{ mb: 1 }}
              >
                Start View to Column Lineage
              </Button>
              <Typography variant="caption" color="text.secondary" align="center">
                Analyze database view dependencies
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Column Lineage Table */}
      <Card>
        <CardContent>
          <ColumnLineageTable searchQuery={searchQuery} />
        </CardContent>
      </Card>
    </Box>
  )
}

export default DashboardPage