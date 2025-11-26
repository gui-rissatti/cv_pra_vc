import { useState } from 'react'
import { Building2, Briefcase, CheckCircle2, XCircle, Edit2, Save, X } from 'lucide-react'
import type { Job } from '../types'

interface JobDetailsCardProps {
  job: Job
  onCompanyUpdate: (newCompany: string) => void
}

export function JobDetailsCard({ job, onCompanyUpdate }: JobDetailsCardProps) {
  const [isEditingCompany, setIsEditingCompany] = useState(false)
  const [editedCompany, setEditedCompany] = useState(job.company || '')

  const handleSaveCompany = () => {
    if (editedCompany.trim()) {
      onCompanyUpdate(editedCompany.trim())
      setIsEditingCompany(false)
    }
  }

  const handleCancelEdit = () => {
    setEditedCompany(job.company || '')
    setIsEditingCompany(false)
  }

  const getExtractionInfo = () => {
    if (!job.extractionMetadata) return null

    const method = job.extractionMetadata.companyExtractionMethod
    const confidence = job.extractionMetadata.companyExtractionConfidence

    if (!method || method === 'scraper') return null

    const methodLabels: Record<string, string> = {
      email: 'Extraído de email',
      context: 'Extraído do contexto',
      url: 'Extraído da URL',
      meta_tag: 'Extraído de meta tag',
      domain: 'Extraído do domínio',
      not_found: 'Não encontrado'
    }

    const confidenceColors: Record<string, string> = {
      high: 'text-emerald-400',
      medium: 'text-yellow-400',
      low: 'text-orange-400'
    }

    return {
      label: methodLabels[method] || 'Extração automática',
      color: confidence ? confidenceColors[confidence] || 'text-slate-400' : 'text-slate-400',
      confidence: confidence || 'low'
    }
  }

  const extractionInfo = getExtractionInfo()

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
      <div className="bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 px-6 py-4 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <CheckCircle2 size={20} className="text-emerald-400" />
          Dados da Vaga Extraídos
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Revise as informações antes de gerar os materiais. Você pode editar o nome da empresa se necessário.
        </p>
      </div>

      <div className="p-6 space-y-4">
        {/* Job Title */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-2">
            <Briefcase size={16} />
            Título da Vaga
          </label>
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
            <p className="text-slate-200 font-medium">{job.title}</p>
          </div>
        </div>

        {/* Company Name - Editable */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-2">
            <Building2 size={16} />
            Empresa
            {extractionInfo && (
              <span className={`text-xs ${extractionInfo.color} ml-2`}>
                ({extractionInfo.label} - {extractionInfo.confidence})
              </span>
            )}
          </label>

          {isEditingCompany ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={editedCompany}
                onChange={(e) => setEditedCompany(e.target.value)}
                className="flex-1 bg-slate-950 border border-emerald-500/50 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
                placeholder="Digite o nome da empresa"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveCompany()
                  if (e.key === 'Escape') handleCancelEdit()
                }}
              />
              <button
                onClick={handleSaveCompany}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-lg transition-colors flex items-center gap-2 font-medium"
                title="Salvar"
              >
                <Save size={16} />
                Salvar
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors flex items-center gap-2"
                title="Cancelar"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 flex items-center justify-between group">
              {job.company ? (
                <p className="text-slate-200 font-medium">{job.company}</p>
              ) : (
                <p className="text-slate-500 italic flex items-center gap-2">
                  <XCircle size={16} className="text-orange-400" />
                  Nome da empresa não identificado - clique para adicionar
                </p>
              )}
              <button
                onClick={() => setIsEditingCompany(true)}
                className="ml-4 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg transition-all opacity-0 group-hover:opacity-100 flex items-center gap-2 text-sm"
              >
                <Edit2 size={14} />
                Editar
              </button>
            </div>
          )}
        </div>

        {/* Skills */}
        {job.skills && job.skills.length > 0 && (
          <div>
            <label className="text-sm font-medium text-slate-400 mb-2 block">
              Habilidades Identificadas ({job.skills.length})
            </label>
            <div className="flex flex-wrap gap-2">
              {job.skills.map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Description Preview */}
        <div>
          <label className="text-sm font-medium text-slate-400 mb-2 block">
            Descrição (preview)
          </label>
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 max-h-32 overflow-y-auto">
            <p className="text-slate-400 text-sm line-clamp-6">
              {job.description.length > 300
                ? `${job.description.substring(0, 300)}...`
                : job.description}
            </p>
          </div>
        </div>

        {/* Extraction Metadata Info */}
        {job.company && extractionInfo && extractionInfo.confidence !== 'high' && (
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <p className="text-sm text-yellow-400">
              <strong>💡 Dica:</strong> O nome da empresa foi extraído automaticamente por {extractionInfo.label}.
              {extractionInfo.confidence === 'low' && ' A confiança é baixa, recomendamos revisar.'}
              {' '}Você pode editá-lo clicando no botão "Editar" acima.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
