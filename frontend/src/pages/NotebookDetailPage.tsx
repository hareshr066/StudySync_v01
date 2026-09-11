import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

import {
  FileText, Upload, MessageSquare, Layout, PanelLeftClose,
  PanelRightClose, Search, Trash, BookOpen, ZoomIn, ZoomOut,
  Plus, Check, RotateCcw, Brain, ClipboardList,
  History, Pencil, AlertCircle
} from 'lucide-react';
import { Button, Select, Badge, Spinner, Modal } from '../components/ui';
import { notebooksApi, documentsApi, conversationsApi, quizzesApi, aiApi, cardsApi, decksApi } from '../api';
import toast from 'react-hot-toast';

type AIMode = 'explain' | 'socratic' | 'summarize' | 'quiz' | 'flashcards';
type CenterTab = 'document' | 'note';
type RightTab = 'chat' | 'history';

interface FlashcardPreview {
  front: string;
  back: string;
  tags: string[];
  difficulty: string;
}

interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  difficulty: string;
}

export default function NotebookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [notebook, setNotebook] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<any[]>([]);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Layout state
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<CenterTab>('document');
  const [rightTab, setRightTab] = useState<RightTab>('chat');

  // PDF state
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);

  // AI Chat state
  const [chatInput, setChatInput] = useState('');
  const [aiMode, setAiMode] = useState<AIMode>('explain');
  const [chatLoading, setChatLoading] = useState(false);

  // Conversation persistence
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [activeConv, setActiveConv] = useState<any | null>(null);
  const [loadingConv, setLoadingConv] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Notes state
  const [notes, setNotes] = useState<any[]>([]);
  const [activeNote, setActiveNote] = useState<any | null>(null);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteContent, setNoteContent] = useState('');
  const [noteSaveStatus, setNoteSaveStatus] = useState<'saved' | 'unsaved' | 'saving'>('saved');
  const noteDebounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Flashcard preview state
  const [flashcards, setFlashcards] = useState<FlashcardPreview[]>([]);
  const [showFlashcardModal, setShowFlashcardModal] = useState(false);
  const [generatingFlashcards, setGeneratingFlashcards] = useState(false);
  const [flashcardCount, setFlashcardCount] = useState(5);
  const [flashcardDifficulty, setFlashcardDifficulty] = useState('medium');
  const [savingFlashcards, setSavingFlashcards] = useState(false);
  const [decks, setDecks] = useState<any[]>([]);
  const [selectedDeckId, setSelectedDeckId] = useState('');

  // Quiz state
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  const [currentQuizId, setCurrentQuizId] = useState<string | null>(null);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [quizCount, setQuizCount] = useState(5);
  const [quizDifficulty, setQuizDifficulty] = useState('medium');
  const [quizAnswers, setQuizAnswers] = useState<string[]>([]);
  const [, setQuizSubmitted] = useState(false);
  const [quizResults, setQuizResults] = useState<any | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (id) {
      loadNotebook(true);
      loadConversations();
      loadNotes();
      decksApi.list().then(r => setDecks(r.data.decks || [])).catch(() => {});
    }
  }, [id]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages]);

  // Poll for processing docs
  useEffect(() => {
    const hasProcessing = sources.some(s => s.status === 'processing' || s.status === 'uploading');
    if (!hasProcessing) return;
    const interval = setInterval(() => loadNotebook(false), 3000);
    return () => clearInterval(interval);
  }, [sources, id]);

  const loadNotebook = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const res = await notebooksApi.get(id!);
      setNotebook(res.data);
      const docsRes = await documentsApi.list();
      const nbDocs = docsRes.data.documents.filter((d: any) =>
        res.data.documents.includes(d.id || d._id)
      );
      setSources(nbDocs);
      if (nbDocs.length > 0 && !selectedSource) {
        setSelectedSource(nbDocs[0]._id || nbDocs[0].id);
      }
    } catch (err: any) {
      if (showLoading) {
        toast.error('Failed to load notebook');
        navigate('/notebooks');
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const res = await conversationsApi.list(id);
      setConversations(res.data.conversations || []);
      if (res.data.conversations?.length > 0 && !activeConvId) {
        // don't auto-select, let user choose or create
      }
    } catch {}
  };

  const loadNotes = async () => {
    try {
      const res = await notebooksApi.getNotes(id!);
      setNotes(res.data.notes || []);
      if (res.data.notes?.length > 0 && !activeNote) {
        openNote(res.data.notes[0]);
      }
    } catch {}
  };

  const openNote = (note: any) => {
    setActiveNote(note);
    setNoteTitle(note.title || '');
    setNoteContent(typeof note.content === 'string' ? note.content : '');
    setNoteSaveStatus('saved');
  };

  const createNewNote = async () => {
    try {
      const res = await notebooksApi.createNote(id!, { title: 'Untitled Note', content: '' });
      const newNote = res.data;
      setNotes(prev => [newNote, ...prev]);
      openNote(newNote);
      toast.success('New note created');
    } catch {
      toast.error('Failed to create note');
    }
  };

  // Debounced note save
  const handleNoteChange = (field: 'title' | 'content', value: string) => {
    if (field === 'title') setNoteTitle(value);
    else setNoteContent(value);
    setNoteSaveStatus('unsaved');
    clearTimeout(noteDebounceRef.current);
    noteDebounceRef.current = setTimeout(async () => {
      if (!activeNote) return;
      setNoteSaveStatus('saving');
      try {
        await import('../api').then(({ notesApi }) =>
          notesApi.update(activeNote._id || activeNote.id, {
            title: field === 'title' ? value : noteTitle,
            content: field === 'content' ? value : noteContent,
          })
        );
        setNoteSaveStatus('saved');
      } catch {
        setNoteSaveStatus('unsaved');
      }
    }, 1500);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const uploadRes = await documentsApi.upload(file.name, 'Uploaded from notebook', file);
      const newDocId = uploadRes.data._id || uploadRes.data.id;
      await notebooksApi.addDocument(id!, newDocId);
      toast.success('Document uploaded. Processing...');
      loadNotebook();
      setSelectedSource(newDocId);
      setActiveTab('document');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleRemoveSource = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notebooksApi.removeDocument(id!, docId);
      setSources(sources.filter(s => (s._id || s.id) !== docId));
      if (selectedSource === docId) setSelectedSource(null);
      toast.success('Source removed');
    } catch {
      toast.error('Failed to remove source');
    }
  };

  // Conversation management
  const createNewConversation = async () => {
    try {
      const res = await conversationsApi.create({
        title: 'New Conversation',
        notebook_id: id,
        context_type: selectedSource ? 'document' : 'notebook',
        context_id: selectedSource || id,
      });
      const conv = res.data;
      setConversations(prev => [conv, ...prev]);
      setActiveConvId(conv._id || conv.id);
      setActiveConv({ ...conv, messages: [] });
      setRightTab('chat');
    } catch {
      toast.error('Failed to create conversation');
    }
  };

  const selectConversation = async (convId: string) => {
    if (convId === activeConvId) return;
    setLoadingConv(true);
    setActiveConvId(convId);
    setRightTab('chat');
    try {
      const res = await conversationsApi.get(convId);
      setActiveConv(res.data);
    } catch {
      toast.error('Failed to load conversation');
    } finally {
      setLoadingConv(false);
    }
  };

  const handleAskAI = async () => {
    if (!chatInput.trim()) return;
    const prompt = chatInput.trim();
    setChatInput('');

    // If no active conversation, create one first
    let convId = activeConvId;
    if (!convId) {
      try {
        const res = await conversationsApi.create({
          title: prompt.slice(0, 60),
          notebook_id: id,
          context_type: selectedSource ? 'document' : 'notebook',
          context_id: selectedSource || id,
        });
        const conv = res.data;
        convId = conv._id || conv.id;
        setConversations(prev => [conv, ...prev]);
        setActiveConvId(convId);
        setActiveConv({ ...conv, messages: [] });
      } catch {
        toast.error('Failed to start conversation');
        return;
      }
    }

    // Optimistically add user message
    const userMsg = { role: 'user', content: prompt, citations: [], created_at: new Date().toISOString() };
    setActiveConv((prev: any) => ({ ...prev, messages: [...(prev?.messages || []), userMsg] }));
    setChatLoading(true);

    if (!convId) return;

    try {
      const res = await conversationsApi.addMessage(convId, {
        prompt,
        mode: aiMode,
        context_type: selectedSource ? 'document' : 'notebook',
        context_id: selectedSource || id || '',
      });
      const aiMsg = res.data.ai_message;
      setActiveConv((prev: any) => ({
        ...prev,
        messages: [...(prev?.messages || []).filter((m: any) => m !== userMsg), userMsg, aiMsg]
      }));
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to get AI response');
      // Remove optimistic message on error
      setActiveConv((prev: any) => ({
        ...prev,
        messages: (prev?.messages || []).filter((m: any) => m !== userMsg)
      }));
    } finally {
      setChatLoading(false);
    }
  };

  // Flashcard generation
  const handleGenerateFlashcards = async () => {
    setGeneratingFlashcards(true);
    try {
      const res = await aiApi.generateFlashcards({
        count: flashcardCount,
        difficulty: flashcardDifficulty,
        context_type: selectedSource ? 'document' : 'notebook',
        context_id: selectedSource || id,
      });
      const cards = res.data.cards || [];
      if (cards.length === 0) {
        toast.error('No flashcards could be generated from this document yet.');
      } else {
        setFlashcards(cards);
        setShowFlashcardModal(true);
        toast.success(`Generated ${cards.length} flashcards!`);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to generate flashcards');
    } finally {
      setGeneratingFlashcards(false);
    }
  };

  const handleSaveFlashcards = async () => {
    if (!selectedDeckId || flashcards.length === 0) return;
    setSavingFlashcards(true);
    try {
      await Promise.all(
        flashcards.map(card =>
          cardsApi.create(selectedDeckId, { front: card.front, back: card.back, tags: card.tags })
        )
      );
      toast.success(`${flashcards.length} flashcards saved to deck!`);
      setShowFlashcardModal(false);
      setFlashcards([]);
    } catch {
      toast.error('Failed to save flashcards');
    } finally {
      setSavingFlashcards(false);
    }
  };

  // Quiz generation
  const handleGenerateQuiz = async () => {
    setGeneratingQuiz(true);
    try {
      const res = await quizzesApi.generate({
        count: quizCount,
        difficulty: quizDifficulty,
        type: 'mcq',
        context_type: selectedSource ? 'document' : 'notebook',
        context_id: selectedSource || id,
      });
      const questions = res.data.questions || [];
      if (questions.length === 0) {
        toast.error('No quiz questions could be generated from this document yet.');
      } else {
        const qId = res.data._id || res.data.id;
        setCurrentQuizId(qId || null);
        setQuizQuestions(questions);
        setQuizAnswers(new Array(questions.length).fill(''));
        setQuizSubmitted(false);
        setQuizResults(null);
        setShowQuizModal(true);
        toast.success(`Generated ${questions.length} quiz questions!`);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to generate quiz');
    } finally {
      setGeneratingQuiz(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizQuestions.length) return;
    if (currentQuizId) {
      try {
        const res = await quizzesApi.attempt(currentQuizId, quizAnswers);
        setQuizResults(res.data);
        setQuizSubmitted(true);
        toast.success(`Quiz completed! Score: ${res.data.percentage}%`);
        return;
      } catch {
        // Fallback to local evaluation
      }
    }
    // Calculate locally
    let score = 0;
    const results = quizQuestions.map((q, i) => {
      const isCorrect = quizAnswers[i]?.trim().toLowerCase() === q.correct_answer?.trim().toLowerCase();
      if (isCorrect) score++;
      return { question: q.question, user_answer: quizAnswers[i], correct_answer: q.correct_answer, is_correct: isCorrect, explanation: q.explanation };
    });
    setQuizResults({ score, total: quizQuestions.length, percentage: Math.round((score / quizQuestions.length) * 100), results });
    setQuizSubmitted(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!notebook) return null;

  const currentDoc = sources.find(s => (s._id || s.id) === selectedSource);
  const messages = activeConv?.messages || [];

  return (
    <div className="h-[calc(100vh-6rem)] -m-4 sm:-m-6 lg:-m-8 flex overflow-hidden bg-surface-50 border border-surface-200 rounded-xl shadow-sm">

      {/* LEFT PANEL: SOURCES */}
      {leftPanelOpen && (
        <div className="w-64 lg:w-72 border-r border-surface-200 flex flex-col bg-white shrink-0">
          <div className="h-14 border-b border-surface-200 flex items-center justify-between px-4 bg-surface-50">
            <h2 className="font-bold text-surface-900 truncate flex items-center gap-2 text-sm">
              <BookOpen className="w-4 h-4 text-primary-600 shrink-0" />
              <span className="truncate">{notebook.title}</span>
            </h2>
            <button onClick={() => setLeftPanelOpen(false)} className="text-surface-400 hover:text-surface-600 p-1 rounded-md hover:bg-surface-200 transition-colors shrink-0">
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>

          <div className="p-3 border-b border-surface-200">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              onChange={handleFileUpload}
              accept=".pdf,.txt,.csv,.docx,.pptx"
            />
            <Button
              variant="outline"
              className="w-full justify-start text-sm"
              leftIcon={isUploading ? <Spinner size="sm" /> : <Upload className="w-4 h-4" />}
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Add Source'}
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            <div className="flex items-center justify-between mb-2 px-1">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider">Sources</h3>
              <Badge variant="secondary" className="text-[10px] py-0.5">{sources.length}</Badge>
            </div>

            {sources.length === 0 ? (
              <div className="text-center py-8 px-4 rounded-xl border border-dashed border-surface-200">
                <FileText className="w-8 h-8 text-surface-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-surface-900">No sources</p>
                <p className="text-xs text-surface-500 mt-1">Upload PDFs or text files to ground the AI.</p>
              </div>
            ) : (
              sources.map(src => {
                const sId = src._id || src.id;
                const isSelected = selectedSource === sId;
                const isFailed = src.status === 'failed';
                const isProcessing = src.status === 'processing' || src.status === 'uploading';
                return (
                  <div
                    key={sId}
                    onClick={() => { setSelectedSource(sId); setActiveTab('document'); }}
                    className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors group ${
                      isSelected ? 'bg-primary-50 border border-primary-100 shadow-sm' : 'hover:bg-surface-100 border border-transparent'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded flex items-center justify-center shrink-0 ${
                      isFailed ? 'bg-red-50 text-red-400' : isSelected ? 'bg-primary-100 text-primary-600' : 'bg-surface-100 text-surface-500'
                    }`}>
                      {isFailed ? <AlertCircle className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${isSelected ? 'text-primary-900' : 'text-surface-700'}`}>
                        {src.title}
                      </p>
                      <p className={`text-[10px] capitalize ${isFailed ? 'text-red-500' : isProcessing ? 'text-amber-500' : 'text-surface-400'}`}>
                        {isProcessing ? (
                          <span className="flex items-center gap-1"><Spinner size="sm" /><span>Processing...</span></span>
                        ) : src.status || 'Ready'}
                      </p>
                    </div>
                    <button
                      onClick={(e: React.MouseEvent) => handleRemoveSource(sId, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-surface-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                    >
                      <Trash className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}

            {/* Retry failed docs */}
            {sources.filter(s => s.status === 'failed').map(src => (
              <button
                key={`retry-${src._id || src.id}`}
                onClick={async () => {
                  try {
                    await documentsApi.retry(src._id || src.id);
                    toast.success('Retrying...');
                    loadNotebook();
                  } catch {
                    toast.error('Retry failed');
                  }
                }}
                className="w-full text-xs text-red-600 hover:text-red-700 font-medium py-1 px-2 rounded bg-red-50 hover:bg-red-100 transition-colors"
              >
                Retry failed: {src.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* CENTER PANEL: WORKSPACE */}
      <div className="flex-1 flex flex-col min-w-0 bg-surface-50">
        <div className="h-14 border-b border-surface-200 flex items-center justify-between px-4 bg-white">
          <div className="flex items-center gap-2">
            {!leftPanelOpen && (
              <button onClick={() => setLeftPanelOpen(true)} className="text-surface-500 hover:text-surface-700 p-1 mr-2 rounded-md hover:bg-surface-100">
                <Layout className="w-4 h-4" />
              </button>
            )}
            <div className="flex p-0.5 bg-surface-100 rounded-lg border border-surface-200">
              <button
                onClick={() => setActiveTab('document')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${activeTab === 'document' ? 'bg-white shadow-sm text-surface-900' : 'text-surface-500 hover:text-surface-700'}`}
              >
                Viewer
              </button>
              <button
                onClick={() => { setActiveTab('note'); }}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${activeTab === 'note' ? 'bg-white shadow-sm text-surface-900' : 'text-surface-500 hover:text-surface-700'}`}
              >
                Notes
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {activeTab === 'document' && currentDoc?.mime_type === 'application/pdf' && (
              <>
                <button onClick={() => setPdfScale(s => Math.max(0.5, s - 0.2))} className="p-1.5 rounded text-surface-500 hover:text-surface-700 hover:bg-surface-100 transition-colors">
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="text-xs font-medium text-surface-500 min-w-[40px] text-center">{Math.round(pdfScale * 100)}%</span>
                <button onClick={() => setPdfScale(s => Math.min(2.5, s + 0.2))} className="p-1.5 rounded text-surface-500 hover:text-surface-700 hover:bg-surface-100 transition-colors">
                  <ZoomIn className="w-4 h-4" />
                </button>
              </>
            )}
            {activeTab === 'note' && (
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={createNewNote}>
                  New Note
                </Button>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  noteSaveStatus === 'saved' ? 'bg-green-50 text-green-600' :
                  noteSaveStatus === 'saving' ? 'bg-amber-50 text-amber-600' :
                  'bg-surface-100 text-surface-500'
                }`}>
                  {noteSaveStatus === 'saved' ? '✓ Saved' : noteSaveStatus === 'saving' ? 'Saving...' : 'Unsaved'}
                </span>
              </div>
            )}
            {!rightPanelOpen && (
              <button onClick={() => setRightPanelOpen(true)} className="text-surface-500 hover:text-surface-700 p-1 ml-2 rounded-md hover:bg-surface-100">
                <MessageSquare className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-auto p-4 lg:p-6 flex justify-center">
          {activeTab === 'document' ? (
            <div className="w-full max-w-4xl bg-white border border-surface-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
              {currentDoc ? (
                <>
                  <div className="px-4 py-3 border-b border-surface-200 flex items-center justify-between bg-surface-50">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-surface-500" />
                      <span className="font-medium text-sm text-surface-900">{currentDoc.title}</span>
                      <Badge variant="secondary" className="text-[10px] ml-2 capitalize">{currentDoc.mime_type?.split('/')[1] || 'file'}</Badge>
                    </div>
                    <a
                      href={`/api/v1/documents/${currentDoc._id || currentDoc.id}/content?token=${localStorage.getItem('access_token') || ''}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
                    >
                      Download
                    </a>
                  </div>
                  <div className="flex-1 flex flex-col items-center justify-start bg-surface-100 relative overflow-y-auto p-4">
                    {currentDoc.mime_type === 'application/pdf' ? (
                      <div className="w-full flex justify-center">
                        <Document
                          file={{
                            url: `/api/v1/documents/${currentDoc._id || currentDoc.id}/content?token=${localStorage.getItem('access_token') || ''}`,
                            httpHeaders: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` }
                          }}
                          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                          loading={<Spinner size="lg" />}
                          error={<div className="text-center py-12 text-red-500 text-sm">Failed to load PDF. The document may still be processing.</div>}
                          className="shadow-sm border border-surface-200"
                        >
                          <Page
                            pageNumber={pageNumber}
                            scale={pdfScale}
                            renderTextLayer={true}
                            renderAnnotationLayer={true}
                          />
                        </Document>
                      </div>
                    ) : (
                      <div className="w-full max-w-2xl bg-white p-8 rounded shadow-sm border border-surface-200">
                        <p className="text-surface-500 italic text-center text-sm">
                          Preview not available for this file type. Click Download to view.
                        </p>
                      </div>
                    )}
                  </div>
                  {currentDoc.mime_type === 'application/pdf' && (
                    <div className="h-12 border-t border-surface-200 flex items-center justify-center gap-4 bg-white shrink-0">
                      <Button variant="ghost" size="sm" onClick={() => setPageNumber(p => Math.max(1, p - 1))} disabled={pageNumber <= 1}>Previous</Button>
                      <span className="text-sm font-medium text-surface-600">Page {pageNumber} of {numPages || '--'}</span>
                      <Button variant="ghost" size="sm" onClick={() => setPageNumber(p => Math.min(numPages || p, p + 1))} disabled={pageNumber >= (numPages || 1)}>Next</Button>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-center p-8">
                  <div>
                    <Search className="w-12 h-12 text-surface-200 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-surface-900">No document selected</h3>
                    <p className="text-surface-500 text-sm mt-1">Select a source from the left panel to view it here.</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Notes Tab */
            <div className="w-full max-w-4xl flex gap-4 h-full">
              {/* Note list */}
              <div className="w-52 shrink-0 flex flex-col gap-2">
                {notes.map(note => (
                  <button
                    key={note._id || note.id}
                    onClick={() => openNote(note)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      activeNote?._id === note._id ? 'bg-white border-primary-200 shadow-sm' : 'bg-white border-surface-200 hover:border-surface-300'
                    }`}
                  >
                    <p className="text-sm font-medium text-surface-900 truncate">{note.title || 'Untitled'}</p>
                    <p className="text-xs text-surface-400 mt-0.5">{new Date(note.updated_at).toLocaleDateString()}</p>
                  </button>
                ))}
                {notes.length === 0 && (
                  <div className="text-center py-8 text-surface-400 text-sm">
                    <Pencil className="w-8 h-8 mx-auto mb-2 text-surface-200" />
                    No notes yet
                  </div>
                )}
              </div>

              {/* Note editor */}
              <div className="flex-1 bg-white border border-surface-200 rounded-xl shadow-sm p-8 lg:p-10 overflow-y-auto">
                {activeNote ? (
                  <>
                    <input
                      type="text"
                      value={noteTitle}
                      onChange={e => handleNoteChange('title', e.target.value)}
                      placeholder="Untitled Note"
                      className="text-3xl font-extrabold border-none focus:ring-0 p-0 w-full mb-6 text-surface-900 placeholder:text-surface-200 outline-none bg-transparent"
                    />
                    <textarea
                      value={noteContent}
                      onChange={e => handleNoteChange('content', e.target.value)}
                      placeholder="Start typing your notes here..."
                      className="w-full min-h-[500px] resize-none border-none focus:ring-0 p-0 text-surface-700 placeholder:text-surface-300 leading-relaxed outline-none bg-transparent text-base"
                    />
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Pencil className="w-12 h-12 text-surface-200 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-surface-900">Select or create a note</h3>
                    <Button className="mt-4" leftIcon={<Plus className="w-4 h-4" />} onClick={createNewNote}>
                      New Note
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* RIGHT PANEL: AI ASSISTANT */}
      {rightPanelOpen && (
        <div className="w-80 lg:w-[380px] border-l border-surface-200 flex flex-col bg-white shrink-0 shadow-[-4px_0_24px_rgba(0,0,0,0.02)]">
          <div className="h-14 border-b border-surface-200 flex items-center justify-between px-4 bg-surface-50">
            <div className="flex items-center gap-1 p-0.5 bg-surface-100 rounded-lg border border-surface-200">
              <button
                onClick={() => setRightTab('chat')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${rightTab === 'chat' ? 'bg-white shadow-sm text-surface-900' : 'text-surface-500'}`}
              >
                <MessageSquare className="w-3.5 h-3.5" /> Chat
              </button>
              <button
                onClick={() => setRightTab('history')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${rightTab === 'history' ? 'bg-white shadow-sm text-surface-900' : 'text-surface-500'}`}
              >
                <History className="w-3.5 h-3.5" /> History
              </button>
            </div>
            <button onClick={() => setRightPanelOpen(false)} className="text-surface-400 hover:text-surface-600 p-1 rounded-md hover:bg-surface-200 transition-colors">
              <PanelRightClose className="w-4 h-4" />
            </button>
          </div>

          {rightTab === 'history' ? (
            /* Conversation History Panel */
            <div className="flex-1 overflow-y-auto p-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider">Conversations</h3>
                <button
                  onClick={createNewConversation}
                  className="p-1 rounded-lg text-primary-600 hover:bg-primary-50 transition-colors"
                  title="New conversation"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              {conversations.length === 0 ? (
                <div className="text-center py-8 text-surface-400 text-sm">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 text-surface-200" />
                  <p>No conversations yet.</p>
                  <button onClick={createNewConversation} className="mt-2 text-primary-600 font-medium hover:underline">
                    Start one
                  </button>
                </div>
              ) : (
                conversations.map(conv => (
                  <button
                    key={conv._id || conv.id}
                    onClick={() => selectConversation(conv._id || conv.id)}
                    className={`w-full text-left p-3 rounded-xl border mb-2 transition-all ${
                      activeConvId === (conv._id || conv.id) ? 'bg-primary-50 border-primary-100' : 'border-surface-200 hover:border-surface-300 hover:bg-surface-50'
                    }`}
                  >
                    <p className="text-sm font-medium text-surface-900 truncate">{conv.title || 'Conversation'}</p>
                    <p className="text-xs text-surface-400 mt-0.5">{new Date(conv.updated_at).toLocaleDateString()}</p>
                  </button>
                ))
              )}
            </div>
          ) : (
            /* Chat Panel */
            <>
              <div className="p-3 border-b border-surface-100 space-y-2">
                <Select
                  value={aiMode}
                  onChange={(e) => setAiMode(e.target.value as AIMode)}
                  className="w-full text-sm py-2 font-medium bg-surface-50"
                >
                  <option value="explain">💡 Explain Concept</option>
                  <option value="socratic">🤔 Socratic Tutor</option>
                  <option value="summarize">📝 Summarize Sources</option>
                  <option value="quiz">❓ Quiz Me</option>
                </Select>
                <div className="text-xs font-medium text-surface-500 flex items-center gap-1.5 px-1">
                  <span>Context:</span>
                  <Badge variant="secondary" className="bg-primary-50 text-primary-700 border-primary-100 text-[10px]">
                    {selectedSource && currentDoc ? currentDoc.title : 'Entire Notebook'}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-xs py-1"
                    leftIcon={generatingFlashcards ? <Spinner size="sm" /> : <Brain className="w-3.5 h-3.5" />}
                    onClick={handleGenerateFlashcards}
                    disabled={generatingFlashcards}
                  >
                    {generatingFlashcards ? 'Generating...' : 'Flashcards'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-xs py-1"
                    leftIcon={generatingQuiz ? <Spinner size="sm" /> : <ClipboardList className="w-3.5 h-3.5" />}
                    onClick={handleGenerateQuiz}
                    disabled={generatingQuiz}
                  >
                    {generatingQuiz ? 'Generating...' : 'Quiz'}
                  </Button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-surface-50/30">
                {/* No active conversation */}
                {!activeConvId && messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center px-4">
                    <div className="w-14 h-14 rounded-full bg-primary-50 flex items-center justify-center mb-4 border border-primary-100">
                      <MessageSquare className="w-7 h-7 text-primary-500" />
                    </div>
                    <h3 className="text-base font-bold text-surface-900 mb-1">How can I help?</h3>
                    <p className="text-sm text-surface-500 max-w-[200px] mb-5">
                      Ask questions about your sources, or generate flashcards and quizzes.
                    </p>
                    <div className="flex flex-col gap-2 w-full">
                      <Button variant="outline" size="sm" className="justify-start bg-white text-xs py-1.5 h-auto" onClick={() => setChatInput("Summarize the key points.")}>
                        Summarize key points
                      </Button>
                      <Button variant="outline" size="sm" className="justify-start bg-white text-xs py-1.5 h-auto" onClick={() => setChatInput("What are the main concepts I should understand?")}>
                        Main concepts
                      </Button>
                      <Button variant="outline" size="sm" className="justify-start bg-white text-xs py-1.5 h-auto" onClick={() => setChatInput("Create a study guide from this material.")}>
                        Create study guide
                      </Button>
                    </div>
                  </div>
                )}

                {loadingConv && (
                  <div className="flex justify-center py-8"><Spinner size="lg" /></div>
                )}

                {/* Messages */}
                {messages.map((msg: any, i: number) => (
                  <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    <div className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white rounded-br-sm'
                        : 'bg-white border border-surface-200 text-surface-800 rounded-bl-sm'
                    }`}>
                      {msg.content}
                    </div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 px-1">
                        {msg.citations.map((cit: any, ci: number) => (
                          <button
                            key={ci}
                            onClick={() => {
                              const targetId = cit.doc_id || cit.source_id;
                              const found = sources.find(s => (s._id || s.id) === targetId || s.gemini_file_id === targetId || s.filename === cit.source_name || s.title === cit.source_name);
                              if (found) {
                                setSelectedSource(found._id || found.id);
                                setActiveTab('document');
                                if (cit.page_number) setPageNumber(cit.page_number);
                              } else if (cit.source_id) {
                                setSelectedSource(cit.source_id);
                                setActiveTab('document');
                              }
                            }}
                            className="flex items-center gap-1 text-[10px] font-medium px-2 py-1 bg-surface-100 hover:bg-surface-200 text-surface-600 rounded-md transition-colors border border-surface-200"
                          >
                            <FileText className="w-3 h-3" />
                            <span>{cit.source_name}</span>
                            {cit.page_number && <span className="text-surface-400">p.{cit.page_number}</span>}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {chatLoading && (
                  <div className="flex items-start">
                    <div className="max-w-[85%] rounded-2xl px-5 py-4 bg-white border border-surface-200 rounded-bl-sm shadow-sm">
                      <div className="flex gap-1.5">
                        <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                        <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              <div className="p-3 bg-white border-t border-surface-200">
                {activeConvId && (
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-surface-400 font-medium truncate max-w-[70%]">
                      {conversations.find(c => (c._id || c.id) === activeConvId)?.title || 'Conversation'}
                    </span>
                    <button
                      onClick={createNewConversation}
                      className="text-xs text-primary-600 font-medium hover:underline shrink-0"
                    >
                      + New
                    </button>
                  </div>
                )}
                <form
                  onSubmit={(e) => { e.preventDefault(); handleAskAI(); }}
                  className="flex items-end gap-2"
                >
                  <div className="flex-1 bg-surface-50 border border-surface-200 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-primary-500/20 focus-within:border-primary-500 transition-all">
                    <textarea
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Ask a question..."
                      className="w-full max-h-32 min-h-[44px] bg-transparent border-none focus:ring-0 text-sm py-3 px-3 resize-none"
                      rows={1}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAskAI(); }
                      }}
                    />
                  </div>
                  <Button type="submit" disabled={!chatInput.trim() || chatLoading} className="shrink-0 h-[46px] w-[46px] p-0 rounded-xl flex items-center justify-center shadow-sm">
                    <MessageSquare className="w-5 h-5" />
                  </Button>
                </form>
                <div className="text-[10px] text-surface-400 text-center mt-2 font-medium">
                  StudySync AI can make mistakes. Always verify facts.
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* FLASHCARD MODAL */}
      <Modal isOpen={showFlashcardModal} onClose={() => setShowFlashcardModal(false)} title="Generated Flashcards" maxWidth="lg">
        <div className="space-y-4">
          {/* Generation controls */}
          {flashcards.length === 0 && (
            <div className="grid grid-cols-2 gap-3 p-4 bg-surface-50 rounded-xl border border-surface-200">
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Count</label>
                <Select value={flashcardCount.toString()} onChange={e => setFlashcardCount(Number(e.target.value))}>
                  <option value="5">5 cards</option>
                  <option value="10">10 cards</option>
                  <option value="15">15 cards</option>
                  <option value="20">20 cards</option>
                </Select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Difficulty</label>
                <Select value={flashcardDifficulty} onChange={e => setFlashcardDifficulty(e.target.value)}>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </Select>
              </div>
            </div>
          )}

          {flashcards.length > 0 && (
            <>
              <div className="text-sm font-medium text-surface-700">
                {flashcards.length} cards generated — review and save to a deck:
              </div>
              <div className="max-h-[40vh] overflow-y-auto space-y-3 pr-1">
                {flashcards.map((card, i) => (
                  <div key={i} className="border border-surface-200 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 bg-surface-50 border-b border-surface-100">
                      <span className="text-xs font-bold text-surface-500 uppercase tracking-wider mr-2">Q</span>
                      <span className="text-sm font-medium text-surface-900">{card.front}</span>
                    </div>
                    <div className="px-4 py-3">
                      <span className="text-xs font-bold text-primary-500 uppercase tracking-wider mr-2">A</span>
                      <span className="text-sm text-surface-700">{card.back}</span>
                    </div>
                    {card.tags?.length > 0 && (
                      <div className="px-4 pb-3 flex gap-1.5">
                        {card.tags.map((t: string) => (
                          <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Deck selector */}
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1.5">Save to deck</label>
                <Select value={selectedDeckId} onChange={e => setSelectedDeckId(e.target.value)} className="w-full">
                  <option value="">Select a deck...</option>
                  {decks.map((d: any) => (
                    <option key={d.id || d._id} value={d.id || d._id}>{d.title}</option>
                  ))}
                </Select>
              </div>

              <div className="flex justify-end gap-3 mt-2">
                <Button variant="ghost" onClick={() => { setFlashcards([]); setShowFlashcardModal(false); }}>Discard</Button>
                <Button
                  onClick={handleSaveFlashcards}
                  isLoading={savingFlashcards}
                  disabled={!selectedDeckId || savingFlashcards}
                  leftIcon={<Check className="w-4 h-4" />}
                >
                  Save {flashcards.length} Cards
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* QUIZ MODAL */}
      <Modal isOpen={showQuizModal} onClose={() => { setShowQuizModal(false); setQuizSubmitted(false); setQuizResults(null); }} title="AI Quiz" maxWidth="lg">
        {quizResults ? (
          /* Results view */
          <div className="space-y-4">
            <div className={`text-center p-6 rounded-xl ${quizResults.percentage >= 70 ? 'bg-green-50' : 'bg-amber-50'}`}>
              <div className={`text-4xl font-bold mb-1 ${quizResults.percentage >= 70 ? 'text-green-600' : 'text-amber-600'}`}>
                {quizResults.percentage}%
              </div>
              <div className="text-surface-600 text-sm">{quizResults.score} of {quizResults.total} correct</div>
            </div>
            <div className="max-h-[40vh] overflow-y-auto space-y-3 pr-1">
              {quizResults.results?.map((r: any, i: number) => (
                <div key={i} className={`border rounded-xl p-4 ${r.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <p className="text-sm font-semibold text-surface-900 mb-2">{i + 1}. {r.question}</p>
                  <p className="text-xs mb-1">
                    <span className="font-medium text-surface-600">Your answer: </span>
                    <span className={r.is_correct ? 'text-green-700' : 'text-red-700'}>{r.user_answer || '(no answer)'}</span>
                  </p>
                  {!r.is_correct && (
                    <p className="text-xs mb-1">
                      <span className="font-medium text-surface-600">Correct: </span>
                      <span className="text-green-700">{r.correct_answer}</span>
                    </p>
                  )}
                  {r.explanation && (
                    <p className="text-xs text-surface-500 mt-2 pt-2 border-t border-surface-200">{r.explanation}</p>
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => { setQuizSubmitted(false); setQuizResults(null); }}>
                <RotateCcw className="w-4 h-4 mr-1" /> Retry
              </Button>
              <Button onClick={() => { setShowQuizModal(false); setQuizResults(null); setQuizSubmitted(false); }}>Done</Button>
            </div>
          </div>
        ) : (
          /* Quiz taking view */
          <div className="space-y-4">
            {quizQuestions.length === 0 ? (
              <div className="grid grid-cols-2 gap-3 p-4 bg-surface-50 rounded-xl border border-surface-200">
                <div>
                  <label className="block text-xs font-semibold text-surface-600 mb-1">Questions</label>
                  <Select value={quizCount.toString()} onChange={e => setQuizCount(Number(e.target.value))}>
                    <option value="5">5 questions</option>
                    <option value="10">10 questions</option>
                    <option value="15">15 questions</option>
                  </Select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-surface-600 mb-1">Difficulty</label>
                  <Select value={quizDifficulty} onChange={e => setQuizDifficulty(e.target.value)}>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </Select>
                </div>
              </div>
            ) : (
              <>
                <div className="max-h-[50vh] overflow-y-auto space-y-5 pr-1">
                  {quizQuestions.map((q, i) => (
                    <div key={i} className="border border-surface-200 rounded-xl p-4">
                      <p className="text-sm font-semibold text-surface-900 mb-3">{i + 1}. {q.question}</p>
                      <div className="space-y-2">
                        {q.options.map((opt, oi) => (
                          <label key={oi} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                            quizAnswers[i] === opt ? 'border-primary-500 bg-primary-50' : 'border-surface-200 hover:bg-surface-50'
                          }`}>
                            <input
                              type="radio"
                              name={`q${i}`}
                              value={opt}
                              checked={quizAnswers[i] === opt}
                              onChange={() => {
                                const newAnswers = [...quizAnswers];
                                newAnswers[i] = opt;
                                setQuizAnswers(newAnswers);
                              }}
                              className="text-primary-600"
                            />
                            <span className="text-sm text-surface-900">{opt}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="ghost" onClick={() => { setQuizQuestions([]); setQuizAnswers([]); }}>
                    Regenerate
                  </Button>
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={quizAnswers.some(a => !a)}
                  >
                    Submit Quiz
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
