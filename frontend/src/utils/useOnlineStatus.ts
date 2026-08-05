import { useEffect, useState } from 'react';

/**
 * Tracks the browser's network connectivity using the `online` / `offline`
 * window events, so UI can react *instantly* to a network drop instead of
 * waiting for the next network request to fail.
 *
 * Note: `navigator.onLine` reflects the browser's network-interface state, not
 * the reachability of a specific server — treat it as an optimistic signal.
 * The import pages combine this with their existing poll-failure tolerance so
 * a brief blip shows the "reconnecting" state immediately, and the poll
 * failures remain the source of truth for a genuinely unreachable server.
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(() => navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
