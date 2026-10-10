import * as SQLite from 'expo-sqlite';
import { FIXTURE_INCIDENTS, FIXTURE_SPECIES } from './fixtureData';
import { IncidentOption, Species } from './types';

export type AppDb = SQLite.SQLiteDatabase;

export async function openAppDb(): Promise<AppDb> {
  const db = await SQLite.openDatabaseAsync('wild_miami.db');
  await db.execAsync('PRAGMA foreign_keys = ON;');
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS species (
      id INTEGER PRIMARY KEY,
      common_name TEXT NOT NULL,
      scientific_name TEXT NOT NULL,
      conservation_status TEXT NOT NULL,
      risk TEXT NOT NULL,
      blurb TEXT NOT NULL,
      default_guidance TEXT NOT NULL,
      photo_credit TEXT NOT NULL,
      source_url TEXT NOT NULL,
      verified_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS incident_option (
      species_id INTEGER NOT NULL,
      incident TEXT NOT NULL,
      label TEXT NOT NULL,
      guidance TEXT NOT NULL,
      phone_label TEXT,
      phone_number TEXT,
      PRIMARY KEY (species_id, incident),
      FOREIGN KEY (species_id) REFERENCES species(id) ON DELETE CASCADE
    );
  `);
  await seedFixtureIfEmpty(db);
  await db.execAsync('PRAGMA user_version = 0;');
  return db;
}

async function seedFixtureIfEmpty(db: AppDb): Promise<void> {
  const row = await db.getFirstAsync<{ count: number }>('SELECT COUNT(*) as count FROM species');
  if ((row?.count ?? 0) > 0) return;

  for (const species of FIXTURE_SPECIES) {
    await db.runAsync(
      `INSERT INTO species
        (id, common_name, scientific_name, conservation_status, risk, blurb, default_guidance, photo_credit, source_url, verified_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      species.id,
      species.commonName,
      species.scientificName,
      species.conservationStatus,
      species.risk,
      species.blurb,
      species.defaultGuidance,
      species.photoCredit,
      species.sourceUrl,
      species.verifiedAt,
    );
  }

  for (const option of FIXTURE_INCIDENTS) {
    await db.runAsync(
      `INSERT INTO incident_option
        (species_id, incident, label, guidance, phone_label, phone_number)
       VALUES (?, ?, ?, ?, ?, ?)`,
      option.speciesId,
      option.incident,
      option.label,
      option.guidance,
      option.phoneLabel ?? null,
      option.phoneNumber ?? null,
    );
  }
}

export async function getUserVersion(db: AppDb): Promise<number> {
  const rows = await db.getAllAsync<{ user_version: number }>('PRAGMA user_version;');
  return rows[0]?.user_version ?? 0;
}

export async function getSpecies(db: AppDb): Promise<Species[]> {
  const rows = await db.getAllAsync<{
    id: number;
    common_name: string;
    scientific_name: string;
    conservation_status: string;
    risk: Species['risk'];
    blurb: string;
    default_guidance: string;
    photo_credit: string;
    source_url: string;
    verified_at: string;
  }>('SELECT * FROM species ORDER BY id');

  return rows.map((row) => ({
    id: row.id,
    commonName: row.common_name,
    scientificName: row.scientific_name,
    conservationStatus: row.conservation_status,
    risk: row.risk,
    blurb: row.blurb,
    defaultGuidance: row.default_guidance,
    photoCredit: row.photo_credit,
    sourceUrl: row.source_url,
    verifiedAt: row.verified_at,
  }));
}

export async function getIncidentOptions(db: AppDb, speciesId: number): Promise<IncidentOption[]> {
  const rows = await db.getAllAsync<{
    species_id: number;
    incident: string;
    label: string;
    guidance: string;
    phone_label: string | null;
    phone_number: string | null;
  }>('SELECT * FROM incident_option WHERE species_id = ? ORDER BY incident', speciesId);

  return rows.map((row) => ({
    speciesId: row.species_id,
    incident: row.incident,
    label: row.label,
    guidance: row.guidance,
    phoneLabel: row.phone_label ?? undefined,
    phoneNumber: row.phone_number ?? undefined,
  }));
}
