<script setup lang="ts">
const route = useRoute()
const meetingId = route.params.id as string

const text = ref<string | null>(null)
const error = ref('')

async function load() {
  error.value = ''
  try {
    const data = await $fetch<{ text: string | null; error?: string }>(`/api/meetings/${meetingId}/transcript`)
    text.value = data.text
    if (!data.text && data.error) error.value = data.error
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać transkrypcji.'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <NuxtLink class="link-button" :to="`/meetings/${meetingId}`">&larr; Powrót do metadanych spotkania</NuxtLink>
    <h1>Transkrypcja (podgląd)</h1>
    <p class="error" v-if="error">{{ error }}</p>
    <pre v-if="text" class="card" style="white-space: pre-wrap; font-family: inherit;">{{ text }}</pre>
  </div>
</template>
