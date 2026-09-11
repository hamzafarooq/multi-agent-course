import { useMemo } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ gfm: true, breaks: false })

export function renderMarkdown(source) {
  const html = marked.parse(source || '')
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
}

export function sanitizeSnippet(snippet) {
  return DOMPurify.sanitize(snippet || '', { ALLOWED_TAGS: ['mark'], ALLOWED_ATTR: [] })
}

export default function Markdown({ source, className }) {
  const html = useMemo(() => renderMarkdown(source), [source])
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
