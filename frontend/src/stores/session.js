import { defineStore } from 'pinia'
import api from '@/api'

export const useSessionStore = defineStore('session', {
  state: () => ({
    currentSession: null,
    sessions: []
  }),

  actions: {
    async createSession() {
      const response = await api.createSession()
      this.currentSession = response
      this.sessions.push(response)
      return response
    },

    async getSession(sessionId) {
      const response = await api.getSession(sessionId)
      this.currentSession = response
      return response
    },

    clearCurrentSession() {
      this.currentSession = null
    }
  }
})
