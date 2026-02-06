import { contextBridge } from 'electron'

// --------- Expose some API to the Renderer process ---------
contextBridge.exposeInMainWorld('ipcRenderer', {
    on(...args: Parameters<typeof window.ipcRenderer.on>) {
        const [channel, listener] = args
        return window.ipcRenderer.on(channel, (event, ...args) => listener(event, ...args))
    },
    off(...args: Parameters<typeof window.ipcRenderer.off>) {
        const [channel, ...omit] = args
        return window.ipcRenderer.off(channel, ...omit)
    },
    send(...args: Parameters<typeof window.ipcRenderer.send>) {
        const [channel, ...omit] = args
        return window.ipcRenderer.send(channel, ...omit)
    },
    invoke(...args: Parameters<typeof window.ipcRenderer.invoke>) {
        const [channel, ...omit] = args
        return window.ipcRenderer.invoke(channel, ...omit)
    },

    // You can expose other apts you need here.
    // ...
})
