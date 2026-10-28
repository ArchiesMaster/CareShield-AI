export const formatDateTime = (value: string | null, fallback?: string) => {
  const raw = value ?? fallback
  if (!raw) return 'Unknown time'

  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw

  return date.toLocaleString([], {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}
