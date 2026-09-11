import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { groupsApi } from '../api';
import type { StudyGroup } from '../types';
import { Users, Plus, ArrowRight } from 'lucide-react';
import { Button, Card, Input, Modal } from '../components/ui';
import toast from 'react-hot-toast';

export default function GroupsPage() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<StudyGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = () => {
    setLoading(true);
    groupsApi.list()
      .then(res => setGroups(res.data.groups))
      .catch(() => toast.error('Failed to load groups'))
      .finally(() => setLoading(false));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await groupsApi.create({ name, description });
      toast.success('Group created successfully');
      setIsModalOpen(false);
      setName('');
      setDescription('');
      fetchGroups();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create group');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-surface-900">Study Groups</h1>
          <p className="text-surface-500 mt-1">Collaborate and learn with others.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Create Group
        </Button>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-surface-200 rounded-2xl animate-pulse" />)}
        </div>
      ) : groups.length === 0 ? (
        <div className="text-center py-20 bg-surface-100 rounded-3xl border border-surface-200 border-dashed">
          <Users className="w-16 h-16 text-surface-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-surface-900 mb-2">No groups yet</h3>
          <p className="text-surface-500 mb-6">Create a group or ask for an invite link to join one.</p>
          <Button onClick={() => setIsModalOpen(true)} variant="secondary">Create Group</Button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-6">
          {groups.map(group => (
            <Card key={group.id} hoverable className="flex flex-col h-full">
              <div className="p-6 flex-1">
                <h3 className="text-lg font-bold text-surface-900 line-clamp-1">{group.name}</h3>
                {group.description && (
                  <p className="text-surface-600 text-sm mt-2 line-clamp-2">{group.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs font-medium text-surface-500 mt-4">
                  <span className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> {group.member_count} members</span>
                  <span>Owner: {group.owner_name}</span>
                </div>
              </div>
              <div className="p-4 border-t border-surface-100 bg-surface-50 flex items-center justify-between rounded-b-2xl">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-primary-600 hover:text-primary-700"
                  onClick={() => navigate(`/groups/${group.id}`)}
                >
                  View Group <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Study Group">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input 
            label="Group Name" 
            placeholder="e.g. CS101 Study Group" 
            value={name} 
            onChange={e => setName(e.target.value)} 
            required 
            maxLength={100}
          />
          <Input 
            label="Description (Optional)" 
            placeholder="What is this group about?" 
            value={description} 
            onChange={e => setDescription(e.target.value)} 
            maxLength={500}
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={creating}>Create Group</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
