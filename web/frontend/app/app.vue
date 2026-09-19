<template>
  <div class="app">
    <nav class="nav">
      <strong>SMDM</strong>
      <NuxtLink to="/recordings">Nagrania</NuxtLink>
      <NuxtLink to="/members">Skład Rady/Zarządu</NuxtLink>
      <NuxtLink to="/meetings">Spotkania</NuxtLink>
      <NuxtLink to="/jobs">Zadania</NuxtLink>
    </nav>
    <main class="main">
      <NuxtPage />
    </main>
  </div>
</template>

<style>
  body { margin: 0; font-family: system-ui, sans-serif; background: #f7f7f8; color: #1a1a1a; }
  .nav { display: flex; gap: 1.5rem; align-items: center; padding: 0.75rem 1.5rem; background: #1f2937; color: #fff; }
  .nav a { color: #cbd5e1; text-decoration: none; }
  .nav a.router-link-active { color: #fff; font-weight: 600; }
  .main { max-width: 960px; margin: 0 auto; padding: 1.5rem; }
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e5e7eb; }
  input, select, textarea { padding: 0.4rem 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font: inherit; }
  button { padding: 0.4rem 0.9rem; border: 1px solid #1f2937; background: #1f2937; color: #fff; border-radius: 4px; cursor: pointer; font: inherit; }
  button.secondary { background: #fff; color: #1f2937; }
  button.danger { background: #fff; color: #b91c1c; border-color: #b91c1c; }
  /* Linki wewnątrz treści (poza .nav) nie mają zmieniać koloru po odwiedzeniu —
     fioletowy ":visited" mylił z rozróżnianiem, co jest czym. */
  .main a { color: #1f2937; }
  .main a:visited { color: #1f2937; }
  /* Linki pełniące rolę akcji (nawigacja między podstronami spotkania, "wstecz",
     pobieranie pliku) mają wyglądać jak przyciski — inaczej łatwo je pomylić ze
     zwykłym tekstem albo zgubić, które są klikalne. */
  a.link-button {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    border: 1px solid #1f2937;
    background: #fff;
    color: #1f2937;
    border-radius: 4px;
    text-decoration: none;
    font: inherit;
  }
  a.link-button:visited { color: #1f2937; }
  a.link-button:hover { background: #f3f4f6; }
  .error { color: #b91c1c; margin: 0.5rem 0; }
  .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .field { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
  .checkbox-list { display: flex; flex-direction: column; gap: 0.25rem; max-height: 220px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.5rem; }
  .row { display: flex; gap: 0.5rem; align-items: center; }
</style>
