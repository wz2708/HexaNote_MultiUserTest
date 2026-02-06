import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatService, NoteService, ContextNote, SemanticSearchResult } from '../services/api'
import { Send, Bot, User, Loader2, Search, MessageSquare, FileText, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { clsx } from 'clsx'

type ChatMode = 'rag' | 'semantic'

interface Message {
    role: 'user' | 'assistant' | 'system'
    content: string
    sources?: ContextNote[]
}

export function ChatInterface() {
    const navigate = useNavigate()
    const [mode, setMode] = useState<ChatMode>('rag')
    const [messages, setMessages] = useState<Message[]>([])
    const [searchResults, setSearchResults] = useState<SemanticSearchResult[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [isReindexing, setIsReindexing] = useState(false)
    const [reindexMessage, setReindexMessage] = useState<string | null>(null)
    const [loadedNoteContext, setLoadedNoteContext] = useState<{ noteId: string; title: string } | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, searchResults])

    const handleModeChange = (newMode: ChatMode) => {
        setMode(newMode)
        // Clear state when switching modes
        setMessages([])
        setSearchResults([])
        setSessionId(null)
        setInput('')
    }

    const handleReindex = async () => {
        setIsReindexing(true)
        setReindexMessage(null)
        try {
            const result = await NoteService.reindex()
            setReindexMessage(`✓ ${result.message}`)
            setTimeout(() => setReindexMessage(null), 5000)
        } catch (error) {
            console.error('Reindex error:', error)
            setReindexMessage('❌ Failed to reindex notes')
        } finally {
            setIsReindexing(false)
        }
    }

    const handleSend = async () => {
        if (!input.trim() || isLoading) return

        setIsLoading(true)

        if (mode === 'rag') {
            // RAG mode: use LLM with context
            const userMessage: Message = { role: 'user', content: input }
            setMessages(prev => [...prev, userMessage])

            // Prepare additional context by searching within loaded note
            let additionalContext: string | undefined = undefined
            if (loadedNoteContext) {
                console.log('🔍 [ChatInterface] Loaded note context:', loadedNoteContext)
                try {
                    console.log('🔍 [ChatInterface] Calling searchWithinNote...')
                    const searchResult = await NoteService.searchWithinNote(
                        loadedNoteContext.noteId,
                        input,
                        2  // 2 chunks before and after
                    )
                    console.log('✓ [ChatInterface] Search result:', searchResult)
                    additionalContext = `Relevant excerpt from "${searchResult.title}" (chunks ${searchResult.chunk_range} of ${searchResult.total_chunks}):\n\n${searchResult.context}`
                    console.log('📝 [ChatInterface] Additional context length:', additionalContext.length)
                } catch (error) {
                    console.error('❌ [ChatInterface] Error searching within note:', error)
                    // Continue without additional context
                }
            }

            setInput('')
            if (loadedNoteContext) {
                setLoadedNoteContext(null) // Clear after use
            }

            try {
                const response = await ChatService.query(input, sessionId, additionalContext)

                if (!sessionId && response.session_id) {
                    setSessionId(response.session_id)
                }

                const botMessage: Message = {
                    role: 'assistant',
                    content: response.message,
                    sources: response.context_notes
                }
                setMessages(prev => [...prev, botMessage])
            } catch (error) {
                console.error('Chat error:', error)
                setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error retrieving the answer.' }])
            }
        } else {
            // Semantic mode: just search, no LLM
            const query = input
            setInput('')
            setSearchResults([])  // Clear previous results

            try {
                const results = await NoteService.search(query)
                // Sort by relevance score (descending)
                const sorted = [...results].sort((a, b) =>
                    (b.relevance_score || 0) - (a.relevance_score || 0)
                )
                setSearchResults(sorted)
            } catch (error) {
                console.error('Search error:', error)
                setSearchResults([])
            }
        }

        setIsLoading(false)
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const handleLoadNoteContext = async (noteId: string, noteTitle: string) => {
        console.log('📌 [ChatInterface] Loading note context:', { noteId, noteTitle })
        // Store note reference for smart context extraction
        setLoadedNoteContext({ noteId, title: noteTitle })

        // Add a system message to show the note was loaded
        const systemMessage: Message = {
            role: 'system',
            content: `✓ Loaded "${noteTitle}" for in-depth Q&A. Ask your next question to search within this note.`
        }
        setMessages(prev => [...prev, systemMessage])
    }

    return (
        <div className="flex flex-col h-full w-full overflow-hidden bg-slate-900">
            {/* Mode Tabs + Reindex Button */}
            <div className="flex-shrink-0 flex items-center justify-between border-b border-slate-800 bg-slate-900/80">
                <div className="flex">
                    <button
                        onClick={() => handleModeChange('rag')}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2",
                            mode === 'rag'
                                ? "border-cyan-500 text-cyan-400 bg-slate-800/50"
                                : "border-transparent text-slate-400 hover:text-slate-300 hover:bg-slate-800/30"
                        )}
                    >
                        <MessageSquare size={16} />
                        RAG Chat
                    </button>
                    <button
                        onClick={() => handleModeChange('semantic')}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2",
                            mode === 'semantic'
                                ? "border-purple-500 text-purple-400 bg-slate-800/50"
                                : "border-transparent text-slate-400 hover:text-slate-300 hover:bg-slate-800/30"
                        )}
                    >
                        <Search size={16} />
                        Semantic Search
                    </button>
                </div>

                {/* Reindex Button */}
                <div className="flex items-center gap-2 px-3">
                    {reindexMessage && (
                        <span className="text-xs text-green-400">{reindexMessage}</span>
                    )}
                    <button
                        onClick={handleReindex}
                        disabled={isReindexing}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-cyan-400 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
                        title="Re-sync all notes to vector database"
                    >
                        <RefreshCw size={14} className={isReindexing ? 'animate-spin' : ''} />
                        {isReindexing ? 'Reindexing...' : 'Reindex'}
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
                {mode === 'rag' ? (
                    // RAG Chat Messages
                    <>
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                <Bot className="w-16 h-16 mb-4 opacity-50" />
                                <p className="text-center">Ask anything about your notes...</p>
                                <p className="text-xs text-slate-600 mt-2">AI will search and synthesize answers from your notes</p>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            msg.role === 'system' ? (
                                // System messages (note loaded notifications)
                                <div key={idx} className="flex justify-center max-w-3xl mx-auto">
                                    <div className="bg-amber-900/20 border border-amber-600/30 rounded-lg px-3 py-2 text-xs text-amber-300">
                                        {msg.content}
                                    </div>
                                </div>
                            ) : (
                                // User and Assistant messages
                                <div
                                    key={idx}
                                    className={clsx(
                                        "flex gap-3 max-w-3xl mx-auto",
                                        msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                                    )}
                                >
                                    <div className={clsx(
                                        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                        msg.role === 'user' ? "bg-cyan-600" : "bg-purple-600"
                                    )}>
                                        {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                    </div>

                                    <div className={clsx(
                                        "rounded-lg p-3 max-w-[80%] text-sm",
                                        msg.role === 'user'
                                            ? "bg-cyan-600/10 text-cyan-100 border border-cyan-600/20"
                                            : "bg-slate-800 text-slate-100 border border-slate-700"
                                    )}>
                                        <ReactMarkdown
                                            className="prose prose-invert prose-sm max-w-none"
                                            remarkPlugins={[remarkMath]}
                                            rehypePlugins={[rehypeKatex]}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>

                                        {msg.sources && msg.sources.length > 0 && (
                                            <div className="mt-3 pt-2 border-t border-slate-700">
                                                <p className="text-xs text-slate-400 font-semibold mb-1">Sources (click to load full content):</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {msg.sources.map((source, i) => (
                                                        <button
                                                            key={i}
                                                            onClick={() => handleLoadNoteContext(source.note_id, source.title)}
                                                            className="text-xs bg-slate-900 px-2 py-1 rounded text-purple-300 hover:bg-purple-900/50 hover:text-purple-200 transition-colors cursor-pointer"
                                                        >
                                                            {source.title}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )
                        ))}
                    </>
                ) : (
                    // Semantic Search Results
                    <>
                        {searchResults.length === 0 && !isLoading && (
                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                <Search className="w-16 h-16 mb-4 opacity-50" />
                                <p className="text-center">Search for notes semantically...</p>
                                <p className="text-xs text-slate-600 mt-2">Find notes by meaning, not just keywords</p>
                            </div>
                        )}

                        {searchResults.length > 0 && (
                            <div className="max-w-3xl mx-auto space-y-3">
                                <p className="text-xs text-purple-400 font-semibold uppercase tracking-wider">
                                    {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} found
                                </p>
                                {searchResults.map((result, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => navigate(`/note/${result.note_id}`)}
                                        className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-purple-500/50 transition-colors cursor-pointer"
                                    >
                                        <div className="flex items-start gap-3">
                                            <FileText className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="font-medium text-slate-200 truncate">
                                                        {result.title || 'Untitled Note'}
                                                    </h3>
                                                    {result.relevance_score && (
                                                        <span className="text-[10px] text-purple-300 bg-purple-900/50 px-2 py-0.5 rounded ml-2">
                                                            {(result.relevance_score * 100).toFixed(0)}% match
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                                                    {result.content.substring(0, 150)}...
                                                </p>
                                                {result.tags && result.tags.length > 0 && (
                                                    <div className="flex gap-1 mt-2 flex-wrap">
                                                        {result.tags.slice(0, 3).map((tag: string, i: number) => (
                                                            <span key={i} className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-purple-300">
                                                                {tag}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {isLoading && (
                    <div className="flex gap-3 max-w-3xl mx-auto">
                        <div className={clsx(
                            "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                            mode === 'rag' ? "bg-purple-600" : "bg-purple-600"
                        )}>
                            {mode === 'rag' ? <Bot size={16} /> : <Search size={16} />}
                        </div>
                        <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="flex-shrink-0 p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <div className="max-w-3xl mx-auto relative">
                    {loadedNoteContext && (
                        <div className="mb-2 text-xs text-amber-400 bg-amber-900/20 border border-amber-600/30 rounded px-2 py-1">
                            💡 Note context loaded - will be included in your next question
                        </div>
                    )}
                    <div className="relative cursor-text">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={mode === 'rag' ? "Ask a question about your notes..." : "Search for notes by meaning..."}
                            className="w-full bg-slate-800 text-white rounded-xl pl-4 pr-12 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none h-[52px] scrollbar-hide"
                            autoFocus
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className={clsx(
                                "absolute right-2 top-2 p-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors",
                                mode === 'rag' ? "bg-cyan-600 hover:bg-cyan-500" : "bg-purple-600 hover:bg-purple-500"
                            )}
                        >
                            {mode === 'rag' ? <Send size={18} /> : <Search size={18} />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
