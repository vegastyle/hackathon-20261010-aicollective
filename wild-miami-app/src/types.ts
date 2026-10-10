export type Verdict = 'likely' | 'possible' | 'unsure';

export type Match = { speciesId: number; score: number };

export type Result = { verdict: Verdict; matches: Match[] };

export type Species = {
  id: number;
  commonName: string;
  scientificName: string;
  conservationStatus: string;
  risk: 'low' | 'caution' | 'danger';
  blurb: string;
  defaultGuidance: string;
  photoCredit: string;
  sourceUrl: string;
  verifiedAt: string;
};

export type IncidentOption = {
  speciesId: number;
  incident: string;
  label: string;
  guidance: string;
  phoneLabel?: string;
  phoneNumber?: string;
};
