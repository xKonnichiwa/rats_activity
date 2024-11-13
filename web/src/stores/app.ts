// Utilities
import { defineStore } from 'pinia'
import { TAnnotationResource, TData } from '@/stores/types'
import { http } from '@/shared'

// const generateNumbers = (offset: number, size: number): number[] => {
//   const pool = new Map()
//
//   for (let j = 0; j < size; j++) {
//     const value = offset + Math.random() * 4
//     pool.set(j, value)
//   }
//
//   return Array.from(pool.values())
// }

const generateSeries = (size: number): number[] => {
  const labels = new Set<number>()

  for (let i = 0; i < size; i++) {
    labels.add(i)
  }

  return Array.from(labels)
}

export const useAppStore = defineStore('app',
  {
    state: (): TData => {
      return ({
        labels: [],
        frl: [],
        frr: [],
        ocr: [],
        annotations: {},
      })
    },
    actions: {
      async load (fileKey: string) {
        const signalsResponse = await http.request(`/get-signals/${fileKey}`, {}, {}, {})
        const signalsData = (signalsResponse.data as { signals: Record<'0' | '1' | '2', number[]> })
        this.frl = signalsData.signals['0'].map(s => s += 6)
        this.frr = signalsData.signals['1'].map(s => s += 3)
        this.ocr = signalsData.signals['2']
        this.labels = generateSeries(signalsData.signals['0'].length)

        const annotationsResponse = await http.request(`/get-annotations/${fileKey}`, {}, {}, {})
        this.annotations = (annotationsResponse.data as TAnnotationResource)
      },
    },
  })
