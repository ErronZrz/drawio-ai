<template>
  <div class="h-screen flex flex-col">
    <!-- 顶部导航 -->
    <header class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <router-link to="/" class="text-gray-500 hover:text-gray-700">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </router-link>
        <h1 class="text-lg font-semibold text-gray-800">AI 绘图对话</h1>
        <span class="text-sm text-gray-400">会话: {{ sessionId }}</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="openPreview"
          class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <span class="flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            预览
          </span>
        </button>
        <button
          @click="downloadDiagram"
          :disabled="downloading"
          class="px-3 py-1.5 text-sm bg-primary-500 text-white hover:bg-primary-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <span class="flex items-center gap-1">
            <svg v-if="downloading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载
          </span>
        </button>
      </div>
    </header>

    <!-- 聊天区域 -->
    <main class="flex-1 overflow-hidden flex flex-col bg-gray-50">
      <!-- 消息列表 -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0 && !streamingMessage" class="text-center py-12">
          <div class="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-800 mb-2">开始创建你的图表</h3>
          <p class="text-gray-500 max-w-md mx-auto">
            描述你想要的图表，例如：「帮我画一个用户登录流程图」或「创建一个三层架构图」
          </p>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-enter"
          :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
        >
          <div
            :class="[
              'max-w-[80%] px-4 py-3 rounded-2xl',
              msg.role === 'user'
                ? 'bg-primary-500 text-white rounded-br-md'
                : 'bg-white text-gray-800 shadow-sm rounded-bl-md'
            ]"
          >
            <!-- 渲染消息内容 -->
            <MessageContent :content="msg.content" :isUser="msg.role === 'user'" />
            <p 
              v-if="msg.diagram_updated" 
              class="mt-2 text-xs opacity-70 flex items-center gap-1"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              图表已更新
            </p>
          </div>
        </div>

        <!-- 流式响应中的消息 -->
        <div v-if="isStreaming" class="flex justify-start">
          <div class="max-w-[80%] px-4 py-3 rounded-2xl bg-white text-gray-800 shadow-sm rounded-bl-md">
            <!-- 灰色小字显示原始输出 -->
            <div v-if="streamingRaw" class="text-xs text-gray-400 mb-2 font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto border border-gray-200 rounded p-2 bg-gray-50">
              {{ streamingRaw }}
            </div>
            <!-- 分隔线 -->
            <div v-if="streamingRaw && streamingMessage" class="border-t border-gray-100 my-2"></div>
            <!-- 解析后的内容 -->
            <MessageContent v-if="streamingMessage" :content="streamingMessage" :isUser="false" />
            <!-- 正在输入指示器 -->
            <div class="flex items-center gap-1 mt-2">
              <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></div>
              <span class="text-xs text-gray-400">AI 正在生成...</span>
            </div>
          </div>
        </div>

        <!-- 加载中（非流式时显示） -->
        <div v-if="loading && !isStreaming" class="flex justify-start">
          <div class="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-gray-200 bg-white p-4">
        <form @submit.prevent="sendMessage" class="flex gap-3">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="描述你想要的图表..."
            class="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            :disabled="loading"
          />
          <button
            type="submit"
            :disabled="!inputMessage.trim() || loading"
            class="px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, h, defineComponent } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useSessionStore } from '@/stores/session'

// 消息内容渲染组件
const MessageContent = defineComponent({
  props: {
    content: { type: String, required: true },
    isUser: { type: Boolean, default: false }
  },
  setup(props) {
    return () => {
      if (props.isUser) {
        // 用户消息：纯文本
        return h('p', { class: 'whitespace-pre-wrap' }, props.content)
      }
      
      // AI 消息：解析代码块
      const parts = []
      const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g
      let lastIndex = 0
      let match
      
      while ((match = codeBlockRegex.exec(props.content)) !== null) {
        // 代码块之前的文本
        if (match.index > lastIndex) {
          const text = props.content.slice(lastIndex, match.index)
          parts.push(h('p', { class: 'whitespace-pre-wrap mb-2' }, text))
        }
        
        // 代码块
        const lang = match[1] || 'text'
        const code = match[2].trim()
        parts.push(
          h('div', { class: 'my-2' }, [
            h('div', { class: 'bg-gray-700 text-gray-300 text-xs px-3 py-1 rounded-t-lg' }, lang.toUpperCase() || 'CODE'),
            h('pre', { class: 'bg-gray-800 text-gray-100 p-3 rounded-b-lg overflow-x-auto text-sm' }, [
              h('code', {}, code)
            ])
          ])
        )
        
        lastIndex = match.index + match[0].length
      }
      
      // 剩余文本
      if (lastIndex < props.content.length) {
        const text = props.content.slice(lastIndex)
        parts.push(h('p', { class: 'whitespace-pre-wrap' }, text))
      }
      
      return h('div', {}, parts.length > 0 ? parts : props.content)
    }
  }
})

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

const chatStore = useChatStore()
const sessionStore = useSessionStore()

const messagesContainer = ref(null)
const inputMessage = ref('')
const loading = ref(false)
const downloading = ref(false)
const messages = ref([])

// 流式响应状态
const streamingMessage = ref('')  // 解析后的回复内容
const streamingRaw = ref('')      // 原始输出内容（灰色小字显示）
const isStreaming = ref(false)    // 是否正在接收流式响应

// 发送消息（使用流式响应）
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage
  })

  await scrollToBottom()
  loading.value = true
  streamingMessage.value = ''
  streamingRaw.value = ''
  isStreaming.value = false

  let finalResult = null

  try {
    await chatStore.sendMessageStream(
      props.sessionId,
      userMessage,
      messages.value,
      (chunk) => {
        // 处理流式数据
        if (chunk.type === 'text') {
          // 开始接收流式数据
          isStreaming.value = true
          // 累积原始输出
          streamingRaw.value += chunk.content
          // 尝试从原始内容中提取 reply
          const replyMatch = streamingRaw.value.match(/"reply"\s*:\s*"([^"]*(?:\\.[^"]*)*)"/s)
          if (replyMatch) {
            try {
              streamingMessage.value = JSON.parse(`"${replyMatch[1]}"`)
            } catch (e) {
              // 解析失败，使用原始匹配
              streamingMessage.value = replyMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
            }
          }
          scrollToBottom()
        } else if (chunk.type === 'complete') {
          // 完整结果
          finalResult = chunk.result
        } else if (chunk.type === 'diagram_status') {
          // 图表更新状态
          if (finalResult) {
            finalResult.diagram_updated = chunk.updated
          }
        } else if (chunk.type === 'error') {
          streamingMessage.value = `错误: ${chunk.message}`
        }
      }
    )

    // 添加最终的助手回复
    if (finalResult) {
      messages.value.push({
        role: 'assistant',
        content: finalResult.reply || streamingMessage.value,
        diagram_updated: finalResult.diagram_updated || false
      })
    } else if (streamingMessage.value) {
      // 如果没有 finalResult，使用流式累积的内容
      messages.value.push({
        role: 'assistant',
        content: streamingMessage.value
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `抱歉，处理请求时出错：${error.message}`
    })
  } finally {
    loading.value = false
    streamingMessage.value = ''
    streamingRaw.value = ''
    isStreaming.value = false
    await scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 打开预览
const openPreview = () => {
  const session = sessionStore.currentSession
  if (session?.preview_url) {
    window.open(session.preview_url, '_blank', 'width=800,height=600')
  }
}

// 下载图表
const downloadDiagram = async () => {
  downloading.value = true
  try {
    await chatStore.downloadDiagram(props.sessionId)
  } catch (error) {
    alert('下载失败: ' + error.message)
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  // 获取会话信息
  sessionStore.getSession(props.sessionId)
})
</script>
