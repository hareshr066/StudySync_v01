import { useEffect, useState } from 'react';
import { studyApi, sessionsApi } from '../api';
import type { StudyStats, StudySession } from '../types';
import { BarChart2, TrendingUp, Layers, Clock, Brain, Calendar, ArrowRight } from 'lucide-react';
import { Card, Button } from '../components/ui';
import { Link } from 'react-router-dom';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      studyApi.overallStats().then(r => setStats(r.data)).catch(() => {}),
      sessionsApi.list().then(r => setSessions(r.data.sessions || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto animate-pulse">
        <div className="h-10 w-48 bg-surface-200 rounded-lg" />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-surface-200 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  // Calculate real 7-day breakdown from actual study sessions
  const now = new Date();
  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(now.getDate() - (6 - i));
    return {
      dateStr: d.toISOString().split('T')[0],
      dayName: daysOfWeek[d.getDay()],
      count: 0
    };
  });

  // Calculate total study time
  let totalTimeSeconds = 0;
  sessions.forEach(s => {
    totalTimeSeconds += s.duration_seconds || 0;
    if (s.started_at) {
      const sDate = s.started_at.split('T')[0];
      const match = last7Days.find(d => d.dateStr === sDate);
      if (match) {
        match.count += s.cards_reviewed || 0;
      }
    }
  });

  const totalCardsStudied = stats?.cards_studied || 0;
  const hasActivity = sessions.length > 0 || (stats?.reviewed_today || 0) > 0;
  const maxDayCount = Math.max(...last7Days.map(d => d.count), 1);

  // 30-Day Activity Heatmap Grid
  const last30Days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setDate(now.getDate() - (29 - i));
    const dStr = d.toISOString().split('T')[0];
    let count = 0;
    sessions.forEach(s => {
      if (s.started_at && s.started_at.startsWith(dStr)) {
        count += s.cards_reviewed || 0;
      }
    });
    return { date: dStr, count };
  });

  const statCards = [
    { label: 'Total Cards', value: stats?.total_cards || 0, icon: Layers, color: 'text-primary-600', bg: 'bg-primary-50', desc: 'Across all decks' },
    { label: 'Cards Due', value: stats?.cards_due || 0, icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50', desc: 'Ready for spaced review' },
    { label: 'Reviewed Today', value: stats?.reviewed_today || 0, icon: Brain, color: 'text-indigo-600', bg: 'bg-indigo-50', desc: 'Cards reviewed today' },
    { label: 'Mastery Progress', value: `${stats?.deck_progress || 0}%`, icon: TrendingUp, color: 'text-emerald-600', bg: 'bg-emerald-50', desc: 'Retention & progression' },
  ];

  const formatDuration = (secs: number) => {
    const hrs = Math.floor(secs / 3600);
    const mins = Math.floor((secs % 3600) / 60);
    if (hrs > 0) return `${hrs}h ${mins}m`;
    return `${mins}m`;
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      <div>
        <h1 className="text-3xl font-bold text-surface-900 flex items-center gap-3">
          <BarChart2 className="w-8 h-8 text-primary-500" /> Study Analytics
        </h1>
        <p className="text-surface-500 mt-1">Real-time mastery tracking powered by spaced repetition sessions.</p>
      </div>

      {/* Stat Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((s, i) => (
          <Card key={i} className="p-6 bg-white shadow-sm">
            <div className={`w-11 h-11 rounded-xl ${s.bg} flex items-center justify-center mb-4`}>
              <s.icon className={`w-5 h-5 ${s.color}`} />
            </div>
            <div className="text-2xl font-bold text-surface-900 mb-1">{s.value}</div>
            <div className="text-sm font-semibold text-surface-700">{s.label}</div>
            <div className="text-xs text-surface-400 mt-1">{s.desc}</div>
          </Card>
        ))}
      </div>

      {!hasActivity ? (
        <div className="text-center py-16 bg-white rounded-3xl border border-surface-200 border-dashed p-8">
          <Brain className="w-12 h-12 text-surface-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-surface-900 mb-1">No study activity recorded yet</h3>
          <p className="text-sm text-surface-500 max-w-md mx-auto mb-6">
            Review 5 cards today to start building your spaced repetition memory curve and activity streak.
          </p>
          <Link to="/decks">
            <Button leftIcon={<ArrowRight className="w-4 h-4" />}>
              Start Reviewing Cards
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Real 7-day Activity Chart */}
            <Card className="lg:col-span-2 p-6 bg-white shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-base font-bold text-surface-900">7-Day Study Volume</h3>
                  <p className="text-xs text-surface-500">Cards reviewed per day</p>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-surface-100 text-surface-600">
                  Total Studied: {totalCardsStudied}
                </span>
              </div>
              <div className="flex items-end gap-3 h-44 pt-4">
                {last7Days.map((d, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                    <div className="text-[10px] font-bold text-surface-500">
                      {d.count > 0 ? d.count : ''}
                    </div>
                    <div
                      className={`w-full rounded-t-lg transition-all duration-500 ${
                        d.count > 0 ? 'bg-primary-500 hover:bg-primary-600' : 'bg-surface-100'
                      }`}
                      style={{ height: `${Math.max(6, (d.count / maxDayCount) * 100)}%` }}
                    />
                    <span className="text-xs text-surface-400 font-medium">{d.dayName}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Retention & Time Summary */}
            <Card className="p-6 bg-white shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="text-base font-bold text-surface-900 mb-4">Study Insights</h3>
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-surface-50 border border-surface-100">
                    <div className="text-xs text-surface-500 font-medium">Total Study Time</div>
                    <div className="text-xl font-bold text-surface-900 mt-1">
                      {formatDuration(totalTimeSeconds)}
                    </div>
                  </div>
                  <div className="p-4 rounded-2xl bg-surface-50 border border-surface-100">
                    <div className="text-xs text-surface-500 font-medium">Session Count</div>
                    <div className="text-xl font-bold text-surface-900 mt-1">
                      {sessions.length} sessions completed
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-surface-400 mt-4 leading-relaxed">
                Spaced repetition automatically optimizes your reviews based on difficulty feedback (Again, Hard, Good, Easy).
              </p>
            </Card>
          </div>

          {/* 30-Day Activity Heatmap */}
          <Card className="p-6 bg-white shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-4 h-4 text-primary-500" />
              <h3 className="text-base font-bold text-surface-900">30-Day Activity Grid</h3>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-2">
              {last30Days.map((d, i) => {
                const intensity = 
                  d.count === 0 ? 'bg-surface-100' :
                  d.count < 10 ? 'bg-primary-200' :
                  d.count < 25 ? 'bg-primary-400' : 'bg-primary-600';
                return (
                  <div
                    key={i}
                    title={`${d.date}: ${d.count} cards reviewed`}
                    className={`w-5 h-5 rounded-md ${intensity} transition-transform hover:scale-125 cursor-pointer`}
                  />
                );
              })}
            </div>
            <div className="flex items-center justify-between text-xs text-surface-400 mt-4">
              <span>30 days ago</span>
              <div className="flex items-center gap-1">
                <span>Less</span>
                <span className="w-3 h-3 rounded-sm bg-surface-100" />
                <span className="w-3 h-3 rounded-sm bg-primary-200" />
                <span className="w-3 h-3 rounded-sm bg-primary-400" />
                <span className="w-3 h-3 rounded-sm bg-primary-600" />
                <span>More</span>
              </div>
              <span>Today</span>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
