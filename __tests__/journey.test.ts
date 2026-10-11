import { demoProfile, matchingConfig } from '../src/data/fixtures';
import {
  canTransition,
  departureFromDraft,
  splitFare,
  validateDraft,
} from '../src/services/journey';
import {
  demoMatchingService,
  rankCandidates,
  windowsOverlap,
} from '../src/services/matching';
import { appReducer, initialDraft, initialState } from '../src/state/reducer';
import { AppState, DemoScenario } from '../src/types/domain';
const now = '2026-10-11T12:00:00.000Z';
function searched(scenario: DemoScenario = 'normal'): AppState {
  let state = initialState();
  state = appReducer(state, { type: 'SIGN_IN', profile: demoProfile });
  state = appReducer(state, {
    type: 'DRAFT',
    patch: initialDraft(new Date(now)),
  });
  state = appReducer(state, { type: 'SCENARIO', scenario });
  return appReducer(state, { type: 'SEARCH', id: 'ride-1', now });
}
function formed(scenario: DemoScenario = 'normal'): AppState {
  let state = searched(scenario);
  state = appReducer(state, { type: 'SEARCH_DONE', rideId: 'ride-1', now });
  state = appReducer(state, { type: 'JOIN', rideId: 'ride-1', now });
  return appReducer(state, { type: 'ACCEPT_DEMO', rideId: 'ride-1', now });
}
describe('request validation', () => {
  const draft = initialDraft(new Date(now));
  it('accepts a future journey', () =>
    expect(validateDraft(draft, Date.parse(now))).toBeUndefined());
  it('rejects invalid calendar dates, hours, missing or identical locations, and past departures', () => {
    expect(
      departureFromDraft({ ...draft, date: '2026-02-30' }),
    ).toBeUndefined();
    expect(departureFromDraft({ ...draft, time: '24:01' })).toBeUndefined();
    expect(
      validateDraft({ ...draft, pickupId: '' }, Date.parse(now)),
    ).toBeDefined();
    expect(
      validateDraft(
        { ...draft, destinationId: draft.pickupId },
        Date.parse(now),
      ),
    ).toBeDefined();
    expect(
      validateDraft({ ...draft, date: '2020-01-01' }, Date.parse(now)),
    ).toBeDefined();
  });
});
describe('matching and money', () => {
  it('matches overlapping windows across midnight and rejects invalid times', () => {
    expect(
      windowsOverlap('2026-10-11T23:55:00Z', 15, '2026-10-12T00:05:00Z', 0),
    ).toBe(true);
    expect(
      windowsOverlap('2026-10-11T23:55:00Z', 0, '2026-10-12T00:05:00Z', 0),
    ).toBe(false);
    expect(windowsOverlap('bad', 15, now, 30)).toBe(false);
    expect(windowsOverlap(now, -1, now, 30)).toBe(false);
  });
  it('uses configurable illustrative weights that sum to 100%', () =>
    expect(
      Object.values(matchingConfig.weights).reduce((a, b) => a + b, 0),
    ).toBeCloseTo(1));
  it('is deterministic and filters detour, pickup, destination, route and capacity', () => {
    const request = searched().rides[0];
    const matches = demoMatchingService.findMatches(request, 'normal');
    expect(matches).toEqual(demoMatchingService.findMatches(request, 'normal'));
    expect(matches).toHaveLength(2);
    const first = matches[0];
    expect(
      rankCandidates(request, [{ ...first, detourMinutes: 99 }]),
    ).toHaveLength(0);
    expect(rankCandidates(request, [{ ...first, pickupKm: 20 }])).toHaveLength(
      0,
    );
    expect(
      rankCandidates(request, [{ ...first, routeOverlap: 0.2 }]),
    ).toHaveLength(0);
    expect(
      rankCandidates(request, [
        { ...first, destinationId: 'other', corridor: 'other' },
      ]),
    ).toHaveLength(0);
    expect(rankCandidates(request, matches, 2)).toHaveLength(1);
    expect(rankCandidates(request, matches, 0)).toHaveLength(0);
    expect(rankCandidates(request, [first, first])).toHaveLength(1);
  });
  it('splits money exactly with a deterministic remainder and rejects invalid inputs', () => {
    expect(splitFare(84000, 3)).toEqual([28000, 28000, 28000]);
    expect(splitFare(62000, 2)).toEqual([31000, 31000]);
    const splits = splitFare(100, 3);
    expect(splits).toEqual([34, 33, 33]);
    expect(splits.reduce((a, b) => a + b, 0)).toBe(100);
    expect(() => splitFare(100, 0)).toThrow();
    expect(() => splitFare(-10, 2)).toThrow();
    expect(() => splitFare(2.5, 2)).toThrow();
  });
});
describe('central ride lifecycle', () => {
  it('prevents impossible transitions and duplicate active requests', () => {
    expect(canTransition('MATCH_FOUND', 'COMPLETED')).toBe(false);
    expect(canTransition('COMPLETED', 'SEARCHING')).toBe(false);
    let state = searched();
    state = appReducer(state, { type: 'SEARCH', id: 'duplicate', now });
    expect(state.rides).toHaveLength(1);
    expect(state.error).toBeDefined();
    state = appReducer(state, { type: 'COMPLETE', rideId: 'ride-1', now });
    expect(state.rides[0].status).toBe('SEARCHING');
  });
  it('requires mutual acceptance, then creates a single group', () => {
    let state = searched();
    state = appReducer(state, { type: 'SEARCH_DONE', rideId: 'ride-1', now });
    expect(state.groups).toHaveLength(0);
    state = appReducer(state, { type: 'JOIN', rideId: 'ride-1', now });
    expect(state.rides[0].status).toBe('WAITING_FOR_ACCEPTANCE');
    expect(state.groups).toHaveLength(0);
    state = appReducer(state, { type: 'ACCEPT_DEMO', rideId: 'ride-1', now });
    expect(state.groups[0].members).toHaveLength(3);
    state = appReducer(state, { type: 'ACCEPT_DEMO', rideId: 'ride-1', now });
    expect(state.groups).toHaveLength(1);
  });
  it('rejects insufficient vehicle capacity and completes the full journey', () => {
    let state = formed();
    state = appReducer(state, {
      type: 'BOOK',
      rideId: 'ride-1',
      optionId: 'auto',
      now,
    });
    expect(state.rides[0].status).toBe('GROUP_FORMED');
    expect(state.error).toBeDefined();
    state = appReducer(state, {
      type: 'BOOK',
      rideId: 'ride-1',
      optionId: 'cab',
      now,
    });
    expect(state.rides[0].status).toBe('RIDE_BOOKED');
    state = appReducer(state, { type: 'START', rideId: 'ride-1', now });
    expect(state.groups[0].status).toBe('IN_PROGRESS');
    state = appReducer(state, { type: 'COMPLETE', rideId: 'ride-1', now });
    expect(state.groups[0].status).toBe('COMPLETED');
    expect(state.rides[0].status).toBe('COMPLETED');
    const messages = state.groups[0].messages.length;
    state = appReducer(state, {
      type: 'MESSAGE',
      rideId: 'ride-1',
      text: 'late message',
      id: 'msg',
      now,
    });
    expect(state.groups[0].messages).toHaveLength(messages);
  });
  it('allows auto for a two-person group', () => {
    const state = appReducer(formed('two-riders'), {
      type: 'BOOK',
      rideId: 'ride-1',
      optionId: 'auto',
      now,
    });
    expect(state.groups[0].booking?.option.id).toBe('auto');
  });
  it('retains the remaining trip and recalculates split after departure of the user', () => {
    let state = appReducer(formed(), {
      type: 'BOOK',
      rideId: 'ride-1',
      optionId: 'cab',
      now,
    });
    state = appReducer(state, { type: 'LEAVE', rideId: 'ride-1', now });
    expect(state.rides[0].status).toBe('CANCELLED');
    expect(state.groups[0].members).toHaveLength(2);
    expect(state.groups[0].status).toBe('RIDE_BOOKED');
    expect(state.groups[0].booking).toBeDefined();
    expect(
      splitFare(
        state.groups[0].booking!.option.farePaise,
        state.groups[0].members.length,
      ),
    ).toEqual([42000, 42000]);
  });
  it('retries a no-match using the same request, then recovers with a sample match', () => {
    let state = searched('no-match');
    state = appReducer(state, { type: 'SEARCH_DONE', rideId: 'ride-1', now });
    expect(state.rides[0].status).toBe('NO_MATCH');
    state = appReducer(state, {
      type: 'REMATCH',
      rideId: 'ride-1',
      flexibility: 45,
    });
    state = appReducer(state, { type: 'SCENARIO', scenario: 'normal' });
    state = appReducer(state, { type: 'SEARCH_DONE', rideId: 'ride-1', now });
    expect(state.rides).toHaveLength(1);
    expect(state.rides[0].status).toBe('MATCH_FOUND');
  });
  it('expires delayed searches and ignores repeated search completion', () => {
    const state = appReducer(searched(), {
      type: 'SEARCH_DONE',
      rideId: 'ride-1',
      now: '2030-01-01T00:00:00Z',
    });
    expect(state.rides[0].status).toBe('EXPIRED');
    expect(
      appReducer(state, { type: 'SEARCH_DONE', rideId: 'ride-1', now }),
    ).toEqual(state);
  });
  it('synchronises pickup changes, departure changes and messages without duplicates', () => {
    let state = formed();
    state = appReducer(state, {
      type: 'PICKUP',
      rideId: 'ride-1',
      mode: 'sequential',
      now,
    });
    expect(state.groups[0].pickupMode).toBe('sequential');
    const departure = Date.parse(state.rides[0].departure);
    state = appReducer(state, { type: 'DELAY', rideId: 'ride-1', now });
    expect(Date.parse(state.rides[0].departure)).toBe(departure + 600000);
    const action = {
      type: 'MESSAGE' as const,
      rideId: 'ride-1',
      text: '  arrived  ',
      id: 'message-1',
      now,
    };
    state = appReducer(state, action);
    const count = state.groups[0].messages.length;
    state = appReducer(state, action);
    expect(state.groups[0].messages).toHaveLength(count);
    expect(state.groups[0].messages.at(-1)?.text).toBe('arrived');
    state = appReducer(state, { ...action, id: 'empty', text: ' ' });
    expect(state.error).toBeDefined();
  });
  it('keeps reports local and resets journeys while preserving the demo identity', () => {
    let state = formed();
    state = appReducer(state, {
      type: 'REPORT',
      text: 'Pickup issue',
      id: 'report-1',
      rideId: 'ride-1',
      now,
    });
    expect(state.reports).toHaveLength(1);
    state = appReducer(state, { type: 'RESET' });
    expect(state.rides).toHaveLength(0);
    expect(state.groups).toHaveLength(0);
    expect(state.reports).toHaveLength(0);
    expect(state.signedIn).toBe(true);
    expect(state.profile).toEqual(demoProfile);
  });
});
