export interface IncidentSummary {
  caseNoteId: number
  incidentType: string
  details: string[]
  confidence?: number
  createdAt?: string
}
