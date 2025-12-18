import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/chat/:sessionId',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    props: true
  },
  {
    path: '/preview/:sessionId',
    name: 'Preview',
    component: () => import('@/views/Preview.vue'),
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
