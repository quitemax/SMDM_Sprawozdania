<script setup lang="ts">
interface Meeting {
  id: number
  meeting_date: string | null
  name: string
  transcript_dir: string
  protocol_number: string | null
}

const meetings = ref<Meeting[]>([])
const error = ref('')
const scanning = ref(false)

async function load() {
  error.value = ''
  try {
    meetings.value = await $fetch<Meeting[]>('/api/meetings')
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać listy spotkań.'
  }
}

async function rescan() {
  scanning.value = true
  error.value = ''
  try {
    await $fetch('/api/meetings/rescan', { method: 'POST' })
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się przeskanować dysku.'
  } finally {
    scanning.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>Spotkania</h1>
    <p>
      Lista pochodzi z plików <code>*.meeting_info.json</code> w
      <code>output/transcripts/</code>. Po uruchomieniu
      <code>scripts/init_meeting_info.py</code> na nowej transkrypcji
      (albo po ręcznym dodaniu pliku) kliknij „Przeskanuj dysk”.
    </p>
    <p class="error" v-if="error">{{ error }}</p>
    <button @click="rescan" :disabled="scanning">
      {{ scanning ? 'Skanowanie…' : 'Przeskanuj dysk' }}
    </button>

    <table>
      <thead>
        <tr>
          <th>Data</th>
          <th>Nazwa</th>
          <th>Nr protokołu</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in meetings" :key="m.id">
          <td>{{ m.meeting_date ?? '—' }}</td>
          <td>{{ m.transcript_dir }} / {{ m.name }}</td>
          <td>{{ m.protocol_number ?? '—' }}</td>
          <td><NuxtLink class="link-button" :to="`/meetings/${m.id}`">Edytuj metadane</NuxtLink></td>
        </tr>
        <tr v-if="!meetings.length">
          <td colspan="4">Brak spotkań — kliknij „Przeskanuj dysk”.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
