import React, { createContext, useContext, useEffect, useReducer, useState } from 'react';
import { Action, appReducer, initialState } from './reducer';
import { AppState } from '../types/domain';
import { persistence } from '../services/storage';
import { api } from '../services/api';

const Context = createContext<
  { state: AppState; dispatch: React.Dispatch<Action>; isHydrated: boolean } | undefined
>(undefined);

export function AppProvider({ children }: React.PropsWithChildren) {
  const [state, dispatch] = useReducer(appReducer, undefined, initialState);
  const [isHydrated, setIsHydrated] = useState(false);

  // Rehydrate on mount (app restart recovery)
  useEffect(() => {
    let mounted = true;
    async function hydrate() {
      try {
        const persisted = await persistence.loadAppState();
        const token = await persistence.loadToken();
        if (token) {
          api.setToken(token);
        }
        if (persisted && mounted) {
          dispatch({
            type: 'HYDRATE',
            payload: {
              ...persisted,
              token: token || persisted.token,
            },
          });
        }
      } catch (err) {
        console.warn('[AppProvider] Rehydration failed:', err);
      } finally {
        if (mounted) {
          setIsHydrated(true);
        }
      }
    }
    hydrate();
    return () => {
      mounted = false;
    };
  }, []);

  // Persist state on meaningful updates after initial hydration
  useEffect(() => {
    if (isHydrated) {
      persistence.saveAppState(state);
      if (state.token) {
        persistence.saveToken(state.token);
      }
    }
  }, [state, isHydrated]);

  return (
    <Context.Provider value={{ state, dispatch, isHydrated }}>{children}</Context.Provider>
  );
}

export function useApp() {
  const context = useContext(Context);
  if (!context) {
    throw new Error('AppProvider is required.');
  }
  return context;
}

let sequence = 0;
export const newId = (prefix: string) =>
  `${prefix}-${Date.now()}-${++sequence}`;
export const nowISO = () => new Date().toISOString();
