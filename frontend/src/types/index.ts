// API Types for StudySync 2.0

export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  daily_goal: number;
  theme: string;
  current_streak: number;
  longest_streak: number;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Deck {
  id: string;
  owner_id: string;
  owner_name?: string;
  title: string;
  description: string;
  visibility: 'private' | 'shared' | 'public';
  member_count: number;
  card_count: number;
  cards_due?: number;
  tags: string[];
  share_token?: string;
  created_at: string;
  updated_at: string;
}

export interface DeckListResponse {
  decks: Deck[];
  total: number;
  page: number;
  page_size: number;
}

export interface Card {
  id: string;
  deck_id: string;
  front: string;
  back: string;
  tags: string[];
  hint: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CardListResponse {
  cards: Card[];
  total: number;
  page: number;
  page_size: number;
}

export interface StudyCard {
  id: string;
  front: string;
  back: string;
  is_new: boolean;
  ease_factor: number;
  interval: number;
  repetitions: number;
  due_date: string;
  tags?: string[];
}

export interface ReviewResult {
  card_id: string;
  repetitions: number;
  interval: number;
  ease_factor: number;
  due_at: string;
}

export interface StudyStats {
  total_cards: number;
  cards_studied: number;
  cards_due: number;
  cards_due_today: number;
  new_cards: number;
  reviewed_today: number;
  deck_progress: number;
}

export interface StudySession {
  id: string;
  deck_id: string;
  deck_title?: string;
  started_at: string;
  ended_at: string | null;
  cards_reviewed: number;
  duration_seconds: number;
}

export interface StudyGroup {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  owner_name?: string;
  member_count: number;
  invite_token?: string;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  user_id: string;
  name: string;
  role: string;
  joined_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface Room {
  id: string;
  deck_id: string;
  deck_title?: string;
  created_by: string;
  creator_name?: string;
  name: string;
  status: 'active' | 'ended';
  member_count: number;
  created_at: string;
  started_at?: string;
  ended_at?: string;
}

export interface RoomMember {
  user_id: string;
  name: string;
  status: string;
  joined_at: string;
  is_online: boolean;
}

export interface RoomDetail {
  room: Room;
  members: RoomMember[];
}

export interface ShareTokenResponse {
  share_token: string;
  share_url: string;
}

export type ReviewRating = 'again' | 'hard' | 'good' | 'easy';
