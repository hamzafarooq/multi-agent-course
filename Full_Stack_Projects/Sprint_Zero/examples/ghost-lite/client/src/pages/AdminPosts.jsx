import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useSession } from '../auth/SessionProvider.jsx'
import { useApi } from '../api/useApi.js'
import AdminLayout from '../components/AdminLayout.jsx'
import { formatDate } from '../components/format.js'

export default function AdminPosts() {
  const { site } = useSession()
  const api = useApi()
  const [posts, setPosts] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!site) return
    let cancelled = false
    api.listMyPosts()
      .then((data) => { if (!cancelled) setPosts(data.posts) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [api, site])

  if (!site) return <Navigate to="/admin/setup" replace />

  return (
    <AdminLayout title="Posts">
      <div className="adm-head">
        <h1>Posts</h1>
        <Link to="/admin/posts/new" className="btn btn-dark btn-sm" data-testid="new-post-button">New post</Link>
      </div>
      {error && <p className="form-error">{error}</p>}
      {posts === null && !error && <p className="adm-muted">Loading posts…</p>}
      {posts && posts.length === 0 && (
        <div className="adm-empty">
          <p>No posts yet. Your first draft is one click away.</p>
        </div>
      )}
      {posts && posts.length > 0 && (
        <div className="adm-list">
          {posts.map((post) => (
            <Link to={`/admin/posts/${post.id}`} className="adm-row" key={post.id} data-testid="post-row">
              <div className="adm-row-main">
                <div className="adm-row-title">{post.title}</div>
                {post.excerpt && <div className="adm-row-excerpt">{post.excerpt}</div>}
              </div>
              <span className={`adm-badge adm-badge--${post.status}`} data-testid="post-row-status">
                {post.status === 'published' ? 'Published' : 'Draft'}
              </span>
              <span className="adm-row-date">
                {post.status === 'published' ? formatDate(post.published_at) : `Edited ${formatDate(post.updated_at)}`}
              </span>
            </Link>
          ))}
        </div>
      )}
    </AdminLayout>
  )
}
