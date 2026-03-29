import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Securities from './pages/Securities';
import Transactions from './pages/Transactions';
import Journal from './pages/Journal';
import Documents from './pages/Documents';
import Valuations from './pages/Valuations';
import Reports from './pages/Reports';
import Export from './pages/Export';
import AuditLog from './pages/AuditLog';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/securities" element={<Securities />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/valuations" element={<Valuations />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/export" element={<Export />} />
            <Route path="/audit" element={<AuditLog />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
