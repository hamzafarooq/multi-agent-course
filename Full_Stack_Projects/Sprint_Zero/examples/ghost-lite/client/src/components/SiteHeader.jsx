import { Link } from 'react-router-dom'

export default function SiteHeader({ site, variant = 'solid' }) {
  return (
    <header className={`gh-head gh-head--${variant}`}>
      <div className="gh-inner">
        <Link className="gh-head-logo" to={`/s/${site.slug}`}>{site.title}</Link>
        <nav className="gh-head-actions">
          <Link className="gh-head-link" to="/login">Sign in</Link>
          <a className="gh-head-button" href="#subscribe">Subscribe</a>
        </nav>
      </div>
    </header>
  )
}
