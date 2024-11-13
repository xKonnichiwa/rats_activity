export type TAnnotationRaw = {
  start: number,
  end: number,
}

export type TAnnotationChart = {
  type: 'line',
  xMin: number,
  xMax: number,
  borderDash: number[],
  borderDashOffset: number,
  label: {
    display: true,
    content: string,
    position: 'start',
  },
  borderColor: string,
  borderWidth: number,
}
export type TAnnotationResource = Record<string, TAnnotationRaw[]>

export type TData = {
  labels: number[],
  frl: number[],
  frr: number[],
  ocr: number[],
  annotations: TAnnotationResource,
}
