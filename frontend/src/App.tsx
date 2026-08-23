import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ConstellationBackground from './components/ConstellationBackground';
import Overview from './pages/Overview';
import Explorer from './pages/Explorer';
import Forecast from './pages/Forecast';
import Recommendations from './pages/Recommendations';
import Simulator from './pages/Simulator';
import Chat from './pages/Chat';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-black text-white font-sans flex relative overflow-hidden">
        <ConstellationBackground />
        <div className="flex z-10 w-full h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto p-8 relative">
            <Routes>
              <Route path="/" element={<Navigate to="/overview" replace />} />
              <Route path="/overview" element={<Overview />} />
              <Route path="/explorer" element={<Explorer />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/simulator" element={<Simulator />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
