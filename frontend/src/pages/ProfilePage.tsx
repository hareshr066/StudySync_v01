import { useAuth } from '../hooks/useAuth';
import { User, Mail, Calendar } from 'lucide-react';

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Profile</h1>
      <div className="p-8 rounded-2xl bg-surface-900/50 border border-surface-800/50">
        <div className="flex items-center gap-6 mb-8">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-3xl font-bold text-white">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{user.name}</h2>
            <p className="text-surface-400">{user.email}</p>
          </div>
        </div>
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-800/30">
            <User className="w-5 h-5 text-primary-400" />
            <div><div className="text-xs text-surface-500">Name</div><div className="text-white font-medium">{user.name}</div></div>
          </div>
          <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-800/30">
            <Mail className="w-5 h-5 text-primary-400" />
            <div><div className="text-xs text-surface-500">Email</div><div className="text-white font-medium">{user.email}</div></div>
          </div>
          <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-800/30">
            <Calendar className="w-5 h-5 text-primary-400" />
            <div><div className="text-xs text-surface-500">Joined</div><div className="text-white font-medium">{new Date(user.created_at).toLocaleDateString()}</div></div>
          </div>
        </div>
      </div>
    </div>
  );
}
