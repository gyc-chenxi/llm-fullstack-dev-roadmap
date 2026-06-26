<template>
  <div class="chat-monitor">
    <h2>Chat Monitor</h2>
    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">Active Requests</div>
        <div class="metric-value">{{ store.snapshot.active_slots || 0 }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Avg TTFT</div>
        <div class="metric-value">{{ (store.snapshot.avg_ttft_ms || 0).toFixed(1) }} ms</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Tokens/s</div>
        <div class="metric-value">{{ (store.snapshot.avg_tokens_per_sec || 0).toFixed(1) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Queue Wait</div>
        <div class="metric-value">{{ queueWaitAvg }} ms</div>
      </div>
    </div>

    <div class="section">
      <h3>Token Generation Rate</h3>
      <div class="chart-container">
        <canvas ref="tokensChart"></canvas>
      </div>
    </div>

    <div class="section">
      <h3>Chat Traces</h3>
      <table class="trace-table">
        <thead>
          <tr><th>Request ID</th><th>TTFT</th><th>TPOT</th><th>Tokens</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="trace in chatTraces" :key="trace.trace_id">
            <td><router-link :to="'/trace/' + trace.trace_id" class="link">{{ trace.request_id }}</router-link></td>
            <td>{{ (trace.ttft_ms || 0).toFixed(1) }} ms</td>
            <td>{{ (trace.tpot_ms || 0).toFixed(1) }} ms</td>
            <td>-</td>
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

const chatTraces = computed(() => store.traces.filter(t => t.run_type === 'chat'))
const queueWaitAvg = computed(() => '0.0')
</script>

<style scoped>
.chat-monitor h2 { margin-bottom: 20px; }
.chat-monitor h3 { margin: 24px 0 12px; color: #cbd5e1; }

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
.metric-value { font-size: 28px; font-weight: 700; color: #38bdf8; }

.chart-container {
  background: #1e293b;
  border-radius: 10px;
  padding: 20px;
  height: 200px;
}

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