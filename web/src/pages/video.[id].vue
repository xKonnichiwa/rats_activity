<template>
  <v-breadcrumbs :items="items" />
  <bar-chart />

</template>

<script setup>

</script>

<script>
  import BarChart from '@/components/ExampleChart.vue'

  export default {
    components: { BarChart },
    data: () => ({
      items: [{
        title: 'Главная',
        disabled: false,
        to: '/',
      }, {
        title: `Карточка файла`,
      }],
    }),
    computed: {
      fileKey () {
        return this.$route.params.id
      },
    },
    mounted () {
    },
    methods: {
      async load () {
      },
    },
  }
</script>
