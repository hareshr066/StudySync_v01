import { Link } from 'react-router-dom';
import { BookOpen, Users, Brain, Zap, ArrowRight, Sparkles } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface-950 overflow-hidden">
      {/* Navbar */}
      <nav className="relative z-10 border-b border-surface-800/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-2 text-xl font-bold">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <span className="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">StudySync</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="px-4 py-2 text-sm font-medium text-surface-200 hover:text-white transition-colors">Log in</Link>
            <Link to="/register" className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-primary-600 to-primary-500 text-white hover:from-primary-500 hover:to-primary-400 transition-all shadow-lg shadow-primary-500/20">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-20 pb-32 px-4">
        {/* Background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-to-b from-primary-500/10 via-accent-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" /> Built for students, by students
          </div>

          <h1 className="text-5xl sm:text-7xl font-extrabold leading-tight tracking-tight">
            <span className="text-white">Study together.</span>
            <br />
            <span className="bg-gradient-to-r from-primary-400 via-accent-400 to-primary-400 bg-clip-text text-transparent">
              Remember more.
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-surface-400 max-w-2xl mx-auto leading-relaxed">
            Create shared study decks, practice with spaced repetition, and study with classmates in live rooms.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="group flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 text-white font-semibold text-lg hover:from-primary-500 hover:to-primary-400 transition-all shadow-xl shadow-primary-500/25">
              Start Studying <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a href="#how-it-works" className="px-8 py-3.5 rounded-xl border border-surface-700 text-surface-300 font-medium hover:bg-surface-800/50 hover:text-white transition-all">
              Explore how it works
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="how-it-works" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-4">How StudySync Works</h2>
          <p className="text-center text-surface-400 mb-16 max-w-xl mx-auto">Three simple steps to supercharge your study sessions</p>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: BookOpen, title: 'Create & Share Decks', desc: 'Build flashcard decks for any subject. Share them with classmates via a simple link.', color: 'from-primary-500 to-primary-600' },
              { icon: Brain, title: 'Spaced Repetition', desc: 'SM-2 algorithm schedules reviews at optimal intervals so you remember more with less effort.', color: 'from-accent-500 to-accent-600' },
              { icon: Users, title: 'Study Rooms', desc: 'Join live study rooms with classmates. See who\'s online and study together in real time.', color: 'from-purple-500 to-purple-600' },
            ].map((f, i) => (
              <div key={i} className="group relative p-8 rounded-2xl bg-surface-900/50 border border-surface-800/50 hover:border-surface-700/50 transition-all duration-300 hover:-translate-y-1">
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-6 shadow-lg`}>
                  <f.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{f.title}</h3>
                <p className="text-surface-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center rounded-3xl bg-gradient-to-br from-primary-900/40 to-surface-900/40 border border-primary-500/20 p-12 sm:p-16">
          <Zap className="w-12 h-12 text-primary-400 mx-auto mb-6" />
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Ready to ace your exams?</h2>
          <p className="text-surface-400 text-lg mb-8 max-w-lg mx-auto">Join thousands of students already using StudySync to study smarter, not harder.</p>
          <Link to="/register" className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 text-white font-semibold text-lg hover:from-primary-500 hover:to-primary-400 transition-all shadow-xl shadow-primary-500/25">
            Create Free Account <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-800/30 py-8 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-surface-500">
          <span>© 2026 StudySync. All rights reserved.</span>
          <span>Built with ❤️ for students</span>
        </div>
      </footer>
    </div>
  );
}
