import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { groupsApi, roomsApi, decksApi } from '../api';
import type { StudyGroup, GroupMember, Room, Deck } from '../types';
import { useAuth } from '../hooks/useAuth';
import { Users, UserPlus, Trash, LogOut, Radio, BookOpen, Copy, Check, ArrowLeft, Shield, Sparkles } from 'lucide-react';
import { Button, Card, Modal, Spinner, Input } from '../components/ui';
import toast from 'react-hot-toast';

export default function GroupDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [group, setGroup] = useState<StudyGroup | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'members' | 'rooms' | 'decks'>('members');

  // Modals
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteUrl, setInviteUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [isCreateRoomOpen, setIsCreateRoomOpen] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [selectedDeckId, setSelectedDeckId] = useState('');
  const [userDecks, setUserDecks] = useState<Deck[]>([]);
  const [activeRooms, setActiveRooms] = useState<Room[]>([]);
  const [creatingRoom, setCreatingRoom] = useState(false);

  useEffect(() => {
    if (id) {
      loadGroupData();
    }
  }, [id]);

  const loadGroupData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await groupsApi.get(id);
      setGroup(res.data.group);
      setMembers(res.data.members);
      // Load rooms and decks
      try {
        const roomsRes = await roomsApi.list();
        setActiveRooms(roomsRes.data.rooms.filter(r => r.status === 'active'));
        const decksRes = await decksApi.list();
        setUserDecks(decksRes.data.decks);
        if (decksRes.data.decks.length > 0) {
          setSelectedDeckId(decksRes.data.decks[0].id);
        }
      } catch {
        // Soft fail
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load group details');
      navigate('/groups');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvite = async () => {
    if (!id) return;
    try {
      const res = await groupsApi.invite(id);
      setInviteUrl(res.data.share_url);
      setIsInviteOpen(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to generate invite');
    }
  };

  const handleCopyInvite = () => {
    if (!inviteUrl) return;
    navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    toast.success('Invite link copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLeaveGroup = async () => {
    if (!id) return;
    if (!confirm('Are you sure you want to leave this group?')) return;
    try {
      await groupsApi.leave(id);
      toast.success('Left group');
      navigate('/groups');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to leave group');
    }
  };

  const handleDeleteGroup = async () => {
    if (!id) return;
    if (!confirm('Are you sure you want to permanently delete this group?')) return;
    try {
      await groupsApi.delete(id);
      toast.success('Group deleted');
      navigate('/groups');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete group');
    }
  };

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeckId || !roomName.trim()) return;
    setCreatingRoom(true);
    try {
      const res = await roomsApi.create({
        name: roomName.trim(),
        deck_id: selectedDeckId,
      });
      toast.success('Study room started!');
      setIsCreateRoomOpen(false);
      navigate(`/rooms/${res.data.id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create room');
    } finally {
      setCreatingRoom(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!group) return null;

  const isOwner = user?.id === group.owner_id;

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Back button */}
      <button
        onClick={() => navigate('/groups')}
        className="inline-flex items-center gap-2 text-sm text-surface-500 hover:text-surface-900 transition-colors font-medium"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Groups
      </button>

      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-surface-200 p-8 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-surface-900">{group.name}</h1>
              {isOwner && (
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-700 border border-primary-200">
                  <Shield className="w-3 h-3" /> Owner
                </span>
              )}
            </div>
            {group.description && (
              <p className="text-surface-600 max-w-2xl text-sm leading-relaxed">{group.description}</p>
            )}
            <div className="flex items-center gap-4 mt-4 text-xs font-medium text-surface-400">
              <span className="flex items-center gap-1.5"><Users className="w-4 h-4" /> {members.length} members</span>
              <span>•</span>
              <span>Owner: {group.owner_name || 'Admin'}</span>
              <span>•</span>
              <span>Created {new Date(group.created_at).toLocaleDateString()}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="secondary"
              leftIcon={<UserPlus className="w-4 h-4" />}
              onClick={handleGenerateInvite}
            >
              Invite
            </Button>
            <Button
              leftIcon={<Radio className="w-4 h-4" />}
              onClick={() => setIsCreateRoomOpen(true)}
            >
              Start Room
            </Button>
            {isOwner ? (
              <Button variant="ghost" onClick={handleDeleteGroup} className="text-red-600 hover:bg-red-50">
                <Trash className="w-4 h-4" />
              </Button>
            ) : (
              <Button variant="ghost" onClick={handleLeaveGroup} className="text-surface-600 hover:bg-surface-100">
                <LogOut className="w-4 h-4 mr-1" /> Leave
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-200 flex gap-6">
        <button
          onClick={() => setActiveTab('members')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'members'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-surface-500 hover:text-surface-700'
          }`}
        >
          Members ({members.length})
        </button>
        <button
          onClick={() => setActiveTab('rooms')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'rooms'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-surface-500 hover:text-surface-700'
          }`}
        >
          Study Rooms ({activeRooms.length})
        </button>
        <button
          onClick={() => setActiveTab('decks')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'decks'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-surface-500 hover:text-surface-700'
          }`}
        >
          Study Decks ({userDecks.length})
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'members' && (
        <Card className="divide-y divide-surface-100 bg-white overflow-hidden shadow-sm">
          {members.map((m) => (
            <div key={m.user_id} className="p-4 sm:p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-sm">
                  {m.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="text-sm font-bold text-surface-900 flex items-center gap-2">
                    {m.name}
                    {m.role === 'owner' && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                        Owner
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-surface-400">
                    Joined {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : 'recently'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Card>
      )}

      {activeTab === 'rooms' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-surface-900">Live Study Rooms</h3>
            <Button size="sm" leftIcon={<Radio className="w-4 h-4" />} onClick={() => setIsCreateRoomOpen(true)}>
              Start New Room
            </Button>
          </div>
          {activeRooms.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-surface-200 border-dashed">
              <Radio className="w-12 h-12 text-surface-300 mx-auto mb-3" />
              <h4 className="text-base font-bold text-surface-800 mb-1">No active study rooms</h4>
              <p className="text-sm text-surface-500 mb-4">Start a live room to study flashcards together with classmates.</p>
              <Button size="sm" onClick={() => setIsCreateRoomOpen(true)}>Start Room Now</Button>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 gap-4">
              {activeRooms.map((room) => (
                <Card key={room.id} hoverable className="p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> Live
                      </span>
                      <span className="text-xs text-surface-400">{room.member_count} joined</span>
                    </div>
                    <h4 className="font-bold text-surface-900 text-base">{room.name}</h4>
                    {room.deck_title && <p className="text-xs text-surface-500 mt-1">Deck: {room.deck_title}</p>}
                  </div>
                  <Button
                    className="mt-4 w-full"
                    size="sm"
                    onClick={() => navigate(`/rooms/${room.id}`)}
                  >
                    Join Room
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'decks' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-surface-900">Available Decks for Study</h3>
            <Button size="sm" leftIcon={<BookOpen className="w-4 h-4" />} onClick={() => navigate('/decks')}>
              Manage Decks
            </Button>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {userDecks.map((deck) => (
              <Card key={deck.id} hoverable className="p-5 flex flex-col justify-between">
                <div>
                  <h4 className="font-bold text-surface-900 text-base">{deck.title}</h4>
                  <p className="text-xs text-surface-500 mt-1 line-clamp-2">{deck.description || 'No description'}</p>
                  <div className="text-xs text-surface-400 mt-3 font-medium">
                    {deck.card_count} cards
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button size="sm" variant="secondary" className="flex-1" onClick={() => navigate(`/decks/${deck.id}`)}>
                    View Deck
                  </Button>
                  <Button size="sm" className="flex-1" onClick={() => navigate(`/decks/${deck.id}/study`)}>
                    Study Now
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Invite Modal */}
      <Modal isOpen={isInviteOpen} onClose={() => setIsInviteOpen(false)} title="Invite Classmates">
        <div className="space-y-4">
          <p className="text-sm text-surface-600">
            Share this link with your classmates. Anyone with this link can join this study group:
          </p>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-surface-50 border border-surface-200">
            <input
              type="text"
              readOnly
              value={inviteUrl}
              className="flex-1 bg-transparent text-sm text-surface-800 outline-none select-all"
            />
            <Button size="sm" onClick={handleCopyInvite} leftIcon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}>
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Start Room Modal */}
      <Modal isOpen={isCreateRoomOpen} onClose={() => setIsCreateRoomOpen(false)} title="Start Study Room">
        <form onSubmit={handleCreateRoom} className="space-y-4">
          <Input
            label="Room Name"
            placeholder="e.g. Finals Prep Room"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            required
          />
          <div>
            <label className="block text-xs font-semibold text-surface-700 uppercase tracking-wider mb-1.5">
              Select Flashcard Deck
            </label>
            <select
              value={selectedDeckId}
              onChange={(e) => setSelectedDeckId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-surface-200 bg-white text-sm text-surface-900 outline-none focus:border-primary-500"
              required
            >
              {userDecks.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.card_count} cards)
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="ghost" onClick={() => setIsCreateRoomOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={creatingRoom} leftIcon={<Sparkles className="w-4 h-4" />}>
              Launch Room
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
