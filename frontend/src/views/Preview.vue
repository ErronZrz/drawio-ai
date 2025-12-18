<template>
  <div class="h-screen flex flex-col bg-gray-100">
    <!-- 顶部工具栏 -->
    <header class="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-gray-800">图表预览</h1>
      <span class="text-sm text-gray-400">会话: {{ sessionId }}</span>
    </header>

    <!-- 预览区域 -->
    <main class="flex-1 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-lg p-4 w-full h-full overflow-auto">
        <!-- 这里将嵌入 drawio 预览或渲染 SVG -->
        <div v-if="loading" class="flex items-center justify-center h-full">
          <div class="text-center">
            <svg class="w-12 h-12 mx-auto text-gray-300 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="mt-4 text-gray-500">加载中...</p>
          </div>
        </div>
        
        <div v-else-if="!diagramXml" class="flex items-center justify-center h-full">
          <div class="text-center text-gray-400">
            <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p>暂无图表</p>
            <p class="text-sm mt-1">请在对话界面描述你想要的图表</p>
          </div>
        </div>
        
        <!-- 图表内容 -->
        <div v-else class="h-full" v-html="renderedSvg"></div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

const loading = ref(true)
const diagramXml = ref('')
const renderedSvg = ref('')

// 获取图表
const fetchDiagram = async () => {
  try {
    const response = await api.getDiagram(props.sessionId)
    diagramXml.value = response.xml
    // TODO: 将 XML 渲染为 SVG
    renderedSvg.value = `<pre class="text-xs overflow-auto">${escapeHtml(diagramXml.value)}</pre>`
  } catch (error) {
    console.error('获取图表失败:', error)
  } finally {
    loading.value = false
  }
}

// HTML 转义
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 定时刷新
let refreshInterval = null

onMounted(() => {
  fetchDiagram()
  // 每 2 秒刷新一次
  refreshInterval = setInterval(fetchDiagram, 2000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
