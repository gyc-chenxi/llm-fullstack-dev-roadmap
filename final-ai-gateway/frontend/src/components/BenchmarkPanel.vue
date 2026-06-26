<template>
  <div class="benchmark-panel">
    <h2>Benchmark Runner</h2>
    <p class="subtitle">Concurrency stress testing for chat, RAG, and agent workloads</p>

    <div class="controls">
      <div class="control-group">
        <label>Concurrency</label>
        <select v-model.number="concurrency">
          <option :value="10">10</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
      <div class="control-group">
        <label>Total Requests</label>
        <input type="number" v-model.number="totalRequests" min="1" max="1000" />
      </div>
      <div class="control-group">
        <label>Max Tokens</label>
        <input type="number" v-model.number="maxTokens" min="64" max="2048" />
      </div>
      <button class="run-btn" @click="runBenchmark" :disabled="running">
        {{ running ? 'Running...' : 'Run Benchmark' }}
      </button>
    </div>

    <div v-if="result" class="result">
      <h3>Results</h3>
      <div class="result-grid">
        <div class="result-card">
          <div class="r-label">Throughput</div>
          <div class="r-value">{{ result.throughput_rps }} rps</div>
        </div>
        <div class="result-card">
          <div class="r-label">Success Rate</div>
          <div class="r-value">{{ (result.success_rate * 100).toFixed(1) }}%</div>
        </div>
        <div class="result-card">
          <div class="r-label">Duration</div>
          <div class="r-value">{{ result.total_duration_sec }}s</div>
        </div>
        <div class="result-card">
          <div class="r-label">Completed / Failed</div>
          <div class="r-value">{{ result.completed }} / {{ result.failed }}</div>
        </div>
      </div>

      <h3>Latency Distribution</h3>
      <table class="result-table">
        <thead>
          <tr><th>Metric</th><th>Avg</th><th>P50</th><th>P95</th><th>P99</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>TTFT</td>
            <td>{{ result.ttft_ms?.avg }} ms</td>
            <td>{{ result.ttft_ms?.p50 }} ms</td>
            <td>{{ result.ttft_ms?.p95 }} ms</td>
            <td>{{ result.ttft_ms?.p99 }} ms</td>
          </tr>
          <tr>
            <td>Total Latency</td>
            <td>{{ result.latency_ms?.avg }} ms</td>
            <td>{{ result.latency_ms?.p50 }} ms</td>
            <td>{{ result.latency_ms?.p95 }} ms</td>
            <td>{{ result.latency_ms?.p99 }} ms</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { runBenchmark } from '../api'

const concurrency = ref(10)
const totalRequests = ref(50)
const maxTokens = ref(256)
const running = ref(false)
const result = ref(null)

async function run() {
  running.value = true
  result.value = null
  try {
    result.value = await runBenchmark(
      concurrency.value,
      totalRequests.value,
      'qwen2.5-7b-instruct-q4_k_m',
      maxTokens.value,
    )
  } catch (e) {
    result.value = { error: e.message }
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.benchmark-panel h2 { margin-bottom: 4px; }
.benchmark-panel h3 { margin: 24px 0 12px; color: #cbd5e1; }
.subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }

.controls {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  background: #1e293b;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}

.control-group label {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.control-group select, .control-group input {
  background: #0f172a;
  border: 1px solid #334155;
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.run-btn {
  background: #38bdf8;
  color: #0f172a;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.result-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}

.r-label { font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
.r-value { font-size: 24px; font-weight: 700; color: #f59e0b; }

.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.result-table th, .result-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
}

.result-table th { color: #94a3b8; }
</style>