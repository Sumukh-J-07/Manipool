import { matchingConfig, students } from '../data/fixtures';
import { DemoScenario, MatchCandidate, RideRequest } from '../types/domain';

export function windowsOverlap(
  a: string,
  aMinutes: number,
  b: string,
  bMinutes: number,
): boolean {
  const first = Date.parse(a);
  const second = Date.parse(b);
  if (
    !Number.isFinite(first) ||
    !Number.isFinite(second) ||
    !Number.isFinite(aMinutes) ||
    !Number.isFinite(bMinutes) ||
    aMinutes < 0 ||
    bMinutes < 0
  ) {
    return false;
  }
  return Math.abs(first - second) <= (aMinutes + bMinutes) * 60000;
}
export function rankCandidates(
  request: RideRequest,
  candidates: MatchCandidate[],
  capacity = matchingConfig.capacity,
): MatchCandidate[] {
  if (!Number.isInteger(capacity) || capacity < 2) {
    return [];
  }
  const weights = matchingConfig.weights;
  return candidates
    .filter(
      candidate =>
        candidate.student.id !== request.userId &&
        Number.isFinite(candidate.pickupKm) &&
        candidate.pickupKm >= 0 &&
        candidate.pickupKm <= matchingConfig.pickupKm &&
        Number.isFinite(candidate.detourMinutes) &&
        candidate.detourMinutes >= 0 &&
        candidate.detourMinutes <= matchingConfig.detourMinutes &&
        candidate.routeOverlap >= 0.65 &&
        candidate.routeOverlap <= 1 &&
        candidate.reliability >= 0 &&
        candidate.reliability <= 1 &&
        (candidate.destinationId === request.destination.id ||
          candidate.corridor === request.destination.corridor) &&
        windowsOverlap(
          request.departure,
          request.flexibility,
          candidate.departure,
          candidate.flexibility,
        ),
    )
    .map(candidate => ({
      ...candidate,
      score:
        candidate.routeOverlap * weights.route +
        (1 - candidate.detourMinutes / matchingConfig.detourMinutes) *
          weights.detour +
        (1 -
          Math.min(
            Math.abs(
              Date.parse(candidate.departure) - Date.parse(request.departure),
            ) /
              60000 /
              90,
            1,
          )) *
          weights.time +
        (candidate.destinationId === request.destination.id ? 1 : 0.8) *
          weights.destination +
        candidate.reliability * weights.reliability,
    }))
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .filter(
      (candidate, index, all) =>
        all.findIndex(other => other.student.id === candidate.student.id) ===
        index,
    )
    .slice(0, capacity - 1);
}
export interface MatchingService {
  findMatches(request: RideRequest, scenario: DemoScenario): MatchCandidate[];
}
// Fixtures are deliberately relative to the requested journey, not live rider availability.
export const demoMatchingService: MatchingService = {
  findMatches(request, scenario) {
    if (scenario === 'no-match') {
      return [];
    }
    const fixtures = students
      .slice(0, scenario === 'two-riders' ? 1 : 2)
      .map((student, index) => ({
        id: `${request.id}-${student.id}`,
        student: { ...student, area: request.pickup.area },
        departure: new Date(
          Date.parse(request.departure) + index * 10 * 60000,
        ).toISOString(),
        flexibility: 15 as const,
        destinationId: request.destination.id,
        corridor: request.destination.corridor,
        pickupKm: 0.6 + index * 0.4,
        detourMinutes: 3 + index,
        routeOverlap: 0.94 - index * 0.04,
        reliability: 0.8,
        score: 0,
      }));
    return rankCandidates(request, fixtures);
  },
};
