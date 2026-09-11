import { useMemo } from 'react'
import { createApi } from './client.js'
import { useSession } from '../auth/SessionProvider.jsx'

export function useApi() {
  const { accessToken } = useSession()
  return useMemo(() => createApi(accessToken), [accessToken])
}
