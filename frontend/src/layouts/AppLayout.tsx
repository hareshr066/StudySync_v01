import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  BookOpen, LayoutDashboard, LogOut, User, Settings, Compass, Users, 
  BarChart2, FileText, Folder, Menu, X, Command
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { CommandPalette } from '../components/ui/CommandPalette';

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Ctrl/Cmd + K to open command palette
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCmdPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const navGroups = [
    {
      title: 'Workspace',
      items: [
        { name: 'Home', path: '/dashboard', icon: LayoutDashboard },
        { name: 'Notebooks', path: '/notebooks', icon: Folder },
        { name: 'Documents', path: '/documents', icon: FileText },
      ]
    },
    {
      title: 'Learning',
      items: [
        { name: 'My Decks', path: '/decks', icon: BookOpen },
        { name: 'Analytics', path: '/analytics', icon: BarChart2 },
      ]
    },
    {
      title: 'Collaborate',
      items: [
        { name: 'Discover', path: '/discover', icon: Compass },
        { name: 'Study Groups', path: '/groups', icon: Users },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-surface-50 flex">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-surface-900/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:sticky top-0 h-screen w-64 bg-white border-r border-surface-200 z-50 flex flex-col transition-transform duration-300
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-16 flex items-center justify-between px-6 border-b border-surface-100">
          <Link to="/dashboard" className="flex items-center gap-2 text-xl font-bold">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shadow-sm">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <span className="text-surface-900">StudySync</span>
          </Link>
          <button className="lg:hidden text-surface-500" onClick={() => setSidebarOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          <button
            onClick={() => setCmdPaletteOpen(true)}
            className="w-full flex items-center justify-between px-3 py-2 text-sm text-surface-500 bg-surface-50 border border-surface-200 rounded-lg hover:bg-surface-100 hover:text-surface-900 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Command className="w-4 h-4" />
              <span>Search...</span>
            </div>
            <div className="flex gap-1 text-[10px] font-medium text-surface-400">
              <kbd className="px-1.5 py-0.5 rounded bg-white border border-surface-200 shadow-sm">Ctrl</kbd>
              <kbd className="px-1.5 py-0.5 rounded bg-white border border-surface-200 shadow-sm">K</kbd>
            </div>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-2 px-3 space-y-6">
          {navGroups.map(group => (
            <div key={group.title}>
              <h3 className="px-3 text-xs font-bold uppercase tracking-wider text-surface-400 mb-2">
                {group.title}
              </h3>
              <div className="space-y-1">
                {group.items.map(item => {
                  const isActive = location.pathname.startsWith(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive ? 'bg-primary-50 text-primary-700' : 'text-surface-600 hover:bg-surface-50 hover:text-surface-900'
                      }`}
                    >
                      <item.icon className="w-4 h-4" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-surface-100">
          <Link to="/profile" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-600 hover:bg-surface-50 hover:text-surface-900 transition-colors">
            <User className="w-4 h-4" /> Profile
          </Link>
          <Link to="/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-600 hover:bg-surface-50 hover:text-surface-900 transition-colors">
            <Settings className="w-4 h-4" /> Settings
          </Link>
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors mt-1">
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <header className="lg:hidden h-16 bg-white border-b border-surface-200 flex items-center justify-between px-4 sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)} className="text-surface-600 p-1">
              <Menu className="w-6 h-6" />
            </button>
            <span className="font-bold text-surface-900">StudySync</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-sm font-bold text-primary-700">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1200px] w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette isOpen={cmdPaletteOpen} onClose={() => setCmdPaletteOpen(false)} />
    </div>
  );
}
