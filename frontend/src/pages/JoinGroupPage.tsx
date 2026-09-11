import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { groupsApi } from '../api';
import { useAuth } from '../hooks/useAuth';
import { Users } from 'lucide-react';
import toast from 'react-hot-toast';

export default function JoinGroupPage() {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate(`/login?redirect=/groups/join/${token}`);
      return;
    }
    if (!token) return;

    setJoining(true);
    groupsApi.join(token)
      .then(res => {
        toast.success(`Joined study group "${res.data.name}"!`);
        navigate(`/groups/${res.data.id}`);
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Invalid or expired invite link');
        toast.error('Failed to join study group');
      })
      .finally(() => setJoining(false));
  }, [token, isAuthenticated, authLoading, navigate]);

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4">
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center mx-auto mb-6">
          <Users className="w-8 h-8 text-white" />
        </div>
        {joining ? (
          <>
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent mx-auto mb-4" />
            <p className="text-surface-400">Joining study group...</p>
          </>
        ) : error ? (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Unable to Join Group</h2>
            <p className="text-surface-400 mb-6">{error}</p>
            <button
              onClick={() => navigate('/groups')}
              className="px-4 py-2 rounded-xl bg-surface-800 text-white text-sm hover:bg-surface-700 transition-colors"
            >
              Go to Groups
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}
