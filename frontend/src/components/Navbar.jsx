import { Menu, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../auth/useAuth';

export default function Navbar({ onMenuClick }) {
  const { user } = useAuth();
  const initials = user.username.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();

  return (
    <header className="topbar">
      <button className="icon-button mobile-menu-button" type="button" onClick={onMenuClick} aria-label="Open navigation"><Menu size={21} /></button>
      <div className="topbar-context"><span className="topbar-label">YOUR TRAINING, IN CONTEXT</span><span>Make today count.</span></div>
      <Link to="/profile" className="account-link" aria-label="Open profile settings">
        <span className="account-avatar">{initials || <UserRound size={17} />}</span>
        <span className="account-name">{user.username}<small>Personal account</small></span>
      </Link>
    </header>
  );
}
