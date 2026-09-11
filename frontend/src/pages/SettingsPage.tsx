import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { LogOut, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success('Logged out');
    navigate('/login');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Settings</h1>
      <div className="p-6 rounded-2xl bg-surface-900/50 border border-surface-800/50 space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Shield className="w-5 h-5 text-primary-400" /> Account</h2>
        <button onClick={handleLogout} className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-all">
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </div>
    </div>
  );
}
