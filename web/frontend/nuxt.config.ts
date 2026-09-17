// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  // Wewnętrzne narzędzie admina — bez potrzeby SSR/SEO; upraszcza to
  // wywołania API (zawsze z przeglądarki, żadnej dwoistości serwer/klient).
  ssr: false,
})
