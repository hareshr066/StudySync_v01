import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { decksApi, cardsApi, studyApi, roomsApi } from '../api';
import { useAuth } from '../hooks/useAuth';
import type { Deck, Card, StudyStats, Room } from '../types';
import { Brain, Users, Share2, Trash2, ArrowLeft, Plus, Check, Copy } from 'lucide-react';
import { Button, Card as UICard, Badge, Input, Modal } from '../components/ui';
import toast from 'react-hot-toast';

export default function DeckDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showAddCard, setShowAddCard] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  
  const [front, setFront] = useState('');
  const [back, setBack] = useState('');
  const [tags, setTags] = useState('');
  const [adding, setAdding] = useState(false);
  
  const [shareUrl, setShareUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [roomName, setRoomName] = useState('');

  const isOwner = deck?.owner_id === user?.id;

  const loadData = async () => {
    if (!id) return;
    try {
      const [deckRes, cardsRes, statsRes, roomsRes] = await Promise.all([
        decksApi.get(id), 
        cardsApi.list(id, 1, 200), 
        studyApi.deckStats(id), 
        roomsApi.list(id)
      ]);
      setDeck(deckRes.data);
      setCards(cardsRes.data.cards);
      setStats(statsRes.data);
      setRooms(roomsRes.data.rooms);
    } catch { 
      toast.error('Failed to load deck'); 
      navigate('/decks'); 
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => { loadData(); }, [id]);

  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setAdding(true);
    try {
      const parsedTags = tags.split(',').map(t => t.trim()).filter(Boolean);
      await cardsApi.create(id, { front, back, tags: parsedTags });
      toast.success('Card added!');
      setFront(''); setBack(''); setTags('');
      loadData();
    } catch (err: any) { 
      toast.error(err.response?.data?.detail || 'Failed to add card'); 
    } finally { 
      setAdding(false); 
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!confirm('Delete this card?')) return;
    try {
      await cardsApi.delete(cardId);
      toast.success('Card deleted');
      loadData();
    } catch { toast.error('Failed to delete card'); }
  };

  const handleShare = async () => {
    if (!id) return;
    try {
      const res = await decksApi.share(id);
      setShareUrl(res.data.share_url);
      setShowShare(true);
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed to generate share link'); }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Link copied!');
  };

  const handleDeleteDeck = async () => {
    if (!id || !confirm('Delete this entire deck and all its cards? This cannot be undone.')) return;
    try {
      await decksApi.delete(id);
      toast.success('Deck deleted');
      navigate('/decks');
    } catch { toast.error('Failed to delete deck'); }
  };

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      const res = await roomsApi.create({ deck_id: id, name: roomName });
      toast.success('Room created!');
      navigate(`/rooms/${res.data.id}`);
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed to create room'); }
  };

  if (loading) return (
    <div className="space-y-6 max-w-5xl mx-auto animate-pulse">
      <div className="h-8 w-64 bg-surface-200 rounded-lg" />
      <div className="h-32 bg-surface-200 rounded-2xl" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-surface-200 rounded-xl" />)}
      </div>
    </div>
  );

  if (!deck) return null;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <Link to="/decks" className="inline-flex items-center gap-1 text-sm font-medium text-surface-500 hover:text-surface-900 mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to decks
          </Link>
          <h1 className="text-3xl font-bold text-surface-900">{deck.title}</h1>
          {deck.description && <p className="text-surface-600 mt-2 text-lg">{deck.description}</p>}
          
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <Badge variant="secondary">{deck.card_count} cards</Badge>
            <Badge variant="secondary">{deck.member_count} member{deck.member_count !== 1 ? 's' : ''}</Badge>
            <Badge variant={deck.visibility === 'public' ? 'success' : deck.visibility === 'shared' ? 'primary' : 'secondary'}>
              {deck.visibility.charAt(0).toUpperCase() + deck.visibility.slice(1)}
            </Badge>
            {deck.tags?.map(tag => (
              <Badge key={tag} variant="info">{tag}</Badge>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {isOwner && (
            <>
              <Button variant="outline" onClick={handleShare} title="Share Deck" leftIcon={<Share2 className="w-4 h-4" />}>
                Share
              </Button>
              <Button variant="danger" onClick={handleDeleteDeck} title="Delete Deck" leftIcon={<Trash2 className="w-4 h-4" />}>
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <UICard className="p-4 flex flex-col items-center text-center justify-center bg-primary-50 border-primary-100">
          <div className="text-3xl font-bold text-primary-700">{stats?.total_cards || 0}</div>
          <div className="text-xs font-medium text-primary-600 uppercase tracking-wider mt-1">Total Cards</div>
        </UICard>
        <UICard className="p-4 flex flex-col items-center text-center justify-center bg-amber-50 border-amber-100">
          <div className="text-3xl font-bold text-amber-700">{stats?.cards_due || 0}</div>
          <div className="text-xs font-medium text-amber-600 uppercase tracking-wider mt-1">Cards Due</div>
        </UICard>
        <UICard className="p-4 flex flex-col items-center text-center justify-center bg-accent-50 border-accent-100">
          <div className="text-3xl font-bold text-accent-700">{stats?.reviewed_today || 0}</div>
          <div className="text-xs font-medium text-accent-600 uppercase tracking-wider mt-1">Reviewed Today</div>
        </UICard>
        <UICard className="p-4 flex flex-col items-center text-center justify-center bg-green-50 border-green-100">
          <div className="text-3xl font-bold text-green-700">{stats?.deck_progress || 0}%</div>
          <div className="text-xs font-medium text-green-600 uppercase tracking-wider mt-1">Progress</div>
        </UICard>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 p-4 bg-surface-100 rounded-2xl">
        {(deck.card_count > 0) && (
          <Button onClick={() => navigate(`/decks/${id}/study`)} leftIcon={<Brain className="w-4 h-4" />}>
            Start Study
          </Button>
        )}
        {isOwner && (
          <Button variant="secondary" onClick={() => setShowAddCard(true)} leftIcon={<Plus className="w-4 h-4" />}>
            Add Card
          </Button>
        )}
        <Button variant="outline" onClick={() => { setRoomName(`${deck.title} Study Session`); setShowCreateRoom(true); }} leftIcon={<Users className="w-4 h-4" />}>
          Create Room
        </Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Col: Cards List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-surface-900">Flashcards ({cards.length})</h2>
          </div>

          {cards.length === 0 ? (
            <UICard className="p-12 text-center border-dashed">
              <p className="text-surface-500 mb-4">No cards yet. Add your first card to start studying.</p>
              {isOwner && (
                <Button onClick={() => setShowAddCard(true)} leftIcon={<Plus className="w-4 h-4" />}>
                  Add Card
                </Button>
              )}
            </UICard>
          ) : (
            <div className="space-y-3">
              {cards.map((card, idx) => (
                <UICard key={card.id} className="p-4 flex items-start gap-4 group">
                  <span className="text-sm font-medium text-surface-400 w-6 text-right shrink-0">{idx + 1}</span>
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="font-medium text-surface-900">{card.front}</div>
                    <div className="text-sm text-surface-600">{card.back}</div>
                    {card.tags && card.tags.length > 0 && (
                      <div className="flex gap-1.5 mt-2">
                        {card.tags.map(t => <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>)}
                      </div>
                    )}
                  </div>
                  {isOwner && (
                    <button 
                      onClick={() => handleDeleteCard(card.id)} 
                      className="opacity-0 group-hover:opacity-100 p-2 rounded-lg text-red-500 hover:bg-red-50 transition-all shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </UICard>
              ))}
            </div>
          )}
        </div>

        {/* Right Col: Rooms */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-surface-900">Active Rooms</h2>
          {rooms.length === 0 ? (
            <UICard className="p-6 text-center border-dashed">
              <p className="text-sm text-surface-500">No active rooms for this deck.</p>
            </UICard>
          ) : (
            <div className="space-y-3">
              {rooms.map(room => (
                <Link key={room.id} to={`/rooms/${room.id}`}>
                  <UICard hoverable className="p-4 border-l-4 border-l-accent-500">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-semibold text-surface-900">{room.name}</div>
                      <div className="flex items-center gap-1.5 text-accent-600 text-xs font-bold uppercase">
                        <div className="w-2 h-2 rounded-full bg-accent-500 animate-pulse" /> Live
                      </div>
                    </div>
                    <div className="text-sm text-surface-500 flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" /> {room.member_count} participant{room.member_count !== 1 ? 's' : ''}
                    </div>
                  </UICard>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <Modal isOpen={showAddCard} onClose={() => setShowAddCard(false)} title="Add Flashcard" maxWidth="md">
        <form onSubmit={handleAddCard} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">Question (Front)</label>
            <textarea 
              value={front} 
              onChange={e => setFront(e.target.value)} 
              required 
              rows={3}
              className="w-full rounded-xl border border-surface-200 px-4 py-2 text-surface-900 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 resize-none"
              placeholder="What is BFS?" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">Answer (Back)</label>
            <textarea 
              value={back} 
              onChange={e => setBack(e.target.value)} 
              required 
              rows={3}
              className="w-full rounded-xl border border-surface-200 px-4 py-2 text-surface-900 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 resize-none"
              placeholder="Breadth First Search traverses..." 
            />
          </div>
          <Input
            label="Tags (Comma separated)"
            placeholder="algo, graph, easy"
            value={tags}
            onChange={e => setTags(e.target.value)}
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="ghost" onClick={() => setShowAddCard(false)}>Cancel</Button>
            <Button type="submit" isLoading={adding}>Add Card</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showShare} onClose={() => setShowShare(false)} title="Share Deck" maxWidth="md">
        <p className="text-surface-600 text-sm mb-4">Share this link with friends so they can join your deck:</p>
        <div className="flex items-center gap-2">
          <Input value={shareUrl} readOnly className="flex-1" />
          <Button onClick={handleCopy} variant="secondary">
            {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
          </Button>
        </div>
      </Modal>

      <Modal isOpen={showCreateRoom} onClose={() => setShowCreateRoom(false)} title="Create Study Room" maxWidth="md">
        <form onSubmit={handleCreateRoom} className="space-y-4">
          <Input 
            label="Room Name"
            value={roomName} 
            onChange={e => setRoomName(e.target.value)} 
            required
            placeholder="e.g. DSA Trees Revision" 
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="ghost" onClick={() => setShowCreateRoom(false)}>Cancel</Button>
            <Button type="submit">Create Room</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
