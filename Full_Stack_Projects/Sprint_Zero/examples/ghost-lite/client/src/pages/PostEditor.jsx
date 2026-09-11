import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { useSession } from '../auth/SessionProvider.jsx'
import { useApi } from '../api/useApi.js'
import { formatDate, wordCount } from '../components/format.js'
import { usePageTitle } from '../components/usePageTitle.js'

export default function PostEditor() {
  const { id } = useParams()
  const { site } = useSession()
  const api = useApi()
  const navigate = useNavigate()
  const [post, setPost] = useState(null)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [loadState, setLoadState] = useState(id ? 'loading' : 'ready')
  const titleRef = useRef(null)

  useEffect(() => {
    const el = titleRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [title, loadState])
  usePageTitle(`${title.trim() || 'New post'} — Editor`)

  useEffect(() => {
    if (!id || !site) return
    let cancelled = false
    setLoadState('loading')
    api.getMyPost(id)
      .then((data) => {
        if (cancelled) return
        setPost(data)
        setTitle(data.title)
        setBody(data.body_markdown)
        setLoadState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message)
        setLoadState('error')
      })
    return () => { cancelled = true }
  }, [api, id, site])

  if (!site) return <Navigate to="/admin/setup" replace />

  const isPublished = post?.status === 'published'
  const fields = () => ({ title: title.trim(), body_markdown: body })

  function validate() {
    if (!title.trim()) {
      setError('Title is required.')
      return false
    }
    setError('')
    return true
  }

  async function persist() {
    if (post) return api.updatePost(post.id, fields())
    const created = await api.createPost(fields())
    navigate(`/admin/posts/${created.id}`, { replace: true })
    return created
  }

  async function onSave() {
    if (!validate()) return
    setBusy('save')
    try {
      setPost(await persist())
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function onPublish() {
    if (!validate()) return
    setBusy('publish')
    try {
      const saved = await persist()
      setPost(await api.publishPost(saved.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function onUnpublish() {
    setBusy('unpublish')
    try {
      setPost(await api.unpublishPost(post.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="ed">
      <div className="ed-bar">
        <div className="ed-bar-left">
          <Link to="/admin" className="ed-back">‹ Posts</Link>
          <span className={`ed-status${isPublished ? ' ed-status--published' : ''}`} data-testid="post-status-label">
            {isPublished ? 'Published' : 'Draft'}
          </span>
        </div>
        <div className="ed-bar-right">
          {isPublished && post.published_at && (
            <span className="ed-date" data-testid="post-published-date">Published {formatDate(post.published_at)}</span>
          )}
          {post && (
            <Link to={`/s/${site.slug}/${post.slug}`} className="ed-preview" target="_blank" rel="noreferrer">
              {isPublished ? 'View' : 'Preview URL'}
            </Link>
          )}
          <button type="button" className="btn btn-outline btn-sm" data-testid="save-draft-button" onClick={onSave} disabled={Boolean(busy) || loadState !== 'ready'}>
            {busy === 'save' ? 'Saving…' : isPublished ? 'Update' : 'Save draft'}
          </button>
          {isPublished ? (
            <button type="button" className="btn btn-outline btn-sm" data-testid="unpublish-button" onClick={onUnpublish} disabled={Boolean(busy)}>
              {busy === 'unpublish' ? 'Unpublishing…' : 'Unpublish'}
            </button>
          ) : (
            <button type="button" className="btn btn-dark btn-sm" data-testid="publish-button" onClick={onPublish} disabled={Boolean(busy) || loadState !== 'ready'}>
              {busy === 'publish' ? 'Publishing…' : 'Publish'}
            </button>
          )}
        </div>
      </div>

      <div className="ed-canvas">
        {loadState === 'loading' && <p className="adm-muted">Loading post…</p>}
        {loadState === 'error' && (
          <p className="form-error">{error} <Link to="/admin">Back to posts</Link></p>
        )}
        {loadState === 'ready' && (
          <>
            <textarea ref={titleRef} className="ed-title" name="title" data-testid="post-title-input" placeholder="Post title" rows={1}
              value={title} onChange={(e) => setTitle(e.target.value.replace(/\n/g, ' '))}
              onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault() }} maxLength={200} />
            <textarea className="ed-body" name="body_markdown" data-testid="post-body-input" placeholder="Begin writing your post… Markdown works."
              value={body} onChange={(e) => setBody(e.target.value)} />
            {error && <p className="form-error ed-error" role="alert">{error}</p>}
          </>
        )}
      </div>
      <div className="ed-count">{wordCount(body).toLocaleString()} words</div>
    </div>
  )
}
