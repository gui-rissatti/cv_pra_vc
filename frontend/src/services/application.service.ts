/**
 * Orquestração de aplicação a uma vaga.
 * Responsável pelo workflow completo: extract → generate → save
 */

import { apiService } from './api'
import { dbService } from './db'
import type { Job, GeneratedAssets } from '../types'

export interface ProcessingOptions {
  language: string
  tone: string
  variance: number
}

export interface ProcessingResult {
  job: Job
  assets: GeneratedAssets
}

/**
 * Service para orquestração de processamento de vagas.
 * Separado do store para reutilização em outros contextos (CLI, testes, scripts).
 */
export class ApplicationService {
  /**
   * Processa uma vaga completa: extração → geração → salvamento.
   *
   * @param url URL da vaga
   * @param cvText Texto do CV
   * @param options Opções de geração (idioma, tom, variância)
   * @returns Job + Assets gerados
   * @throws Error se alguma etapa falhar
   */
  async processJobUrl(
    url: string,
    cvText: string,
    options: ProcessingOptions = {
      language: 'auto',
      tone: 'professional',
      variance: 3,
    },
  ): Promise<ProcessingResult> {
    // Step 1: Extract Job Details
    const job = await apiService.extractJobDetails(url)

    // Step 2: Generate Materials
    const assets = await apiService.generateMaterials(job, cvText, options)

    // Step 3: Save to History
    await dbService.saveApplication(job, assets)

    return { job, assets }
  }

  /**
   * Salva uma aplicação manualmente (sem gerar).
   */
  async saveApplication(job: Job, assets: GeneratedAssets): Promise<void> {
    await dbService.saveApplication(job, assets)
  }
}

// Singleton
export const applicationService = new ApplicationService()
