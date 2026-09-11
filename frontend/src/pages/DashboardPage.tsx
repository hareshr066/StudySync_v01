import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { studyApi, sessionsApi, notebooksApi, documentsApi } from '../api';
import type { StudyStats, StudySession } from '../types';
import { 
  BookOpen, Flame, Target, Sparkles, Clock, Folder, 
  FileText, ArrowRight, Plus, Brain, Radio, CheckCircle2 
} from 'lucide-react';
import { Card, Badge, Button } from '../components/ui';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [recentSessions, setRecentSessions] = useState<StudySession[]>([]);
  const [recentNotebooks, setRecentNotebooks] = useState<any[]>([]);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      studyApi.overallStats().then(r => setStats(r.data)).catch(() => {}),
      sessionsApi.list().then(r => setRecentSessions(r.data.sessions.slice(0, 3))).catch(() => {}),
      notebooksApi.list().then(r => setRecentNotebooks((r.data.notebooks || []).slice(0, 4))).catch(() => {}),
      documentsApi.list().then(r => setDocumentsCount(r.data.total || r.data.documents?.length || 0)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse max-w-5xl mx-auto">
        <div className="h-36 bg-surface-200 rounded-3xl" />
        <div className="grid sm:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="h-32 bg-surface-200 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  const isNewUser = (stats?.total_cards || 0) === 0 && recentNotebooks.length === 0;
  const dailyProgress = Math.min(100, Math.round(((stats?.reviewed_today || 0) / (user?.daily_goal || 30)) * 100));

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primary-600 via-primary-500 to-indigo-600 text-white p-8 sm:p-10 shadow-lg shadow-primary-500/15">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-48 h-48 bg-white/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <span className="inline-block px-3 py-1 rounded-full bg-white/15 text-xs font-semibold uppercase tracking-wider mb-3 text-primary-100 backdrop-blur-sm">
              Study Workspace
            </span>
            <h1 className="text-3xl sm:text-4xl font-bold mb-2">Welcome back, {user?.name.split(' ')[0]}!</h1>
            <p className="text-primary-100 text-base max-w-lg">
              Turn your study materials into an interactive, AI-grounded learning system.
            </p>
          </div>
          <div className="flex items-center gap-4 bg-white/10 rounded-2xl p-4 backdrop-blur-md border border-white/10 self-start sm:self-auto">
            <div className="flex flex-col items-center justify-center">
              <div className="flex items-center gap-1.5 text-amber-300 font-bold text-2xl">
                <Flame className="w-6 h-6 fill-current" /> {user?.current_streak || 0}
              </div>
              <span className="text-primary-100 text-[10px] font-bold uppercase tracking-wider mt-0.5">Day Streak</span>
            </div>
            <div className="w-px h-10 bg-white/20" />
            <div className="flex flex-col items-center justify-center">
              <div className="text-white font-bold text-2xl">{stats?.reviewed_today || 0}</div>
              <span className="text-primary-100 text-[10px] font-bold uppercase tracking-wider mt-0.5">Cards Today</span>
            </div>
          </div>
        </div>
      </div>

      {/* Onboarding Wizard for New Users */}
      {isNewUser && (
        <div className="bg-white rounded-3xl border border-primary-200 p-8 shadow-sm">
          <div className="flex items-center gap-2.5 text-primary-600 font-bold text-sm uppercase tracking-wider mb-2">
            <Sparkles className="w-4 h-4" /> Getting Started with StudySync
          </div>
          <h2 className="text-2xl font-bold text-surface-900 mb-2">3 steps to supercharge your learning</h2>
          <p className="text-surface-600 text-sm mb-6 max-w-2xl">
            Upload your syllabus, lecture slides, or lecture notes. Our AI assistant will ground your learning, answer questions with exact citations, and generate custom flashcards and quizzes.
          </p>

          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-2xl bg-surface-50 border border-surface-200/70">
              <div className="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-sm mb-3">1</div>
              <h3 className="font-bold text-surface-900 text-sm mb-1">Create Notebook</h3>
              <p className="text-xs text-surface-500">Create a focused workspace for each subject or exam.</p>
            </div>
            <div className="p-4 rounded-2xl bg-surface-50 border border-surface-200/70">
              <div className="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-sm mb-3">2</div>
              <h3 className="font-bold text-surface-900 text-sm mb-1">Upload Study Material</h3>
              <p className="text-xs text-surface-500">Upload PDF slides, textbook chapters, or text notes.</p>
            </div>
            <div className="p-4 rounded-2xl bg-surface-50 border border-surface-200/70">
              <div className="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-sm mb-3">3</div>
              <h3 className="font-bold text-surface-900 text-sm mb-1">AI Study & SM-2</h3>
              <p className="text-xs text-surface-500">Generate flashcards and retain knowledge with spaced repetition.</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button onClick={() => navigate('/notebooks')} leftIcon={<Plus className="w-4 h-4" />}>
              Create First Notebook
            </Button>
            <Button variant="secondary" onClick={() => navigate('/documents')} leftIcon={<FileText className="w-4 h-4" />}>
              Upload Document
            </Button>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Daily Goal & Due Today Card */}
          <Card className="p-6 bg-white shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-surface-900 flex items-center gap-2">
                <Target className="w-4 h-4 text-primary-500" /> Daily Review Goal
              </h2>
              <span className="text-xs font-semibold text-surface-500">
                {stats?.reviewed_today || 0} / {user?.daily_goal || 30} cards
              </span>
            </div>
            <div className="h-3 w-full bg-surface-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary-500 to-indigo-500 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${dailyProgress}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-4 text-xs font-medium text-surface-500">
              {dailyProgress >= 100 ? (
                <span className="text-green-600 flex items-center gap-1 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Goal completed for today!
                </span>
              ) : (
                <span>{(user?.daily_goal || 30) - (stats?.reviewed_today || 0)} cards remaining to hit daily goal.</span>
              )}
              {stats?.cards_due_today ? (
                <Link to="/decks" className="text-primary-600 hover:text-primary-700 font-bold flex items-center gap-1">
                  Study {stats.cards_due_today} due cards <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              ) : null}
            </div>
          </Card>

          {/* Quick Nav Workspaces */}
          <div className="grid sm:grid-cols-3 gap-4">
            <Link to="/notebooks" className="group block">
              <Card hoverable className="p-5 h-full flex flex-col justify-between bg-white border border-surface-200/80">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                    <Folder className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-semibold text-surface-400">{recentNotebooks.length} total</span>
                </div>
                <div>
                  <h3 className="font-bold text-surface-900 text-sm">Notebooks</h3>
                  <p className="text-xs text-surface-500 mt-0.5">Study workspaces & AI Tutor</p>
                </div>
              </Card>
            </Link>

            <Link to="/documents" className="group block">
              <Card hoverable className="p-5 h-full flex flex-col justify-between bg-white border border-surface-200/80">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                    <FileText className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-semibold text-surface-400">{documentsCount} files</span>
                </div>
                <div>
                  <h3 className="font-bold text-surface-900 text-sm">Documents</h3>
                  <p className="text-xs text-surface-500 mt-0.5">Uploaded study material</p>
                </div>
              </Card>
            </Link>

            <Link to="/decks" className="group block">
              <Card hoverable className="p-5 h-full flex flex-col justify-between bg-white border border-surface-200/80">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-semibold text-surface-400">{stats?.total_cards || 0} cards</span>
                </div>
                <div>
                  <h3 className="font-bold text-surface-900 text-sm">Flashcards</h3>
                  <p className="text-xs text-surface-500 mt-0.5">SM-2 Spaced Repetition</p>
                </div>
              </Card>
            </Link>
          </div>

          {/* Recent Notebooks Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-surface-900">Recent Notebooks</h2>
              <Link to="/notebooks" className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            {recentNotebooks.length === 0 ? (
              <div className="text-center py-10 bg-white rounded-2xl border border-surface-200 border-dashed">
                <Brain className="w-8 h-8 text-surface-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-surface-600">No notebooks created yet</p>
                <p className="text-xs text-surface-400 mt-0.5 mb-4">Create a notebook to upload documents and ask AI questions.</p>
                <Button size="sm" onClick={() => navigate('/notebooks')} leftIcon={<Plus className="w-3.5 h-3.5" />}>
                  Create Notebook
                </Button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {recentNotebooks.map(nb => (
                  <Card key={nb._id || nb.id} hoverable className="p-5 flex flex-col justify-between bg-white">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary-700 bg-primary-50 px-2 py-0.5 rounded-full">
                          Workspace
                        </span>
                        <span className="text-xs text-surface-400">
                          {nb.documents?.length || 0} sources
                        </span>
                      </div>
                      <h3 className="font-bold text-surface-900 text-sm line-clamp-1">{nb.title}</h3>
                      <p className="text-xs text-surface-500 mt-1 line-clamp-2">{nb.description || 'No description'}</p>
                    </div>
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="mt-4 text-primary-600 justify-start px-0 hover:bg-transparent"
                      onClick={() => navigate(`/notebooks/${nb._id || nb.id}`)}
                    >
                      Open Notebook <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Widgets */}
        <div className="space-y-6">
          {/* Overview Stats */}
          <Card className="p-6 bg-white shadow-sm">
            <h2 className="text-base font-bold text-surface-900 mb-4">Study Overview</h2>
            <div className="space-y-3.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-surface-500">Total Cards</span>
                <span className="font-bold text-surface-900">{stats?.total_cards || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-surface-500">Cards Due Today</span>
                <span className="font-bold text-amber-600">{stats?.cards_due_today || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-surface-500">Cards Studied</span>
                <span className="font-bold text-surface-900">{stats?.cards_studied || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm pt-2 border-t border-surface-100">
                <span className="text-surface-500 font-medium">Deck Progress</span>
                <Badge variant="success">{stats?.deck_progress || 0}%</Badge>
              </div>
            </div>
          </Card>

          {/* Recent Sessions */}
          <Card className="p-6 bg-white shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-surface-900">Recent Sessions</h2>
              <Link to="/analytics" className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                Analytics
              </Link>
            </div>
            {recentSessions.length === 0 ? (
              <div className="text-center py-6 text-surface-400 text-xs">
                No study sessions recorded yet.
              </div>
            ) : (
              <div className="space-y-3">
                {recentSessions.map(session => (
                  <div key={session.id} className="flex items-start gap-3 p-2 rounded-xl hover:bg-surface-50 transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center shrink-0">
                      <Clock className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-surface-900 truncate">
                        {session.deck_title || 'Flashcard Session'}
                      </p>
                      <p className="text-[11px] text-surface-400 mt-0.5">
                        {new Date(session.started_at).toLocaleDateString()} • {session.cards_reviewed} cards reviewed
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Collaborate Promo */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50 to-primary-50 border border-primary-100 flex flex-col justify-between">
            <div className="flex items-center gap-2 text-primary-700 font-bold text-xs uppercase tracking-wider mb-2">
              <Radio className="w-3.5 h-3.5 text-primary-600 animate-pulse" /> Live Collaboration
            </div>
            <h3 className="font-bold text-surface-900 text-sm mb-1">Study together in real time</h3>
            <p className="text-xs text-surface-600 mb-4 leading-relaxed">
              Create a study group or start a live room to review flashcards and share study material.
            </p>
            <Button size="sm" variant="secondary" onClick={() => navigate('/groups')} className="w-full">
              Explore Study Groups
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
