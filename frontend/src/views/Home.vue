<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- Logo 和标题 -->
    <div class="text-center mb-8">
      <div class="w-20 h-20 mx-auto mb-4 bg-primary-500 rounded-2xl flex items-center justify-center shadow-lg">
        <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
      </div>
      <h1 class="text-4xl font-bold text-gray-800 mb-2">DrawIO AI</h1>
      <p class="text-lg text-gray-600">AI 驱动的智能绘图助手</p>
    </div>

    <!-- 功能介绍 -->
    <div class="max-w-2xl mx-auto px-4 mb-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white p-4 rounded-xl shadow-sm text-center">
          <div class="w-10 h-10 mx-auto mb-2 bg-blue-100 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 class="font-medium text-gray-800">自然语言描述</h3>
          <p class="text-sm text-gray-500 mt-1">用对话的方式描述图表</p>
        </div>
        <div class="bg-white p-4 rounded-xl shadow-sm text-center">
          <div class="w-10 h-10 mx-auto mb-2 bg-green-100 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <h3 class="font-medium text-gray-800">实时预览</h3>
          <p class="text-sm text-gray-500 mt-1">边对话边看图表变化</p>
        </div>
        <div class="bg-white p-4 rounded-xl shadow-sm text-center">
          <div class="w-10 h-10 mx-auto mb-2 bg-purple-100 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </div>
          <h3 class="font-medium text-gray-800">一键导出</h3>
          <p class="text-sm text-gray-500 mt-1">下载标准 .drawio 文件</p>
        </div>
      </div>
    </div>

    <!-- 开始按钮 -->
    <button
      @click="createSession"
      :disabled="loading"
      class="px-8 py-4 bg-primary-500 hover:bg-primary-600 text-white font-medium text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
    >
      <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>{{ loading ? '创建中...' : '开始绘图' }}</span>
    </button>

    <!-- 错误提示 -->
    <p v-if="error" class="mt-4 text-red-500 text-sm">{{ error }}</p>

    <!-- 页脚 -->
    <p class="mt-12 text-gray-400 text-sm">Powered by GLM & draw.io</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const sessionStore = useSessionStore()

const loading = ref(false)
const error = ref('')

const createSession = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const session = await sessionStore.createSession()
    
    // 注意：MCP Server 的 start_session 会自动打开浏览器预览
    // 无需手动 window.open，否则会打开两个窗口
    
    // 跳转到对话页面
    router.push({ name: 'Chat', params: { sessionId: session.session_id } })
  } catch (e) {
    error.value = e.message || '创建会话失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
