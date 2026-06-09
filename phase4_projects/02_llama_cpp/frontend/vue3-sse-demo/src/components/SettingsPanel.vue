<script setup lang="ts">
/**
 * SettingsPanel — collapsible sidebar panel for model & inference parameters.
 *
 * Enterprise note: In production, these would be driven by a Gateway
 * config endpoint. For now, local reactive state sourced from a single
 * settings object passed via v-model.
 */
import { computed } from 'vue'
import type { AppSettings } from '../types'

const props = defineProps<{
  modelValue: AppSettings
}>()

const emit = defineEmits<{
  'update:modelValue': [value: AppSettings]
}>()

function update<K extends keyof AppSettings>(key: K, value: AppSettings[K]): void {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

const modelOptions = [
  { value: 'local-qwen2.5-7b-q4', label: 'Qwen2.5-7B-Q4_K_M' },
  { value: 'local-qwen2.5-7b-q5', label: 'Qwen2.5-7B-Q5_K_M' },
]
</script>

<template>
  <aside class="settings">
    <h3 class="settings__title">Inference Settings</h3>

    <!-- Model -->
    <label class="settings__field">
      <span class="settings__label">Model</span>
      <select
        class="settings__select"
        :value="modelValue.model"
        @change="update('model', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="m in modelOptions" :key="m.value" :value="m.value">
          {{ m.label }}
        </option>
      </select>
    </label>

    <!-- System Prompt -->
    <label class="settings__field">
      <span class="settings__label">System Prompt</span>
      <textarea
        class="settings__textarea"
        rows="4"
        :value="modelValue.systemPrompt"
        @input="update('systemPrompt', ($event.target as HTMLTextAreaElement).value)"
      />
    </label>

    <!-- Temperature -->
    <label class="settings__field">
      <span class="settings__label">
        Temperature <code>{{ modelValue.temperature.toFixed(2) }}</code>
      </span>
      <input
        type="range"
        class="settings__range"
        min="0"
        max="2"
        step="0.05"
        :value="modelValue.temperature"
        @input="update('temperature', parseFloat(($event.target as HTMLInputElement).value))"
      />
    </label>

    <!-- Top-P -->
    <label class="settings__field">
      <span class="settings__label">
        Top-P <code>{{ modelValue.topP.toFixed(2) }}</code>
      </span>
      <input
        type="range"
        class="settings__range"
        min="0"
        max="1"
        step="0.05"
        :value="modelValue.topP"
        @input="update('topP', parseFloat(($event.target as HTMLInputElement).value))"
      />
    </label>

    <!-- Max Tokens -->
    <label class="settings__field">
      <span class="settings__label">Max Tokens</span>
      <input
        type="number"
        class="settings__number"
        min="16"
        max="4096"
        step="16"
        :value="modelValue.maxTokens"
        @input="update('maxTokens', parseInt(($event.target as HTMLInputElement).value, 10) || 512)"
      />
    </label>
  </aside>
</template>

<style scoped>
.settings {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-bottom: 1px solid var(--color-border);
}

.settings__title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.settings__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings__label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.settings__label code {
  font-size: 0.72rem;
  background: var(--color-surface-2);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--color-accent);
}

.settings__select,
.settings__number {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 0.825rem;
  font-family: inherit;
  background: var(--color-surface-2);
  color: var(--color-text);
  outline: none;
}

.settings__select:focus,
.settings__number:focus {
  border-color: var(--color-accent);
}

.settings__textarea {
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 0.8rem;
  font-family: inherit;
  background: var(--color-surface-2);
  color: var(--color-text);
  outline: none;
  resize: vertical;
  line-height: 1.45;
}

.settings__textarea:focus {
  border-color: var(--color-accent);
}

.settings__range {
  width: 100%;
  accent-color: var(--color-accent);
}
</style>
