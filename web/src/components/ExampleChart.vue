<template>
  <div class="d-flex ga-2 mb-2">
    <v-btn
      icon="mdi-eye"
      :ripple="false"
      slim
      variant="text"
      @click="showChart"
    />
    <v-divider v-if="display" vertical />
    <v-btn
      v-if="display"
      icon="mdi-cached"
      :ripple="false"
      slim
      variant="text"
      @click="() => store.load()"
    />
    <v-divider v-if="display" vertical />
    <v-btn
      v-if="display"
      icon="mdi-arrow-expand"
      :ripple="false"
      slim
      variant="text"
      @click="resetZoom"
    />
    <v-divider v-if="display" vertical />
    <v-btn
      v-if="display"
      icon="mdi-unfold-less-horizontal"
      :ripple="false"
      slim
      variant="text"
      @click="minusZoomY"
    />
    <v-btn
      v-if="display"
      icon="mdi-unfold-more-horizontal"
      :ripple="false"
      slim
      variant="text"
      @click="plusZoomY"
    />
    <v-btn
      v-if="display"
      icon="mdi-unfold-less-vertical"
      :ripple="false"
      slim
      variant="text"
      @click="minusZoomX"
    />
    <v-btn
      v-if="display"
      icon="mdi-unfold-more-vertical"
      :ripple="false"
      slim
      variant="text"
      @click="plusZoomX"
    />
  </div>
  <v-card v-show="display" class="px-4 py-4 mb-4">
    <line-js
      id="my-chart-id"
      ref="charts"
      class="cursor-grab"
      :data="chartData"
      :options="chartOptions"
    />
  </v-card>
</template>

<script>
  import { Line as LineJs } from 'vue-chartjs'
  import ChartJSDragDataPlugin from 'chartjs-plugin-dragdata'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import annotationPlugin from 'chartjs-plugin-annotation'
  import {
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip,
  } from 'chart.js'
  import { useAppStore } from '@/stores/app'
  import { AnnotationFactory } from '@/stores/adapters'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    zoomPlugin,
    ChartJSDragDataPlugin,
    annotationPlugin
  )

  const renderOnHoverCirclesTrail = false
  const factory = new AnnotationFactory()
  const drawDragMarker = e => {
    console.log(e)
  }
  const defaultDatasetOption = {
    tension: 0.4,
    borderWidth: 1,
    pointHitRadius: 0, // 3
    pointRadius: 0,
    pointBorderWidth: 0, // 3
    pointHoverRadius: 0, // 3
    pointHoverBorderWidth: 0, // 3
    pointStyle: 'rectRounded',
  }
  export default {
    name: 'BarChart',
    components: { LineJs },
    data () {
      const store = useAppStore()
      return {
        store,
        display: false,
      }
    },
    computed: {
      fileKey () {
        return this.$route.params.id
      },
      chartData () {
        return {
          labels: this.store.labels, // x
          datasets: [ // y
            {
              label: 'FrL',
              data: this.store.frl,
              backgroundColor: '#fca5a5',
              borderColor: '#fca5a5',
              ...defaultDatasetOption,
            },
            {
              label: 'FrR',
              data: this.store.frr,
              backgroundColor: '#5eead4',
              borderColor: '#5eead4',
              ...defaultDatasetOption,

            },
            {
              label: 'OcR',
              data: this.store.ocr,
              backgroundColor: '#fcd34d',
              borderColor: '#fcd34d',
              ...defaultDatasetOption,
            },
          ],
        }
      },
      chartOptions () {
        return {
          normalized: true,
          responsive: true,
          animation: false,
          spanGaps: true,
          transitions: {
            zoom: {
              animation: {
                duration: 0,
              },
            },
          },
          plugins: {
            zoom: {
              limits: {
                x: { minRange: 3 },
                y: { min: -2, max: 8, minRange: 2 },
              },
              pan: {
                enabled: true,
                mode: 'xy',
              },
              zoom: {
                wheel: {
                  enabled: true,
                },
                pinch: {
                  enabled: true,
                },
                drag: {
                  enabled: true,
                },
                mode: 'xy',
              },
            },
            dragData: {
              dragX: false,
              dragY: false,
              round: 2,
              showTooltip: true,
              onDragStart (e) {
                if (renderOnHoverCirclesTrail) drawDragMarker(e)
              },
              onDrag (...args) {
                const [e] = args
                if (e.target?.style) {
                  e.target.style.cursor = 'grabbing'
                }

                if (renderOnHoverCirclesTrail) drawDragMarker(e)
              },
              onDragEnd (e) {
                if (e.target?.style) {
                  e.target.style.cursor = 'default'
                }

                if (renderOnHoverCirclesTrail) drawDragMarker(e)
              },
            },
            annotation: {
              annotations: factory.make(this.store.annotations),
            },
          },
        }
      },
    },
    created () {
      this.store.load(this.fileKey)
    },
    methods: {
      showChart () {
        if (!this.$refs.charts) {
          console.log('skip')
          return
        }

        if (this.display) {
          this.display = false
          return
        }

        // this.randomize()
        this.$refs.charts?.chart.zoomScale('x', { min: 380000, max: 400000 }, 'default')
        this.$refs.charts?.chart.zoomScale('y', { min: -2, max: 8 }, 'default')
        this.display = true
      },
      resetZoom () {
        this.$refs.charts?.chart.resetZoom()
      },
      plusZoomY () {
        this.$refs.charts?.chart.zoom({ y: 1.1 })
      },
      minusZoomY () {
        this.$refs.charts?.chart.zoom({ y: 0.9 })
      },
      plusZoomX () {
        this.$refs.charts?.chart.zoom({ x: 1.1 })
      },
      minusZoomX () {
        this.$refs.charts?.chart.zoom({ x: 0.9 })
      },
      prevZoom () {
        this.$refs.charts?.chart.pan({ x: 1 }, undefined, 'default')
      },
      nextZoom () {
        this.$refs.charts?.chart.pan({ x: -1 }, undefined, 'default')
      },
      randomize () {
        // const size = 6 * 60 * 60 * 400
        const size = 10 * 60
        const newChartData = this.chartData

        const labels = new Set()
        for (let i = 0; i < size; i++) {
          labels.add(i)
        }
        newChartData.labels = Array.from(labels)

        for (let i = 0; i < newChartData.datasets.length; i++) {
          const pool = new Map()
          for (let j = 0; j < size; j++) {
            const value = i * 200 + Math.random() * 4
            pool.set(j, value)
          }
          newChartData.datasets[i].data = Array.from(pool.values())
        }

        this.chartData = newChartData

        console.log(this.$refs.charts?.chart)
      },
    },
  }
</script>
