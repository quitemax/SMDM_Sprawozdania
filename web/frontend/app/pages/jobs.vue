<script setup lang="ts">
interface Job {
  id: number
  type: string
  status: 'pending' | 'running' | 'success' | 'failed'
  params: Record<string, unknown>
  exit_code: number | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  log?: string
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

const jobs = ref<Job[]>([])
const error = ref('')
const selected = ref<Job | null>(null)
let listTimer: ReturnType<typeof setInterval> | null = null
let detailTimer: ReturnType<typeof setInterval> | null = null

async function loadList() {
  try {
    jobs.value = await $fetch<Job[]>('/api/jobs')
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać listy zadań.'
  }
}

async function loadDetail(id: number) {
  try {
    const job = await $fetch<Job>(`/api/jobs/${id}`)
    if (selected.value?.id === id) selected.value = job
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać szczegółów zadania.'
  }
}

function select(job: Job) {
  selected.value = job
  loadDetail(job.id)
  if (detailTimer) clearInterval(detailTimer)
  detailTimer = setInterval(() => {
    if (!selected.value) return
    if (selected.value.status === 'pending' || selected.value.status === 'running') {
      loadDetail(selected.value.id)
    }
  }, 2000)
}

async function retry(job: Job) {
  error.value = ''
  try {
    await $fetch(`/api/jobs/${job.id}/retry`, { method: 'POST' })
    await loadList()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się ponowić zadania.'
  }
}

onMounted(() => {
  loadList()
  listTimer = setInterval(loadList, 3000)
})

onUnmounted(() => {
  if (listTimer) clearInterval(listTimer)
  if (detailTimer) clearInterval(detailTimer)
})
</script>

<template>
  <div>
    <h1>Zadania</h1>
    <p style="color:#6b7280">
      Kolejka zadań pipeline'u — każde zadanie to jedno uruchomienie jednego skryptu z <code>scripts/</code>
      przez workera w kontenerze <code>app</code>. Uruchamia się je z widoku <NuxtLink to="/recordings">Nagrania</NuxtLink>.
    </p>
    <p class="error" v-if="error">{{ error }}</p>

    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Typ</th>
          <th>Status</th>
          <th>Utworzono</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="j in jobs" :key="j.id">
          <td>{{ j.id }}</td>
          <td>{{ TYPE_LABELS[j.type] ?? j.type }}</td>
          <td>{{ STATUS_LABELS[j.status] ?? j.status }}</td>
          <td>{{ new Date(j.created_at).toLocaleString('pl-PL') }}</td>
          <td class="row">
            <button class="secondary" @click="select(j)">Podgląd</button>
            <button class="secondary" v-if="j.status === 'failed'" @click="retry(j)">Ponów</button>
          </td>
        </tr>
        <tr v-if="!jobs.length">
          <td colspan="5">Brak zadań.</td>
        </tr>
      </tbody>
    </table>

    <div class="card" v-if="selected">
      <h3>Zadanie #{{ selected.id }} — {{ TYPE_LABELS[selected.type] ?? selected.type }}</h3>
      <p>
        Status: <strong>{{ STATUS_LABELS[selected.status] ?? selected.status }}</strong>
        <span v-if="selected.exit_code !== null"> (kod wyjścia: {{ selected.exit_code }})</span>
      </p>
      <pre style="background:#111827; color:#d1d5db; padding:0.75rem; border-radius:6px; max-height:420px; overflow:auto; white-space:pre-wrap;">{{ selected.log || '(brak logu — jeszcze się nie zaczęło)' }}</pre>
    </div>
  </div>
</template>
