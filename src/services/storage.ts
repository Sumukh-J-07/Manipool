/**
 * ManiPool Local Persistence & Recovery Service
 *
 * Implements persistent local storage for student profiles, active journeys,
 * saved places, notifications, and auth sessions across app restarts.
 */

import { AppState } from '../types/domain';

const STATE_KEY = '@manipool_persisted_state_v1';
const TOKEN_KEY = '@manipool_auth_token_v1';

// In-memory fallback map for test environments and headless execution
const memoryStore = new Map<string, string>();

class PersistenceService {
  private async setItem(key: string, value: string): Promise<void> {
    try {
      if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
        (globalThis as any).localStorage.setItem(key, value);
      }
    } catch {
      // Fallback to memoryStore
    }
    memoryStore.set(key, value);
  }

  private async getItem(key: string): Promise<string | null> {
    try {
      if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
        const val = (globalThis as any).localStorage.getItem(key);
        if (val !== null && val !== undefined) {
          return val;
        }
      }
    } catch {
      // Fallback to memoryStore
    }
    return memoryStore.get(key) ?? null;
  }

  private async removeItem(key: string): Promise<void> {
    try {
      if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
        (globalThis as any).localStorage.removeItem(key);
      }
    } catch {
      // Fallback
    }
    memoryStore.delete(key);
  }

  /**
   * Persists the current app state snapshot to durable storage.
   */
  async saveAppState(state: AppState): Promise<void> {
    try {
      const serialized = JSON.stringify({
        profile: state.profile,
        signedIn: state.signedIn,
        draft: state.draft,
        rides: state.rides,
        groups: state.groups,
        scenario: state.scenario,
        notifications: state.notifications,
        savedPlaces: state.savedPlaces,
        reports: state.reports,
        token: state.token,
      });
      await this.setItem(STATE_KEY, serialized);
    } catch (err) {
      console.warn('[PersistenceService] Failed to save state:', err);
    }
  }

  /**
   * Loads the persisted app state snapshot, restoring journeys, profiles, and saved places.
   */
  async loadAppState(): Promise<Partial<AppState> | null> {
    try {
      const data = await this.getItem(STATE_KEY);
      if (!data) {
        return null;
      }
      const parsed = JSON.parse(data) as Partial<AppState>;
      return parsed;
    } catch (err) {
      console.warn('[PersistenceService] Corrupted state encountered; resetting to clean initial state:', err);
      await this.removeItem(STATE_KEY);
      return null;
    }
  }

  /**
   * Clears all persisted state and session tokens (used upon user Sign Out / Data Reset).
   */
  async clearAppState(): Promise<void> {
    try {
      await this.removeItem(STATE_KEY);
      await this.removeItem(TOKEN_KEY);
    } catch (err) {
      console.warn('[PersistenceService] Failed to clear state:', err);
    }
  }

  /**
   * Saves authentication JWT bearer token.
   */
  async saveToken(token: string): Promise<void> {
    await this.setItem(TOKEN_KEY, token);
  }

  /**
   * Retrieves saved authentication token.
   */
  async loadToken(): Promise<string | null> {
    return this.getItem(TOKEN_KEY);
  }

  /**
   * Clears saved authentication token.
   */
  async clearToken(): Promise<void> {
    await this.removeItem(TOKEN_KEY);
  }
}

export const persistence = new PersistenceService();
