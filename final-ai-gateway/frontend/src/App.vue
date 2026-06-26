<template>
  <div id="dashboard">
    <header class="header">
      <h1>AI-Gateway Dashboard</h1>
      <nav>
        <router-link to="/">Overview</router-link>
        <router-link to="/chat">Chat</router-link>
        <router-link to="/rag">RAG</router-link>
        <router-link to="/agent">Agent</router-link>
        <router-link to="/benchmark">Benchmark</router-link>
      </nav>
      <div class="status-bar">
        <span :class="['status-dot', online ? 'online' : 'offline']"></span>
        <span>{{ online ? 'Connected' : 'Disconnected' }}</span>
        <span class="refresh" @click="refresh">⟳ Refresh</span>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from './stores/metrics'

const store = useMetricsStore()
const online = ref(true)

const refresh = () => {
  store.refreshAll()
}

onMounted(() => {
  store.startPolling(5000)
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<style>
#dashboard {
  min-height: 100vh;
  background: #0f172a;
  color: #e2e8f0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}

.header h1 {
  font-size: 20px;
  color: #38bdf8;
}

.header nav {
  display: flex;
  gap: 20px;
}

.header nav a {
  color: #94a3b8;
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.header nav a:hover,
.header nav a.router-link-active {
  color: #38bdf8;
  background: #0f172a;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #94a3b8;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.online { background: #22c55e; }
.status-dot.offline { background: #ef4444; }

.refresh {
  cursor: pointer;
  color: #38bdf8;
  margin-left: 12px;
}

.refresh:hover { text-decoration: underline; }

main {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}
</style>