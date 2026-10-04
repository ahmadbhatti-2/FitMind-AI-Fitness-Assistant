import { useState } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const closeNavigation = () => setNavigationOpen(false);

  return (
    <div className="app-shell">
      <Sidebar isOpen={navigationOpen} onNavigate={closeNavigation} />
      <div className="main-column">
        <Navbar onMenuClick={() => setNavigationOpen((open) => !open)} />
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
