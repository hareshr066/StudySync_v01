import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { roomsApi } from '../api';
import { useAuth } from '../hooks/useAuth';

import type { Room, RoomMember } from '../types';
import { ArrowLeft, Users, Clock, LogOut, Play, Send, MessageSquare, ChevronDown } from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';
import toast from 'react-hot-toast';

interface WSUser { user_id: string; name: string; is_online?: boolean; }
interface ChatMessage { user_id: string; name: string; text: string; timestamp: string; }

export default function RoomPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [room, setRoom] = useState<Room | null>(null);
  const [members, setMembers] = useState<RoomMember[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<WSUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  const [chatOpen, setChatOpen] = useState(true);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');

  const ws = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const pingRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const connectWS = useCallback(() => {
    if (!id) return;
    const token = localStorage.getItem('access_token');
    const apiUrl = import.meta.env.VITE_API_URL || '';
    let wsBase = '';
    if (apiUrl) {
      const url = new URL(apiUrl);
      wsBase = `${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsBase = `${protocol}//${window.location.host}`;
    }
    const wsUrl = `${wsBase}/api/v1/ws/rooms/${id}?token=${token}`;

    const socket = new WebSocket(wsUrl);
    ws.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
          case 'room_state':
          case 'presence_update':
            setOnlineUsers(msg.data.users || []);
            break;
          case 'user_joined':
            toast(`${msg.data.name} joined the room`, { icon: '👋' });
            setOnlineUsers(prev => {
              if (prev.find(u => u.user_id === msg.data.user_id)) return prev;
              return [...prev, { user_id: msg.data.user_id, name: msg.data.name, is_online: true }];
            });
            break;
          case 'user_left':
            toast(`${msg.data.name} left the room`, { icon: '👋' });
            setOnlineUsers(prev => prev.filter(u => u.user_id !== msg.data.user_id));
            break;
          case 'chat_message':
            setChatMessages(prev => [...prev, {
              user_id: msg.data.user_id,
              name: msg.data.name,
              text: msg.data.text,
              timestamp: new Date().toISOString()
            }]);
            break;
        }
      } catch {}
    };

    socket.onclose = () => {
      console.log('WebSocket closed');
      setTimeout(() => {
        if (ws.current === socket) connectWS();
      }, 3000);
    };

    socket.onerror = () => {};
  }, [id]);

  useEffect(() => {
    if (!id) return;
    roomsApi.get(id)
      .then(res => {
        setRoom(res.data.room);
        setMembers(res.data.members);
      })
      .catch(() => { toast.error('Room not found'); navigate('/dashboard'); })
      .finally(() => setLoading(false));

    roomsApi.join(id).catch(() => {});
    connectWS();

    timerRef.current = setInterval(() => setElapsed(prev => prev + 1), 1000);
    pingRef.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      if (ws.current) { ws.current.onclose = null; ws.current.close(); }
      if (timerRef.current) clearInterval(timerRef.current);
      if (pingRef.current) clearInterval(pingRef.current);
      if (id) roomsApi.leave(id).catch(() => {});
    };
  }, [id, connectWS, navigate]);

  const handleLeave = async () => {
    if (!id) return;
    if (ws.current) { ws.current.onclose = null; ws.current.close(); }
    await roomsApi.leave(id).catch(() => {});
    toast.success('Left room');
    navigate(`/decks/${room?.deck_id || ''}`);
  };

  const sendChatMessage = () => {
    if (!chatInput.trim() || ws.current?.readyState !== WebSocket.OPEN) return;
    ws.current.send(JSON.stringify({
      type: 'chat_message',
      data: { text: chatInput.trim() }
    }));
    // Optimistic local message
    setChatMessages(prev => [...prev, {
      user_id: user?.id || '',
      name: user?.name || 'You',
      text: chatInput.trim(),
      timestamp: new Date().toISOString()
    }]);
    setChatInput('');
  };

  const formatTime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return h > 0
      ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
      : `${m}:${String(sec).padStart(2, '0')}`;
  };

  if (loading) return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent" />
    </div>
  );

  if (!room) return null;

  const displayUsers = onlineUsers.length > 0 ? onlineUsers : members.filter(m => m.is_online);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link to={`/decks/${room.deck_id}`} className="flex items-center gap-1 text-sm font-medium text-surface-500 hover:text-surface-900 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to deck
        </Link>
        <Button variant="danger" onClick={handleLeave} leftIcon={<LogOut className="w-4 h-4" />}>
          Leave Room
        </Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: Room info + controls */}
        <div className="lg:col-span-2 space-y-4">
          {/* Room card */}
          <Card className="p-8 text-center bg-gradient-to-br from-white to-surface-50">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Badge variant="info" className="uppercase tracking-widest text-xs flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-accent-500 animate-pulse" /> Live Session
              </Badge>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-surface-900 mb-2">{room.name}</h1>
            <p className="text-surface-500 font-medium">{room.deck_title || 'Study Session'}</p>

            {/* Timer */}
            <div className="mt-8 inline-flex items-center gap-3 px-6 py-4 rounded-2xl bg-surface-100 border border-surface-200">
              <Clock className="w-6 h-6 text-primary-500" />
              <span className="text-3xl font-mono font-bold text-surface-900">{formatTime(elapsed)}</span>
            </div>
          </Card>

          {/* Participants */}
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-5">
              <Users className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-bold text-surface-900">Participants ({displayUsers.length})</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {displayUsers.map((u, i) => (
                <div key={u.user_id || i} className="flex items-center gap-3 p-3 rounded-xl bg-surface-50 border border-surface-100">
                  <div className="w-9 h-9 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold shrink-0">
                    {u.name?.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-surface-900 truncate">{u.name}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-accent-500" />
                      <span className="text-[10px] font-medium text-surface-500">Online</span>
                    </div>
                  </div>
                </div>
              ))}
              {displayUsers.length === 0 && (
                <p className="col-span-full text-sm text-surface-400 text-center py-4">
                  No other users online. Share the room link to invite others.
                </p>
              )}
            </div>
          </Card>

          {/* Start studying */}
          {room.deck_id && (
            <Button
              size="lg"
              className="w-full py-6 text-lg shadow-xl shadow-primary-500/20"
              onClick={() => navigate(`/decks/${room.deck_id}/study`)}
              leftIcon={<Play className="w-5 h-5" />}
            >
              Start Studying
            </Button>
          )}
        </div>

        {/* Right: Chat */}
        <div className="flex flex-col">
          <Card className="flex flex-col h-[520px]">
            <button
              onClick={() => setChatOpen(o => !o)}
              className="flex items-center justify-between p-4 border-b border-surface-100 hover:bg-surface-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary-500" />
                <span className="font-bold text-surface-900 text-sm">Room Chat</span>
                {chatMessages.length > 0 && (
                  <Badge variant="primary" className="text-[10px]">{chatMessages.length}</Badge>
                )}
              </div>
              <ChevronDown className={`w-4 h-4 text-surface-400 transition-transform ${chatOpen ? 'rotate-180' : ''}`} />
            </button>

            {chatOpen && (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface-50/50">
                  {chatMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <MessageSquare className="w-8 h-8 text-surface-200 mx-auto mb-2" />
                      <p className="text-xs text-surface-400">No messages yet. Say hello!</p>
                    </div>
                  ) : (
                    chatMessages.map((msg, i) => {
                      const isOwn = msg.user_id === user?.id;
                      return (
                        <div key={i} className={`flex flex-col ${isOwn ? 'items-end' : 'items-start'}`}>
                          {!isOwn && (
                            <span className="text-[10px] font-semibold text-surface-500 mb-1 px-1">{msg.name}</span>
                          )}
                          <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                            isOwn
                              ? 'bg-primary-600 text-white rounded-br-sm'
                              : 'bg-white border border-surface-200 text-surface-800 rounded-bl-sm'
                          }`}>
                            {msg.text}
                          </div>
                          <span className="text-[9px] text-surface-400 mt-0.5 px-1">
                            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      );
                    })
                  )}
                  <div ref={chatBottomRef} />
                </div>

                {/* Input */}
                <div className="p-3 border-t border-surface-100 bg-white">
                  <form
                    onSubmit={e => { e.preventDefault(); sendChatMessage(); }}
                    className="flex items-center gap-2"
                  >
                    <input
                      value={chatInput}
                      onChange={e => setChatInput(e.target.value)}
                      placeholder="Type a message..."
                      className="flex-1 text-sm bg-surface-50 border border-surface-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all"
                      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); } }}
                    />
                    <button
                      type="submit"
                      disabled={!chatInput.trim()}
                      className="w-9 h-9 rounded-xl bg-primary-600 text-white flex items-center justify-center hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </form>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
