import { InputSection } from '../components/InputSection'
import { OutputSection } from '../components/OutputSection'
import { HistorySidebar } from '../components/HistorySidebar'
import { JobDetailsCard } from '../components/JobDetailsCard'
import { useAppStore } from '../store/useAppStore'

export function HomePage() {
  const {
    processUrl,
    isLoading,
    error,
    job,
    assets,
    cvText,
    setCvText,
    language,
    setLanguage,
    tone,
    setTone,
    variance,
    setVariance,
    history,
    updateJobCompany
  } = useAppStore()

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <HistorySidebar />
      
      <main className={`flex-1 transition-all duration-300 ${history.length > 0 ? 'lg:ml-80' : ''}`}>
        <section className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-16 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">
            CV Sob Medida
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-white sm:text-5xl">
            Gere materiais de candidatura personalizados a partir de uma única URL
          </h1>
          <p className="text-base text-slate-300 sm:text-lg mb-8">
            Cole o link de uma vaga, valide os dados extraídos e receba currículo, carta de
            apresentação, rede de contatos e dicas práticas — tudo em um único fluxo.
          </p>
          
          <InputSection
            onSubmit={processUrl}
            isLoading={isLoading}
            error={error}
            cvText={cvText}
            onCvChange={setCvText}
            language={language}
            onLanguageChange={setLanguage}
            tone={tone}
            onToneChange={setTone}
            variance={variance}
            onVarianceChange={setVariance}
          />

          {job && <JobDetailsCard job={job} onCompanyUpdate={updateJobCompany} />}

          {assets && <OutputSection assets={assets} />}
          
          <div className="mt-12">
            <p className="text-sm text-slate-500">
              Baseado em LangChain + Gemini · Sem necessidade de cadastro · Histórico local com IndexedDB
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}
