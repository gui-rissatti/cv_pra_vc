export interface Job {
  id: string;
  url: string;
  title: string;
  company: string | null;
  description: string;
  skills: string[];
  createdAt: string; // ISO timestamp
  extractionMetadata?: {
    companyExtractionMethod?: string;
    companyExtractionConfidence?: string;
  };
}

export interface GeneratedAssets {
  jobId: string;
  cv: string;
  coverLetter: string;
  networking: string;
  insights: string;
  matchScore: number; // 0-100
  generatedAt: string; // ISO timestamp
}

export interface ApplicationHistoryEntry {
  id: string;
  jobTitle: string;
  companyName: string | null;
  applicationDate: string; // ISO timestamp
  jobUrl: string;
  generatedAssetsId: string;
}
