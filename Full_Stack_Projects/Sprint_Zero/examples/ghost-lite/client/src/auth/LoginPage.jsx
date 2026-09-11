import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSession } from './SessionProvider.jsx'
import { usePageTitle } from '../components/usePageTitle.js'

export default function LoginPage() {
  usePageTitle('Log in — Inkwell')
  const { signIn } = useSession()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!email.trim() || !password) {
      setError('Email and password are required.')
      return
    }
    setBusy(true)
    try {
      const data = await signIn(email.trim(), password)
      navigate(data.site ? '/admin' : '/admin/setup')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-brand">Inkwell</Link>
        <h1>Log in</h1>
        <p className="auth-sub">Welcome back. Your posts are where you left them.</p>
        <form onSubmit={onSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" autoComplete="email" data-testid="email-input"
              value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" autoComplete="current-password" data-testid="password-input"
              value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button type="submit" className="btn btn-dark btn-block" data-testid="login-button" disabled={busy}>
            {busy ? 'Logging in…' : 'Log in'}
          </button>
        </form>
        <p className="auth-alt">
          New to Inkwell? <Link to="/signup" data-testid="go-to-signup">Sign up</Link>
        </p>
      </div>
    </div>
  )
}
