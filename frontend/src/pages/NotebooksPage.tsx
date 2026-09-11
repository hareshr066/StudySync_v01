import { useState, useEffect } from 'react';
import { Card, Button, Input, Spinner, Badge, Modal } from '../components/ui';
import { Folder, Plus, Search, Trash, FileText, Calendar } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { notebooksApi } from '../api';
import toast from 'react-hot-toast';

export default function NotebooksPage() {
  const [search, setSearch] = useState('');
  const [notebooks, setNotebooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Modal state
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadNotebooks();
  }, []);

  const loadNotebooks = async () => {
    try {
      setLoading(true);
      const res = await notebooksApi.list();
      setNotebooks(res.data.notebooks);
    } catch (err) {
      toast.error('Failed to load notebooks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNotebook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const res = await notebooksApi.create({ title: newTitle.trim(), description: newDescription.trim() || undefined });
      toast.success('Notebook created!');
      setShowCreate(false);
      setNewTitle('');
      setNewDescription('');
      navigate(`/notebooks/${res.data._id || res.data.id}`);
    } catch {
      toast.error('Failed to create notebook');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this notebook? Sources will not be deleted.')) return;
    try {
      await notebooksApi.delete(id);
      setNotebooks(notebooks.filter(nb => (nb._id || nb.id) !== id));
      toast.success('Notebook deleted');
    } catch {
      toast.error('Failed to delete notebook');
    }
  };

  const filteredNotebooks = notebooks.filter(nb => nb.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-surface-900">Notebooks</h1>
          <p className="text-surface-500 mt-1">Organize your study sources and get AI-powered insights.</p>
        </div>
        <div className="flex items-center gap-3">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search notebooks..."
            leftIcon={<Search className="w-4 h-4" />}
            className="w-full sm:w-64"
          />
          <Button leftIcon={<Plus className="w-4 h-4" />} onClick={() => setShowCreate(true)}>
            New Notebook
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : notebooks.length === 0 ? (
        <div className="text-center py-20 rounded-3xl bg-white border border-surface-200 shadow-sm">
          <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-6">
            <Folder className="w-10 h-10 text-primary-500" />
          </div>
          <h3 className="text-xl font-bold text-surface-900 mb-2">No notebooks yet</h3>
          <p className="text-surface-500 max-w-md mx-auto mb-8">
            Create a notebook to group related documents and use AI across multiple sources.
          </p>
          <Button leftIcon={<Plus className="w-4 h-4" />} onClick={() => setShowCreate(true)} size="lg">
            Create Notebook
          </Button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotebooks.map((nb, i) => (
            <Link key={nb._id || nb.id || i} to={`/notebooks/${nb._id || nb.id}`}>
              <Card hoverable className="p-6 h-full flex flex-col bg-white group border-t-4 border-t-primary-500 transition-all hover:shadow-lg hover:-translate-y-0.5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center text-primary-600 border border-primary-100">
                      <Folder className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-surface-900 line-clamp-1">{nb.title}</h3>
                      <div className="flex items-center gap-1 text-xs text-surface-400 mt-0.5">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(nb.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(nb._id || nb.id, e)}
                    className="text-surface-400 hover:text-red-600 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50"
                  >
                    <Trash className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-sm text-surface-500 line-clamp-2 flex-1 mb-4">
                  {nb.description || 'No description provided.'}
                </p>
                <div className="pt-4 border-t border-surface-100 flex items-center gap-2">
                  <Badge variant="secondary" className="bg-surface-50 flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    {(nb.documents || []).length} sources
                  </Badge>
                  <Badge variant="secondary" className="bg-surface-50">
                    {(nb.notes || []).length} notes
                  </Badge>
                </div>
              </Card>
            </Link>
          ))}
          {filteredNotebooks.length === 0 && search && (
            <div className="col-span-full text-center py-12 text-surface-500">
              No notebooks match your search.
            </div>
          )}
        </div>
      )}

      {/* Create Notebook Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setNewTitle(''); setNewDescription(''); }} title="Create Notebook" maxWidth="md">
        <form onSubmit={handleCreateNotebook} className="space-y-4">
          <Input
            label="Notebook Title"
            placeholder="e.g. Machine Learning Fundamentals"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            required
            autoFocus
          />
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">Description (optional)</label>
            <textarea
              value={newDescription}
              onChange={e => setNewDescription(e.target.value)}
              placeholder="What will you study in this notebook?"
              rows={2}
              className="w-full rounded-xl border border-surface-200 px-4 py-2 text-sm text-surface-900 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 resize-none transition-all"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" isLoading={creating} disabled={!newTitle.trim()}>Create Notebook</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
