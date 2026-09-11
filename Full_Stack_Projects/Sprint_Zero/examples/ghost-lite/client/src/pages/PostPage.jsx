import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useApi } from '../api/useApi.js'
import SiteHeader from '../components/SiteHeader.jsx'
import SiteFooter from '../components/SiteFooter.jsx'
import MemberJoin from '../components/MemberJoin.jsx'
import Markdown from '../components/Markdown.jsx'
import { formatDate, readingTime } from '../components/format.js'

export default function PostPage() {
  const { slug, postSlug } = useParams()
  const api = useApi()
  const [site, setSite] = useState(null)
  const [post, setPost] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setPost(null)
    let loadedSite = null
    api.getSite(slug)
      .then((s) => {
        if (cancelled) return
        loadedSite = s
        setSite(s)
        return api.getSitePost(slug, postSlug)
      })
      .then((p) => {
        if (cancelled || !p) return
        setPost(p)
        setStatus('ready')
        document.title = `${p.title} — ${loadedSite.title}`
        window.scrollTo(0, 0)
      })
      .catch((err) => {
        if (cancelled) return
        setStatus(err.status === 404 ? 'notfound' : 'error')
      })
    return () => { cancelled = true }
  }, [api, slug, postSlug])

  if (status === 'loading') return <div className="loading">Loading…</div>

  if (!site) {
    return (
      <div className="gh-notfound">
        <h1>Site not found</h1>
        <p>There is no site at <code>/s/{slug}</code>. <Link to="/">Back to Inkwell</Link></p>
      </div>
    )
  }

  return (
    <div className="gh-site" style={{ '--accent': site.accent_color }}>
      <SiteHeader site={site} variant="solid" />

      {status === 'notfound' && (
        <div className="gh-notfound" data-testid="post-not-found">
          <h1>Post not found</h1>
          <p>That post does not exist or is not published. <Link to={`/s/${site.slug}`}>Back to {site.title}</Link></p>
        </div>
      )}

      {status === 'error' && (
        <div className="gh-notfound"><h1>Something went wrong</h1><p>Could not load this post.</p></div>
      )}

      {status === 'ready' && post && (
        <article className="gh-article">
          <div className="gh-article-inner">
            <header className="gh-article-header">
              <h1 className="gh-article-title">{post.title}</h1>
              {post.excerpt && <p className="gh-article-excerpt">{post.excerpt}</p>}
              <div className="gh-byline">
                <span className="gh-avatar" aria-hidden="true">{(post.author_name || site.title).charAt(0).toUpperCase()}</span>
                <div>
                  <div className="gh-byline-name">{post.author_name}</div>
                  <div className="gh-byline-meta">
                    <time dateTime={post.published_at || undefined}>{formatDate(post.published_at)}</time>
                    <span className="gh-card-dot">•</span>
                    <span>{readingTime(post.reading_time_minutes)}</span>
                  </div>
                </div>
              </div>
            </header>
            <Markdown className="gh-content" source={post.body_markdown} />
          </div>
        </article>
      )}

      <MemberJoin site={site} />
      <SiteFooter site={site} />
    </div>
  )
}
