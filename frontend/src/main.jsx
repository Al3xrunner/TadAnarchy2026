import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { SnapshotProvider } from './api/useSnapshot'
import Resident from './screens/Resident'
import Dashboard from './screens/Dashboard'
import Director from './screens/Director'


createRoot(document.getElementById('root')).render(
  <SnapshotProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/app" element={<Resident />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/director" element={<Director />} />
      </Routes>
    </BrowserRouter>
  </SnapshotProvider>,
)