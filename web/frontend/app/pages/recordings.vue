<script setup lang="ts">
interface Recording {
  date_dir: string
  filename: string
  path: string
  size_bytes: number
  modified_at: string
  has_transcript: boolean
}

const recordings = ref<Recording[]>([])
const error = ref('')
const uploading = ref(false)
const uploadDate = ref(new Date().toISOString().slice(0, 10))
const fileInput = ref<HTMLInputElement | null>(null)

function formatSize(bytes: number): string {
  const mb = bytes / (1024 * 1024)
  return mb >= 1024 ? `${(mb / 1024).toFixed(2)} GB` : `${mb.toFixed(1)} MB`
}

async function load() {
  error.value = ''
  try {
    recordings.value = await $fetch<Recording[]>('/api/recordings')
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać listy nagrań.'
  }
}

async function upload() {
  const file = fileInput.value?.files?.[0]
  if (!file) {
    error.value = 'Wybierz plik audio.'
    return
  }
  error.value = ''
  uploading.value = true
  try {
    const form = new FormData()
    form.append('date', uploadDate.value)
    form.append('file', file)
    await $fetch('/api/recordings', { method: 'POST', body: form })
    if (fileInput.value) fileInput.value.value = ''
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się wgrać nagrania.'
  } finally {
    uploading.value = false
  }
}

async function remove(recording: Recording) {
  if (!confirm(`Usunąć plik „${recording.filename}” z dysku? Tej operacji nie da się cofnąć.`)) return
  error.value = ''
  try {
    await $fetch('/api/recordings', { method: 'DELETE', query: { path: recording.path } })
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się usunąć pliku.'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>Nagrania</h1>
    <p class="error" v-if="error">{{ error }}</p>

    <div class="card">
      <h3>Wgraj nowe nagranie</h3>
      <form @submit.prevent="upload">
        <div class="field">
          <label>Data spotkania</label>
          <input type="date" v-model="uploadDate" required />
        </div>
        <div class="field">
          <label>Plik audio (mp3, m4a, wav…)</label>
          <input type="file" ref="fileInput" accept="audio/*" required />
        </div>
        <button type="submit" :disabled="uploading">
          {{ uploading ? 'Wgrywanie… (duże pliki mogą chwilę potrwać)' : 'Wgraj' }}
        </button>
      </form>
    </div>

    <table>
      <thead>
        <tr>
          <th>Data</th>
          <th>Plik</th>
          <th>Rozmiar</th>
          <th>Transkrypcja</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in recordings" :key="r.path">
          <td>{{ r.date_dir }}</td>
          <td>{{ r.filename }}</td>
          <td>{{ formatSize(r.size_bytes) }}</td>
          <td>{{ r.has_transcript ? '✅ jest' : '— brak' }}</td>
          <td><button class="danger" @click="remove(r)">Usuń</button></td>
        </tr>
        <tr v-if="!recordings.length">
          <td colspan="5">Brak nagrań — wgraj pierwsze powyżej.</td>
        </tr>
      </tbody>
    </table>

    <p style="color:#6b7280">
      Kolejny krok (transkrypcja) na razie robi się z CLI, np.:
      <code>docker compose exec app python scripts/transcribe.py "input/{{ recordings[0]?.path ?? 'audio/...' }}"</code>
      — uruchamianie tego z przeglądarki to Faza 3 (job runner).
    </p>
  </div>
</template>
