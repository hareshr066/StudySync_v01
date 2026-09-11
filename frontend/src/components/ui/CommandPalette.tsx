import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, LayoutDashboard, Folder, FileText, BookOpen,
  BarChart2, Compass, Users, Brain, Settings, X
} from 'lucide-react';
import { Spinner } from './Spinner';

interface SearchResult {
  id: string;
  title: string;
  type: 'notebook' | 'document' | 'deck' | 'note';
  description?: string;
}

interface CommandAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  group: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const navigate_and_close = useCallback((path: string) => {
    navigate(path);
    onClose();
  }, [navigate, onClose]);

  const staticActions: CommandAction[] = [
    { id: 'dashboard', label: 'Go to Dashboard', icon: <LayoutDashboard className="w-4 h-4" />, action: () => navigate_and_close('/dashboard'), group: 'Navigate' },
    { id: 'notebooks', label: 'Go to Notebooks', icon: <Folder className="w-4 h-4" />, action: () => navigate_and_close('/notebooks'), group: 'Navigate' },
    { id: 'documents', label: 'Go to Documents', icon: <FileText className="w-4 h-4" />, action: () => navigate_and_close('/documents'), group: 'Navigate' },
    { id: 'decks', label: 'Go to My Decks', icon: <BookOpen className="w-4 h-4" />, action: () => navigate_and_close('/decks'), group: 'Navigate' },
    { id: 'analytics', label: 'Go to Analytics', icon: <BarChart2 className="w-4 h-4" />, action: () => navigate_and_close('/analytics'), group: 'Navigate' },
    { id: 'discover', label: 'Discover Public Decks', icon: <Compass className="w-4 h-4" />, action: () => navigate_and_close('/discover'), group: 'Navigate' },
    { id: 'groups', label: 'Study Groups', icon: <Users className="w-4 h-4" />, action: () => navigate_and_close('/groups'), group: 'Navigate' },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" />, action: () => navigate_and_close('/settings'), group: 'Navigate' },
  ];

  // Search debounced
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    clearTimeout(searchTimeout.current);
    setSearching(true);
    searchTimeout.current = setTimeout(async () => {
      try {
        const token = localStorage.getItem('access_token');
        const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
        const res = await fetch(`${apiBase}/api/v1/search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          const results: SearchResult[] = [
            ...data.results.notebooks.map((n: any) => ({ ...n, type: 'notebook' as const })),
            ...data.results.documents.map((d: any) => ({ ...d, type: 'document' as const })),
            ...data.results.decks.map((d: any) => ({ ...d, type: 'deck' as const })),
            ...data.results.notes.map((n: any) => ({ ...n, type: 'note' as const })),
          ];
          setSearchResults(results);
        }
      } catch {
        // Search failed silently
      } finally {
        setSearching(false);
      }
    }, 300);
  }, [query]);

  // Focus on open
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSearchResults([]);
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const filteredActions = query
    ? staticActions.filter(a => a.label.toLowerCase().includes(query.toLowerCase()))
    : staticActions;

  const allItems = [
    ...searchResults.map(r => ({ type: 'result', data: r })),
    ...filteredActions.map(a => ({ type: 'action', data: a })),
  ];

  const handleResultClick = (result: SearchResult) => {
    const paths: Record<string, string> = {
      notebook: `/notebooks/${result.id}`,
      document: `/documents`,
      deck: `/decks/${result.id}`,
      note: `/notebooks`,
    };
    navigate_and_close(paths[result.type] || '/dashboard');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, allItems.length - 1));
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const item = allItems[selectedIndex];
      if (!item) return;
      if (item.type === 'result') handleResultClick(item.data as SearchResult);
      else (item.data as CommandAction).action();
    }
  };

  const typeIcons: Record<string, React.ReactNode> = {
    notebook: <Folder className="w-4 h-4 text-primary-500" />,
    document: <FileText className="w-4 h-4 text-amber-500" />,
    deck: <BookOpen className="w-4 h-4 text-accent-500" />,
    note: <Brain className="w-4 h-4 text-purple-500" />,
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[10vh] px-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-surface-900/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-surface-200 overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-surface-100">
          <Search className="w-5 h-5 text-surface-400 shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Search or type a command..."
            className="flex-1 text-sm text-surface-900 placeholder:text-surface-400 bg-transparent border-none outline-none"
          />
          {searching && <Spinner size="sm" />}
          <button onClick={onClose} className="p-1 rounded-lg text-surface-400 hover:text-surface-600 hover:bg-surface-100 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-[380px] overflow-y-auto">
          {searchResults.length > 0 && (
            <div className="py-2">
              <div className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-surface-400">Search Results</div>
              {searchResults.map((result, i) => (
                <button
                  key={`r-${result.id}`}
                  onClick={() => handleResultClick(result)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-surface-50 transition-colors ${selectedIndex === i ? 'bg-primary-50' : ''}`}
                >
                  {typeIcons[result.type]}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-surface-900 truncate">{result.title}</div>
                    <div className="text-xs text-surface-400 capitalize">{result.type}</div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Static Actions grouped */}
          {(() => {
            const offset = searchResults.length;
            const groups = Array.from(new Set(filteredActions.map(a => a.group)));
            let actionIdx = 0;
            return groups.map(group => (
              <div key={group} className="py-2">
                <div className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-surface-400">{group}</div>
                {filteredActions.filter(a => a.group === group).map(action => {
                  const idx = offset + actionIdx++;
                  return (
                    <button
                      key={action.id}
                      onClick={action.action}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-surface-50 transition-colors ${selectedIndex === idx ? 'bg-primary-50' : ''}`}
                    >
                      <span className="text-surface-500">{action.icon}</span>
                      <span className="flex-1 text-sm font-medium text-surface-900">{action.label}</span>
                      {action.shortcut && (
                        <kbd className="text-[10px] font-medium text-surface-400 px-1.5 py-0.5 rounded border border-surface-200 bg-surface-50">{action.shortcut}</kbd>
                      )}
                    </button>
                  );
                })}
              </div>
            ));
          })()}

          {query && !searching && searchResults.length === 0 && filteredActions.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-sm text-surface-500">No results for "{query}"</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-surface-100 flex items-center gap-4 text-[11px] text-surface-400 font-medium">
          <span><kbd className="font-mono">↑↓</kbd> navigate</span>
          <span><kbd className="font-mono">↵</kbd> select</span>
          <span><kbd className="font-mono">esc</kbd> close</span>
        </div>
      </div>
    </div>
  );
}
