<template>
  <div class="trace-detail">
    <h2>Trace Detail</h2>
    <router-link to="/" class="back-link">← Back to Overview</router-link>

    <div v-if="loading" class="loading">Loading trace...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="trace" class="trace-content">
      <div class="trace-header">
        <div class="header-item">
          <span class="h-label">Trace ID</span>
          <span class="h-value">{{ trace.trace_id }}</span>
        </div>
        <div class="header-item">
          <span class="h-label">Request ID</span>
          <span class="h-value">{{ trace.request_id }}</span>
        </div>
        <div class="header-item">
          <span class="h-label">Type</span>
          <span :class="'type-badge ' + trace.run_type">{{ trace.run_type }}</span>
        </div>
        <div class="header-item">
          <span class="h-label">Status</span>
          <span :class="'status-badge ' + trace.final_status">{{ trace.final_status }}</span>
        </div>
      </div>

      <div class="metric-grid">
        <div class="metric-card">
          <div class="m-label">TTFT</div>
          <div class="m-value">{{ (trace.ttft_ms || 0).toFixed(1) }} ms</div>
        </div>
        <div class="metric-card">
          <div class="m-label">Total Latency</div>
          <div class="m-value">{{ (trace.latency_ms || 0).toFixed(1) }} ms</div>
        </div>
        <div class="metric-card">
          <div class="m-label">TPOT</div>
          <div class="m-value">{{ (trace.tpot_ms || 0).toFixed(1) }} ms</div>
        </div>
        <div class="metric-card">
          <div class="m-label">Queue Wait</div>
          <div class="m-value">{{ (trace.queue_wait_ms || 0).toFixed(1) }} ms</div>
        </div>
        <div class="metric-card">
          <div class="m-label">Prompt Tokens</div>
          <div class="m-value">{{ trace.prompt_tokens || 0 }}</div>
        </div>
        <div class="metric-card">
          <div class="m-label">Completion Tokens</div>
          <div class="m-value">{{ trace.completion_tokens || 0 }}</div>
        </div>
      </div>

      <div v-if="trace.spans && trace.spans.length" class="section">
        <h3>Spans</h3>
        <div class="span-list">
          <div v-for="(span, idx) in trace.spans" :key="idx" class="span-item">
            <span class="span-name">{{ span.name || 'Span ' + idx }}</span>
            <span class="span-duration">{{ span.duration_ms || '--' }} ms</span>
          </div>
        </div>
      </div>

      <div v-if="trace.errors && trace.errors.length" class="section">
        <h3>Errors</h3>
        <div v-for="(err, idx) in trace.errors" :key="idx" class="error-item">
          {{ err.message || err }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchTrace } from '../api'

const route = useRoute()
const trace = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    trace.value = await fetchTrace(route.params.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.trace-detail h2 { margin-bottom: 8px; }
.trace-detail h3 { margin: 24px 0 12px; color: #cbd5e1; }

.back-link { color: #38bdf8; text-decoration: none; font-size: 14px; }
.back-link:hover { text-decoration: underline; }

.loading, .error { margin-top: 40px; text-align: center; color: #94a3b8; }
.error { color: #ef4444; }

.trace-header {
  display: flex;
  gap: 24px;
  background: #1e293b;
  border-radius: 10px;
  padding: 20px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.header-item { display: flex; flex-direction: column; gap: 4px; }
.h-label { font-size: 12px; color: #94a3b8; }
.h-value { font-size: 14px; color: #e2e8f0; font-family: monospace; }

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.metric-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}

.m-label { font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
.m-value { font-size: 24px; font-weight: 700; color: #38bdf8; }

.type-badge, .status-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.type-badge.chat { background: #1e40af; color: #93c5fd; }
.type-badge.rag { background: #166534; color: #86efac; }
.type-badge.agent { background: #7e22ce; color: #d8b4fe; }

.status-badge.completed { background: #166534; color: #86efac; }
.status-badge.failed { background: #991b1b; color: #fca5a5; }

.span-list { display: flex; flex-direction: column; gap: 8px; }

.span-item {
  display: flex;
  justify-content: space-between;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 16px;
}

.span-name { font-size: 14px; color: #e2e8f0; }
.span-duration { font-size: 13px; color: #94a3b8; }

.error-item {
  background: #7f1d1d;
  border: 1px solid #991b1b;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #fca5a5;
}
</style>