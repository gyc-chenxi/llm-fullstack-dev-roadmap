<script setup lang="ts">
/**
 * HealthBadge — real-time upstream status indicator in the header.
 *
 * Polls the Gateway /healthz endpoint and renders a compact status pill.
 */
import { computed } from 'vue'
import type { HealthStatus } from '../types'

const props = defineProps<{
  status: HealthStatus
  upstream: string
  detail: string | null
}>()

const label = computed(() => {
  switch (props.status) {
    case 'ok':
      return 'UPSTREAM OK'
    case 'degraded':
      return 'DEGRADED'
    case 'error':
      return 'DOWN'
  }
})

const tooltip = computed(() => {
  const parts = [`Upstream: ${props.upstream}`]
  if (props.detail) parts.push(`Detail: ${props.detail}`)
  return parts.join('\n')
})
</script>

<template>
  <div
    class="health-badge"
    :class="`health-badge--${status}`"
    :title="tooltip"
    role="status"
    aria-live="polite"
  >
    <span class="health-badge__dot" />
    <span class="health-badge__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.health-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  cursor: default;
  transition: background 0.3s ease;
}

.health-badge--ok {
  background: color-mix(in srgb, var(--color-success) 15%, transparent);
  color: var(--color-success);
  border: 1px solid color-mix(in srgb, var(--color-success) 30%, transparent);
}

.health-badge--degraded {
  background: color-mix(in srgb, var(--color-warning) 15%, transparent);
  color: var(--color-warning);
  border: 1px solid color-mix(in srgb, var(--color-warning) 30%, transparent);
}

.health-badge--error {
  background: color-mix(in srgb, var(--color-error) 15%, transparent);
  color: var(--color-error);
  border: 1px solid color-mix(in srgb, var(--color-error) 30%, transparent);
}

.health-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.health-badge--ok .health-badge__dot {
  animation: pulse-ok 2s ease-in-out infinite;
}

@keyframes pulse-ok {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}
</style>
