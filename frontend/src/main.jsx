import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { SnapshotProvider } from './api/useSnapshot'
import Resident from './screens/Resident'
import Dashboard from './screens/Dashboard'
import Director from './screens/Director'
import Transit from './screens/Transit'

createRoot(document.getElementById('root')).render(
  <SnapshotProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/app" element={<Resident />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/director" element={<Director />} />
        <Route path="/transit" element={<Transit />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </BrowserRouter>
  </SnapshotProvider>,
)
