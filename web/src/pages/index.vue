<template>
  <v-container class="px-0" />

</template>
<script>

  export default {
    data: () => ({
    }),
    created () {
      this.$router.push(`/video`)
    },
    methods: {
      rowClick (item, row) {
        this.$router.push(`/video/${row.item.id}`)
      },
      async loadItems ({ page, itemsPerPage }) {
      },
    },
  }
</script>
