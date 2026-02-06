import { HashRouter, Routes, Route } from 'react-router-dom'
import { MainLayout } from './layout/MainLayout'
import { NotesPage } from './pages/NotesPage'
import { ChatPage } from './pages/ChatPage'

function App() {
    return (
        <HashRouter>
            <Routes>
                <Route element={<MainLayout />}>
                    <Route path="/" element={<NotesPage />} />
                    <Route path="/note/:noteId" element={<NotesPage />} />
                    <Route path="/chat" element={<ChatPage />} />
                </Route>
            </Routes>
        </HashRouter>
    )
}

export default App
