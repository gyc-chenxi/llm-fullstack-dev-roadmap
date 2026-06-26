<template>
  <div class="agent-monitor">
    <h2>Agent Monitor</h2>
    <p class="subtitle">LangGraph agent execution state and tool call tracing</p>

    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">Active Runs</div>
        <div class="metric-value">--</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Avg Steps</div>
        <div class="metric-value">--</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Tool Success Rate</div>
        <div class="metric-value">--%</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Loop Breaks</div>
        <div class="metric-value">0</div>
      </div>
    </div>

    <div class="section">
      <h3>Agent Traces</h3>
      <table class="trace-table">
        <thead>
          <tr><th>Run ID</th><th>Type</th><th>Steps</th><th>Tools</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="trace in agentTraces" :key="trace.trace_id">
            <td><router-link :to="'/trace/' + trace.trace_id" class="link">{{ trace.request_id }}</router-link></td>
            <td><span class="type-badge agent">agent</span></td>
            <td>--</td>
            <td>--</td>
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
const agentTraces = computed(() => store.traces.filter(t => t.run_type === 'agent'))
</script>

<style scoped>
.agent-monitor h2 { margin-bottom: 4px; }
.agent-monitor h3 { margin: 24px 0 12px; color: #cbd5e1; }
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
.metric-value { font-size: 28px; font-weight: 700; color: #d8b4fe; }

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

.type-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.type-badge.agent { background: #7e22ce; color: #d8b4fe; }

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.completed { background: #166534; color: #86efac; }
.status-badge.failed { background: #991b1b; color: #fca5a5; }
</style>