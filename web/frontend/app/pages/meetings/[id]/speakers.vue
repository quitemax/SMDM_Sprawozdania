<script setup lang="ts">
interface Speaker {
  speaker_label: string
  proposed_name: string | null
  confidence: string
  source: 'model' | 'manual'
  evidence: string
  audio_samples: string[]
}

const route = useRoute()
const meetingId = route.params.id as string

const speakers = ref<Speaker[]>([])
const error = ref('')
const saving = ref<string | null>(null)
const drafts = reactive<Record<string, string>>({})

async function load() {
  error.value = ''
  try {
    const data = await $fetch<{ speakers: Speaker[] }>(`/api/meetings/${meetingId}/speakers`)
    speakers.value = data.speakers
    for (const s of data.speakers) {
      drafts[s.speaker_label] = s.proposed_name ?? ''
    }
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać listy mówców.'
  }
}

async function save(speaker: Speaker) {
  saving.value = speaker.speaker_label
  error.value = ''
  try {
    await $fetch(`/api/meetings/${meetingId}/speakers/${encodeURIComponent(speaker.speaker_label)}`, {
      method: 'PUT',
      body: { proposed_name: drafts[speaker.speaker_label], confidence: 'wysoka' },
    })
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się zapisać.'
  } finally {
    saving.value = null
  }
}

function sampleUrl(speaker: Speaker, index: number): string {
  return `/api/meetings/${meetingId}/speakers/${encodeURIComponent(speaker.speaker_label)}/sample/${index + 1}`
}

onMounted(load)
</script>

<template>
  <div>
    <NuxtLink class="link-button" :to="`/meetings/${meetingId}`">&larr; Powrót do metadanych spotkania</NuxtLink>
    <h1>Identyfikacja mówców</h1>
    <p>
      Odsłuchaj próbki i wpisz imię/nazwisko. Zapisanie tutaj oznacza wpis
      jako <strong>potwierdzony ręcznie</strong> — <code>clean_transcript.py</code>
      nie doda już znaku zapytania przy tej etykiecie.
    </p>
    <p class="error" v-if="error">{{ error }}</p>
    <p v-if="!speakers.length && !error">
      Brak pliku <code>*.speakers.json</code> dla tego spotkania — uruchom
      najpierw <code>scripts/extract_speaker_samples.py</code> i/lub
      <code>scripts/identify_speakers.py</code> z CLI.
    </p>

    <div class="card" v-for="speaker in speakers" :key="speaker.speaker_label">
      <h3>
        {{ speaker.speaker_label }}
        <span v-if="speaker.source === 'manual'" title="Potwierdzone ręcznie">✅</span>
        <span v-else title="Propozycja modelu — niepotwierdzona">🤖 {{ speaker.confidence }}</span>
      </h3>
      <p v-if="speaker.evidence" style="color:#6b7280; font-size:0.9em">{{ speaker.evidence }}</p>

      <div class="row" v-if="speaker.audio_samples?.length">
        <audio v-for="(sample, idx) in speaker.audio_samples" :key="sample" :src="sampleUrl(speaker, idx)" controls preload="none" />
      </div>
      <p v-else style="color:#6b7280">Brak wyciętych próbek audio dla tego mówcy.</p>

      <div class="row" style="margin-top:0.75rem">
        <input v-model="drafts[speaker.speaker_label]" placeholder="Imię i nazwisko" style="flex:1" />
        <button @click="save(speaker)" :disabled="saving === speaker.speaker_label">
          {{ saving === speaker.speaker_label ? 'Zapisywanie…' : 'Zapisz' }}
        </button>
      </div>
    </div>
  </div>
</template>
