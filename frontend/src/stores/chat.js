import { defineStore } from 'pinia'
import api from '@/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: {},  // sessionId -> messages[]
    loading: false
  }),

  actions: {
    async sendMessage(sessionId, message, history = []) {
      this.loading = true
      try {
        // 构建历史消息
        const chatHistory = history.slice(-10).map(msg => ({
          role: msg.role,
          content: msg.content
        }))

        const response = await api.chat(sessionId, message, chatHistory)
        return response
      } finally {
        this.loading = false
      }
    },

    // 流式发送消息
    async sendMessageStream(sessionId, message, history = [], onChunk) {
      this.loading = true
      try {
        const chatHistory = history.slice(-10).map(msg => ({
          role: msg.role,
          content: msg.content
        }))

        await api.chatStream(sessionId, message, chatHistory, onChunk)
      } finally {
        this.loading = false
      }
    },

    async downloadDiagram(sessionId) {
      const blob = await api.downloadDiagram(sessionId)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `diagram_${sessionId}.drawio`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }
  }
})
