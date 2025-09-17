interface SimulationSession {
  id: string;
  timestamp: number;
  parameters: any;
  data: {
    transactions: any[];
    cust1: any[];
    cust2: any[];
    products: any[];
  };
  status: 'running' | 'completed' | 'failed';
}

const CACHE_KEY_PREFIX = 'walmart_sim_';
const MAX_CACHE_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

export class SimulationCache {
  static saveSession(session: SimulationSession): void {
    try {
      const key = `${CACHE_KEY_PREFIX}${session.id}`;
      localStorage.setItem(key, JSON.stringify(session));
    } catch (error) {
      console.warn('Failed to save simulation session to cache:', error);
    }
  }

  static getSession(sessionId: string): SimulationSession | null {
    try {
      const key = `${CACHE_KEY_PREFIX}${sessionId}`;
      const data = localStorage.getItem(key);
      if (!data) return null;

      const session: SimulationSession = JSON.parse(data);

      // Check if cache is still valid
      if (Date.now() - session.timestamp > MAX_CACHE_AGE_MS) {
        this.removeSession(sessionId);
        return null;
      }

      return session;
    } catch (error) {
      console.warn('Failed to retrieve simulation session from cache:', error);
      return null;
    }
  }

  static getAllSessions(): SimulationSession[] {
    const sessions: SimulationSession[] = [];

    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(CACHE_KEY_PREFIX)) {
          const sessionId = key.replace(CACHE_KEY_PREFIX, '');
          const session = this.getSession(sessionId);
          if (session) {
            sessions.push(session);
          }
        }
      }
    } catch (error) {
      console.warn('Failed to retrieve all sessions:', error);
    }

    return sessions.sort((a, b) => b.timestamp - a.timestamp);
  }

  static removeSession(sessionId: string): void {
    try {
      const key = `${CACHE_KEY_PREFIX}${sessionId}`;
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to remove simulation session:', error);
    }
  }

  static clearExpiredSessions(): void {
    const allSessions = this.getAllSessions();
    const expiredSessions = allSessions.filter(
      session => Date.now() - session.timestamp > MAX_CACHE_AGE_MS
    );

    expiredSessions.forEach(session => this.removeSession(session.id));
  }

  static getCacheUsage(): { used: number; total: number } {
    try {
      let used = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(CACHE_KEY_PREFIX)) {
          const value = localStorage.getItem(key);
          used += (key.length + (value?.length || 0)) * 2; // Approximate bytes
        }
      }

      // Estimate total available (5-10MB typical)
      const total = 5 * 1024 * 1024; // 5MB conservative estimate

      return { used, total };
    } catch (error) {
      return { used: 0, total: 0 };
    }
  }
}