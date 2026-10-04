import { useContext } from 'react';
import AuthContext from './context';

export default function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within the application.');
  return value;
}
