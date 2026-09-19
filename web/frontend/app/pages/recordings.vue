<script setup lang="ts">
interface Recording {
  date_dir: string
  filename: string
  path: string
  size_bytes: number
  modified_at: string
  transcript_path: string
  has_transcript: boolean
  has_speakers: boolean
  clean_transcript_path: string
  has_clean: boolean
  has_meeting_info: boolean
}

interface Job {
  id: number
  type: string
  status: 'pending' | 'running' | 'success' | 'failed'
}

interface Action {
  label: string
  type: string
  path: string
}

const TYPE_LABELS: Record<string, string> = {
  transcribe: 'Transkrypcja',
  identify_speakers: 'Identyfikacja mówców',
  clean_transcript: 'Czyszczenie transkrypcji',
  init_meeting_info: 'Szablon danych spotkania',
  generate_report: 'Generowanie projektu sprawozdania',
}

const STATUS_LABELS: Record<string, string> = {
  pending: '⏳ oczekuje',
  running: '▶️ w toku',
  success: '✅ sukces',
  failed: '❌ błąd',
}

const recordings = ref<Recording[]>([])
const error = ref('')
const uploading = ref(false)
const uploadDate = ref(new Date().toISOString().slice(0, 10))
const fileInput = ref<HTMLInputElement | null>(null)
// Ostatnie zadanie uruchomione dla danego nagrania (klucz = recording.path), do pokazania statusu na żywo.
const lastJobs = ref<Record<string, Job>>({})
let pollTimer: ReturnType<typeof setInterval> | null = null

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

function nextActions(r: Recording): Action[] {
  const actions: Action[] = []
  if (!r.has_transcript) {
    actions.push({ label: 'Transkrybuj', type: 'transcribe', path: r.path })
    return actions
  }
  if (!r.has_speakers) actions.push({ label: 'Identyfikuj mówców', type: 'identify_speakers', path: r.transcript_path })
  if (!r.has_clean) actions.push({ label: 'Wyczyść transkrypt', type: 'clean_transcript', path: r.transcript_path })
  if (!r.has_meeting_info) actions.push({ label: 'Szablon danych spotkania', type: 'init_meeting_info', path: r.transcript_path })
  if (r.has_clean && r.has_meeting_info) {
    actions.push({ label: 'Generuj projekt sprawozdania', type: 'generate_report', path: r.clean_transcript_path })
  }
  return actions
}

async function runAction(r: Recording, action: Action) {
  error.value = ''
  try {
    const job = await $fetch<Job>('/api/jobs', { method: 'POST', body: { type: action.type, path: action.path } })
    lastJobs.value[r.path] = job
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się uruchomić zadania.'
  }
}

async function pollJobs() {
  const active = Object.values(lastJobs.value).filter((j) => j.status === 'pending' || j.status === 'running')
  if (!active.length) return
  await Promise.all(
    active.map(async (job) => {
      try {
        const fresh = await $fetch<Job>(`/api/jobs/${job.id}`)
        for (const path of Object.keys(lastJobs.value)) {
          if (lastJobs.value[path]?.id === fresh.id) lastJobs.value[path] = fresh
        }
      } catch {
        // Cichy błąd odpytywania — spróbuje ponownie przy kolejnym tyknięciu.
      }
    })
  )
  // Zadanie mogło właśnie ukończyć plik (np. transkrypcję) — odśwież flagi pipeline'u.
  if (active.some((j) => j.status === 'pending' || j.status === 'running')) return
  await load()
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

onMounted(() => {
  load()
  pollTimer = setInterval(pollJobs, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
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
          <th>Pipeline</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in recordings" :key="r.path">
          <td>{{ r.date_dir }}</td>
          <td>{{ r.filename }}</td>
          <td>{{ formatSize(r.size_bytes) }}</td>
          <td>
            <div v-if="lastJobs[r.path]" style="margin-bottom: 0.4rem;">
              {{ TYPE_LABELS[lastJobs[r.path].type] }}: {{ STATUS_LABELS[lastJobs[r.path].status] }}
              <NuxtLink to="/jobs">(log)</NuxtLink>
            </div>
            <div class="row" style="flex-wrap: wrap;">
              <button
                class="secondary"
                v-for="action in nextActions(r)"
                :key="action.type"
                :disabled="lastJobs[r.path]?.status === 'pending' || lastJobs[r.path]?.status === 'running'"
                @click="runAction(r, action)"
              >
                {{ action.label }}
              </button>
              <span v-if="!nextActions(r).length">✅ pipeline ukończony</span>
            </div>
          </td>
          <td><button class="danger" @click="remove(r)">Usuń</button></td>
        </tr>
        <tr v-if="!recordings.length">
          <td colspan="5">Brak nagrań — wgraj pierwsze powyżej.</td>
        </tr>
      </tbody>
    </table>

    <p style="color:#6b7280">
      Po zakończeniu kroku "Szablon danych spotkania" spotkanie pojawi się na liście
      <NuxtLink to="/meetings">Spotkania</NuxtLink> po kliknięciu tam „Przeskanuj dysk” — tam uzupełnia się
      listę obecności, protokolanta, sekretarza i przewodniczącego.
    </p>
  </div>
</template>
