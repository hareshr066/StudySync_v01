import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { decksApi } from '../api';
import type { Deck } from '../types';
import { BookOpen, Plus, Search, Layers, User } from 'lucide-react';
import { Button, Card, Input, Modal, Badge } from '../components/ui';
import toast from 'react-hot-toast';

export default function DecksPage() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [tags, setTags] = useState('');
  const [creating, setCreating] = useState(false);
  
  const [search, setSearch] = useState('');

  const loadDecks = () => {
    decksApi.list(1, 100).then(r => setDecks(r.data.decks)).catch(() => toast.error('Failed to load decks')).finally(() => setLoading(false));
  };

  useEffect(() => { loadDecks(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const parsedTags = tags.split(',').map(t => t.trim()).filter(Boolean);
      await decksApi.create({ title, description, visibility, tags: parsedTags });
      toast.success('Deck created!');
      setShowCreate(false);
      setTitle('');
      setDescription('');
      setVisibility('private');
      setTags('');
      loadDecks();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create deck');
    } finally {
      setCreating(false);
    }
  };

  const filtered = decks.filter(d => d.title.toLowerCase().includes(search.toLowerCase()));

  if (loading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto animate-pulse">
        <div className="h-10 w-48 bg-surface-200 rounded-lg" />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => <div key={i} className="h-48 bg-surface-200 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-surface-900">My Decks</h1>
          <p className="text-surface-500 mt-1">Manage your study collections.</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Input 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
            placeholder="Search decks..."
            leftIcon={<Search className="w-5 h-5" />}
            className="w-full sm:w-64"
          />
          <Button onClick={() => setShowCreate(true)} leftIcon={<Plus className="w-5 h-5" />} className="shrink-0">
            New Deck
          </Button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20 rounded-3xl bg-surface-100 border border-surface-200 border-dashed">
          <BookOpen className="w-16 h-16 text-surface-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-surface-900 mb-2">
            {decks.length === 0 ? "You don't have any decks yet." : "No decks match your search."}
          </h3>
          {decks.length === 0 && (
            <Button onClick={() => setShowCreate(true)} leftIcon={<Plus className="w-4 h-4" />} className="mt-4">
              Create your first deck
            </Button>
          )}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map(deck => (
            <Link key={deck.id} to={`/decks/${deck.id}`}>
              <Card hoverable className="flex flex-col h-full border-t-4 border-t-primary-500">
                <div className="p-6 flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-xl font-bold text-surface-900 line-clamp-1">{deck.title}</h3>
                    <Badge variant={deck.visibility === 'public' ? 'success' : deck.visibility === 'shared' ? 'primary' : 'secondary'}>
                      {deck.visibility.charAt(0).toUpperCase() + deck.visibility.slice(1)}
                    </Badge>
                  </div>
                  {deck.description && <p className="text-surface-600 text-sm mb-4 line-clamp-2">{deck.description}</p>}
                  {deck.tags && deck.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {deck.tags.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="p-4 border-t border-surface-100 bg-surface-50 flex items-center justify-between rounded-b-2xl text-xs font-medium text-surface-500">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-4 h-4" /> {deck.card_count} cards
                  </div>
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4" /> {deck.member_count} member{deck.member_count !== 1 ? 's' : ''}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create New Deck">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input 
            label="Title"
            value={title} 
            onChange={e => setTitle(e.target.value)} 
            required 
            maxLength={200}
            placeholder="e.g. DSA — Trees" 
          />
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">Description (optional)</label>
            <textarea 
              value={description} 
              onChange={e => setDescription(e.target.value)} 
              rows={3} 
              maxLength={1000}
              className="w-full rounded-xl border border-surface-200 px-4 py-2 text-surface-900 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 resize-none"
              placeholder="What's this deck about?" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">Visibility</label>
            <select
              value={visibility}
              onChange={e => setVisibility(e.target.value)}
              className="w-full rounded-xl border border-surface-200 px-4 py-2.5 text-surface-900 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-white"
            >
              <option value="private">Private - Only you can access</option>
              <option value="shared">Shared - Anyone with link can access</option>
              <option value="public">Public - Discoverable by anyone</option>
            </select>
          </div>
          <Input 
            label="Tags (Comma separated)"
            value={tags} 
            onChange={e => setTags(e.target.value)} 
            placeholder="e.g. computer science, algorithms" 
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" isLoading={creating}>Create Deck</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
