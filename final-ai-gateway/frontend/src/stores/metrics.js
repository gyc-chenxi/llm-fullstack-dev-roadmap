import { defineStore } from 'pinia'
import { fetchMetricsSnapshot, fetchSlots, fetchTraces, fetchQueueInfo } from '../api'

export const useMetricsStore = defineStore('metrics', {
  state: () => ({
    snapshot: {},
    slots: [],
    traces: [],
    queue: {},
    loading: false,
    error: null,
    refreshInterval: null,
  }),

  actions: {
    async refreshAll() {
      this.loading = true
      this.error = null
      try {
        const [snapshot, slots, traces, queue] = await Promise.all([
          fetchMetricsSnapshot(),
          fetchSlots(),
          fetchTraces('', 20),
          fetchQueueInfo(),
        ])
        this.snapshot = snapshot
        this.slots = slots.slots || []
        this.traces = traces.traces || []
        this.queue = queue
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    startPolling(intervalMs = 5000) {
      this.stopPolling()
      this.refreshAll()
      this.refreshInterval = setInterval(() => this.refreshAll(), intervalMs)
    },

    stopPolling() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },
  },
})