<script setup lang="ts">
interface ReportInfo {
  exists: boolean
  markdown: string | null
  report_path: string
  clean_transcript_path: string
  generated_at: string | null
}

interface Job {
  id: number
  type: string
  status: 'pending' | 'running' | 'success' | 'failed'
}

const route = useRoute()
const meetingId = route.params.id as string

const info = ref<ReportInfo | null>(null)
const error = ref('')
const job = ref<Job | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

// Bardzo wąski "renderer" — obsługuje TYLKO to, co faktycznie produkuje
// scripts/generate_report.py (patrz ReportDocxRenderer.php po stronie
// backendu, ten sam zestaw reguł, po prostu do HTML zamiast do .docx).
function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)
}

function inlineHtml(text: string): string {
  return text
    .split(/(\*\*.+?\*\*)/)
    .map((part) => (part.startsWith('**') && part.endsWith('**') && part.length > 4
      ? `<strong>${escapeHtml(part.slice(2, -2))}</strong>`
      : escapeHtml(part)))
    .join('')
}

function renderMarkdown(markdown: string): string {
  const lines = markdown.split(/\r\n|\r|\n/)
  const html: string[] = []
  let listOpen = false

  const closeList = () => {
    if (listOpen) {
      html.push('</ul>')
      listOpen = false
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trimEnd()
    if (line === '') continue

    if (line.startsWith('# ')) {
      closeList()
      html.push(`<h1>${inlineHtml(line.slice(2).replace(/\*\*/g, ''))}</h1>`)
      continue
    }
    if (line.startsWith('>')) {
      closeList()
      const quote: string[] = []
      while (i < lines.length && lines[i].trimEnd().startsWith('>')) {
        const text = lines[i].trimEnd().slice(1).trim()
        if (text) quote.push(text)
        i++
      }
      i--
      html.push(`<blockquote>${inlineHtml(quote.join(' '))}</blockquote>`)
      continue
    }
    if (line.startsWith('- ')) {
      if (!listOpen) {
        html.push('<ul>')
        listOpen = true
      }
      html.push(`<li>${inlineHtml(line.slice(2))}</li>`)
      continue
    }
    closeList()
    const signatureMatch = /^\*(?!\*)(.+)(?<!\*)\*$/.exec(line)
    if (signatureMatch) {
      html.push(`<p class="signature">${inlineHtml(signatureMatch[1])}</p>`)
      continue
    }
    html.push(`<p>${inlineHtml(line)}</p>`)
  }
  closeList()
  return html.join('\n')
}

const renderedHtml = computed(() => (info.value?.markdown ? renderMarkdown(info.value.markdown) : ''))

async function load() {
  error.value = ''
  try {
    info.value = await $fetch<ReportInfo>(`/api/meetings/${meetingId}/report`)
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać projektu sprawozdania.'
  }
}

async function generate() {
  if (!info.value) return
  error.value = ''
  try {
    job.value = await $fetch<Job>('/api/jobs', {
      method: 'POST',
      body: { type: 'generate_report', path: info.value.clean_transcript_path },
    })
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = setInterval(poll, 3000)
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się uruchomić generowania.'
  }
}

async function poll() {
  if (!job.value) return
  try {
    job.value = await $fetch<Job>(`/api/jobs/${job.value.id}`)
    if (job.value.status === 'success' || job.value.status === 'failed') {
      if (pollTimer) clearInterval(pollTimer)
      if (job.value.status === 'success') await load()
    }
  } catch {
    // ciche pominięcie — spróbuje ponownie przy kolejnym tyknięciu
  }
}

onMounted(load)
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div>
    <NuxtLink class="link-button" :to="`/meetings/${meetingId}`">&larr; Powrót do metadanych spotkania</NuxtLink>
    <h1>Projekt sprawozdania</h1>
    <p class="row">
      <NuxtLink class="link-button" :to="`/meetings/${meetingId}/speakers`">Identyfikacja mówców</NuxtLink>
      <NuxtLink class="link-button" :to="`/meetings/${meetingId}/transcript`">Podgląd transkrypcji</NuxtLink>
    </p>
    <p class="error" v-if="error">{{ error }}</p>

    <div class="card" v-if="info">
      <div class="row" style="justify-content: space-between; flex-wrap: wrap;">
        <div>
          <span v-if="info.exists">
            Wygenerowano: {{ info.generated_at ? new Date(info.generated_at).toLocaleString('pl-PL') : '—' }}
          </span>
          <span v-else>Projekt jeszcze nie wygenerowany dla tego spotkania.</span>
        </div>
        <div class="row">
          <a v-if="info.exists" class="link-button" :href="`/api/meetings/${meetingId}/report/docx`" download>
            Pobierz .docx
          </a>
          <button @click="generate" :disabled="job?.status === 'pending' || job?.status === 'running'">
            {{ info.exists ? 'Generuj ponownie' : 'Generuj projekt' }}
          </button>
        </div>
      </div>
      <p v-if="job" style="margin-top: 0.5rem;">
        Zadanie #{{ job.id }}: {{ job.status }}
        <NuxtLink to="/jobs">(pełny log)</NuxtLink>
      </p>
    </div>

    <p v-if="info && !info.exists" style="color:#6b7280">
      Wymaga oczyszczonej transkrypcji (<code>.clean.json</code>) i uzupełnionych danych spotkania — patrz
      <NuxtLink to="/recordings">Nagrania</NuxtLink> (kolejne kroki pipeline'u) i
      <NuxtLink :to="`/meetings/${meetingId}`">metadane tego spotkania</NuxtLink>.
    </p>

    <div class="card" v-if="info?.markdown" v-html="renderedHtml" style="line-height: 1.6;"></div>
  </div>
</template>

<style>
.card blockquote {
  border-left: 3px solid #cbd5e1;
  margin: 0.5rem 0;
  padding: 0.25rem 1rem;
  color: #595959;
  font-style: italic;
}
.card h1 {
  font-size: 1.4rem;
}
.card p.signature {
  font-style: italic;
}
</style>
