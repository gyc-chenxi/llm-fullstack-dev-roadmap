<template>
  <div class="rag-monitor">
    <h2>RAG Monitor</h2>
    <p class="subtitle">Retrieval-Augmented Generation quality and latency metrics</p>

    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">Avg Recall@5</div>
        <div class="metric-value">--</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Avg MRR</div>
        <div class="metric-value">--</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Citation Accuracy</div>
        <div class="metric-value">--</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Retrieval Latency</div>
        <div class="metric-value">-- ms</div>
      </div>
    </div>

    <div class="section">
      <h3>RAG Traces</h3>
      <table class="trace-table">
        <thead>
          <tr><th>Request ID</th><th>Retrieval</th><th>Rerank</th><th>LLM</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="trace in ragTraces" :key="trace.trace_id">
            <td><router-link :to="'/trace/' + trace.trace_id" class="link">{{ trace.request_id }}</router-link></td>
            <td>-- ms</td>
            <td>-- ms</td>
            <td>{{ (trace.latency_ms || 0).toFixed(1) }} ms</td>
            <td><span :class="'status-badge ' + trace.final_status">{{ trace.final_status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMetricsStore } from '../stores/metrics'

const store = useMetricsStore()
const ragTraces = computed(() => store.traces.filter(t => t.run_type === 'rag'))
</script>

<style scoped>
.rag-monitor h2 { margin-bottom: 4px; }
.rag-monitor h3 { margin: 24px 0 12px; color: #cbd5e1; }
.subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }

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

.metric-label { font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: #86efac; }

.trace-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.trace-table th, .trace-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
}

.trace-table th { color: #94a3b8; }

.link { color: #38bdf8; text-decoration: none; }
.link:hover { text-decoration: underline; }

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.completed { background: #166534; color: #86efac; }
.status-badge.failed { background: #991b1b; color: #fca5a5; }
</style>