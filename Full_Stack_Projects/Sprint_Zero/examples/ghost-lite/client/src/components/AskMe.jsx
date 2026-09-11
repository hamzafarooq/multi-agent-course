import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useApi } from '../api/useApi.js'
import { sanitizeSnippet } from './Markdown.jsx'

export default function AskMe({ site }) {
  const api = useApi()
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    const q = question.trim()
    if (!q) {
      setError('Please enter a question.')
      return
    }
    setLoading(true)
    setResult(null)
    try {
      setResult(await api.ask(site.slug, q))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const postHref = (slug) => `/s/${site.slug}/${slug}`

  return (
    <section className="gh-ask" aria-label="Ask me">
      <form className="gh-ask-form" onSubmit={onSubmit} noValidate>
        <span className="gh-ask-icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          </svg>
        </span>
        <input className="gh-ask-input" name="question" data-testid="ask-input" placeholder={`Ask ${site.title} a question`}
          value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Ask this site a question" />
        <button type="submit" className="gh-ask-button" data-testid="ask-button" disabled={loading}>Ask</button>
      </form>

      {error && <div className="gh-ask-body"><p className="gh-ask-error" role="alert">{error}</p></div>}

      {loading && (
        <div className="gh-ask-body">
          <p className="gh-ask-loading">Reading through {site.title}…</p>
        </div>
      )}

      {!loading && result && (
        <div className="gh-ask-body" data-testid="ask-result">
          {result.results.length === 0 ? (
            <p className="gh-ask-empty">No matches. Nothing published here uses those words — try phrasing it the way the writer might.</p>
          ) : result.mode === 'answer' ? (
            <>
              <p className="gh-ask-label" data-testid="ask-mode-label">Answer</p>
              <p className="gh-ask-answer">{result.answer}</p>
              {result.citations && result.citations.length > 0 && (
                <>
                  <p className="gh-ask-label">Cited from</p>
                  <ul className="gh-ask-sources">
                    {result.citations.map((c) => (
                      <li key={c.post_id}>
                        <Link data-testid="ask-citation" to={postHref(c.slug)}>{c.title}</Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </>
          ) : (
            <>
              <p className="gh-ask-label" data-testid="ask-mode-label">Search results</p>
              {result.answer_error && <p className="gh-ask-note">{result.answer_error}</p>}
              <div className="gh-ask-hits">
                {result.results.map((r) => (
                  <article className="gh-ask-hit" key={r.post_id}>
                    <p className="gh-ask-snippet" dangerouslySetInnerHTML={{ __html: sanitizeSnippet(r.snippet) }} />
                    <Link data-testid="ask-citation" to={postHref(r.slug)}>{r.title}</Link>
                  </article>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  )
}
