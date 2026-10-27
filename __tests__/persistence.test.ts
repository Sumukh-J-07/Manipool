import { persistence } from '../src/services/storage';
import { appReducer, initialState } from '../src/state/reducer';
import { AppState, CarpoolGroup, RideRequest } from '../src/types/domain';

describe('Local Persistence & App Restart Journey Recovery', () => {
  beforeEach(async () => {
    await persistence.clearAppState();
    await persistence.clearToken();
  });

  afterEach(async () => {
    await persistence.clearAppState();
    await persistence.clearToken();
  });

  test('persists and restores student profile, saved places, and session token', async () => {
    const customState: AppState = {
      ...initialState(),
      signedIn: true,
      profile: {
        id: 'student-kkrish-1',
        name: 'Kkrish Verma',
        email: 'kkrish.verma@learner.manipal.edu',
        area: 'MAHE Campus',
      },
      savedPlaces: ['campus', 'airport', 'yelahanka'],
      token: 'jwt-token-xyz-123',
    };

    // Save state
    await persistence.saveAppState(customState);

    // Simulate closing and reopening the app: load state from persistence
    const loaded = await persistence.loadAppState();
    expect(loaded).not.toBeNull();
    expect(loaded?.signedIn).toBe(true);
    expect(loaded?.profile?.name).toBe('Kkrish Verma');
    expect(loaded?.profile?.email).toBe('kkrish.verma@learner.manipal.edu');
    expect(loaded?.savedPlaces).toEqual(['campus', 'airport', 'yelahanka']);
    expect(loaded?.token).toBe('jwt-token-xyz-123');
  });

  test('active journey and carpool group survive simulated app restart', async () => {
    const activeRide: RideRequest = {
      id: 'ride-99',
      userId: 'student-kkrish-1',
      pickup: {
        id: 'campus',
        name: 'MAHE Bengaluru Campus',
        area: 'Govindapura, Yelahanka',
        kind: 'campus',
        corridor: 'campus',
      },
      destination: {
        id: 'airport',
        name: 'Kempegowda International Airport (BLR)',
        area: 'Devanahalli',
        kind: 'airport',
        corridor: 'airport',
      },
      departure: '2026-10-28T18:45:00.000Z',
      flexibility: 30,
      createdAt: '2026-10-27T12:00:00.000Z',
      status: 'RIDE_BOOKED',
      matches: [],
      groupId: 'grp-77',
    };

    const activeGroup: CarpoolGroup = {
      id: 'grp-77',
      rideId: 'ride-99',
      pickupMode: 'sequential',
      status: 'RIDE_BOOKED',
      members: [
        {
          id: 'student-kkrish-1',
          name: 'Kkrish Verma',
          email: 'kkrish.verma@learner.manipal.edu',
          area: 'MAHE Campus',
        },
        {
          id: 'student-ananya-2',
          name: 'Ananya Sharma',
          email: 'ananya.sharma@learner.manipal.edu',
          area: 'Campus South Gate',
        },
      ],
      messages: [
        {
          id: 'msg-1',
          senderId: 'student-kkrish-1',
          sender: 'Kkrish Verma',
          text: 'Shared cab booked via Uber.',
          timestamp: '2026-10-27T12:05:00.000Z',
          system: false,
        },
      ],
      booking: {
        option: {
          id: 'cab',
          name: 'Shared Cab',
          capacity: 4,
          farePaise: 84000,
        },
        confirmedAt: '2026-10-27T12:04:00.000Z',
      },
    };

    const stateBeforeRestart: AppState = {
      ...initialState(),
      signedIn: true,
      profile: {
        id: 'student-kkrish-1',
        name: 'Kkrish Verma',
        email: 'kkrish.verma@learner.manipal.edu',
        area: 'MAHE Campus',
      },
      rides: [activeRide],
      groups: [activeGroup],
    };

    // Save state before app process termination
    await persistence.saveAppState(stateBeforeRestart);

    // App restarts: fresh initial state
    const cleanAppLaunchState = initialState();
    expect(cleanAppLaunchState.rides).toHaveLength(0);
    expect(cleanAppLaunchState.groups).toHaveLength(0);

    // App rehydrates from storage
    const restoredSnapshot = await persistence.loadAppState();
    expect(restoredSnapshot).not.toBeNull();

    // Reducer applies HYDRATE action
    const recoveredState = appReducer(cleanAppLaunchState, {
      type: 'HYDRATE',
      payload: restoredSnapshot!,
    });

    // Verification evidence:
    // 1. Journey survived app restart
    expect(recoveredState.signedIn).toBe(true);
    expect(recoveredState.rides).toHaveLength(1);
    expect(recoveredState.rides[0].id).toBe('ride-99');
    expect(recoveredState.rides[0].status).toBe('RIDE_BOOKED');

    // 2. Group details, members, and messages recovered
    expect(recoveredState.groups).toHaveLength(1);
    expect(recoveredState.groups[0].id).toBe('grp-77');
    expect(recoveredState.groups[0].pickupMode).toBe('sequential');
    expect(recoveredState.groups[0].members).toHaveLength(2);
    expect(recoveredState.groups[0].messages).toHaveLength(1);
    expect(recoveredState.groups[0].booking?.option.farePaise).toBe(84000);
  });

  test('safely handles corrupted storage data without crashing', async () => {
    // Write corrupted JSON to storage
    (persistence as any).memoryStore?.set('@manipool_persisted_state_v1', '{invalid-json');
    if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
      (globalThis as any).localStorage.setItem('@manipool_persisted_state_v1', '{invalid-json');
    }

    const loaded = await persistence.loadAppState();
    // Must gracefully return null and not throw
    expect(loaded).toBeNull();
  });

  test('clears persisted state and tokens upon reset', async () => {
    await persistence.saveAppState({
      ...initialState(),
      signedIn: true,
      token: 'token-abc',
    });
    await persistence.saveToken('token-abc');

    await persistence.clearAppState();

    const loadedState = await persistence.loadAppState();
    const loadedToken = await persistence.loadToken();

    expect(loadedState).toBeNull();
    expect(loadedToken).toBeNull();
  });
});
