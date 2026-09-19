<script setup lang="ts">
interface Member {
  id: number
  full_name: string
  default_body: string
  active: boolean
  role_label: string | null
}

interface Attendee {
  id: number
  member_id: number
  full_name: string
  body: string
  role: string | null
  role_label: string | null
}

// Tylko podpowiedzi (datalist) — można też wpisać dowolny tekst. Musi się
// zgadzać z listą w members.vue (tam to samo, dla domyślnej funkcji osoby).
const ROLE_LABEL_PRESETS: Record<string, string[]> = {
  rada_nadzorcza: [
    'Przewodniczący Rady Nadzorczej',
    'Zastępca Przewodniczącego Rady Nadzorczej',
    'Sekretarz Rady Nadzorczej',
    'Członek Rady Nadzorczej delegowany do czasowego pełnienia funkcji Członka Zarządu',
  ],
  zarzad: ['Prezes Zarządu', 'Członek Zarządu ds. technicznych', 'Członek Zarządu – Główna Księgowa'],
  inny: [],
}

const route = useRoute()
const meetingId = route.params.id as string

const members = ref<Member[]>([])
const meeting = ref<any>(null)
const error = ref('')
const saved = ref(false)

const protocolNumber = ref('')
// Prawdziwe dane historyczne mogą istnieć TYLKO w pliku (np. spotkania
// zaimportowane przed Fazą 1, zanim baza w ogóle śledziła uczestników) —
// jeśli baza nie ma ani jednego wiersza, a plik ma jakąkolwiek listę
// obecności, zapisanie formularza bez ręcznego zaznaczenia osób
// NADPISAŁOBY plik pustą listą. Ostrzegamy przed tym wprost.
const fileHasUnmatchedAttendees = ref(false)
const selected = reactive<Record<string, Set<number>>>({
  rada_nadzorcza: new Set(),
  zarzad: new Set(),
  inny: new Set(),
})
const roles = reactive<Record<string, number | null>>({
  protokolant: null,
  sekretarz: null,
  przewodniczacy: null,
})
// member_id -> funkcja/tytuł NA TYM SPOTKANIU. Wczytywane z zapisanego wcześniej
// stanu spotkania (nie z bieżącej domyślnej funkcji osoby!) — patrz load().
const titles = reactive<Record<number, string>>({})

// Osoba może na danym spotkaniu pełnić inną funkcję niż jej domyślna (np.
// delegacja Członka RN do Zarządu) — więc każda aktywna osoba jest wybieralna
// w każdym z trzech organów, nie tylko w swoim domyślnym.
function membersByBody(body: string): Member[] {
  return [...members.value].sort((a, b) => {
    const aMatch = a.default_body === body ? 0 : 1
    const bMatch = b.default_body === body ? 0 : 1
    return aMatch - bMatch || a.full_name.localeCompare(b.full_name)
  })
}

function toggle(body: string, member: Member) {
  const set = selected[body]
  if (set.has(member.id)) {
    set.delete(member.id)
  } else {
    set.add(member.id)
    if (titles[member.id] === undefined) titles[member.id] = member.role_label ?? ''
  }
}

async function load() {
  error.value = ''
  const [membersData, infoData] = await Promise.all([
    $fetch<Member[]>('/api/members'),
    $fetch<any>(`/api/meetings/${meetingId}/meeting-info`),
  ])
  members.value = membersData
  meeting.value = infoData.meeting
  protocolNumber.value = infoData.meeting_info?.protocol_number ?? infoData.meeting?.protocol_number ?? ''

  const attendees: Attendee[] = infoData.attendees ?? []
  for (const a of attendees) {
    if (selected[a.body]) selected[a.body].add(a.member_id)
    if (a.role) roles[a.role] = a.member_id
    // Zapisany wcześniej stan TEGO spotkania ma pierwszeństwo przed bieżącą
    // domyślną funkcją osoby — to jest właśnie ochrona historii przed
    // późniejszymi zmianami składu (np. koniec delegacji).
    titles[a.member_id] = a.role_label ?? ''
  }

  const fileAttendees = infoData.meeting_info?.attendees ?? {}
  const fileHasAnyone =
    (fileAttendees.rada_nadzorcza?.length ?? 0) > 0 ||
    (fileAttendees.zarzad?.length ?? 0) > 0 ||
    (fileAttendees.inni?.length ?? 0) > 0
  fileHasUnmatchedAttendees.value = attendees.length === 0 && fileHasAnyone
}

async function submit() {
  error.value = ''
  saved.value = false
  if (fileHasUnmatchedAttendees.value) {
    const totalSelected = selected.rada_nadzorcza.size + selected.zarzad.size + selected.inny.size
    if (
      totalSelected === 0 &&
      !confirm(
        'Ta lista obecności istnieje TYLKO w pliku na dysku (baza nie ma jeszcze ' +
          'dopasowanych osób do tego spotkania) — nie zaznaczono nikogo. Zapisanie ' +
          'teraz NADPISZE plik pustą listą obecności. Kontynuować mimo to?'
      )
    ) {
      return
    }
  }
  try {
    await $fetch(`/api/meetings/${meetingId}/meeting-info`, {
      method: 'PUT',
      body: {
        protocol_number: protocolNumber.value || null,
        attendee_member_ids: {
          rada_nadzorcza: [...selected.rada_nadzorcza],
          zarzad: [...selected.zarzad],
          inny: [...selected.inny],
        },
        protokolant_member_id: roles.protokolant,
        sekretarz_member_id: roles.sekretarz,
        przewodniczacy_member_id: roles.przewodniczacy,
        role_labels: { ...titles },
      },
    })
    saved.value = true
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się zapisać.'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <NuxtLink to="/meetings">&larr; Powrót do listy spotkań</NuxtLink>
    <h1>Metadane spotkania <span v-if="meeting">— {{ meeting.transcript_dir }} / {{ meeting.name }}</span></h1>
    <p class="row">
      <NuxtLink :to="`/meetings/${meetingId}/speakers`">Identyfikacja mówców</NuxtLink>
      ·
      <NuxtLink :to="`/meetings/${meetingId}/transcript`">Podgląd transkrypcji</NuxtLink>
      ·
      <NuxtLink :to="`/meetings/${meetingId}/report`">Projekt sprawozdania</NuxtLink>
    </p>
    <p class="error" v-if="error">{{ error }}</p>
    <p v-if="saved">Zapisano — plik <code>meeting_info.json</code> zaktualizowany na dysku.</p>
    <p class="error" v-if="fileHasUnmatchedAttendees">
      ⚠️ Lista obecności dla tego spotkania istnieje na razie tylko w pliku na dysku —
      poniższe pola startują puste. Zaznacz osoby ręcznie przed zapisaniem, w przeciwnym
      razie zapis nadpisze plik pustą listą obecności.
    </p>

    <form @submit.prevent="submit" v-if="meeting">
      <div class="card">
        <div class="field">
          <label>Numer protokołu (np. 10/R/26)</label>
          <input v-model="protocolNumber" placeholder="np. 10/R/26" />
        </div>
      </div>

      <div class="card" v-for="body in ['rada_nadzorcza', 'zarzad', 'inny']" :key="body">
        <h3>
          {{ body === 'rada_nadzorcza' ? 'Rada Nadzorcza' : body === 'zarzad' ? 'Zarząd' : 'Inni (radca prawny, obserwatorzy…)' }}
        </h3>
        <p style="color:#6b7280; margin-top: -0.5rem;" v-if="body !== 'inny'">
          Funkcja obok nazwiska dotyczy WYŁĄCZNIE tego spotkania — zmiana funkcji danej
          osoby na przyszłość (w <NuxtLink to="/members">składzie</NuxtLink>) nie zmieni tego, co tu zapisane.
        </p>
        <datalist :id="`presets-${body}`">
          <option v-for="preset in ROLE_LABEL_PRESETS[body]" :key="preset" :value="preset" />
        </datalist>
        <div class="checkbox-list">
          <div v-for="m in membersByBody(body)" :key="m.id" style="display:flex; flex-direction:column; gap:0.25rem;">
            <label class="row">
              <input type="checkbox" :checked="selected[body].has(m.id)" @change="toggle(body, m)" />
              {{ m.full_name }}
            </label>
            <input
              v-if="selected[body].has(m.id)"
              v-model="titles[m.id]"
              :list="`presets-${body}`"
              placeholder="Funkcja na tym spotkaniu (opcjonalnie)"
              style="margin-left: 1.5rem; margin-bottom: 0.4rem;"
            />
          </div>
        </div>
      </div>

      <div class="card">
        <h3>Funkcje na tym spotkaniu</h3>
        <div class="field">
          <label>Protokołowała/protokołował</label>
          <select v-model="roles.protokolant">
            <option :value="null">—</option>
            <option v-for="m in members" :key="m.id" :value="m.id">{{ m.full_name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Sekretarz</label>
          <select v-model="roles.sekretarz">
            <option :value="null">—</option>
            <option v-for="m in members" :key="m.id" :value="m.id">{{ m.full_name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Przewodnicząca/y</label>
          <select v-model="roles.przewodniczacy">
            <option :value="null">—</option>
            <option v-for="m in members" :key="m.id" :value="m.id">{{ m.full_name }}</option>
          </select>
        </div>
      </div>

      <button type="submit">Zapisz</button>
    </form>
  </div>
</template>
