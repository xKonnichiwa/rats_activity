import { TAnnotationChart, TAnnotationRaw, TAnnotationResource } from '@/stores/types'

export class AnnotationFactory {
  private colors: Record<'swd' | 'ds' | 'is', { start: string, end: string }> = {
    swd: { start: '#f87171', end: '#fca5a5' },
    is: { start: '#facc15', end: '#fde047' },
    ds: { start: '#a78bfa', end: '#c4b5fd' },

  }

  make (original: TAnnotationResource): Record<string, TAnnotationChart> {
    const annotations = []

    for (const name in original) {
      for (const raw of original[name]) {
        annotations.push(...this.makeFromOne(name, raw))
      }
    }

    const result: Record<string, TAnnotationChart> = {}
    for (let i = 0; i < annotations.length; i++) {
      result['line' + i] = annotations[i]
    }

    return result
  }

  private makeFromOne (key: string, annotation: TAnnotationRaw): TAnnotationChart[] {
    switch (key) {
      case 'swd':
      case 'ds':
      case 'is':
        return [
          this.create(key + '1', annotation.start, this.colors[key].start),
          this.create(key + '2', annotation.end, this.colors[key].end),
        ]
    }
    return []
  }

  private create (name: string, pos: number, color: string): TAnnotationChart {
    return {
      type: 'line',
      xMin: pos * 400,
      xMax: pos * 400,
      borderDash: [12],
      borderDashOffset: 4,
      label: {
        display: true,
        content: name,
        position: 'start',
      },
      borderColor: color,
      borderWidth: 2,
    }
  }
}
