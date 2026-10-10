import { IncidentOption, Species } from './types';

export const SAFETY_FOOTER = "Watch from a distance. Don’t feed, touch or chase.";

export const FIXTURE_SPECIES: Species[] = [
  {
    id: 1,
    commonName: 'American alligator',
    scientificName: 'Alligator mississippiensis',
    conservationStatus: 'FIXTURE - verify',
    risk: 'danger',
    blurb: 'Large freshwater reptile. Identification and status text are fixture placeholders.',
    defaultGuidance: `Keep extra distance near water and supervise pets. ${SAFETY_FOOTER}`,
    photoCredit: 'FIXTURE DATA - no submitted photo credit',
    sourceUrl: 'FIXTURE DATA - not verified',
    verifiedAt: 'FIXTURE DATA',
  },
  {
    id: 2,
    commonName: 'Green iguana',
    scientificName: 'Iguana iguana',
    conservationStatus: 'FIXTURE - verify',
    risk: 'caution',
    blurb: 'Large lizard often seen basking. Identification and status text are fixture placeholders.',
    defaultGuidance: `Do not handle or corner it. ${SAFETY_FOOTER}`,
    photoCredit: 'FIXTURE DATA - no submitted photo credit',
    sourceUrl: 'FIXTURE DATA - not verified',
    verifiedAt: 'FIXTURE DATA',
  },
  {
    id: 3,
    commonName: 'Raccoon',
    scientificName: 'Procyon lotor',
    conservationStatus: 'FIXTURE - verify',
    risk: 'caution',
    blurb: 'Masked mammal active around neighborhoods. Identification and status text are fixture placeholders.',
    defaultGuidance: `Secure trash and keep pets away. ${SAFETY_FOOTER}`,
    photoCredit: 'FIXTURE DATA - no submitted photo credit',
    sourceUrl: 'FIXTURE DATA - not verified',
    verifiedAt: 'FIXTURE DATA',
  },
];

export const FIXTURE_INCIDENTS: IncidentOption[] = [
  {
    speciesId: 1,
    incident: 'posing_threat',
    label: 'Animal may pose a threat',
    guidance: 'Fixture option. In the real pack this must be reviewed against FWC guidance before release.',
    phoneLabel: 'Gator hotline (fixture)',
    phoneNumber: '866-392-4286',
  },
  {
    speciesId: 1,
    incident: 'injured_or_dead',
    label: 'Injured or dead animal',
    guidance: 'Fixture option. In the real pack this must be verified before release.',
    phoneLabel: 'Wildlife Alert (fixture)',
    phoneNumber: '888-404-3922',
  },
  {
    speciesId: 2,
    incident: 'injured_or_dead',
    label: 'Injured or dead animal',
    guidance: 'Fixture option. Do not capture or move the animal; use reviewed guidance in the real pack.',
  },
  {
    speciesId: 3,
    incident: 'injured_or_dead',
    label: 'Injured or dead animal',
    guidance: 'Fixture option. Avoid contact; use reviewed local guidance in the real pack.',
  },
];
