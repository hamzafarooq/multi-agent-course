import { Navigate } from 'react-router-dom'
import { useSession } from './SessionProvider.jsx'

export default function ProtectedRoute({ children }) {
  const { accessToken, loading } = useSession()
  if (loading) return <div className="loading">Loading your workspace…</div>
  if (!accessToken) return <Navigate to="/login" replace />
  return children
}
