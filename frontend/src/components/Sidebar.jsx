import { Apple, Dumbbell, LayoutDashboard, LogOut, MessageSquareText, Settings2, TrendingUp } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';
import useAuth from '../auth/useAuth';
import BrandMark from './BrandMark';

const ITEMS = [
  { icon: LayoutDashboard, label: 'Overview', path: '/' },
  { icon: MessageSquareText, label: 'AI Coach', path: '/coach' },
  { icon: Dumbbell, label: 'Workouts', path: '/workouts' },
  { icon: Apple, label: 'Nutrition', path: '/nutrition' },
  { icon: TrendingUp, label: 'Progress', path: '/progress' },
];

export default function Sidebar({ isOpen, onNavigate }) {
  const { signOut } = useAuth();

  return (
    <>
      {isOpen && <button className="sidebar-backdrop" type="button" aria-label="Close navigation" onClick={onNavigate} />}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <Link className="brand sidebar-brand" to="/" onClick={onNavigate}>
          <span className="brand-mark"><BrandMark /></span><span>fitmind<span className="brand-dot">.</span></span>
        </Link>
        <span className="sidebar-caption">YOUR SPACE</span>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {ITEMS.map(({ icon: Icon, label, path }) => (
            <NavLink end={path === '/'} key={path} to={path} onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}>
              <Icon size={19} strokeWidth={1.9} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <NavLink to="/profile" onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}><Settings2 size={19} /><span>My profile</span></NavLink>
          <button className="nav-item signout-button" type="button" onClick={signOut}><LogOut size={19} /><span>Sign out</span></button>
          <p className="sidebar-version">FITMIND · PERSONAL FITNESS</p>
        </div>
      </aside>
    </>
  );
}
