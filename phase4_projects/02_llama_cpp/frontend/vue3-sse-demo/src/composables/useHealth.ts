/**
 * useHealth — periodic Gateway health polling.
 *
 * Polls /healthz every N seconds and exposes reactive status for
 * the header badge.
 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue'
import { fetchHealth } from '../api/health'
import type { HealthStatus } from '../types'

export interface UseHealthOptions {
  baseUrl: string
  /** Poll interval in milliseconds (default 15s). */
  intervalMs?: number
}

export function useHealth(opts: UseHealthOptions) {
  const status = ref<HealthStatus>('error')
  const upstream = ref('')
  const detail = ref<string | null>(null)
  const lastChecked = ref<Date | null>(null)

  let _timer: ReturnType<typeof setInterval> | null = null

  async function check(): Promise<void> {
    const result = await fetchHealth(opts.baseUrl)
    status.value = result.status
    upstream.value = result.upstream
    detail.value = result.detail
    lastChecked.value = new Date()
  }

  onMounted(() => {
    check()
    _timer = setInterval(check, opts.intervalMs ?? 15_000)
  })

  onUnmounted(() => {
    if (_timer !== null) {
      clearInterval(_timer)
      _timer = null
    }
  })

  return { status, upstream, detail, lastChecked, refresh: check }
}
