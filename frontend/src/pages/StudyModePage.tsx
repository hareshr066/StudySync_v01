import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { studyApi, decksApi } from '../api';
import type { StudyCard, Deck, StudyStats, ReviewRating } from '../types';
import { ArrowLeft, RotateCcw, CheckCircle2 } from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';
import toast from 'react-hot-toast';

export default function StudyModePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [card, setCard] = useState<StudyCard | null>(null);
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewedCount, setReviewedCount] = useState(0);
  const [done, setDone] = useState(false);

  const loadNext = useCallback(async () => {
    if (!id) return;
    setShowAnswer(false);
    setLoading(true);
    try {
      const [cardRes, statsRes] = await Promise.all([
        studyApi.nextCard(id),
        studyApi.deckStats(id),
      ]);
      setStats(statsRes.data);
      if (cardRes.data) {
        setCard(cardRes.data);
        setDone(false);
      } else {
        setCard(null);
        setDone(true);
      }
    } catch {
      toast.error('Failed to load card');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    decksApi.get(id).then(r => setDeck(r.data)).catch(() => navigate('/decks'));
    loadNext();
  }, [id, loadNext, navigate]);

  const handleRate = async (rating: ReviewRating) => {
    if (!card || !id || submitting) return;
    setSubmitting(true);
    try {
      await studyApi.submitReview({ card_id: card.id, deck_id: id, rating });
      setReviewedCount(prev => prev + 1);
      await loadNext();
    } catch {
      toast.error('Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (submitting) return;
      if (!showAnswer) {
        if (e.code === 'Space' || e.code === 'Enter') { e.preventDefault(); setShowAnswer(true); }
      } else {
        if (e.key === '1') handleRate('again');
        if (e.key === '2') handleRate('hard');
        if (e.key === '3') handleRate('good');
        if (e.key === '4') handleRate('easy');
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showAnswer, card, submitting]);

  const ratingButtons: { rating: ReviewRating; label: string; color: string; key: string }[] = [
    { rating: 'again', label: 'Again', color: 'bg-red-500 hover:bg-red-600 text-white', key: '1' },
    { rating: 'hard', label: 'Hard', color: 'bg-amber-500 hover:bg-amber-600 text-white', key: '2' },
    { rating: 'good', label: 'Good', color: 'bg-primary-500 hover:bg-primary-600 text-white', key: '3' },
    { rating: 'easy', label: 'Easy', color: 'bg-accent-500 hover:bg-accent-600 text-white', key: '4' },
  ];

  if (loading && !card) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link to={`/decks/${id}`} className="flex items-center gap-1 text-sm font-medium text-surface-500 hover:text-surface-900 transition-colors">
          <ArrowLeft className="w-4 h-4" /> {deck?.title || 'Back'}
        </Link>
        <div className="text-sm font-medium text-surface-500">
          {reviewedCount} reviewed {stats ? `• ${stats.cards_due + stats.new_cards} remaining` : ''}
        </div>
      </div>

      {/* Progress bar */}
      {stats && stats.total_cards > 0 && (
        <div className="w-full h-2 rounded-full bg-surface-100 overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-500"
            style={{ width: `${Math.min(100, stats.deck_progress)}%` }} />
        </div>
      )}

      {done ? (
        /* Done state */
        <Card className="text-center py-20 px-4 border-dashed border-2 border-surface-200">
          <CheckCircle2 className="w-16 h-16 text-accent-500 mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-surface-900 mb-3">You're all caught up! 🎉</h2>
          <p className="text-surface-500 mb-2">You've reviewed all due cards in this deck.</p>
          <p className="text-surface-600 font-medium text-sm mb-8">Reviewed {reviewedCount} card{reviewedCount !== 1 ? 's' : ''} this session</p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="secondary" onClick={() => navigate(`/decks/${id}`)}>
              Back to Deck
            </Button>
            <Button onClick={() => { setReviewedCount(0); loadNext(); }} leftIcon={<RotateCcw className="w-4 h-4" />}>
              Study Again
            </Button>
          </div>
        </Card>
      ) : card ? (
        /* Card display */
        <div className="space-y-6">
          {/* Card */}
          <Card className={`min-h-[360px] p-8 flex flex-col justify-center text-center transition-all duration-500 transform ${showAnswer ? 'rotate-0' : 'rotate-0'}`}>
            <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
              {card.is_new && (
                <Badge variant="primary">New Card</Badge>
              )}
              {card.tags && card.tags.length > 0 && (
                <div className="flex gap-1.5 ml-auto">
                  {card.tags.map((t: string) => <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>)}
                </div>
              )}
            </div>

            <div className="text-xl sm:text-2xl font-bold text-surface-900 leading-relaxed mb-6 mt-8">
              {card.front}
            </div>

            {showAnswer && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="w-24 h-1 bg-gradient-to-r from-surface-100 via-surface-200 to-surface-100 mx-auto rounded-full my-8" />
                <div className="text-lg text-surface-600 font-medium leading-relaxed whitespace-pre-wrap">
                  {card.back}
                </div>
              </div>
            )}
          </Card>

          {/* Actions */}
          {!showAnswer ? (
            <Button 
              size="lg" 
              className="w-full py-6 text-lg shadow-xl shadow-primary-500/20" 
              onClick={() => setShowAnswer(true)}
            >
              Show Answer
              <span className="text-sm font-normal opacity-70 ml-2">(Space)</span>
            </Button>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {ratingButtons.map(btn => (
                <button key={btn.rating} onClick={() => handleRate(btn.rating)} disabled={submitting}
                  className={`py-4 rounded-2xl ${btn.color} font-semibold hover:scale-[1.02] transition-all disabled:opacity-50 disabled:scale-100 shadow-md`}>
                  {btn.label}
                  <span className="block text-xs font-normal opacity-80 mt-1">{btn.key}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
