import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { createApi } from '../api/client.js'

const TOKEN_KEY = 'inkwell_token'
const SessionContext = createContext(null)

function readToken() {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}

export function SessionProvider({ children }) {
  const [accessToken, setAccessToken] = useState(readToken)
  const [user, setUser] = useState(null)
  const [site, setSite] = useState(null)
  const [loading, setLoading] = useState(Boolean(accessToken))

  useEffect(() => {
    const token = readToken()
    if (!token) return
    let cancelled = false
    createApi(token).me()
      .then((data) => {
        if (cancelled) return
        setUser(data.user)
        setSite(data.site)
      })
      .catch((err) => {
        if (cancelled) return
        if (err.status === 401) {
          localStorage.removeItem(TOKEN_KEY)
          setAccessToken(null)
        }
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const applyAuth = useCallback((data) => {
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setAccessToken(data.access_token)
    setUser(data.user)
    setSite(data.site)
    return data
  }, [])

  const signUp = useCallback((email, password) => createApi().signup(email, password).then(applyAuth), [applyAuth])
  const signIn = useCallback((email, password) => createApi().login(email, password).then(applyAuth), [applyAuth])
  const signOut = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setAccessToken(null)
    setUser(null)
    setSite(null)
  }, [])

  const value = useMemo(() => ({
    session: accessToken ? { accessToken } : null,
    accessToken,
    user,
    site,
    setSite,
    loading,
    signUp,
    signIn,
    signOut,
  }), [accessToken, user, site, loading, signUp, signIn, signOut])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used inside SessionProvider')
  return ctx
}
