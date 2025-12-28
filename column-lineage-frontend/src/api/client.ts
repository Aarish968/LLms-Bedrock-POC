import axios from 'axios'
import { Auth } from 'aws-amplify'

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Get JWT token from Amplify
      const session = await Auth.currentSession()
      const token = session.getAccessToken().getJwtToken()
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (error) {
      // If no session, try to get from localStorage (fallback)
      const token = localStorage.getItem('jwt') || localStorage.getItem('authToken')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      try {
        await Auth.signOut()
        localStorage.removeItem('jwt')
        localStorage.removeItem('authToken')
        window.location.reload()
      } catch (signOutError) {
        console.error('Error signing out:', signOutError)
        window.location.reload()
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient