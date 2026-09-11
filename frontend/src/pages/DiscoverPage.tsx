import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { decksApi } from '../api';
import type { Deck } from '../types';
import { Compass, Search } from 'lucide-react';
import { Input, Button, Card, Badge } from '../components/ui';
import toast from 'react-hot-toast';

export default function DiscoverPage() {
  const navigate = useNavigate();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [joining, setJoining] = useState<string | null>(null);

  useEffect(() => {
    fetchDecks();
  }, []);

  const fetchDecks = (query = '') => {
    setLoading(true);
    // If search is empty, show popular decks. If not, search.
    const promise = query.trim() 
      ? decksApi.list(1, 20, query) 
      : decksApi.discover(1, 20, 'popular');

    promise
      .then(res => setDecks(res.data.decks))
      .catch(() => toast.error('Failed to load decks'))
      .finally(() => setLoading(false));
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDecks(search);
  };

  const handleJoin = async (deckId: string) => {
    setJoining(deckId);
    try {
      const res = await decksApi.joinPublic(deckId);
      toast.success('Joined deck successfully!');
      navigate(`/decks/${res.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to join deck');
    } finally {
      setJoining(null);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="bg-gradient-to-r from-accent-600 to-accent-500 rounded-3xl p-8 sm:p-12 text-white shadow-lg shadow-accent-500/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Compass className="w-48 h-48" />
        </div>
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">Discover Public Decks</h1>
          <p className="text-accent-100 text-lg mb-8">
            Explore and join study decks created by the StudySync community.
          </p>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input 
              placeholder="Search subjects, topics, or keywords..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder:text-accent-200 focus:bg-white focus:text-surface-900 focus:placeholder:text-surface-400 h-12"
              leftIcon={<Search className="w-5 h-5" />}
            />
            <Button type="submit" variant="secondary" className="h-12 px-8">Search</Button>
          </form>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-surface-900">
            {search.trim() ? `Search results for "${search}"` : 'Popular Decks'}
          </h2>
        </div>

        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-surface-200 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : decks.length === 0 ? (
          <div className="text-center py-20">
            <Compass className="w-16 h-16 text-surface-300 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-surface-900 mb-2">No decks found</h3>
            <p className="text-surface-500">Try adjusting your search terms.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {decks.map(deck => (
              <Card key={deck.id} hoverable className="flex flex-col h-full">
                <div className="p-6 flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-bold text-surface-900 line-clamp-1">{deck.title}</h3>
                  </div>
                  {deck.description && (
                    <p className="text-surface-600 text-sm mb-4 line-clamp-2">{deck.description}</p>
                  )}
                  {deck.tags && deck.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {deck.tags.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary">{tag}</Badge>
                      ))}
                      {deck.tags.length > 3 && (
                        <Badge variant="secondary">+{deck.tags.length - 3}</Badge>
                      )}
                    </div>
                  )}
                  <div className="text-xs font-medium text-surface-500 mb-2">
                    Created by {deck.owner_name || 'Anonymous'}
                  </div>
                </div>
                <div className="p-4 border-t border-surface-100 bg-surface-50 flex items-center justify-between rounded-b-2xl">
                  <div className="flex gap-4 text-xs font-medium text-surface-500">
                    <span>{deck.card_count} cards</span>
                    <span>{deck.member_count} members</span>
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => handleJoin(deck.id)}
                    isLoading={joining === deck.id}
                  >
                    Join Deck
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
