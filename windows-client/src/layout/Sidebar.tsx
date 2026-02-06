import { Link, useLocation } from 'react-router-dom'
import { Sticker, MessageSquare, Settings, Hexagon } from 'lucide-react'
import { clsx } from 'clsx'

export function Sidebar() {
    const location = useLocation()

    const navItems = [
        { name: 'Notes', icon: Sticker, path: '/' },
        { name: 'Chat', icon: MessageSquare, path: '/chat' },
        // { name: 'Settings', icon: Settings, path: '/settings' },
    ]

    return (
        <div className="w-16 md:w-64 h-full bg-slate-900 border-r border-slate-800 flex flex-col transition-all duration-300">
            <div className="h-16 flex items-center justify-center border-b border-slate-800">
                <Hexagon className="w-8 h-8 text-cyan-500" />
                <span className="ml-3 font-bold text-xl text-white hidden md:block">HexaNote</span>
            </div>

            <nav className="flex-1 py-4 flex flex-col gap-2 p-2">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={clsx(
                                'flex items-center p-3 rounded-lg transition-colors group',
                                isActive
                                    ? 'bg-cyan-500/10 text-cyan-400'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            )}
                        >
                            <item.icon className="w-6 h-6" />
                            <span className="ml-3 font-medium hidden md:block">{item.name}</span>
                            {isActive && (
                                <div className="absolute left-0 w-1 h-8 bg-cyan-500 rounded-r-full" />
                            )}
                        </Link>
                    )
                })}
            </nav>

            <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center hidden md:block">
                v0.1.0 Alpha
            </div>
        </div>
    )
}
