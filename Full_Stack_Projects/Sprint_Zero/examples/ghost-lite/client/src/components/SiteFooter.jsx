import { Link } from 'react-router-dom'

export default function SiteFooter({ site }) {
  return (
    <footer className="gh-footer">
      <div className="gh-inner">
        <div className="gh-footer-copy">
          <Link to={`/s/${site.slug}`}>{site.title}</Link> © {new Date().getFullYear()}
        </div>
        <div className="gh-footer-right">
          <Link to="/">Published with Inkwell</Link>
        </div>
      </div>
    </footer>
  )
}
