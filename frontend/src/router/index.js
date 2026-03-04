import { createRouter, createWebHistory } from 'vue-router'
import GameFlow from '../views/GameFlow.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'home',
            component: GameFlow
        },
        {
            path: '/admin',
            name: 'admin',
            component: () => import('../views/AdminPanel.vue')
        }
    ]
})

export default router
