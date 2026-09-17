<script setup lang="ts">
interface Member {
  id: number
  full_name: string
  default_body: string
  active: boolean
}

interface Attendee {
  id: number
  member_id: number
  full_name: string
  body: string
  role: string | null
}

const route = useRoute()
const meetingId = route.params.id as string

const members = ref<Member[]>([])
const meeting = ref<any>(null)
const error = ref('')
const saved = ref(false)

const protocolNumber = ref('')
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

const membersByBody = computed(() => (body: string) =>
  members.value.filter((m) => m.default_body === body || selected[body].has(m.id))
)

function toggle(body: string, memberId: number) {
  const set = selected[body]
  if (set.has(memberId)) set.delete(memberId)
  else set.add(memberId)
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
  }
}

async function submit() {
  error.value = ''
  saved.value = false
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
    </p>
    <p class="error" v-if="error">{{ error }}</p>
    <p v-if="saved">Zapisano — plik <code>meeting_info.json</code> zaktualizowany na dysku.</p>

    <form @submit.prevent="submit" v-if="meeting">
      <div class="card">
        <div class="field">
          <label>Numer protokołu (np. 10/R/26)</label>
          <input v-model="protocolNumber" placeholder="np. 10/R/26" />
        </div>
      </div>

      <div class="card">
        <h3>Rada Nadzorcza</h3>
        <div class="checkbox-list">
          <label v-for="m in membersByBody('rada_nadzorcza')" :key="m.id" class="row">
            <input type="checkbox" :checked="selected.rada_nadzorcza.has(m.id)" @change="toggle('rada_nadzorcza', m.id)" />
            {{ m.full_name }}
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Zarząd</h3>
        <div class="checkbox-list">
          <label v-for="m in membersByBody('zarzad')" :key="m.id" class="row">
            <input type="checkbox" :checked="selected.zarzad.has(m.id)" @change="toggle('zarzad', m.id)" />
            {{ m.full_name }}
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Inni (radca prawny, obserwatorzy…)</h3>
        <div class="checkbox-list">
          <label v-for="m in membersByBody('inny')" :key="m.id" class="row">
            <input type="checkbox" :checked="selected.inny.has(m.id)" @change="toggle('inny', m.id)" />
            {{ m.full_name }}
          </label>
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
