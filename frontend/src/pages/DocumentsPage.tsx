import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, Input, Spinner } from '../components/ui';
import { FileText, Upload, Search, Trash, AlertCircle, RotateCcw, CheckCircle } from 'lucide-react';
import { documentsApi } from '../api';
import toast from 'react-hot-toast';

export default function DocumentsPage() {
  const [search, setSearch] = useState('');
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
    // Poll if any processing
    const interval = setInterval(() => {
      setDocuments(prev => {
        const hasProcessing = prev.some(d => d.status === 'processing' || d.status === 'uploading');
        if (hasProcessing) loadDocuments();
        return prev;
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const loadDocuments = async () => {
    try {
      const res = await documentsApi.list();
      setDocuments(res.data.documents);
    } catch {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    // Client-side validation
    const allowedExts = ['.pdf', '.txt', '.csv', '.docx', '.pptx'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExts.includes(ext)) {
      toast.error(`Unsupported file type: ${ext}. Allowed: ${allowedExts.join(', ')}`);
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 50MB.');
      return;
    }

    setIsUploading(true);
    try {
      await documentsApi.upload(file.name, '', file);
      toast.success(`${file.name} uploaded. Processing...`);
      loadDocuments();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      await uploadFile(file);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      await uploadFile(file);
    }
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await documentsApi.delete(id);
      setDocuments(documents.filter(d => (d._id || d.id) !== id));
      toast.success('Document deleted');
    } catch {
      toast.error('Failed to delete document');
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await documentsApi.retry(id);
      toast.success('Retrying document processing...');
      setTimeout(loadDocuments, 1000);
    } catch {
      toast.error('Retry failed');
    }
  };

  const filteredDocs = documents.filter(doc => doc.title.toLowerCase().includes(search.toLowerCase()));

  const statusConfig: Record<string, { icon: React.ReactNode; color: string; bg: string; label: string }> = {
    ready: { icon: <CheckCircle className="w-3 h-3" />, color: 'text-green-700', bg: 'bg-green-50', label: 'Ready' },
    processing: { icon: <Spinner size="sm" />, color: 'text-amber-700', bg: 'bg-amber-50', label: 'Processing' },
    uploading: { icon: <Spinner size="sm" />, color: 'text-blue-700', bg: 'bg-blue-50', label: 'Uploading' },
    failed: { icon: <AlertCircle className="w-3 h-3" />, color: 'text-red-700', bg: 'bg-red-50', label: 'Failed' },
  };

  const getFileIcon = (mimeType?: string) => {
    if (!mimeType) return '📄';
    if (mimeType.includes('pdf')) return '📕';
    if (mimeType.includes('text')) return '📝';
    if (mimeType.includes('csv')) return '📊';
    if (mimeType.includes('word') || mimeType.includes('document')) return '📘';
    if (mimeType.includes('presentation')) return '📙';
    return '📄';
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-surface-900">Document Center</h1>
          <p className="text-surface-500 mt-1">Upload PDFs, slides, and notes to use in notebooks and AI.</p>
        </div>
        <div className="flex items-center gap-3">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            leftIcon={<Search className="w-4 h-4" />}
            className="w-full sm:w-64"
          />
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.txt,.csv,.docx,.pptx"
            multiple
          />
          <Button
            leftIcon={isUploading ? <Spinner size="sm" /> : <Upload className="w-4 h-4" />}
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload File'}
          </Button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-primary-500 bg-primary-50 scale-[1.01]'
            : 'border-surface-200 hover:border-primary-300 hover:bg-surface-50'
        }`}
      >
        <Upload className={`w-10 h-10 mx-auto mb-3 transition-colors ${isDragging ? 'text-primary-500' : 'text-surface-300'}`} />
        <p className="text-sm font-semibold text-surface-700">
          {isDragging ? 'Drop to upload' : 'Drag & drop files here'}
        </p>
        <p className="text-xs text-surface-400 mt-1">or click to browse • PDF, TXT, CSV, DOCX, PPTX • Max 50MB</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-20 rounded-3xl bg-white border border-surface-200 shadow-sm">
          <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-6">
            <FileText className="w-10 h-10 text-primary-500" />
          </div>
          <h3 className="text-xl font-bold text-surface-900 mb-2">No documents yet</h3>
          <p className="text-surface-500 max-w-md mx-auto mb-8">
            Upload study materials to extract concepts, generate flashcards, and use the AI study assistant.
          </p>
          <Button
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => fileInputRef.current?.click()}
            size="lg"
          >
            Upload your first document
          </Button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filteredDocs.map((doc, i) => {
            const docId = doc._id || doc.id;
            const status = statusConfig[doc.status] || statusConfig.ready;
            const isFailed = doc.status === 'failed';

            return (
              <Card key={docId || i} hoverable className="flex flex-col h-full bg-white group overflow-hidden">
                <div className="h-28 bg-surface-50 border-b border-surface-100 flex flex-col items-center justify-center relative">
                  <span className="text-3xl mb-1">{getFileIcon(doc.mime_type)}</span>
                  <span className="text-xs font-semibold text-surface-400 uppercase tracking-wider">
                    {doc.mime_type?.split('/')[1]?.replace('vnd.openxmlformats-officedocument.', '').split('.')[0] || 'file'}
                  </span>
                  {/* Status badge */}
                  <div className={`absolute top-2 right-2 flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full ${status.bg} ${status.color}`}>
                    {status.icon}
                    <span>{status.label}</span>
                  </div>
                  {/* Retry overlay for failed */}
                  {isFailed && (
                    <button
                      onClick={() => handleRetry(docId)}
                      className="absolute bottom-2 right-2 flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" /> Retry
                    </button>
                  )}
                </div>
                <div className="p-4 flex flex-col flex-1">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-sm font-bold text-surface-900 line-clamp-2 leading-snug flex-1 mr-2" title={doc.title}>
                      {doc.title}
                    </h3>
                    <button
                      onClick={() => handleDelete(docId)}
                      className="text-surface-400 hover:text-red-600 p-1 -mr-1 rounded opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                    >
                      <Trash className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="mt-auto pt-3 flex items-center justify-between text-[11px] font-medium text-surface-400">
                    <span>{(doc.size / 1024 / 1024).toFixed(1)} MB</span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </Card>
            );
          })}
          {filteredDocs.length === 0 && search && (
            <div className="col-span-full text-center py-12 text-surface-500">
              No documents match your search.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
