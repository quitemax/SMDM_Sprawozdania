<script setup lang="ts">
interface Member {
  id: number
  full_name: string
  default_body: 'rada_nadzorcza' | 'zarzad' | 'inny'
  active: boolean
  role_label: string | null
  notes: string | null
}

const BODY_LABELS: Record<string, string> = {
  rada_nadzorcza: 'Rada Nadzorcza',
  zarzad: 'Zarząd',
  inny: 'Inny',
}

// Podpowiedzi funkcji per organ — domyślna (najczęstsza) wartość to brak
// funkcji szczególnej ("zwykły" członek), stąd pusta opcja na początku.
// Można też wpisać własną etykietę — to tylko podpowiedzi, nie sztywny enum.
const ROLE_LABEL_PRESETS: Record<string, string[]> = {
  rada_nadzorcza: [
    'Przewodniczący Rady Nadzorczej',
    'Zastępca Przewodniczącego Rady Nadzorczej',
    'Sekretarz Rady Nadzorczej',
    'Członek Rady Nadzorczej delegowany do czasowego pełnienia funkcji Członka Zarządu',
  ],
  zarzad: [
    'Prezes Zarządu',
    'Członek Zarządu ds. technicznych',
    'Członek Zarządu – Główna Księgowa',
  ],
  inny: [],
}

const CUSTOM_LABEL = '__custom__'
const roleLabelMode = ref<'preset' | 'custom'>('preset')

function presetsFor(body: string): string[] {
  return ROLE_LABEL_PRESETS[body] ?? []
}

function onRoleLabelSelect(value: string) {
  if (value === CUSTOM_LABEL) {
    roleLabelMode.value = 'custom'
    form.role_label = ''
  } else {
    roleLabelMode.value = 'preset'
    form.role_label = value
  }
}

const members = ref<Member[]>([])
const showInactive = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)

const form = reactive({
  full_name: '',
  default_body: 'rada_nadzorcza',
  role_label: '',
  notes: '',
})

async function load() {
  error.value = ''
  try {
    members.value = await $fetch<Member[]>('/api/members', {
      query: { include_inactive: showInactive.value ? '1' : '0' },
    })
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się pobrać listy.'
  }
}

function resetForm() {
  editingId.value = null
  form.full_name = ''
  form.default_body = 'rada_nadzorcza'
  form.role_label = ''
  form.notes = ''
  roleLabelMode.value = 'preset'
}

function edit(member: Member) {
  editingId.value = member.id
  form.full_name = member.full_name
  form.default_body = member.default_body
  form.role_label = member.role_label ?? ''
  form.notes = member.notes ?? ''
  roleLabelMode.value =
    form.role_label && !presetsFor(member.default_body).includes(form.role_label) ? 'custom' : 'preset'
}

async function submit() {
  error.value = ''
  try {
    if (editingId.value) {
      await $fetch(`/api/members/${editingId.value}`, { method: 'PUT', body: form })
    } else {
      await $fetch('/api/members', { method: 'POST', body: form })
    }
    resetForm()
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się zapisać.'
  }
}

async function deactivate(member: Member) {
  if (!confirm(`Dezaktywować „${member.full_name}”? (dane z poprzednich spotkań zostają)`)) return
  try {
    await $fetch(`/api/members/${member.id}`, { method: 'DELETE' })
    await load()
  } catch (e: any) {
    error.value = e?.data?.error ?? 'Nie udało się dezaktywować.'
  }
}

watch(showInactive, load)
onMounted(load)
</script>

<template>
  <div>
    <h1>Skład Rady Nadzorczej / Zarządu</h1>
    <p class="error" v-if="error">{{ error }}</p>

    <div class="card">
      <h3>{{ editingId ? 'Edytuj osobę' : 'Dodaj osobę' }}</h3>
      <form @submit.prevent="submit">
        <div class="field">
          <label>Imię i nazwisko</label>
          <input v-model="form.full_name" required />
        </div>
        <div class="field">
          <label>Domyślna rola</label>
          <select v-model="form.default_body">
            <option value="rada_nadzorcza">Rada Nadzorcza</option>
            <option value="zarzad">Zarząd</option>
            <option value="inny">Inny (np. radca prawny, obserwator)</option>
          </select>
        </div>
        <div class="field" v-if="form.default_body === 'inny'">
          <label>Etykieta roli (widoczna w sprawozdaniu, np. "radca prawny")</label>
          <input v-model="form.role_label" placeholder="radca prawny" />
        </div>
        <div class="field" v-else>
          <label>Funkcja (opcjonalnie — domyślna, można nadpisać per spotkanie)</label>
          <select
            :value="roleLabelMode === 'custom' ? CUSTOM_LABEL : form.role_label"
            @change="onRoleLabelSelect(($event.target as HTMLSelectElement).value)"
          >
            <option value="">— brak (zwykły członek)</option>
            <option v-for="preset in presetsFor(form.default_body)" :key="preset" :value="preset">{{ preset }}</option>
            <option :value="CUSTOM_LABEL">Inna (wpisz ręcznie)…</option>
          </select>
          <input
            v-if="roleLabelMode === 'custom'"
            v-model="form.role_label"
            placeholder="Wpisz funkcję"
            style="margin-top: 0.4rem"
          />
        </div>
        <div class="field">
          <label>Notatki (opcjonalnie)</label>
          <textarea v-model="form.notes" rows="2" />
        </div>
        <div class="row">
          <button type="submit">{{ editingId ? 'Zapisz zmiany' : 'Dodaj' }}</button>
          <button type="button" class="secondary" v-if="editingId" @click="resetForm">Anuluj</button>
        </div>
      </form>
    </div>

    <label class="row">
      <input type="checkbox" v-model="showInactive" />
      Pokaż nieaktywne
    </label>

    <table>
      <thead>
        <tr>
          <th>Imię i nazwisko</th>
          <th>Rola</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in members" :key="m.id">
          <td>{{ m.full_name }}</td>
          <td>{{ BODY_LABELS[m.default_body] }}<span v-if="m.role_label"> ({{ m.role_label }})</span></td>
          <td>{{ m.active ? 'aktywna/y' : 'nieaktywna/y' }}</td>
          <td class="row">
            <button class="secondary" @click="edit(m)">Edytuj</button>
            <button class="danger" v-if="m.active" @click="deactivate(m)">Dezaktywuj</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
