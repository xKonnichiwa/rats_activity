<template>
  <v-card
    class="mx-auto px-4 py-4 pb-6"
    max-width="600"
    subtitle="Загрузка на сервер и запуск процесса разметки"
    title="Новая разметка"
  >
    <v-form
      v-model="form"
      @submit.prevent="onSubmit"
    >

      <v-file-input
        v-model="file"
        class="py-4"
        label="Файл"
        show-size
        variant="outlined"
      />

      <v-btn
        block
        color="success"
        :disabled="!form"
        :loading="loading"
        size="large"
        type="submit"
        variant="elevated"
      >
        Старт
      </v-btn>
    </v-form>
  </v-card>
</template>

<script>
  import { http } from '@/shared'
  export default {
    data: () => ({
      form: false,
      file: undefined,
      loading: false,
    }),
    methods: {
      async onSubmit () {
        try {
          this.loading = true
          const formData = new FormData()
          formData.append('file', this.file, this.file.name)
          const response = await http.request('/upload-edf/', formData, {}, {}, 'post')

          this.$router.push(`/video/${response.data.file_id}`)
        } finally {
          this.loading = false
        }
      },
    },
  }
</script>
