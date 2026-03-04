<template>
  <div class="app-container">
    <div class="bg-particles"></div>
    <header class="app-header">
      <div class="header-inner">
        <div class="header-brand">
          <span class="brand-ornament">༄</span>
          <h1>时空修复图鉴</h1>
          <span class="brand-ornament">༄</span>
        </div>
        <div class="subtitle">Thangka Restoration Scroll</div>
      </div>
    </header>
    <main class="app-main">
      <router-view></router-view>
    </main>
    <div class="tashi-container" v-if="showTashi">
      <DialogBox />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DialogBox from './components/DialogBox.vue'
import { useGameStore, GameStages } from './stores/game'

const gameStore = useGameStore()
const showTashi = computed(() => {
    // Tashi was unmounting while receiving new messages during PURIFYING/RESTORING,
    // which caused the Vue Transition crash. We keep him always visible now.
    return true
})
</script>

<style>
/* ============================================================
   「法界之门 · Dharma Gate」 Design System
   ============================================================ */

/* --- CSS Custom Properties (Design Tokens) --- */
:root {
  --bg-deep: #0a0612;
  --bg-surface: #0d1117;
  --bg-card: rgba(13, 17, 23, 0.85);
  --bg-glass: rgba(255, 255, 255, 0.04);
  --border-subtle: rgba(201, 162, 39, 0.15);
  --border-glow: rgba(201, 162, 39, 0.4);
  --gold-primary: #c9a227;
  --gold-light: #e8d48b;
  --gold-dim: #a48e65;
  --lapis: #2a4a7f;
  --lapis-glow: rgba(42, 74, 127, 0.3);
  --text-primary: #e8dbb0;
  --text-secondary: #9a8e72;
  --text-bright: #fff8e7;
  --shadow-deep: 0 8px 32px rgba(0, 0, 0, 0.6);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --transition-smooth: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --font-display: 'Noto Serif SC', 'STSong', 'SimSun', Georgia, serif;
  --font-body: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* --- Global Resets --- */
*, *::before, *::after {
  box-sizing: border-box;
}

body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: var(--font-body);
  background-color: var(--bg-deep);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
}

/* --- App Container with Deep Space Background --- */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: relative;
  overflow: hidden;
  /* Multi-layered background: radial glow + noise texture */
  background:
    radial-gradient(ellipse at 30% 20%, rgba(42, 74, 127, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(201, 162, 39, 0.05) 0%, transparent 50%),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-surface) 100%);
}

/* Floating golden dust particles (pure CSS) */
.bg-particles {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-particles::before,
.bg-particles::after {
  content: '';
  position: absolute;
  width: 3px; height: 3px;
  background: var(--gold-light);
  border-radius: 50%;
  opacity: 0;
  animation: floatParticle 12s ease-in-out infinite;
}

.bg-particles::before {
  left: 20%; top: 30%;
  animation-delay: 0s;
  box-shadow:
    60vw 10vh 0 0 rgba(232, 212, 139, 0.3),
    25vw 70vh 0 0 rgba(232, 212, 139, 0.2),
    80vw 40vh 0 0 rgba(232, 212, 139, 0.15),
    10vw 85vh 0 0 rgba(232, 212, 139, 0.25),
    45vw 15vh 0 0 rgba(232, 212, 139, 0.1),
    70vw 60vh 0 0 rgba(232, 212, 139, 0.2);
}

.bg-particles::after {
  left: 50%; top: 60%;
  animation-delay: 6s;
  box-shadow:
    30vw 20vh 0 0 rgba(232, 212, 139, 0.2),
    75vw 75vh 0 0 rgba(232, 212, 139, 0.15),
    15vw 50vh 0 0 rgba(232, 212, 139, 0.25),
    55vw 35vh 0 0 rgba(232, 212, 139, 0.1),
    90vw 90vh 0 0 rgba(232, 212, 139, 0.2);
}

@keyframes floatParticle {
  0%, 100% { opacity: 0; transform: translateY(0); }
  20% { opacity: 0.6; }
  50% { opacity: 0.3; transform: translateY(-30px); }
  80% { opacity: 0.5; }
}

/* --- Header: Compact Glassmorphism --- */
.app-header {
  padding: 12px 24px;
  text-align: center;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(10, 6, 18, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 100;
  position: relative;
}

.header-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-ornament {
  color: var(--gold-dim);
  font-size: 14px;
  opacity: 0.5;
}

.app-header h1 {
  margin: 0;
  color: var(--gold-primary);
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: 6px;
  font-size: 22px;
  text-shadow: 0 0 20px rgba(201, 162, 39, 0.3);
}

.subtitle {
  font-size: 10px;
  color: var(--text-secondary);
  letter-spacing: 5px;
  text-transform: uppercase;
  opacity: 0.7;
}

/* --- Main Content --- */
.app-main {
  flex: 1;
  overflow-y: auto;
  position: relative;
  z-index: 5;
  padding: 0; /* Let children control their own padding */
}

/* --- Tashi Floating Orb Container (bottom-right, non-blocking) --- */
.tashi-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 500;
  pointer-events: none;
}

/* --- Common Ritual Button (Glassmorphism Upgrade) --- */
.ritual-btn {
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: var(--gold-primary);
  border: 1px solid var(--border-subtle);
  padding: 12px 30px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.4s var(--transition-smooth);
  border-radius: var(--radius-sm);
  letter-spacing: 2px;
  font-family: var(--font-body);
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-deep);
}

.ritual-btn::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(201, 162, 39, 0.1), transparent);
  transition: left 0.6s ease;
}

.ritual-btn:hover {
  background: rgba(201, 162, 39, 0.08);
  border-color: var(--border-glow);
  box-shadow: 0 0 25px rgba(201, 162, 39, 0.15), var(--shadow-deep);
  transform: translateY(-2px);
}

.ritual-btn:hover::before {
  left: 120%;
}

.ritual-btn.primary {
  border-width: 1.5px;
  border-color: var(--border-glow);
  font-weight: 500;
  color: var(--text-bright);
}

/* --- Scrollbar: Minimal Dark --- */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(201, 162, 39, 0.2);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(201, 162, 39, 0.4);
}
</style>
