import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function MainLayout() {
    return (
        <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
            <Sidebar />
            <main className="flex-1 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-900/5 via-transparent to-purple-900/5 pointer-events-none" />
                <div className="relative h-full w-full">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
