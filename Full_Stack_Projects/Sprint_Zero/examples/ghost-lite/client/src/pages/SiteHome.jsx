import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useApi } from '../api/useApi.js'
import SiteHeader from '../components/SiteHeader.jsx'
import SiteFooter from '../components/SiteFooter.jsx'
import MemberJoin from '../components/MemberJoin.jsx'
import AskMe from '../components/AskMe.jsx'
import { formatDate, readingTime } from '../components/format.js'

function PostCard({ post, siteSlug, lead }) {
  const href = `/s/${siteSlug}/${post.slug}`
  return (
    <article className={`gh-card${lead ? ' gh-card--lead' : ''}`} data-testid="post-card">
      <div className="gh-card-head">
        <h2 className="gh-card-title"><Link to={href}>{post.title}</Link></h2>
      </div>
      <div className="gh-card-body">
        <p className="gh-card-excerpt">{post.excerpt}</p>
        <div className="gh-card-meta">
          <span className="gh-card-author">{post.author_name}</span>
          <span className="gh-card-dot">•</span>
          <time dateTime={post.published_at || undefined}>{formatDate(post.published_at)}</time>
          <span className="gh-card-dot">•</span>
          <span>{readingTime(post.reading_time_minutes)}</span>
        </div>
      </div>
    </article>
  )
}

export default function SiteHome() {
  const { slug } = useParams()
  const api = useApi()
  const [site, setSite] = useState(null)
  const [posts, setPosts] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    Promise.all([api.getSite(slug), api.getSitePosts(slug)])
      .then(([s, p]) => {
        if (cancelled) return
        setSite(s)
        setPosts(p.posts)
        setStatus('ready')
        document.title = s.title
      })
      .catch((err) => {
        if (cancelled) return
        setStatus(err.status === 404 ? 'notfound' : 'error')
      })
    return () => { cancelled = true }
  }, [api, slug])

  if (status === 'loading') return <div className="loading">Loading…</div>
  if (status === 'notfound') {
    return (
      <div className="gh-notfound">
        <h1>Site not found</h1>
        <p>There is no site at <code>/s/{slug}</code>. <Link to="/">Back to Inkwell</Link></p>
      </div>
    )
  }
  if (status === 'error') return <div className="gh-notfound"><h1>Something went wrong</h1><p>Could not load this site. Is the server running?</p></div>

  return (
    <div className="gh-site" style={{ '--accent': site.accent_color }}>
      <div className="gh-cover-wrap">
        <SiteHeader site={site} variant="cover" />
        <section className="gh-cover" data-testid="site-cover" style={{ backgroundColor: site.accent_color }}>
          <h1 className="gh-site-title" data-testid="site-cover-title">{site.title}</h1>
          {site.description && <p className="gh-site-description" data-testid="site-cover-description">{site.description}</p>}
        </section>
      </div>

      <main className="gh-outer">
        <div className="gh-inner">
          <AskMe site={site} />
          {posts.length === 0 ? (
            <p className="gh-feed-empty">Nothing published here yet.</p>
          ) : (
            <div className="gh-feed">
              {posts.map((post, i) => <PostCard key={post.id} post={post} siteSlug={site.slug} lead={i === 0} />)}
            </div>
          )}
        </div>
      </main>

      <MemberJoin site={site} />
      <SiteFooter site={site} />
    </div>
  )
}
