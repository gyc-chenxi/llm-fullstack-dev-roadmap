/**
 * Health-check API client.
 *
 * Polls the Gateway's /healthz endpoint to determine upstream status.
 */
import type { HealthResponse, HealthStatus } from '../types'

const HEALTH_TIMEOUT_MS = 5_000

export async function fetchHealth(baseUrl: string): Promise<{
  status: HealthStatus
  upstream: string
  detail: string | null
}> {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS)

    const resp = await fetch(`${baseUrl}/healthz`, {
      signal: controller.signal,
    })
    clearTimeout(timer)

    if (!resp.ok) {
      return {
        status: 'error',
        upstream: 'unknown',
        detail: `Gateway returned HTTP ${resp.status}`,
      }
    }

    const data: HealthResponse = await resp.json()
    return {
      status: data.status,
      upstream: data.upstream,
      detail: data.detail,
    }
  } catch (err: unknown) {
    return {
      status: 'error',
      upstream: 'unknown',
      detail: err instanceof Error ? err.message : String(err),
    }
  }
}
