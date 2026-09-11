import { useState } from 'react'
import { useApi } from '../api/useApi.js'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function MemberJoin({ site }) {
  const api = useApi()
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setMessage('')
    const value = email.trim()
    if (!EMAIL_RE.test(value)) {
      setError('Please enter a valid email address.')
      return
    }
    setBusy(true)
    try {
      const data = await api.joinSite(site.slug, value)
      setMessage(data.already_member
        ? `You're already a member of ${site.title}. Nothing to do.`
        : `Welcome — you're now a member of ${site.title}.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="gh-subscribe" id="subscribe">
      <div className="gh-subscribe-inner">
        <h2 className="gh-subscribe-title">Sign up for more like this.</h2>
        <p className="gh-subscribe-desc">Become a free member of {site.title}. Just your email, no password.</p>
        <form className="gh-subscribe-form" onSubmit={onSubmit} noValidate>
          <input type="email" name="email" data-testid="member-email-input" placeholder="jamie@example.com"
            value={email} onChange={(e) => setEmail(e.target.value)} aria-label="Email address" />
          <button type="submit" data-testid="join-button" disabled={busy}>{busy ? 'Joining…' : 'Subscribe'}</button>
        </form>
        {error && <p className="gh-subscribe-error" role="alert">{error}</p>}
        {message && <p className="gh-subscribe-msg" data-testid="member-confirmation">{message}</p>}
      </div>
    </section>
  )
}
