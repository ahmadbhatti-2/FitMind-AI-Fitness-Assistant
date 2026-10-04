import { useEffect, useMemo, useState } from 'react';
import AuthContext from './context';

const SESSION_KEY = 'fitmind.session';

function readSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
  } catch {
    localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export default function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession);
  useEffect(() => {
    const expireSession = () => setSession(null);
    window.addEventListener('fitmind:session-expired', expireSession);
    return () => window.removeEventListener('fitmind:session-expired', expireSession);
  }, []);
  const auth = useMemo(() => ({
    user: session?.user || null,
    signIn: (nextSession) => {
      localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
    },
    signOut: () => {
      localStorage.removeItem(SESSION_KEY);
      setSession(null);
    },
  }), [session]);

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}
