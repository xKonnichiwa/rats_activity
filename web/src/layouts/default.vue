<template>
  <v-responsive class="border rounded">
    <v-app class="bg-surface-light" :theme="theme">
      <v-app-bar class="pr-4 text-grey-darken-1" title="GPT Enjoyers">
        <header-navigation/>
        <v-spacer />
        <v-btn
          :prepend-icon="theme === 'light' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          slim
          :text="theme === 'light' ? 'Светлая' : 'Темная'"
          @click="onClick"
        />
      </v-app-bar>

      <v-main>
        <v-container>
          <router-view />
        </v-container>
      </v-main>
    </v-app>
  </v-responsive>
</template>

<script lang="ts" setup>
  import { ref } from 'vue'
  import HeaderNavigation from "@/components/HeaderNavigation";

  const theme = ref('light')

  function onClick () {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }
</script>
