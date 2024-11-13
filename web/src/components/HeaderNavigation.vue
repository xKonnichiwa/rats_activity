<template>
  <v-tabs fixed-tabs>
    <v-tab prepend-icon="mdi-video-plus" to="/video">Создание</v-tab>
  </v-tabs>
</template>
<script>
  export default {
    data: () => ({
      tab: null,
    }),
  }
</script>
