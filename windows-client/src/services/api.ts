import axios from 'axios'

const API_Base = 'http://localhost:8001/api/v1'

export interface Note {
    id: string
    title: string
    content: string
    tags: string[]
    version: number
    created_at?: string
    updated_at?: string
}

export interface SemanticSearchResult {
    note_id: string
    title: string
    content: string
    tags: string[]
    created_at?: string
    updated_at?: string
    relevance_score?: number
}

export interface ChatRequest {
    message: string
    session_id?: string
    limit?: number
    additional_context?: string
}

export interface ContextNote {
    note_id: string
    title: string
    content_preview: string
    relevance_score?: number
}

export interface ChatResponse {
    message: string
    session_id: string
    context_notes: ContextNote[]
    created_at: string
}

const api = axios.create({
    baseURL: API_Base,
    headers: {
        'Content-Type': 'application/json',
    },
})

export const NoteService = {
    getAll: async () => {
        // Backend returns { notes: [], total: ... }
        const response = await api.get<{ notes: Note[] }>('/notes')
        return response.data.notes
    },

    getById: async (id: string): Promise<Note> => {
        const response = await api.get<Note>(`/notes/${id}`)
        return response.data
    },

    create: async (note: { title: string; content: string; tags: string[] }) => {
        const response = await api.post<Note>('/notes', note)
        return response.data
    },

    search: async (query: string): Promise<SemanticSearchResult[]> => {
        const response = await api.get<{ results: SemanticSearchResult[] }>('/notes/search/semantic', {
            params: { q: query, limit: 10 }
        })
        return response.data.results
    },

    update: async (id: string, note: { title: string; content: string; tags: string[]; version: number }) => {
        const response = await api.put<Note>(`/notes/${id}`, note)
        return response.data
    },

    delete: async (id: string) => {
        await api.delete(`/notes/${id}`)
    },

    reindex: async () => {
        const response = await api.post<{ message: string; total: number; success: number; errors: number }>('/notes/reindex')
        return response.data
    },

    searchWithinNote: async (noteId: string, query: string, window: number = 2) => {
        const response = await api.get<{
            context: string;
            title: string;
            chunk_range: string;
            total_chunks: number;
            best_chunk_index: number;
        }>(`/notes/${noteId}/search`, {
            params: { q: query, window }
        })
        return response.data
    },
}

export const ChatService = {
    query: async (message: string, sessionId?: string | null, additionalContext?: string) => {
        const payload: any = {
            message,
            limit: 5
        }
        if (sessionId) {
            payload.session_id = sessionId
        }
        if (additionalContext) {
            payload.additional_context = additionalContext
        }

        const response = await api.post<ChatResponse>('/chat/query', payload)
        return response.data
    }
}
