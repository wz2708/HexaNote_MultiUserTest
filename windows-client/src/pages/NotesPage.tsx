import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { NoteService, Note } from '../services/api'
import { NoteEditor } from '../components/NoteEditor'
import { Plus, Search, FileText, Loader2, Trash2, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'

export function NotesPage() {
    const { noteId } = useParams<{ noteId?: string }>()
    const [notes, setNotes] = useState<Note[]>([])
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedNote, setSelectedNote] = useState<Note | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [isSaving, setIsSaving] = useState(false)

    const fetchNotes = async () => {
        setIsLoading(true)
        try {
            const data = await NoteService.getAll()
            setNotes(data)
        } catch (error) {
            console.error('Failed to fetch notes', error)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchNotes()
    }, [])

    // Load specific note from URL param (e.g., /note/abc-123)
    useEffect(() => {
        if (noteId && notes.length > 0) {
            const note = notes.find(n => n.id === noteId)
            if (note) {
                setSelectedNote(note)
            }
        }
    }, [noteId, notes])

    // Filter notes locally by search query
    const filteredNotes = searchQuery
        ? notes.filter(n =>
            n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            n.content.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : notes

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        // Local filter, no need to fetch
    }

    const handleCreateNote = () => {
        const newNote: Note = {
            id: 'new', // Placeholder, backend will generate real ID
            title: '',
            content: '',
            tags: [],
            version: 0  // Placeholder, backend will generate
        }
        setSelectedNote(newNote)
    }

    const handleSaveNote = async (data: { title: string; content: string; tags: string[] }) => {
        if (!selectedNote) return
        setIsSaving(true)
        try {
            let savedNote: Note
            if (selectedNote.id === 'new') {
                // Create new note
                const noteToCreate = {
                    title: data.title || 'Untitled Note',
                    content: data.content,
                    tags: data.tags
                }
                savedNote = await NoteService.create(noteToCreate)
            } else {
                // Update existing note - include version for conflict detection
                const noteToUpdate = {
                    title: data.title || 'Untitled Note',
                    content: data.content,
                    tags: data.tags,
                    version: selectedNote.version
                }
                savedNote = await NoteService.update(selectedNote.id, noteToUpdate)
            }

            setSelectedNote(savedNote)
            fetchNotes() // Refresh list
        } catch (error) {
            console.error('Failed to save note', error)
        } finally {
            setIsSaving(false)
        }
    }

    const handleDeleteNote = async (noteId: string) => {
        if (noteId === 'new') {
            setSelectedNote(null)
            return
        }

        if (!confirm('Are you sure you want to delete this note?')) return

        try {
            await NoteService.delete(noteId)
            setSelectedNote(null)
            fetchNotes()
        } catch (error) {
            console.error('Failed to delete note', error)
        }
    }

    return (
        <div className="flex h-full">
            {/* Note List Sidebar */}
            <div className="w-80 border-r border-slate-800 bg-slate-900 flex flex-col">
                <div className="p-4 border-b border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="font-bold text-lg">My Notes</h2>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={fetchNotes}
                                className="p-1.5 bg-slate-800 text-cyan-400 rounded hover:bg-slate-800/90 transition-colors"
                                title="Refresh notes"
                            >
                                {isLoading ? (
                                    <Loader2 className="animate-spin text-cyan-500" />
                                ) : (
                                    <RefreshCw size={18} />
                                )}
                            </button>
                            <button
                                onClick={handleCreateNote}
                                className="p-1.5 bg-cyan-600 text-white rounded hover:bg-cyan-500 transition-colors"
                            >
                                <Plus size={18} />
                            </button>
                        </div>
                    </div>
                    <form onSubmit={handleSearch} className="relative">
                        <Search className="absolute left-3 top-2.5 text-cyan-500 w-4 h-4" />
                        <input
                            type="text"
                            placeholder="Filter notes..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-slate-800 text-sm pl-9 pr-3 py-2 rounded-lg focus:outline-none focus:ring-1 focus:ring-cyan-500/50 placeholder:text-slate-600"
                        />
                    </form>
                    {searchQuery && (
                        <div className="text-[10px] uppercase tracking-wider text-cyan-500 font-bold px-1">
                            {filteredNotes.length} notes found
                        </div>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <div className="flex justify-center p-4">
                            <Loader2 className="animate-spin text-cyan-500" />
                        </div>
                    ) : (
                        filteredNotes.map(note => (
                            <div
                                key={note.id}
                                onClick={() => setSelectedNote(note)}
                                className={clsx(
                                    "p-3 border-b border-slate-800/50 cursor-pointer hover:bg-slate-800 transition-colors",
                                    selectedNote?.id === note.id ? "bg-slate-800 border-l-2 border-l-cyan-500" : ""
                                )}
                            >
                                <div className="font-medium text-sm text-slate-200 truncate">
                                    {note.title || 'Untitled Note'}
                                </div>
                                <div className="text-xs text-slate-500 mt-1 truncate">
                                    {note.content.substring(0, 50)}
                                </div>
                                {note.tags && note.tags.length > 0 && (
                                    <div className="flex gap-1 mt-2 flex-wrap">
                                        {note.tags.slice(0, 3).map((tag: any, i: number) => (
                                            <span key={i} className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-cyan-400">
                                                {typeof tag === 'string' ? tag : tag.name}
                                            </span>
                                        ))}
                                        {note.tags.length > 3 && (
                                            <span className="text-[10px] text-slate-500">+{note.tags.length - 3}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Main Area */}
            <div className="flex-1 bg-slate-950 flex flex-col">
                {selectedNote ? (
                    <>
                        {/* Delete button header */}
                        <div className="flex justify-end p-2 bg-slate-900 border-b border-slate-800">
                            <button
                                onClick={() => handleDeleteNote(selectedNote.id)}
                                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                title="Delete note"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <NoteEditor
                                key={selectedNote.id}
                                initialTitle={selectedNote.title}
                                initialContent={selectedNote.content}
                                initialTags={selectedNote.tags}
                                onSave={handleSaveNote}
                                autosaveDelayMs={5000}
                            />
                        </div>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                        <FileText className="w-16 h-16 mb-4 opacity-20" />
                        <p>Select a note or create a new one</p>
                    </div>
                )}
            </div>
        </div>
    )
}
