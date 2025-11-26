import { create } from 'zustand'
import type { Job, GeneratedAssets, ApplicationHistoryEntry } from '../types'
import { applicationService } from '../services/application.service'
import { dbService } from '../services/db'

interface AppState {
  job: Job | null
  assets: GeneratedAssets | null
  cvText: string
  language: string
  tone: string
  variance: number
  isLoading: boolean
  error: string | null
  history: ApplicationHistoryEntry[]

  setCvText: (text: string) => void
  setLanguage: (language: string) => void
  setTone: (tone: string) => void
  setVariance: (variance: number) => void
  updateJobCompany: (newCompany: string) => Promise<void>
  processUrl: (url: string) => Promise<void>
  reset: () => void
  loadHistory: () => Promise<void>
  loadApplication: (id: string) => Promise<void>
  deleteApplication: (id: string) => Promise<void>
  exportHistory: () => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  job: null,
  assets: null,
  cvText: '', 
  language: 'auto',
  tone: 'professional',
  variance: 3,
  isLoading: false,
  error: null,
  history: [],

  setCvText: (text) => set({ cvText: text }),
  setLanguage: (language) => set({ language }),
  setTone: (tone) => set({ tone }),
  setVariance: (variance) => set({ variance }),

  updateJobCompany: async (newCompany: string) => {
    const { job } = get()
    if (!job) return

    // Update job with new company name
    const updatedJob = { ...job, company: newCompany }
    set({ job: updatedJob })

    // Update in IndexedDB if the job has been saved
    try {
      const app = await dbService.getApplication(job.id)
      if (app) {
        await dbService.saveApplication({
          ...app,
          job: updatedJob,
          companyName: newCompany,
        })
        await get().loadHistory()
      }
    } catch (error) {
      console.error('Failed to update company in database:', error)
    }
  },

  processUrl: async (url: string) => {
    const { cvText, language, tone, variance } = get()

    if (!cvText.trim()) {
      set({ error: 'Por favor, insira o texto do seu currículo antes de continuar.' })
      return
    }

    set({ isLoading: true, error: null, job: null, assets: null })

    try {
      // Use the application service for orchestration
      const result = await applicationService.processJobUrl(url, cvText, {
        language,
        tone,
        variance,
      })

      set({ job: result.job, assets: result.assets })
      await get().loadHistory()
    } catch (err: any) {
      console.error(err)
      set({ error: err.response?.data?.message || 'Ocorreu um erro ao processar sua solicitação.' })
    } finally {
      set({ isLoading: false })
    }
  },

  reset: () => set({ job: null, assets: null, error: null, isLoading: false }),

  loadHistory: async () => {
    try {
      const history = await dbService.getAllApplications()
      set({ history })
    } catch (error) {
      console.error('Failed to load history:', error)
    }
  },

  loadApplication: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const app = await dbService.getApplication(id)
      if (app) {
        set({ job: app.job, assets: app.assets })
      } else {
        set({ error: 'Aplicação não encontrada.' })
      }
    } catch (error) {
      set({ error: 'Erro ao carregar aplicação.' })
    } finally {
      set({ isLoading: false })
    }
  },

  deleteApplication: async (id: string) => {
    try {
      await dbService.deleteApplication(id)
      await get().loadHistory()
    } catch (error) {
      console.error('Failed to delete application:', error)
    }
  },

  exportHistory: async () => {
    try {
      const apps = await dbService.getAllFullApplications()
      const blob = new Blob([JSON.stringify(apps, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cv-sob-medida-history-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export history:', error)
    }
  }
}))
