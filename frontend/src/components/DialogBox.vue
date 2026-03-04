<template>
  <div class="tashi-orb-wrapper">
    <!-- Auto-dismiss text bubble -->
    <transition name="bubble">
      <div v-if="showBubble" class="tashi-bubble" @click="showBubble = false">
        <p class="bubble-text">{{ displayedText }}</p>
      </div>
    </transition>
    
    <!-- Floating Orb -->
    <div class="tashi-orb" @click="toggleBubble" :class="{ 'has-message': hasNewMessage }">
      <span class="orb-glyph">༄</span>
      <div class="orb-ring"></div>
      <div class="orb-pulse" v-if="hasNewMessage"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useGameStore } from '../stores/game'

const gameStore = useGameStore()
const displayedText = ref('')
const showBubble = ref(false)
const hasNewMessage = ref(false)
const isTyping = ref(false)
let typingTimer = null
let dismissTimer = null

const DISMISS_DELAY = 6000 // 文本显示6秒后自动消失

const typeText = (text, index = 0) => {
  if (index === 0) {
    isTyping.value = true
    displayedText.value = ''
    if (typingTimer) clearTimeout(typingTimer)
  }
  
  if (index < text.length) {
    displayedText.value += text.charAt(index)
    typingTimer = setTimeout(() => typeText(text, index + 1), 25)
  } else {
    isTyping.value = false
    // 打字完成后开始倒计时自动收起
    startDismissTimer()
  }
}

const startDismissTimer = () => {
  if (dismissTimer) clearTimeout(dismissTimer)
  dismissTimer = setTimeout(() => {
    showBubble.value = false
  }, DISMISS_DELAY)
}

const toggleBubble = () => {
  if (showBubble.value) {
    showBubble.value = false
  } else {
    showBubble.value = true
    hasNewMessage.value = false
    startDismissTimer()
  }
}

// 新消息来时：弹出气泡，打字动画，然后自动收起
watch(() => gameStore.tashiMessage, (newMessage) => {
  if (newMessage) {
    showBubble.value = true
    hasNewMessage.value = true
    typeText(newMessage)
  }
})

onMounted(() => {
  if (gameStore.tashiMessage) {
    showBubble.value = true
    typeText(gameStore.tashiMessage)
  }
})

onUnmounted(() => {
  if (typingTimer) clearTimeout(typingTimer)
  if (dismissTimer) clearTimeout(dismissTimer)
})
</script>

<style scoped>
.tashi-orb-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  pointer-events: auto;
}

/* --- Text Bubble --- */
.tashi-bubble {
  max-width: 340px;
  padding: 12px 16px;
  background: rgba(10, 6, 18, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(201, 162, 39, 0.25);
  border-radius: 14px 14px 4px 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 1px rgba(201, 162, 39, 0.3);
  cursor: pointer;
  animation: bubbleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bubble-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: rgba(232, 219, 176, 0.9);
  letter-spacing: 0.3px;
}

/* --- Floating Orb --- */
.tashi-orb {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #2a4a7f, #0d1630);
  border: 2px solid rgba(201, 162, 39, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 
    0 4px 16px rgba(42, 74, 127, 0.4),
    0 0 0 1px rgba(201, 162, 39, 0.1);
}

.tashi-orb:hover {
  transform: scale(1.1);
  border-color: rgba(201, 162, 39, 0.8);
  box-shadow: 
    0 6px 24px rgba(42, 74, 127, 0.6),
    0 0 20px rgba(201, 162, 39, 0.15);
}

.tashi-orb:active {
  transform: scale(0.95);
}

.orb-glyph {
  font-size: 20px;
  color: #e8d48b;
  line-height: 1;
  z-index: 2;
  filter: drop-shadow(0 0 4px rgba(232, 212, 139, 0.5));
}

/* Spinning ring */
.orb-ring {
  position: absolute;
  top: -4px; left: -4px; right: -4px; bottom: -4px;
  border: 1px dashed rgba(201, 162, 39, 0.3);
  border-radius: 50%;
  animation: orbSpin 15s linear infinite;
}

@keyframes orbSpin {
  100% { transform: rotate(360deg); }
}

/* New message pulse indicator */
.orb-pulse {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  background: #c9a227;
  border-radius: 50%;
  z-index: 3;
  animation: pulseDot 1.5s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

/* --- Bubble Transition --- */
.bubble-enter-active {
  animation: bubbleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bubble-leave-active {
  animation: bubbleOut 0.25s ease-in forwards;
}

@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes bubbleOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(6px) scale(0.95);
  }
}
</style>
