import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSession } from './SessionProvider.jsx'
import { usePageTitle } from '../components/usePageTitle.js'

export default function SignupPage() {
  usePageTitle('Sign up — Inkwell')
  const { signUp } = useSession()
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
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setBusy(true)
    try {
      await signUp(email.trim(), password)
      navigate('/admin/setup')
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
        <h1>Create your account</h1>
        <p className="auth-sub">One writer, one site, a few minutes to your first post.</p>
        <form onSubmit={onSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" autoComplete="email" data-testid="email-input"
              value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" autoComplete="new-password" data-testid="password-input"
              value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button type="submit" className="btn btn-dark btn-block" data-testid="signup-button" disabled={busy}>
            {busy ? 'Creating account…' : 'Sign up'}
          </button>
        </form>
        <p className="auth-alt">
          Already have an account? <Link to="/login" data-testid="go-to-login">Log in</Link>
        </p>
      </div>
    </div>
  )
}
