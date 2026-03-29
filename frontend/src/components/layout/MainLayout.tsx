import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import CopilotPanel from '../copilot/CopilotPanel';
import CopilotFAB from '../copilot/CopilotFAB';

export default function MainLayout() {
  const [copilotOpen, setCopilotOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <CopilotFAB isOpen={copilotOpen} onClick={() => setCopilotOpen(true)} />
      <CopilotPanel isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  );
}
