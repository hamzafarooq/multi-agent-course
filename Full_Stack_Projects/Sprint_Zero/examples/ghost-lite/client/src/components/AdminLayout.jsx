import { startTransition } from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useSession } from '../auth/SessionProvider.jsx'
import { usePageTitle } from './usePageTitle.js'

export default function AdminLayout({ children, title }) {
  const { user, site, signOut } = useSession()
  const navigate = useNavigate()

  function onLogout() {
    startTransition(() => {
      signOut()
      navigate('/')
    })
  }

  const brand = site ? site.title : 'Inkwell'
  usePageTitle(`${title || 'Admin'} — ${brand}`)

  return (
    <div className="adm">
      <aside className="adm-side">
        <div className="adm-brand">
          <span className="adm-brand-icon" style={site ? { background: site.accent_color } : undefined}>
            {brand.charAt(0).toUpperCase()}
          </span>
          <span className="adm-brand-name" data-testid="sidebar-site-title">{brand}</span>
        </div>
        <nav className="adm-nav">
          <NavLink to="/admin" end>Posts</NavLink>
          <NavLink to="/admin/setup">{site ? 'Site settings' : 'Set up site'}</NavLink>
          {site && <Link to={`/s/${site.slug}`}>View site</Link>}
        </nav>
        <div className="adm-side-bottom">
          {user && <div className="adm-user">{user.email}</div>}
          <button type="button" className="btn btn-outline btn-sm btn-block" data-testid="logout-button" onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>
      <main className="adm-main">{children}</main>
    </div>
  )
}
