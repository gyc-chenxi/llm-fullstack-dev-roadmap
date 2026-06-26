import { createRouter, createWebHistory } from 'vue-router'
import Overview from '../components/OverviewPanel.vue'
import ChatMonitor from '../components/ChatMonitor.vue'
import RagMonitor from '../components/RagMonitor.vue'
import AgentMonitor from '../components/AgentMonitor.vue'
import BenchmarkPanel from '../components/BenchmarkPanel.vue'
import TraceDetail from '../components/TraceDetail.vue'

const routes = [
  { path: '/', name: 'Overview', component: Overview },
  { path: '/chat', name: 'ChatMonitor', component: ChatMonitor },
  { path: '/rag', name: 'RagMonitor', component: RagMonitor },
  { path: '/agent', name: 'AgentMonitor', component: AgentMonitor },
  { path: '/benchmark', name: 'Benchmark', component: BenchmarkPanel },
  { path: '/trace/:id', name: 'TraceDetail', component: TraceDetail, props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})