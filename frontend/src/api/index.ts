import api from './client';
import type {
  TokenResponse, User, Deck, DeckListResponse, Card, CardListResponse,
  StudyCard, ReviewResult, StudyStats, Room, RoomDetail, ShareTokenResponse,
  ReviewRating, StudySession, StudyGroup, GroupMember, Notification,
} from '../types';

// Auth
export const authApi = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post<TokenResponse>('/api/v1/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/api/v1/auth/login', data),
  me: () => api.get<User>('/api/v1/auth/me'),
  logout: () => api.post('/api/v1/auth/logout'),
};

// Users
export const usersApi = {
  getProfile: () => api.get<User>('/api/v1/users/me/profile'),
  updateProfile: (data: Partial<{ name: string; daily_goal: number; theme: string }>) =>
    api.patch<User>('/api/v1/users/me/profile', data),
};

// Decks
export const decksApi = {
  list: (page = 1, pageSize = 20, search?: string) =>
    api.get<DeckListResponse>('/api/v1/decks', { params: { page, page_size: pageSize, search } }),
  discover: (page = 1, pageSize = 20, sort = 'popular') =>
    api.get<DeckListResponse>('/api/v1/decks/discover', { params: { page, page_size: pageSize, sort } }),
  joinPublic: (deckId: string) => api.post<Deck>(`/api/v1/decks/discover/${deckId}/join`),
  get: (id: string) => api.get<Deck>(`/api/v1/decks/${id}`),
  create: (data: { title: string; description?: string; visibility?: string; tags?: string[] }) =>
    api.post<Deck>('/api/v1/decks', data),
  update: (id: string, data: Partial<{ title: string; description: string; visibility: string; tags: string[] }>) =>
    api.patch<Deck>(`/api/v1/decks/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/decks/${id}`),
  share: (id: string) => api.post<ShareTokenResponse>(`/api/v1/decks/${id}/share`),
  join: (token: string) => api.post<Deck>(`/api/v1/decks/join/${token}`),
};

// Cards
export const cardsApi = {
  list: (deckId: string, page = 1, pageSize = 50) =>
    api.get<CardListResponse>(`/api/v1/decks/${deckId}/cards`, { params: { page, page_size: pageSize } }),
  create: (deckId: string, data: { front: string; back: string; tags?: string[]; hint?: string }) =>
    api.post<Card>(`/api/v1/decks/${deckId}/cards`, data),
  update: (cardId: string, data: Partial<{ front: string; back: string; tags: string[]; hint: string }>) =>
    api.patch<Card>(`/api/v1/cards/${cardId}`, data),
  delete: (cardId: string) => api.delete(`/api/v1/cards/${cardId}`),
  importCsv: (deckId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ imported: number; skipped: number; errors: number; details: string[] }>(`/api/v1/decks/${deckId}/cards/import`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  exportCsv: (deckId: string) => api.get(`/api/v1/decks/${deckId}/cards/export`, { responseType: 'blob' }),
};

// Study
export const studyApi = {
  nextCard: (deckId: string) => api.get<StudyCard | null>(`/api/v1/study/${deckId}/next`),
  submitReview: (data: { card_id: string; deck_id: string; rating: ReviewRating }) =>
    api.post<ReviewResult>('/api/v1/study/review', data),
  deckStats: (deckId: string) => api.get<StudyStats>(`/api/v1/study/${deckId}/stats`),
  overallStats: () => api.get<StudyStats>('/api/v1/study/stats/overall'),
};

// Sessions
export const sessionsApi = {
  list: () => api.get<{ sessions: StudySession[]; total: number }>('/api/v1/study/sessions'),
  start: (deckId: string) => api.post<StudySession>('/api/v1/study/sessions', { deck_id: deckId }),
  end: (sessionId: string, cardsReviewed: number) => api.patch<StudySession>(`/api/v1/study/sessions/${sessionId}`, { cards_reviewed: cardsReviewed }),
};

// Groups
export const groupsApi = {
  list: () => api.get<{ groups: StudyGroup[]; total: number }>('/api/v1/groups'),
  create: (data: { name: string; description: string }) => api.post<StudyGroup>('/api/v1/groups', data),
  get: (id: string) => api.get<{ group: StudyGroup; members: GroupMember[] }>(`/api/v1/groups/${id}`),
  update: (id: string, data: Partial<{ name: string; description: string }>) => api.patch<StudyGroup>(`/api/v1/groups/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/groups/${id}`),
  invite: (id: string) => api.post<ShareTokenResponse>(`/api/v1/groups/${id}/invite`),
  join: (token: string) => api.post<StudyGroup>(`/api/v1/groups/join/${token}`),
  leave: (id: string) => api.post(`/api/v1/groups/${id}/leave`),
};

// Notifications
export const notificationsApi = {
  list: () => api.get<{ notifications: Notification[]; total: number; unread_count: number }>('/api/v1/notifications'),
  markRead: (id: string) => api.patch(`/api/v1/notifications/${id}/read`),
  markAllRead: () => api.post('/api/v1/notifications/read-all'),
};

// Rooms
export const roomsApi = {
  list: (deckId?: string) =>
    api.get<{ rooms: Room[]; total: number }>('/api/v1/rooms', { params: { deck_id: deckId } }),
  get: (id: string) => api.get<RoomDetail>(`/api/v1/rooms/${id}`),
  create: (data: { deck_id: string; name: string }) =>
    api.post<Room>('/api/v1/rooms', data),
  join: (id: string) => api.post(`/api/v1/rooms/${id}/join`),
  leave: (id: string) => api.post(`/api/v1/rooms/${id}/leave`),
  end: (id: string) => api.post(`/api/v1/rooms/${id}/end`),
};

// Documents
export const documentsApi = {
  list: () => api.get<{ documents: any[]; total: number }>('/api/v1/documents'),
  get: (id: string) => api.get<any>(`/api/v1/documents/${id}`),
  upload: (title: string, description: string, file: File) => {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('file', file);
    return api.post<any>('/api/v1/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  delete: (id: string) => api.delete(`/api/v1/documents/${id}`),
  retry: (id: string) => api.post(`/api/v1/documents/${id}/retry`),
};

// Notebooks
export const notebooksApi = {
  list: () => api.get<{ notebooks: any[]; total: number }>('/api/v1/notebooks'),
  get: (id: string) => api.get<any>(`/api/v1/notebooks/${id}`),
  create: (data: { title: string; description?: string }) => api.post<any>('/api/v1/notebooks', data),
  update: (id: string, data: { title?: string; description?: string }) => api.patch<any>(`/api/v1/notebooks/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/notebooks/${id}`),
  addDocument: (nbId: string, docId: string) => api.post<any>(`/api/v1/notebooks/${nbId}/documents/${docId}`),
  removeDocument: (nbId: string, docId: string) => api.delete(`/api/v1/notebooks/${nbId}/documents/${docId}`),
  getNotes: (nbId: string) => api.get<{ notes: any[]; total: number }>(`/api/v1/notebooks/${nbId}/notes`),
  createNote: (nbId: string, data: { title: string; content?: any; tags?: string[] }) =>
    api.post<any>(`/api/v1/notebooks/${nbId}/notes`, data),
};

// Notes
export const notesApi = {
  list: () => api.get<{ notes: any[]; total: number }>('/api/v1/notes'),
  get: (id: string) => api.get<any>(`/api/v1/notes/${id}`),
  create: (data: { title: string; content?: any; tags?: string[] }) => api.post<any>('/api/v1/notes', data),
  update: (id: string, data: { title?: string; content?: any; tags?: string[] }) => api.patch<any>(`/api/v1/notes/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/notes/${id}`),
};

// AI
export const aiApi = {
  generate: (data: { prompt: string; context_type?: string; context_id?: string; mode?: string }) =>
    api.post<any>('/api/v1/ai/generate', data),
  generateFlashcards: (data: { count: number; difficulty: string; context_type?: string; context_id?: string }) =>
    api.post<any>('/api/v1/ai/flashcards', data),
};

// AI Conversations (persistent chat)
export const conversationsApi = {
  list: (notebookId?: string) =>
    api.get<{ conversations: any[]; total: number }>('/api/v1/conversations', { params: notebookId ? { notebook_id: notebookId } : {} }),
  create: (data: { title?: string; context_type?: string; context_id?: string; notebook_id?: string }) =>
    api.post<any>('/api/v1/conversations', data),
  get: (id: string) => api.get<any>(`/api/v1/conversations/${id}`),
  updateTitle: (id: string, title: string) => api.patch(`/api/v1/conversations/${id}`, { title }),
  delete: (id: string) => api.delete(`/api/v1/conversations/${id}`),
  addMessage: (id: string, data: { prompt: string; mode?: string; context_type?: string; context_id?: string }) =>
    api.post<any>(`/api/v1/conversations/${id}/messages`, data),
};

// Quizzes
export const quizzesApi = {
  generate: (data: { count?: number; difficulty?: string; type?: string; context_type?: string; context_id?: string }) =>
    api.post<any>('/api/v1/quizzes/generate', data),
  list: () => api.get<{ quizzes: any[]; total: number }>('/api/v1/quizzes'),
  get: (id: string) => api.get<any>(`/api/v1/quizzes/${id}`),
  attempt: (id: string, answers: string[]) => api.post<any>(`/api/v1/quizzes/${id}/attempt`, { answers }),
  delete: (id: string) => api.delete(`/api/v1/quizzes/${id}`),
};

// Study Plans
export const studyPlansApi = {
  generate: (data: { goal: string; exam_date: string; minutes_per_day: number; deck_ids: string[] }) =>
    api.post<any>('/api/v1/study-plans/generate', data),
  list: () => api.get<{ plans: any[]; total: number }>('/api/v1/study-plans'),
  get: (id: string) => api.get<any>(`/api/v1/study-plans/${id}`),
  delete: (id: string) => api.delete(`/api/v1/study-plans/${id}`),
};

// Search
export const searchApi = {
  search: (q: string) => api.get<any>('/api/v1/search', { params: { q } }),
};



