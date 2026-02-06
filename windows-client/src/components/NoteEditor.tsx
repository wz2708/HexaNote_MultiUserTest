import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { clsx } from 'clsx'
import { X, Plus } from 'lucide-react'

interface NoteEditorProps {
    initialTitle?: string
    initialContent?: string
    initialTags?: string[]
    onSave?: (data: { title: string; content: string; tags: string[] }) => void
}

export function NoteEditor({
    initialTitle = '',
    initialContent = '',
    initialTags = [],
    onSave
}: NoteEditorProps) {
    const [title, setTitle] = useState(initialTitle)
    const [content, setContent] = useState(initialContent)
    const [tags, setTags] = useState<string[]>(initialTags)
    const [tagInput, setTagInput] = useState('')
    const [isPreview, setIsPreview] = useState(false)
    const tagInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        setTitle(initialTitle)
        setContent(initialContent)
        setTags(initialTags)
    }, [initialTitle, initialContent, initialTags])

    const handleAddTag = () => {
        const newTag = tagInput.trim().toLowerCase()
        if (newTag && !tags.includes(newTag)) {
            setTags([...tags, newTag])
        }
        setTagInput('')
        tagInputRef.current?.focus()
    }

    const handleRemoveTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove))
    }

    const handleTagKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddTag()
        } else if (e.key === 'Backspace' && tagInput === '' && tags.length > 0) {
            // Remove last tag on backspace when input is empty
            setTags(tags.slice(0, -1))
        }
    }

    const handleSave = () => {
        if (onSave) {
            onSave({ title: title || 'Untitled Note', content, tags })
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Title and Tags Header */}
            <div className="p-4 border-b border-slate-700 bg-slate-800 space-y-3">
                {/* Title Input */}
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Note Title..."
                    className="w-full bg-transparent text-2xl font-bold text-white placeholder:text-slate-500 focus:outline-none border-b border-transparent focus:border-cyan-500 pb-1 transition-colors"
                />

                {/* Tags */}
                <div className="flex flex-wrap items-center gap-2">
                    {tags.map((tag, idx) => (
                        <span
                            key={idx}
                            className="inline-flex items-center gap-1 text-xs bg-cyan-600/20 text-cyan-300 px-2 py-1 rounded-full border border-cyan-600/30"
                        >
                            {tag}
                            <button
                                onClick={() => handleRemoveTag(tag)}
                                className="hover:text-red-400 transition-colors"
                            >
                                <X size={12} />
                            </button>
                        </span>
                    ))}
                    <div className="flex items-center gap-1">
                        <input
                            ref={tagInputRef}
                            type="text"
                            value={tagInput}
                            onChange={(e) => setTagInput(e.target.value)}
                            onKeyDown={handleTagKeyDown}
                            placeholder="Add tag..."
                            className="bg-transparent text-xs text-slate-300 placeholder:text-slate-600 focus:outline-none w-20"
                        />
                        {tagInput && (
                            <button
                                onClick={handleAddTag}
                                className="p-0.5 text-cyan-500 hover:text-cyan-400"
                            >
                                <Plus size={14} />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Editor Toolbar */}
            <div className="flex items-center justify-between p-2 border-b border-slate-700 bg-slate-800">
                <div className="flex gap-2">
                    <button
                        onClick={() => setIsPreview(false)}
                        className={clsx(
                            'px-3 py-1 rounded text-sm font-medium transition-colors',
                            !isPreview ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-cyan-400'
                        )}
                    >
                        Edit
                    </button>
                    <button
                        onClick={() => setIsPreview(true)}
                        className={clsx(
                            'px-3 py-1 rounded text-sm font-medium transition-colors',
                            isPreview ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-cyan-400'
                        )}
                    >
                        Preview
                    </button>
                </div>
                {onSave && (
                    <button
                        onClick={handleSave}
                        className="px-3 py-1 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-500"
                    >
                        Save
                    </button>
                )}
            </div>

            {/* Editor / Preview Area */}
            <div className="flex-1 overflow-hidden relative">
                {/* Editor */}
                <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className={clsx(
                        "w-full h-full p-4 bg-slate-900 text-slate-100 resize-none focus:outline-none font-mono",
                        isPreview ? 'hidden' : 'block'
                    )}
                    placeholder="# Start writing...

Supports Markdown and Math ($E=mc^2$)"
                />

                {/* Preview */}
                <div
                    className={clsx(
                        "w-full h-full p-4 bg-slate-900 text-slate-100 overflow-auto prose prose-invert prose-cyan max-w-none",
                        !isPreview ? 'hidden' : 'block'
                    )}
                >
                    <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        components={{
                            h1: ({ node, ...props }) => <h1 className="text-3xl font-bold mt-6 mb-4 text-cyan-400" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-2xl font-bold mt-5 mb-3 text-cyan-300" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-xl font-bold mt-4 mb-2 text-cyan-200" {...props} />,
                            p: ({ node, ...props }) => <p className="mb-4 leading-relaxed" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-4" {...props} />,
                            ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4" {...props} />,
                            blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-cyan-500 pl-4 italic text-slate-400 my-4" {...props} />,
                            code: ({ node, className, children, ...props }: any) => {
                                const match = /language-(\w+)/.exec(className || '')
                                return match ? (
                                    <div className="bg-slate-950 rounded-lg p-4 my-4 overflow-x-auto border border-slate-800">
                                        <code className={className} {...props}>
                                            {children}
                                        </code>
                                    </div>
                                ) : (
                                    <code className="bg-slate-800 px-1.5 py-0.5 rounded text-sm text-cyan-300" {...props}>
                                        {children}
                                    </code>
                                )
                            }
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    )
}
