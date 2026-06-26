<template>
  <div class="overview">
    <h2>System Overview</h2>
    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">Active Slots</div>
        <div class="metric-value">{{ store.snapshot.active_slots || 0 }} / {{ store.snapshot.total_slots || 0 }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Queue Depth</div>
        <div class="metric-value">{{ store.queue.queue_depth || 0 }}</div>
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
        <div class="metric-label">Memory Pressure</div>
        <div class="metric-value">{{ ((store.snapshot.memory_pressure || 0) * 100).toFixed(1) }}%</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Error Rate</div>
        <div class="metric-value">{{ errorRate }}%</div>
      </div>
    </div>

    <div class="section">
      <h3>Slot Status</h3>
      <div class="slot-grid">
        <div v-for="slot in store.slots" :key="slot.slot_id" :class="['slot-card', slot.status]">
          <div class="slot-id">Slot {{ slot.slot_id }}</div>
          <div class="slot-status">{{ slot.status }}</div>
          <div v-if="slot.current_request_id" class="slot-request">{{ slot.current_request_id }}</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>Recent Traces</h3>
      <table class="trace-table">
        <thead>
          <tr>
            <th>Trace ID</th>
            <th>Type</th>
            <th>TTFT</th>
            <th>Latency</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trace in store.traces.slice(0, 10)" :key="trace.trace_id">
            <td>
              <router-link :to="'/trace/' + trace.trace_id" class="trace-link">
                {{ trace.trace_id.slice(0, 14) }}...
              </router-link>
            </td>
            <td><span :class="'type-badge ' + trace.run_type">{{ trace.run_type }}</span></td>
            <td>{{ (trace.ttft_ms || 0).toFixed(1) }} ms</td>
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

const errorRate = computed(() => {
  const total = store.snapshot.counters?.total_requests || 1
  const errors = store.snapshot.counters?.total_errors || 0
  return ((errors / total) * 100).toFixed(2)
})
</script>

<style scoped>
.overview h2 { margin-bottom: 20px; color: #f1f5f9; }
.overview h3 { margin: 24px 0 12px; color: #cbd5e1; }

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

.slot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.slot-card {
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.slot-card.busy { border-color: #f59e0b; }
.slot-card.idle { border-color: #22c55e; }
.slot-card.unavailable { border-color: #ef4444; }

.slot-id { font-size: 13px; color: #94a3b8; }
.slot-status { font-size: 18px; font-weight: 600; text-transform: uppercase; }
.slot-request { font-size: 11px; color: #64748b; margin-top: 4px; word-break: break-all; }

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

.trace-table th { color: #94a3b8; font-weight: 600; }

.trace-link { color: #38bdf8; text-decoration: none; }
.trace-link:hover { text-decoration: underline; }

.type-badge, .status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.type-badge.chat { background: #1e40af; color: #93c5fd; }
.type-badge.rag { background: #166534; color: #86efac; }
.type-badge.agent { background: #7e22ce; color: #d8b4fe; }

.status-badge.completed { background: #166534; color: #86efac; }
.status-badge.failed { background: #991b1b; color: #fca5a5; }
.status-badge.queued { background: #854d0e; color: #fde68a; }
</style>