import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default {
  // 会话管理
  createSession() {
    return apiClient.post('/session')
  },

  getSession(sessionId) {
    return apiClient.get(`/session/${sessionId}`)
  },

  deleteSession(sessionId) {
    return apiClient.delete(`/session/${sessionId}`)
  },

  // 对话
  chat(sessionId, message, history = []) {
    return apiClient.post(`/chat/${sessionId}`, {
      message,
      history
    })
  },

  // 流式对话
  async chatStream(sessionId, message, history = [], onChunk) {
    const response = await fetch(`/api/chat/${sessionId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, history })
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onChunk(data)
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  },

  // 图表操作
  getDiagram(sessionId) {
    return apiClient.get(`/diagram/${sessionId}`)
  },

  editDiagram(sessionId, operations) {
    return apiClient.post(`/diagram/${sessionId}/edit`, {
      operations
    })
  },

  async downloadDiagram(sessionId) {
    const response = await axios.get(`/api/diagram/${sessionId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }
}
