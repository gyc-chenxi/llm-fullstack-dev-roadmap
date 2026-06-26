import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export function fetchMetricsSnapshot() {
  return api.get('/metrics/snapshot').then(r => r.data)
}

export function fetchSlots() {
  return api.get('/slots').then(r => r.data)
}

export function fetchTraces(runType = '', limit = 20) {
  return api.get('/trace', { params: { run_type: runType, limit } }).then(r => r.data)
}

export function fetchTrace(traceId) {
  return api.get(`/trace/${traceId}`).then(r => r.data)
}

export function fetchQueueInfo() {
  return api.get('/admin/queue-info').then(r => r.data)
}

export function runBenchmark(concurrency, totalRequests, model, maxTokens) {
  return api.post('/benchmark/run', {
    concurrency,
    total_requests: totalRequests,
    model,
    max_tokens: maxTokens,
  }).then(r => r.data)
}

export function submitChat(messages, stream = false) {
  return api.post('/chat', { messages, stream }).then(r => r.data)
}

export default api