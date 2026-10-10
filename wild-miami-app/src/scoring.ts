import { Match, Result, Species } from './types';

export type ScoringConfig = {
  theta: number;
  delta: number;
  possibleFloor: number;
};

export const FIXTURE_SCORING: ScoringConfig = {
  theta: 0.86,
  delta: 0.015,
  possibleFloor: 0.78,
};

export function rankMatches(scores: Match[], speciesOrder: number[]): Match[] {
  const orderIndex = new Map(speciesOrder.map((speciesId, index) => [speciesId, index]));
  return [...scores].sort((a, b) => {
    const scoreDiff = b.score - a.score;
    if (scoreDiff !== 0) return scoreDiff;
    return (orderIndex.get(a.speciesId) ?? Number.MAX_SAFE_INTEGER) - (orderIndex.get(b.speciesId) ?? Number.MAX_SAFE_INTEGER);
  });
}

export function verdictForMatches(matches: Match[], config: ScoringConfig = FIXTURE_SCORING): Result['verdict'] {
  const top = matches[0]?.score ?? Number.NEGATIVE_INFINITY;
  const second = matches[1]?.score ?? Number.NEGATIVE_INFINITY;
  if (top >= config.theta && top - second >= config.delta) return 'likely';
  if (top >= config.possibleFloor) return 'possible';
  return 'unsure';
}

export function scoreToResult(scores: Match[], speciesOrder: number[], config: ScoringConfig = FIXTURE_SCORING): Result {
  const matches = rankMatches(scores, speciesOrder).slice(0, 3);
  return {
    verdict: verdictForMatches(matches, config),
    matches,
  };
}

export function identifyWithFixtureModel(photoUri: string, species: Species[]): Result {
  const speciesOrder = species.map((item) => item.id);
  const hash = stableHash(photoUri || 'demo-fixture');
  const scores = speciesOrder.map((speciesId, index) => ({
    speciesId,
    score: fixtureScore(hash, index),
  }));
  return scoreToResult(scores, speciesOrder);
}

function stableHash(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function fixtureScore(hash: number, index: number): number {
  const shifted = (hash >>> ((index * 7) % 24)) & 0xff;
  return 0.74 + shifted / 1200;
}
