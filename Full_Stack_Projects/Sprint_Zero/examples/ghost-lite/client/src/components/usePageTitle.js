import { useEffect } from 'react'

export function usePageTitle(title) {
  useEffect(() => {
    if (title) document.title = title
  }, [title])
}
