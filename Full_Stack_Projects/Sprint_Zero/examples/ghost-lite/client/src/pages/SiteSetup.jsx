import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSession } from '../auth/SessionProvider.jsx'
import { useApi } from '../api/useApi.js'
import AdminLayout from '../components/AdminLayout.jsx'

const HEX_RE = /^#[0-9a-fA-F]{6}$/

export default function SiteSetup() {
  const { site, setSite } = useSession()
  const api = useApi()
  const navigate = useNavigate()
  const [title, setTitle] = useState(site?.title || '')
  const [description, setDescription] = useState(site?.description || '')
  const [accent, setAccent] = useState(site?.accent_color || '#15171a')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!title.trim()) {
      setError('Title is required.')
      return
    }
    if (!HEX_RE.test(accent.trim())) {
      setError('Accent colour must be a hex value like #1f6f43.')
      return
    }
    setBusy(true)
    const fields = { title: title.trim(), description: description.trim(), accent_color: accent.trim().toLowerCase() }
    try {
      const saved = site ? await api.updateSite(fields) : await api.createSite(fields)
      setSite(saved)
      navigate('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const swatch = HEX_RE.test(accent) ? accent : '#e1e1e1'

  return (
    <AdminLayout title={site ? 'Site settings' : 'Set up your site'}>
      <div className="adm-head">
        <h1>{site ? 'Site settings' : 'Set up your site'}</h1>
      </div>
      {!site && <p className="adm-lead">Give your site a name, a line about it, and a colour. Readers will see all three.</p>}
      {site && (
        <p className="adm-lead">
          Your site lives at <Link to={`/s/${site.slug}`} className="adm-link">/s/{site.slug}</Link>. The address stays the same when you rename it.
        </p>
      )}
      <form className="adm-form" onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="title">Site title</label>
          <input id="title" name="title" data-testid="site-title-input" value={title} maxLength={120}
            onChange={(e) => setTitle(e.target.value)} placeholder="Field Notes" />
        </div>
        <div className="field">
          <label htmlFor="description">Description</label>
          <textarea id="description" name="description" data-testid="site-description-input" value={description} maxLength={500}
            onChange={(e) => setDescription(e.target.value)} placeholder="Essays on soil and weather" rows={3} />
        </div>
        <div className="field">
          <label htmlFor="accent_color">Accent colour</label>
          <div className="field-row">
            <input id="accent_color" name="accent_color" data-testid="site-accent-input" value={accent}
              onChange={(e) => setAccent(e.target.value)} placeholder="#1f6f43" className="field-hex" />
            <label className="swatch" style={{ background: swatch }} title="Pick a colour">
              <input type="color" value={HEX_RE.test(accent) ? accent : '#15171a'} onChange={(e) => setAccent(e.target.value)} aria-label="Colour picker" />
            </label>
          </div>
          <p className="field-hint">Paints your cover, links and Subscribe button.</p>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="adm-actions">
          <button type="submit" className="btn btn-dark" data-testid="create-site-button" disabled={busy}>
            {busy ? 'Saving…' : site ? 'Save changes' : 'Create site'}
          </button>
          {site && <Link to="/admin" className="btn btn-outline">Cancel</Link>}
        </div>
      </form>
    </AdminLayout>
  )
}
