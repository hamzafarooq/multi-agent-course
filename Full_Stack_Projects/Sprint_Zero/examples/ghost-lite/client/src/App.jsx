import { Routes, Route, Link, useParams } from 'react-router-dom'
import ProtectedRoute from './auth/ProtectedRoute.jsx'
import LoginPage from './auth/LoginPage.jsx'
import SignupPage from './auth/SignupPage.jsx'
import LandingPage from './marketing/LandingPage.jsx'
import AdminPosts from './pages/AdminPosts.jsx'
import SiteSetup from './pages/SiteSetup.jsx'
import PostEditor from './pages/PostEditor.jsx'
import SiteHome from './pages/SiteHome.jsx'
import PostPage from './pages/PostPage.jsx'
import { usePageTitle } from './components/usePageTitle.js'

function EditorRoute() {
  const { id } = useParams()
  return <PostEditor key={id || 'new'} />
}

function NotFound() {
  usePageTitle('Page not found — Inkwell')
  return (
    <div className="gh-notfound">
      <h1>Page not found</h1>
      <p><Link to="/">Back to Inkwell</Link></p>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/admin" element={<ProtectedRoute><AdminPosts /></ProtectedRoute>} />
      <Route path="/admin/setup" element={<ProtectedRoute><SiteSetup /></ProtectedRoute>} />
      <Route path="/admin/posts/new" element={<ProtectedRoute><EditorRoute /></ProtectedRoute>} />
      <Route path="/admin/posts/:id" element={<ProtectedRoute><EditorRoute /></ProtectedRoute>} />
      <Route path="/s/:slug" element={<SiteHome />} />
      <Route path="/s/:slug/:postSlug" element={<PostPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
