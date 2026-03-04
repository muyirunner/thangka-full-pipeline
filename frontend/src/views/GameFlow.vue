<template>
  <div class="game-flow-container">
    
    <!-- Stage: GALLERY (Immersive Exhibit Hall) -->
    <transition name="fade">
      <div v-if="gameStore.currentStage === GameStages.GALLERY" class="stage-gallery" key="gallery">
        
        <!-- Gallery Header -->
        <div class="gallery-hero">
          <h2 class="gallery-title">馆 藏 珍 宝</h2>
          <p class="gallery-subtitle">{{ restoredCount }} / {{ gameStore.galleryItems.length }} 已修复 · 选择一幅残卷，唤醒它的力量</p>
        </div>

        <!-- Fixed Scroll Arrows (outside carousel to avoid scrolling with it) -->
        <button class="scroll-arrow scroll-arrow-left" @click="scrollCarousel(-400)" aria-label="向左滚动">‹</button>
        <button class="scroll-arrow scroll-arrow-right" @click="scrollCarousel(400)" aria-label="向右滚动">›</button>

        <!-- Horizontal Scroll Carousel -->
        <div class="gallery-carousel" ref="galleryCarouselRef" @wheel.prevent="onCarouselWheel">
          <div class="carousel-track">
            <div 
              v-for="item in gameStore.galleryItems" 
              :key="item.id" 
              class="exhibit-card"
              :class="{ 'is-restored': item.isRestored, 'is-active': hoveredItem?.id === item.id }"
              @mouseenter="hoverItem(item)"
              @click="selectThangka(item)"
            >
              <div class="exhibit-image-frame">
                <img :src="item.isRestored ? item.url : (item.damagedUrl || item.url)" class="exhibit-image" :class="{ 'no-filter': item.isRestored }" />
                <div class="exhibit-glow"></div>
                <div v-if="item.isRestored" class="exhibit-restored-tag">✨ 已焕新</div>
                <div v-else class="exhibit-dust-overlay"></div>
              </div>
              <div class="exhibit-info">
                <h3 class="exhibit-title">{{ item.title }}</h3>
                <p class="exhibit-desc">{{ item.desc }}</p>
              </div>
              <div class="exhibit-action">
                <span class="exhibit-cta">{{ item.isRestored ? '再次观想' : '唤醒此卷' }}</span>
                <span class="exhibit-arrow">→</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stage: WORKTABLE (High Freedom Sandbox) -->
      <div v-else class="stage-worktable-v3" key="worktable-v3">
        
        <!-- Top Navigation -->
        <div class="worktable-header">
           <button class="back-btn" @click="gameStore.resetGame()">
             <span class="icon">⟵</span> 返回珍宝阁
           </button>
           <h2 class="section-title">
             时空神坛 · {{ gameStore.currentSelectedThangka?.title }}
             <span v-if="gameStore.currentSelectedThangka?.isRestored" class="restored-tag">✨ 已焕新</span>
             <button v-if="displayUrl && gameStore.currentStage !== GameStages.FINISHED" class="fullscreen-btn" @click="isFullscreen = true" title="全屏鉴赏">
               <span class="icon">⛶</span>
             </button>
           </h2>
        </div>

        <!-- Main Content Area (With Ambient Dust) -->
        <div class="main-workspace">
          <!-- Ethereal Global Dust Particles -->
          <div class="global-dust-container">
            <div class="dust-particle" v-for="n in 30" :key="'dust-'+n" :style="dustStyle(n)"></div>
          </div>

          <div class="visual-area">
            <Teleport to="body" :disabled="!isFullscreen">
               <div class="image-wrapper" :class="{ 'is-fullscreen': isFullscreen }">
               
               <!-- Premium Processing Overlay (no transition wrapper to avoid Vue crash) -->
                 <div v-if="isLoading" class="processing-overlay">
                   <!-- 扫描动画 (YOLO Detection) -->
                   <div v-if="gameStore.currentStage === GameStages.SCANNING" class="process-effect scan-effect">
                     <div class="scan-rune-ring"></div>
                     <div class="scan-rune-ring delay2"></div>
                     <div class="process-label">🔍 {{ loadingText }}</div>
                     <div class="process-progress"><div class="progress-fill scan-fill"></div></div>
                   </div>
                   <!-- 降噪动画 (Water Ripple Purification) -->
                   <div v-else-if="gameStore.currentStage === GameStages.PURIFYING" class="process-effect purify-effect">
                     <div class="water-ripple r1"></div>
                     <div class="water-ripple r2"></div>
                     <div class="water-ripple r3"></div>
                     <div class="purify-sweep"></div>
                     <div class="process-label">💧 {{ loadingText }}</div>
                     <div class="process-progress"><div class="progress-fill purify-fill"></div></div>
                   </div>
                   <!-- 超分动画 (Golden Dust Restoration) -->
                   <div v-else-if="gameStore.currentStage === GameStages.RESTORING" class="process-effect restore-effect">
                     <div class="golden-burst"></div>
                     <div class="golden-particles">
                       <span v-for="i in 24" :key="i" class="g-particle" :style="particleStyle(i)"></span>
                     </div>
                     <div class="process-label">⏳ {{ loadingText }}</div>
                     <div class="process-progress"><div class="progress-fill restore-fill"></div></div>
                   </div>
                 </div>
              
                 <!-- Fullscreen Close Button -->
              <button v-if="isFullscreen" class="close-fullscreen-btn" @click="isFullscreen = false" title="退出全屏">×</button>

              <!-- Main Image (After / Processed or Current State) -->
              <img
                  :src="displayUrl"
                  class="thangka-image"
                  ref="thangkaImgRef"
                  @load="calculateImageScale"
                  alt="Thangka"
              />

              <div v-if="gameStore.currentStage === GameStages.SCANNING" class="scan-line"></div>

              <!-- Bounding Boxes Layer -->
              <div v-if="gameStore.currentStage === GameStages.SCANNED" class="bounding-boxes" @click.self="hoveredBBox = null" ref="bboxContainerRef">
                 <div class="dimmer-overlay" :class="{'active': hoveredBBox !== null}" :style="dimmerClipStyle"></div>
                 
                 <div v-for="(det, index) in filteredScanResults" :key="index"
                      class="bbox"
                      :class="{ 'bbox-hovered': hoveredBBox === index }"
                      @mouseenter="hoveredBBox = index"
                      @mouseleave="hoveredBBox = null"
                      @click="onBBoxClick(index, det)"
                      :style="getBBoxStyle(det.bbox)">
                      <div class="bbox-label-container">
                         <span class="bbox-label">{{ det.class_zh }}</span>
                         <span class="bbox-conf">{{ (det.confidence * 100).toFixed(0) }}%</span>
                      </div>
                 </div>
              </div>

            <!-- Advanced Comparison System (Active after Purify/Restore) -->
            <div v-if="showSlider" class="advanced-comparison-container"
                 @mousemove="onComparisonMouseMove"
                 @mouseleave="onComparisonMouseLeave"
                 @mousedown="onComparisonMouseDown"
                 @mouseup="onComparisonMouseUp"
                 @touchstart.prevent="onComparisonTouchStart"
                 @touchmove.prevent="onComparisonTouchMove"
                 @touchend.prevent="onComparisonTouchEnd">
                 
                 <!-- The After (Restored) Image is always the base layer now (from line 85) -->
                 
                 <!-- Mode 1: Blink Compare (Hold to view Original) -->
                 <div v-show="comparisonMode === 'blink'" class="blink-overlay" :class="{ 'is-active': isHoldingCompare }">
                     <img :src="localBlobUrl || gameStore.uploadedImage" class="comparison-image-original" :style="sliderImgStyle" alt="Original" />
                     <div class="blink-hint" v-show="!isHoldingCompare">长按查看原图</div>
                 </div>

                 <!-- Mode 2: Magic Lens (Hover Magnifier) -->
                 <div v-show="comparisonMode === 'lens'" class="lens-overlay">
                     <!-- Base layer in lens mode is the Original image -->
                     <img :src="localBlobUrl || gameStore.uploadedImage" class="comparison-image-original" :style="sliderImgStyle" alt="Original" />
                     
                     <!-- The Lens: revealing the Restored Image inside a clipped circle -->
                     <div v-show="isLensActive" class="magic-lens" :style="lensStyle">
                         <img :src="displayUrl" class="lens-inner-image" :style="lensInnerImgStyle" alt="Restored Inside Lens" />
                         <div class="lens-ring"></div>
                     </div>
                 </div>
            </div>
                 <!-- Magic effect overlay during processing -->
                 <div v-if="[GameStages.PURIFYING, GameStages.RESTORING].includes(gameStore.currentStage)" class="magic-overlay"></div>
               </div>
            </Teleport>
          </div>
          
          <!-- Results Sidebar -->
          <transition name="fade">
              <div v-if="gameStore.currentStage === GameStages.SCANNED" class="results-sidebar">
                  <h3 class="sidebar-title">检测图谱 ({{ filteredScanResults.length }})</h3>
                  <div class="sidebar-list">
                      <div v-for="(det, index) in filteredScanResults" :key="index"
                           class="sidebar-item"
                           :class="{ 'active': hoveredBBox === index }"
                           @mouseenter="hoveredBBox = index"
                           @mouseleave="hoveredBBox = null"
                           @click="onBBoxClick(index, det)">
                           <span class="item-name">{{ det.class_zh }}</span>
                           <span class="item-conf">{{ (det.confidence * 100).toFixed(0) }}%</span>
                      </div>
                  </div>
              </div>
          </transition>
        </div>

        <!-- High Freedom Controls Area -->
        <div class="controls-area">
          <div class="controls-wrapper">
            <div class="tool-dock">
              <button class="ritual-tool" @click="onStartPurify" :disabled="isLoading">
                <div class="tool-icon">💧</div>
                <div class="tool-name">净水拂尘</div>
                <div class="tool-sub">智能降噪</div>
              </button>

              <button class="ritual-tool action-ultimate" @click="onStartRestore" :disabled="isLoading">
                <div class="tool-icon">⏳</div>
                <div class="tool-name">时光重塑</div>
                <div class="tool-sub">超分复原并保存</div>
              </button>

              <button class="ritual-tool" @click="onStartScan" :disabled="isLoading">
                <div class="tool-icon">👁</div>
                <div class="tool-name">慧眼洞察</div>
                <div class="tool-sub">特征扫描</div>
              </button>
            </div>
            
            <!-- Comparison Mode Toggle (Appears only when there's a result to compare) -->
            <transition name="fade">
              <div v-if="showSlider" class="comparison-toggles">
                 <button class="ritual-tool mini" :class="{ active: comparisonMode === 'blink' }" @click="comparisonMode = 'blink'">
                    <div class="tool-icon">👁️</div>
                    <div class="tool-name">瞬目对比</div>
                 </button>
                 <button class="ritual-tool mini" :class="{ active: comparisonMode === 'lens' }" @click="comparisonMode = 'lens'">
                    <div class="tool-icon">🔍</div>
                    <div class="tool-name">时空透镜</div>
                 </button>
              </div>
            </transition>
            
            <!-- Confidence Threshold Slider (Zero-latency front-end filter) -->
            <transition name="fade">
                <div v-if="gameStore.currentStage === GameStages.SCANNED" class="confidence-control">
                   <div class="conf-header">
                       <span class="conf-label">慧眼敏锐度 (置信度滤网)</span>
                       <span class="conf-value">{{ Math.round(confidenceThreshold * 100) }}%</span>
                   </div>
                   <input type="range" class="conf-slider" v-model.number="confidenceThreshold" min="0.05" max="0.95" step="0.01" />
                </div>
            </transition>
          </div>
        </div>

        <!-- BBox Detail Modal (Click to Zoom) -->
        <Teleport to="body">
          <transition name="fade">
             <div v-if="selectedBBoxInfo" class="bbox-modal-overlay" @click.self="selectedBBoxInfo = null">
                 <div class="bbox-modal-content">
                     <button class="close-modal-btn" @click="selectedBBoxInfo = null">×</button>
                     <div class="modal-layout">
                         <div class="zoom-view">
                             <div class="zoom-lens">
                                <img :src="displayUrl" class="zoomed-img" :style="zoomedImgStyle" />
                             </div>
                         </div>
                         <div class="lore-view">
                             <h3>特征提取：{{ selectedBBoxInfo.class_zh }}</h3>
                             <div class="conf-badge">置信度: {{ (selectedBBoxInfo.confidence * 100).toFixed(1) }}%</div>
                             <p class="lore-text">
                                 这是神坛慧眼在繁杂的历史长河中锚定的『{{ selectedBBoxInfo.class_zh }}』。
                                 <br/><br/>
                                 在藏传佛教与唐卡艺术中，每一个标志物都蕴含着深邃的宗教象征意义。此元素被精准定位，代表着这幅史诗画卷的核心精神枢纽之一。
                             </p>
                             <button class="ritual-btn primary mt-20" @click="selectedBBoxInfo = null">收起观测</button>
                         </div>
                     </div>
                 </div>
             </div>
          </transition>
        </Teleport>

        <!-- Restored Image Auto-Zoom Modal -->
        <Teleport to="body">
          <transition name="fade">
             <div v-if="showRestoredModal" class="bbox-modal-overlay" @click.self="showRestoredModal = false">
                 <div class="bbox-modal-content restored-modal">
                     <button class="close-modal-btn" @click="showRestoredModal = false">×</button>
                     <div class="modal-title-bar">时光重塑完成 · 细节鉴赏</div>
                     <div class="restored-zoom-container">
                         <img :src="displayUrl" class="zoomed-restored-img" />
                     </div>
                     <div class="modal-footer-bar">
                         <button class="ritual-btn primary" @click="showRestoredModal = false">惊叹膜拜</button>
                     </div>
                 </div>
             </div>
          </transition>
        </Teleport>


        
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useGameStore, GameStages } from '../stores/game'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const gameStore = useGameStore()
const selectedFile = ref(null)

// --- Gallery Logic ---
const hoveredItem = ref(null)
const defaultItem = computed(() => {
    return gameStore.galleryItems.length > 0 ? gameStore.galleryItems[0] : null
})
const displayItem = computed(() => hoveredItem.value || defaultItem.value)
const restoredCount = computed(() => gameStore.galleryItems.filter(i => i.isRestored).length)

const hoverItem = (item) => {
    hoveredItem.value = item
}

// --- Gallery Carousel Scroll ---
const galleryCarouselRef = ref(null)

const scrollCarousel = (delta) => {
    if (galleryCarouselRef.value) {
        galleryCarouselRef.value.scrollBy({ left: delta, behavior: 'smooth' })
    }
}

const onCarouselWheel = (e) => {
    // Convert vertical scroll to horizontal scroll for the carousel
    if (galleryCarouselRef.value) {
        galleryCarouselRef.value.scrollLeft += e.deltaY * 2
    }
}

// --- Loading Logic ---
const isLoading = computed(() => {
    return [GameStages.SCANNING, GameStages.PURIFYING, GameStages.RESTORING].includes(gameStore.currentStage)
})
const loadingText = computed(() => {
    if (gameStore.currentStage === GameStages.SCANNING) return '正在结印：慧眼洞察...'
    if (gameStore.currentStage === GameStages.PURIFYING) return '正在施咒：净水拂尘...'
    if (gameStore.currentStage === GameStages.RESTORING) return '正在逆转：时光重塑...'
    return ''
})

// For displaying the selected gallery image immediately before blob fetching finishes
const localBlobUrl = ref(null)
// Display processed image if taking action, otherwise show the loaded original
const displayUrl = computed(() => {
    // If we have a processed image from the backend, show it as the main image.
    // Otherwise, show the local blob URL. If blob is pending, show the uploadedImage url.
   return gameStore.processedImage || localBlobUrl.value || gameStore.uploadedImage
})

const showRestoredModal = ref(false)
const isFullscreen = ref(false)

// Recalculate bbox rendering when entering/exiting fullscreen to keep boxes aligned
watch(isFullscreen, (isFull) => {
    if (isFull) {
        document.body.classList.add('fullscreen-mode-active');
    } else {
        document.body.classList.remove('fullscreen-mode-active');
    }
    nextTick(() => {
        if (typeof calculateImageScale === 'function') {
            calculateImageScale();
            // Fire twice just in case browser layout needs an extra frame
            setTimeout(() => calculateImageScale(), 50);
        }
    })
})

// Fix: when ResetGame is called from Header, we must also reset localBlobUrl!
watch(() => gameStore.currentStage, (newStage) => {
    if (newStage === GameStages.GALLERY) {
        if (localBlobUrl.value) {
            URL.revokeObjectURL(localBlobUrl.value);
            localBlobUrl.value = null;
        }
        selectedFile.value = null;
        showRestoredModal.value = false;
        
        // Ensure we always have the freshest state (e.g. if Admin batches toggle) when returning to Gallery
        gameStore.fetchGallery();
    } else if (newStage === GameStages.FINISHED) {
        showRestoredModal.value = true;
    }
})

// --- Bounding Box & Slider State ---
const hoveredBBox = ref(null)
const confidenceThreshold = ref(0.1)

const filteredScanResults = computed(() => {
    return gameStore.scanResults.filter(r => r.confidence >= confidenceThreshold.value)
})

const bboxContainerRef = ref(null)
const dimmerClipStyle = computed(() => {
    if (hoveredBBox.value === null) {
        return { clipPath: 'none' };
    }
    // We get the original relative coordinates from the detection
    const det = filteredScanResults.value[hoveredBBox.value];
    if (!det || !thangkaImgRef.value) return { clipPath: 'none' };

    const [origX1, origY1, origX2, origY2] = det.bbox
    
    // Scale down to match displayed image coordinates
    const { scale, offsetX, offsetY } = imageRenderInfo.value;
    const x1 = origX1 * scale + offsetX
    const y1 = origY1 * scale + offsetY
    const width = (origX2 - origX1) * scale
    const height = (origY2 - origY1) * scale
    
    // Add a tiny bit of padding (e.g. 4px) to the hole so border glow fits
    const p = 6;
    const tX = x1 - p;
    const tY = y1 - p;
    const tR = x1 + width + p;
    const tB = y1 + height + p;

    // Create a polygon that covers everything EXCEPT the box hole
    return {
         clipPath: `polygon(0% 0%, 0% 100%, ${tX}px 100%, ${tX}px ${tY}px, ${tR}px ${tY}px, ${tR}px ${tB}px, ${tX}px ${tB}px, ${tX}px 100%, 100% 100%, 100% 0%)`
    };
})

const onBBoxClick = (index, det) => {
    // Ensure the modal ALWAYS opens on click to prevent any state mismatch
    hoveredBBox.value = index;
    openBBoxModal(det);
}

const showSlider = computed(() => {
    // Show comparison when:
    // 1. Denoise is complete (PURIFIED) — compare original vs denoised
    // 2. Restore is complete (FINISHED) — compare original vs fully restored
    // Do NOT show during loading states or gallery/scan states
    return [GameStages.PURIFIED, GameStages.FINISHED].includes(gameStore.currentStage)
        && !!gameStore.processedImage;
})

// Shared style for comparison overlay images (replaces the old sliderImgStyle)
const sliderImgStyle = computed(() => {
    return {
        width: '100%',
        height: '100%',
        objectFit: 'contain'
    }
})

const comparisonMode = ref('blink') // 'blink' or 'lens'

// --- Mode 1: Blink Compare State ---
const isHoldingCompare = ref(false)

// --- Mode 2: Magic Lens State ---
const isLensActive = ref(false)
const lensPos = ref({ x: 0, y: 0 })
const LENS_RADIUS = 120

// The styling for the Magic Lens container
const lensStyle = computed(() => {
    return {
        left: `${lensPos.value.x - LENS_RADIUS}px`,
        top: `${lensPos.value.y - LENS_RADIUS}px`,
        width: `${LENS_RADIUS * 2}px`,
        height: `${LENS_RADIUS * 2}px`,
    }
})

// The most critical part: the inside of the lens must show the Restored Image
// exactly aligned with the Base Image.
// We use the actual container dimensions (not viewport), and shift the image
// in the opposite direction of the lens position for pixel-perfect alignment.
const lensInnerImgStyle = computed(() => {
    // Get the actual rendered container dimensions from the image wrapper
    const wrapper = thangkaImgRef.value?.parentElement;
    const w = wrapper?.clientWidth || 600;
    const h = wrapper?.clientHeight || 400;
    return {
        width: `${w}px`,
        height: `${h}px`,
        objectFit: 'contain',
        transform: `translate(${-lensPos.value.x + LENS_RADIUS}px, ${-lensPos.value.y + LENS_RADIUS}px)`,
    }
})


// --- Unified Mouse/Touch Handlers ---
const updateLensPosition = (clientX, clientY, container) => {
    if (comparisonMode.value !== 'lens') return;
    const rect = container.getBoundingClientRect();
    lensPos.value = {
        x: clientX - rect.left,
        y: clientY - rect.top
    }
}

const onComparisonMouseMove = (e) => {
    if (comparisonMode.value === 'lens') {
        isLensActive.value = true;
        updateLensPosition(e.clientX, e.clientY, e.currentTarget);
    }
}

const onComparisonMouseLeave = (e) => {
    isHoldingCompare.value = false;
    isLensActive.value = false;
}

const onComparisonMouseDown = (e) => {
    if (comparisonMode.value === 'blink') {
        isHoldingCompare.value = true;
    }
}

const onComparisonMouseUp = (e) => {
    if (comparisonMode.value === 'blink') {
        isHoldingCompare.value = false;
    }
}

// Touch equivalents for Mobile
const onComparisonTouchStart = (e) => {
    if (comparisonMode.value === 'blink') {
        isHoldingCompare.value = true;
    } else if (comparisonMode.value === 'lens') {
        isLensActive.value = true;
        updateLensPosition(e.touches[0].clientX, e.touches[0].clientY, e.currentTarget);
    }
}

const onComparisonTouchMove = (e) => {
    if (comparisonMode.value === 'lens') {
        updateLensPosition(e.touches[0].clientX, e.touches[0].clientY, e.currentTarget);
    }
}

const onComparisonTouchEnd = (e) => {
    isHoldingCompare.value = false;
    isLensActive.value = false;
}

// --- BBox Zoom Modal ---
const selectedBBoxInfo = ref(null)

const openBBoxModal = (det) => {
    console.log("Opening bbox modal for det:", det);
    selectedBBoxInfo.value = det
}

const zoomedImgStyle = computed(() => {
    if (!selectedBBoxInfo.value || !imageRenderInfo.value.loaded || !thangkaImgRef.value) return {}
    
    // Calculate the center percentage of the bbox relative to the original image dimensions
    const [x1, y1, x2, y2] = selectedBBoxInfo.value.bbox
    const centerX = (x1 + x2) / 2
    const centerY = (y1 + y2) / 2
    
    const img = thangkaImgRef.value
    const naturalW = img.naturalWidth
    const naturalH = img.naturalHeight
    
    const percentX = (centerX / naturalW) * 100
    const percentY = (centerY / naturalH) * 100
    
    return {
        transformOrigin: `${percentX}% ${percentY}%`,
        transform: 'scale(4)' // Zoom in 4x!
    }
})

const thangkaImgRef = ref(null)
const imageRenderInfo = ref({ scale: 1, offsetX: 0, offsetY: 0, loaded: false })
let resizeObserver = null

const calculateImageScale = () => {
    if (!thangkaImgRef.value) return;
    const img = thangkaImgRef.value;
    const naturalW = img.naturalWidth;
    const naturalH = img.naturalHeight;
    const clientW = img.clientWidth;
    const clientH = img.clientHeight;

    if (naturalW === 0 || naturalH === 0 || clientW === 0 || clientH === 0) return;

    // The image-wrapper is a flex container with align-items/justify-content center.
    // However, the .bounding-boxes absolute container overlays the entire wrapper.
    // The img.clientWidth and img.clientHeight are the BOUNDING BOX of the img element 
    // INSIDE the wrapper. Because of object-fit: contain, the actual rendered pixels 
    // might be smaller than clientW/clientH if the aspect ratios don't match.

    const imageAspectRatio = naturalW / naturalH;
    const containerAspectRatio = clientW / clientH;

    let renderedW, renderedH;
    let offsetX = 0;
    let offsetY = 0;

    if (imageAspectRatio > containerAspectRatio) {
        // Image is wider than container, so it fills width and has gaps top/bottom
        renderedW = clientW;
        renderedH = clientW / imageAspectRatio;
        offsetY = (clientH - renderedH) / 2;
    } else {
        // Image is taller than container, so it fills height and has gaps left/right
        renderedH = clientH;
        renderedW = clientH * imageAspectRatio;
        offsetX = (clientW - renderedW) / 2;
    }

    // `img.offsetLeft` and `img.offsetTop` give the position of the img element within the `.image-wrapper`.
    // We add this to our calculated gap offsets to find the true top-left of the actual image pixels.
    const trueOffsetX = img.offsetLeft + offsetX;
    const trueOffsetY = img.offsetTop + offsetY;

    const scaleX = renderedW / naturalW;

    imageRenderInfo.value = { scale: scaleX, offsetX: trueOffsetX, offsetY: trueOffsetY, loaded: true };
}

const getBBoxStyle = (bbox) => {
    if (!imageRenderInfo.value.loaded) return { display: 'none' }
    const { scale, offsetX, offsetY } = imageRenderInfo.value;
    const [x1, y1, x2, y2] = bbox;
    
    return {
        left: `${(x1 * scale) + offsetX}px`,
        top: `${(y1 * scale) + offsetY}px`,
        width: `${(x2 - x1) * scale}px`,
        height: `${(y2 - y1) * scale}px`
    }
}

watch(() => gameStore.scanResults, () => {
    nextTick(() => calculateImageScale())
})

onMounted(() => {
    // 从后端加载画廊数据和运行模式
    gameStore.fetchGallery()
    
    window.addEventListener('resize', calculateImageScale)
    if (window.ResizeObserver && thangkaImgRef.value?.parentElement) {
        resizeObserver = new window.ResizeObserver(() => calculateImageScale())
        resizeObserver.observe(thangkaImgRef.value.parentElement)
    }
})

onUnmounted(() => {
    window.removeEventListener('resize', calculateImageScale)
    if (resizeObserver) resizeObserver.disconnect()
})

// --- Actions ---

// Convert gallery URL to File object for the backend expecting FormData uploads
const selectThangka = async (item) => {
    // 核心判定：如果该图鉴已经被点亮（全局或本地），则展示清晰原图。
    // 否则（未点亮状态），优先展示损坏版（预设受损图）。
    const displayUrl = item.isRestored ? item.url : (item.damagedUrl || item.url)
    gameStore.loadImage(displayUrl, item)
    try {
        // 对于 YOLO 扫描，始终传原图（清晰版）给后端，确保检测准确
        const response = await fetch(item.url)
        const blob = await response.blob()
        const filename = item.url.split('/').pop() || "thangka.jpg"
        const file = new File([blob], filename, { type: blob.type })
        
        selectedFile.value = file
        // 渲染视口层使用与 displayUrl 严格一致的图像版本
        if (displayUrl === item.damagedUrl) {
            const damagedResponse = await fetch(item.damagedUrl)
            const damagedBlob = await damagedResponse.blob()
            localBlobUrl.value = URL.createObjectURL(damagedBlob)
        } else {
            localBlobUrl.value = URL.createObjectURL(blob)
        }
    } catch (err) {
        console.error("Failed to load thangka image into file object:", err)
        ElMessage.error("未找到法卷实体数据，请检查网络！")
    }
}

// Backend API call wrappers
const onStartScan = async () => {
    if (!selectedFile.value) return
    gameStore.startScan()
    try {
        const formData = new FormData()
        formData.append('file', selectedFile.value) 
        // 动态适配 API 路径，如果前端部署了代理，请注意跨域配置
        const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'http://' + window.location.hostname + ':8000'
        const res = await axios.post(`${API_BASE}/api/v1/scan`, formData)
        
        if (res.data.success) {
            gameStore.completeScan(res.data.detections)
        } else {
             ElMessage.error("结印失败：扫描接口未能响应。")
             gameStore.currentStage = GameStages.IMAGE_LOADED
        }
    } catch (error) {
        const errMsg = error.response?.data?.detail || error.message;
        ElMessage.error(`服务端报错: ${errMsg}`);
        gameStore.currentStage = GameStages.IMAGE_LOADED
    }
}

const onStartPurify = async () => {
    
    // 获取当前唐卡的预设降噪图 URL
    const thangka = gameStore.currentSelectedThangka
    const presetUrl = thangka?.purifiedUrl
    
    // 优先使用预设模式：只要有预设图片就直接用
    if (presetUrl) {
        // ⚠️ 必须先注册计时器，再改状态。因为 startPurify() 触发的 Vue 过渡
        // 可能抛出错误、中断后续同步代码的执行。
        setTimeout(() => {
            try {
                gameStore.completePurify(presetUrl)
            } catch (e) {
                console.error('[Preset] completePurify error:', e)
                gameStore.currentStage = GameStages.IMAGE_LOADED
            }
        }, 3500)
        try { gameStore.startPurify() } catch(e) { /* Vue transition error, safe to ignore */ }
        return
    }
    
    // 回退：调用真实后端算法
    if (!selectedFile.value) {
        ElMessage.error('未找到法卷实体数据')
        gameStore.currentStage = GameStages.IMAGE_LOADED
        return
    }
    try { gameStore.startPurify() } catch(e) { /* Vue transition error */ }
    try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'http://' + window.location.hostname + ':8000'
        const res = await axios.post(`${API_BASE}/api/v1/purify`, formData)
        
        if (res.data.success) {
            gameStore.completePurify(res.data.result_image)
        } else {
            ElMessage.error('仪式中断：降噪失败。')
            gameStore.currentStage = GameStages.IMAGE_LOADED
        }
    } catch (error) {
        const errMsg = error.response?.data?.detail || error.message;
        ElMessage.error(`服务端报错: ${errMsg}`);
        gameStore.currentStage = GameStages.IMAGE_LOADED
    }
}

const onStartRestore = async () => {
    
    // 获取当前唐卡的预设修复图 URL
    const thangka = gameStore.currentSelectedThangka
    const presetUrl = thangka?.restoredUrl || thangka?.url  // 修复图 = 原始清晰图
    
    // 优先使用预设模式
    if (presetUrl) {
        // ⚠️ 先注册计时器，再改状态（同 onStartPurify 的策略）
        setTimeout(() => {
            try {
                gameStore.completeRestore(presetUrl)
                ElMessage.success('时光重塑完成！图鉴已被点亮并永久保存。')
            } catch (e) {
                console.error('[Preset] completeRestore error:', e)
                gameStore.currentStage = GameStages.IMAGE_LOADED
            }
        }, 4500)
        try { gameStore.startRestore() } catch(e) { /* Vue transition error, safe to ignore */ }
        return
    }
    
    // 回退：调用真实后端算法
    if (!selectedFile.value) {
        ElMessage.error('未找到法卷实体数据')
        gameStore.currentStage = GameStages.IMAGE_LOADED
        return
    }
    
    try { gameStore.startRestore() } catch(e) { /* Vue transition error */ }
    
    try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'http://' + window.location.hostname + ':8000'
        const res = await axios.post(`${API_BASE}/api/v1/restore`, formData)
        
        if (res.data.success) {
            gameStore.completeRestore(res.data.result_image)
            ElMessage.success('时光重塑完成！图鉴已被点亮并永久保存。')
        } else {
            ElMessage.error('仪式中断：超分辨率失败。')
            gameStore.currentStage = GameStages.IMAGE_LOADED
        }
    } catch (error) {
        const errMsg = error.response?.data?.detail || error.message;
        ElMessage.error(`服务端报错: ${errMsg}`);
        gameStore.currentStage = GameStages.IMAGE_LOADED
    }
}

// 金色粒子样式生成器（用于时光重塑动画）
const particleStyle = (i) => {
    const angle = (i / 24) * 360 + Math.random() * 15
    const dist = 60 + Math.random() * 120
    const delay = Math.random() * 2
    const size = 2 + Math.random() * 4
    return {
        '--angle': `${angle}deg`,
        '--dist': `${dist}px`,
        '--delay': `${delay}s`,
        '--size': `${size}px`,
    }
}

// 全局微尘样式生成器 (Ambient Gold Dust)
const dustStyle = (i) => {
    // 随机散布在全屏，不同的模糊度、大小和极长的动画周期，制造无缝悬浮感
    return {
        '--startX': `${Math.random() * 100}vw`,
        '--startY': `${Math.random() * 100}vh`,
        '--endX': `${Math.random() * 100}vw`,
        '--endY': `${Math.random() * 100 - 20}vh`, 
        '--size': `${Math.random() * 3 + 1}px`,
        '--duration': `${20 + Math.random() * 30}s`,
        '--delay': `-${Math.random() * 20}s`,
        '--opacity': Math.random() * 0.4 + 0.1,
        '--blur': `${Math.random() * 2}px`
    }
}

// 预设模式的模拟加载函数：返回 Promise，在指定毫秒后 resolve
const simulateProcessing = (durationMs) => {
    return new Promise(resolve => setTimeout(resolve, durationMs))
}
</script>

<style scoped>
/* Page Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.game-flow-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* --- Immersive Gallery (Exhibit Hall) --- */
.stage-gallery {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  padding: 30px 0;
  overflow: hidden;
  position: relative; /* For scroll arrow positioning */
}

.gallery-hero {
  text-align: center;
  padding: 20px 40px 30px;
}

.gallery-title {
  margin: 0;
  color: var(--gold-primary);
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 42px;
  letter-spacing: 16px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8), 0 0 30px var(--gold-glow);
}

.gallery-subtitle {
  margin: 12px 0 0;
  color: var(--gold-glow-intense);
  font-size: 14px;
  letter-spacing: 4px;
}

.gallery-carousel {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0 60px 30px;
  position: relative;
  /* Hide scrollbar for aesthetics */
  scrollbar-width: none;
  -ms-overflow-style: none;
  cursor: grab;
}

.gallery-carousel:active {
  cursor: grabbing;
}

/* Scroll Arrow Buttons — fixed at gallery edges */
.scroll-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 20;
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-subtle);
  border-radius: 50%;
  background: rgba(10, 6, 18, 0.85);
  backdrop-filter: blur(12px);
  color: var(--gold-primary);
  font-size: 22px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s var(--transition-smooth);
  opacity: 0.7;
  font-family: var(--font-body);
}

.scroll-arrow:hover {
  opacity: 1;
  border-color: var(--border-glow);
  box-shadow: 0 0 20px rgba(201, 162, 39, 0.2);
  transform: translateY(-50%) scale(1.1);
}

.scroll-arrow-left {
  left: 12px;
}

.scroll-arrow-right {
  right: 12px;
}

.gallery-carousel::-webkit-scrollbar {
  display: none;
}

.carousel-track {
  display: flex;
  gap: 30px;
  height: 100%;
  padding: 10px 0;
}

/* --- Exhibit Card (Each gallery item) --- */
.exhibit-card {
  flex: 0 0 280px;
  scroll-snap-align: center;
  display: flex;
  flex-direction: column;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s var(--transition-smooth);
  position: relative;
}

.exhibit-card:hover,
.exhibit-card.is-active {
  transform: translateY(-8px) scale(1.02);
  border-color: var(--border-glow);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(201, 162, 39, 0.1);
}

.exhibit-card.is-restored {
  border-color: rgba(201, 162, 39, 0.3);
}

.exhibit-card.is-restored .exhibit-glow {
  opacity: 1;
}

/* Image Frame */
.exhibit-image-frame {
  position: relative;
  height: 320px;
  overflow: hidden;
  background: #030101;
}

.exhibit-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: sepia(0.5) brightness(0.6) saturate(0.8);
  transition: filter 0.6s ease, transform 0.6s ease;
}

.exhibit-image.no-filter {
  filter: none;
}

.exhibit-card:hover .exhibit-image {
  transform: scale(1.05);
  filter: sepia(0.3) brightness(0.8) saturate(1);
}

.exhibit-card.is-restored:hover .exhibit-image {
  filter: brightness(1.05) saturate(1.1);
}

/* Glow effect for restored items */
.exhibit-glow {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 80px;
  background: linear-gradient(transparent, rgba(201, 162, 39, 0.1));
  opacity: 0;
  transition: opacity 0.4s;
}

.exhibit-dust-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(0,0,0,0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(0,0,0,0.2) 0%, transparent 50%);
  pointer-events: none;
}

.exhibit-restored-tag {
  position: absolute;
  top: 12px; right: 12px;
  background: rgba(201, 162, 39, 0.9);
  color: var(--bg-deep);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  letter-spacing: 1px;
}

/* Info Section */
.exhibit-info {
  padding: 16px 20px 8px;
  flex: 1;
}

.exhibit-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.exhibit-desc {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Action Row */
.exhibit-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px 16px;
  border-top: 1px solid var(--border-subtle);
  margin-top: auto;
}

.exhibit-cta {
  font-size: 13px;
  color: var(--gold-primary);
  letter-spacing: 2px;
  font-weight: 500;
}

.exhibit-arrow {
  font-size: 18px;
  color: var(--gold-dim);
  transition: transform 0.3s, color 0.3s;
}

.exhibit-card:hover .exhibit-arrow {
  transform: translateX(5px);
  color: var(--gold-primary);
}

/* --- Worktable Styles (Full-Screen Sanctuary) --- */
.stage-worktable-v3 {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  padding: 15px 20px 0;
}

.worktable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto 10px;
  width: 100%;
  padding: 10px 20px;
  background: var(--bg-glass-solid);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 30px rgba(0,0,0,0.6);
  z-index: 100;
}

.back-btn {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  padding: 8px 18px;
  transition: all 0.3s var(--transition-smooth);
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
}

.back-btn:hover {
  background: rgba(222, 184, 135, 0.08);
  border-color: var(--border-glow);
  color: var(--gold-primary);
}

.section-title {
  color: var(--gold-primary);
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 22px;
  letter-spacing: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.restored-tag {
  font-size: 12px;
  background: rgba(222, 184, 135, 0.15);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid var(--border-glow);
  color: var(--gold-light);
}

.main-workspace {
  display: flex;
  justify-content: center;
  align-items: stretch;
  max-width: 1500px;
  margin: 0 auto;
  gap: 20px;
  width: 100%;
  flex: 1;
  min-height: 0; /* Allow flex children to shrink */
}

.visual-area {
  display: flex;
  justify-content: center;
  align-items: stretch;
  flex: 1;
  position: relative;
  min-height: 0;
}

/* Subtle vignette around the image */
.visual-area::before {
  content: '';
  position: absolute;
  top: -30px; left: -30px; right: -30px; bottom: -30px;
  background: radial-gradient(circle at center, transparent 40%, rgba(10, 6, 18, 0.5) 100%);
  pointer-events: none;
  z-index: -1;
}

.image-wrapper {
  position: relative;
  flex: 1;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  background-color: #030208;
  background-image: radial-gradient(circle at center, #0d1117 0%, #030208 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    inset 0 0 60px rgba(0,0,0,0.9),
    0 15px 40px rgba(0,0,0,0.5),
    0 0 1px var(--border-subtle);
}

.thangka-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  transition: filter 1s ease;
  z-index: 1;
}

.sepia-filter { filter: sepia(0.6) brightness(0.6) contrast(1.2); }
.restored-glow { 
    filter: drop-shadow(0 0 25px var(--gold-glow)) contrast(1.05); 
    animation: divineGlow 4s ease-in-out infinite alternate;
}

@keyframes divineGlow {
    0% { filter: drop-shadow(0 0 10px var(--gold-glow)) contrast(1.05); }
    100% { filter: drop-shadow(0 0 35px var(--gold-glow-intense)) contrast(1.1); }
}

/* Bounding Boxes */
.bounding-boxes {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: auto; /* Allow self click to clear hover */
  z-index: 5;
}

.dimmer-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.75);
  opacity: 0; pointer-events: none;
  transition: opacity 0.4s ease;
  z-index: 8; /* Cover unselected boxes */
}
.dimmer-overlay.active {
  opacity: 1;
}

.bbox {
  position: absolute; 
  border: 2px solid var(--gold-glow-intense); 
  background: rgba(212, 175, 55, 0.05);
  box-shadow: 0 0 10px var(--gold-glow), inset 0 0 5px rgba(222, 184, 135, 0.1); 
  animation: pulseBox 3s infinite;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 2; /* Normal z-index */
}

.bbox:hover, .bbox.bbox-hovered {
  border: 3px solid var(--gold-light);
  background: transparent;
  box-shadow: 0 0 30px rgba(255, 223, 0, 0.8), inset 0 0 20px rgba(255, 223, 0, 0.4);
  z-index: 10; /* Pop above the dimmer (8) */
  transform: scale(1.02);
}

.bbox::before, .bbox::after {
    content: ''; position: absolute; width: 12px; height: 12px; border: 3px solid #fff; transition: all 0.3s;
}
.bbox::before { top: -3px; left: -3px; border-right: none; border-bottom: none; border-top-left-radius: 4px; }
.bbox::after { bottom: -3px; right: -3px; border-left: none; border-top: none; border-bottom-right-radius: 4px; }

.bbox:hover::before, .bbox.bbox-hovered::before,
.bbox:hover::after, .bbox.bbox-hovered::after {
    border-color: var(--gold-light);
    width: 20px; height: 20px;
}

.bbox-label-container {
  position: absolute; top: -2px; left: -2px; 
  display: flex; align-items: stretch;
  background: rgba(10, 6, 18, 0.92);
  border: 1.5px solid var(--gold-primary);
  border-radius: 5px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.6);
  transition: all 0.3s;
  backdrop-filter: blur(8px);
  white-space: nowrap;
  z-index: 20;
}

.bbox:hover .bbox-label-container, .bbox.bbox-hovered .bbox-label-container {
  transform: translateY(-5px) scale(1.1);
  border-color: var(--gold-light);
  box-shadow: 0 8px 25px rgba(222, 184, 135, 0.5);
}

.bbox-label {
  background: linear-gradient(135deg, var(--gold-primary), #b8860b); 
  color: var(--bg-deep);
  padding: 4px 10px; 
  font-size: 13px; 
  font-weight: 800; 
  white-space: nowrap;
  letter-spacing: 1px;
}

.bbox-conf {
  color: var(--gold-primary); 
  font-size: 13px; 
  padding: 0 10px; 
  font-family: 'Courier New', Courier, monospace;
  display: flex;
  align-items: center;
  font-weight: bold;
}
@keyframes pulseBox { 0% { box-shadow: 0 0 5px var(--gold-glow); } 50% { box-shadow: 0 0 15px var(--gold-glow); } 100% { box-shadow: 0 0 5px var(--gold-glow); } }

/* --- Advanced Comparison UI --- */
.advanced-comparison-container {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 20;
  overflow: hidden;
  /* Disable text selection during drag/hold */
  user-select: none;
  -webkit-user-select: none;
}

/* Original Image Shared Style */
.comparison-image-original {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: sepia(0.6) brightness(0.6) contrast(1.2); /* Keep ancient look */
  pointer-events: none;
}

/* --- Mode 1: Blink Compare --- */
.blink-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  opacity: 0;
  transition: opacity 0.15s ease-out; /* Fast, snappy transition */
  z-index: 25;
}

.blink-overlay.is-active {
  opacity: 1; /* Instantly covers the restored image with the original */
}

.blink-hint {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(10, 5, 2, 0.85);
  border: 1px solid var(--gold-glow);
  color: #e8dbb0;
  padding: 8px 24px;
  border-radius: 30px;
  font-size: 14px;
  letter-spacing: 2px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.5);
  pointer-events: none;
  animation: floatHint 3s ease-in-out infinite;
  backdrop-filter: blur(4px);
}

@keyframes floatHint {
  0%, 100% { transform: translate(-50%, 0); }
  50% { transform: translate(-50%, -10px); }
}

/* --- Mode 2: Magic Lens --- */
.lens-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 26;
  /* Original image acts as the base in this mode, so we keep it opaque */
}

.magic-lens {
  position: absolute;
  border-radius: 50%;
  overflow: hidden;
  /* Glowing ring aesthetic */
  box-shadow: 
    0 0 20px 5px var(--gold-glow),
    inset 0 0 30px 10px rgba(0, 0, 0, 0.5),
    0 10px 30px rgba(0,0,0,0.8);
  pointer-events: none;
  z-index: 30;
  background: #030101; /* Fallback */
}

/* The actual ring border to look like an artifact */
.lens-ring {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  border: 2px solid var(--gold-primary);
  border-radius: 50%;
  box-sizing: border-box;
  pointer-events: none;
  z-index: 35;
}

.lens-inner-image {
  position: absolute;
  top: 0; left: 0;
  /* Width/Height/Transform are bound dynamically in JS to match the exact fullscreen grid */
  object-fit: contain;
  filter: drop-shadow(0 0 10px rgba(212,175,55,0.4)); /* Slight glow to restored content */
}

/* Magic Effects */
.scan-line {
  position: absolute; width: 100%; height: 4px; background: var(--gold-primary);
  box-shadow: 0 0 15px 5px rgba(222, 184, 135, 0.5); animation: scanMove 2s ease-in-out infinite; z-index: 10;
}
@keyframes scanMove { 0% { top: 0; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
.magic-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle, transparent 20%, rgba(212, 175, 55, 0.15) 80%);
  animation: pulseBg 2s linear infinite; pointer-events: none;
}
@keyframes pulseBg { 0% { opacity: 0.2; } 50% { opacity: 0.8; } 100% { opacity: 0.2; } }

/* --- Controls Area (Bottom Dock) --- */
.controls-area {
  display: flex;
  justify-content: center;
  padding: 15px 20px;
  z-index: 50;
}

.controls-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.confidence-control {
  width: 100%;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-subtle);
  padding: 10px 24px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-deep);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
  font-size: 13px;
  letter-spacing: 1px;
}
.conf-value {
  color: var(--gold-primary);
  font-family: 'Courier New', monospace;
  font-weight: bold;
}

.conf-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 3px;
  background: rgba(222, 184, 135, 0.15);
  border-radius: 2px;
  outline: none;
}
.conf-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--gold-primary);
  cursor: pointer;
  box-shadow: 0 0 10px var(--gold-primary);
}

/* --- Glassmorphism Tool Dock --- */
.tool-dock {
  display: flex;
  gap: 12px;
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 12px 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-deep);
}

.ritual-tool {
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-secondary);
  transition: all 0.5s var(--transition-spring);
  padding: 12px 24px;
  border-radius: var(--radius-sm);
  position: relative;
  overflow: hidden;
  font-family: var(--font-body);
}

.ritual-tool::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at center, rgba(222, 184, 135, 0.08) 0%, transparent 70%);
  opacity: 0; transition: opacity 0.5s var(--transition-spring);
}

.ritual-tool:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--border-glow);
  transform: translateY(-6px) scale(1.03);
  box-shadow: 0 12px 30px rgba(0,0,0,0.6), 0 0 20px var(--gold-glow);
}

.ritual-tool:hover:not(:disabled)::before {
  opacity: 1;
}

.ritual-tool:active:not(:disabled) {
  transform: translateY(1px);
}

.ritual-tool:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  filter: grayscale(0.8);
}

/* Tool Icon & Text */
.tool-icon {
  font-size: 28px;
  margin-bottom: 8px;
  filter: drop-shadow(0 0 5px rgba(201, 162, 39, 0.3));
  transition: filter 0.3s, transform 0.3s;
}

.ritual-tool:hover:not(:disabled) .tool-icon {
  filter: drop-shadow(0 0 12px rgba(201, 162, 39, 0.6));
  transform: scale(1.1);
}

.tool-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-primary);
  margin-bottom: 3px;
}

.tool-sub {
  font-size: 11px;
  color: var(--text-secondary);
}

/* Ultimate Action (Restore) */
.action-ultimate {
  border-color: rgba(180, 50, 50, 0.3);
  background: rgba(60, 15, 15, 0.3);
}
.action-ultimate .tool-name {
  color: #ff8a8a;
}
.action-ultimate:hover:not(:disabled) {
  border-color: rgba(255, 100, 100, 0.5);
  box-shadow: 0 8px 20px rgba(0,0,0,0.4), 0 0 20px rgba(255, 100, 100, 0.1);
}

/* --- Comparison Mode Toggles --- */
.comparison-toggles {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

.ritual-tool.mini {
  padding: 8px 18px;
  min-width: 110px;
  flex-direction: row;
  gap: 8px;
  border-radius: var(--radius-sm);
}

.ritual-tool.mini .tool-icon {
  font-size: 18px;
  margin-bottom: 0;
}

.ritual-tool.mini .tool-name {
  font-size: 13px;
  margin-bottom: 0;
}

.ritual-tool.mini.active {
  background: rgba(201, 162, 39, 0.12);
  border-color: var(--border-glow);
  box-shadow: inset 0 0 12px rgba(201, 162, 39, 0.3);
}

/* --- BBox Detail Modal --- */
.bbox-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(5, 3, 10, 0.92);
  backdrop-filter: blur(12px);
  z-index: 2000000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bbox-modal-content {
  background: var(--bg-card);
  border: 1.5px solid var(--border-glow);
  border-radius: var(--radius-md);
  max-width: 900px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.8), 0 0 40px rgba(222, 184, 135, 0.08);
  position: relative;
  overflow: hidden;
  animation: modalIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes modalIn {
  0% { transform: scale(0.8) translateY(50px); opacity: 0; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}

.close-modal-btn {
  position: absolute;
  top: 15px; right: 20px;
  background: transparent; border: none;
  color: #a48e65; font-size: 30px;
  cursor: pointer; z-index: 10;
  transition: all 0.3s;
}

.close-modal-btn:hover { color: #fff; transform: rotate(90deg); }

.modal-layout {
  display: flex;
  height: 500px;
}

.zoom-view {
  flex: 1;
  background: #030208;
  border-right: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.zoom-lens {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: 0 0 30px rgba(0,0,0,1);
  background: #030208;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.zoomed-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.8s cubic-bezier(0.25, 1, 0.5, 1);
}

.lore-view {
  flex: 0 0 350px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-deep) 0%, rgba(13, 17, 23, 0.9) 100%);
}

.lore-view h3 {
  color: var(--gold-primary);
  font-family: var(--font-display);
  font-size: 26px;
  letter-spacing: 2px;
  margin-top: 0; margin-bottom: 12px;
}

.conf-badge {
  display: inline-block;
  background: rgba(222, 184, 135, 0.15);
  color: var(--text-primary);
  padding: 5px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-glow);
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin-bottom: 25px;
}

.lore-text {
  color: var(--text-secondary);
  line-height: 1.8;
  font-size: 15px;
  flex: 1;
}

.mt-20 { margin-top: 20px; width: 100%; padding: 12px; }

/* --- Sidebar --- */
.results-sidebar {
  width: 250px;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 15px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-deep);
}

.sidebar-title {
  color: var(--gold-primary);
  font-family: var(--font-display);
  font-size: 15px;
  margin-top: 5px;
  margin-bottom: 15px;
  text-align: center;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 10px;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Custom Scrollbar */
.sidebar-list::-webkit-scrollbar { width: 6px; }
.sidebar-list::-webkit-scrollbar-track { background: transparent; }
.sidebar-list::-webkit-scrollbar-thumb { background: var(--gold-glow); border-radius: 3px; }

.sidebar-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.25s var(--transition-smooth);
  color: var(--text-primary);
  font-size: 13px;
}

.sidebar-item:hover, .sidebar-item.active {
  background: rgba(222, 184, 135, 0.1);
  border-color: var(--border-glow);
  color: var(--text-bright);
  transform: translateX(3px);
}
.item-conf {
  color: var(--gold-primary);
  font-family: 'Courier New', monospace;
}

/* --- Restored Modal --- */
.restored-modal {
  display: flex !important;
  flex-direction: column;
  height: 85vh;
  max-width: 1200px;
  z-index: 10000;
}
.modal-title-bar {
  padding: 18px;
  text-align: center;
  font-size: 20px;
  font-family: var(--font-display);
  color: var(--gold-primary);
  letter-spacing: 3px;
  background: rgba(10, 6, 18, 0.8);
  border-bottom: 1px solid var(--border-subtle);
}
.restored-zoom-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  overflow: hidden;
  background: #030208;
}
.zoomed-restored-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  box-shadow: 0 0 50px rgba(0,0,0,0.8);
  border-radius: var(--radius-sm);
  animation: zoomIn 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes zoomIn {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.modal-footer-bar {
  padding: 16px;
  display: flex;
  justify-content: center;
  background: rgba(10, 6, 18, 0.8);
  border-top: 1px solid var(--border-subtle);
}

/* --- Global Transition --- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* --- Mobile Compatibility --- */
@media (max-width: 768px) {
  .stage-gallery {
    padding: 15px 0;
  }
  
  .gallery-carousel {
    padding: 0 20px 20px;
  }
  
  .exhibit-card {
    flex: 0 0 240px;
  }
  
  .exhibit-image-frame {
    height: 240px;
  }

  .visual-area { max-height: 55vh; min-height: 40vh; }
  
  .controls-area { 
    position: fixed; 
    bottom: 0; left: 0; right: 0;
    margin: 0; padding: 12px;
    background: rgba(10, 6, 18, 0.8);
    backdrop-filter: blur(16px) saturate(150%);
    border-top: 1px solid var(--border-subtle);
    z-index: 50; 
  }
  
  .controls-wrapper { width: 100%; }
  
  .tool-dock { 
    width: 100%;
    flex-wrap: wrap; 
    justify-content: center; 
    gap: 8px; 
    border-radius: var(--radius-md); 
    padding: 8px;
    background: transparent; border: none; box-shadow: none;
  }
  
  .ritual-tool { 
    padding: 8px 10px; flex: 1; min-width: 80px;
    background: var(--bg-glass); border-radius: var(--radius-sm);
  }
  
  .action-ultimate { 
    border-left: none; padding-left: 10px;
    background: rgba(60, 15, 15, 0.3);
  }
  
  .confidence-control {
    border-radius: var(--radius-sm);
    background: rgba(0,0,0,0.3);
  }
  
  .stage-worktable-v3 { padding-bottom: 120px; }
  
  .worktable-header { padding: 5px 10px; }
  .section-title { font-size: 14px; }
  
  .bbox-modal-content { max-width: 95%; }
  .modal-layout { flex-direction: column; height: auto; max-height: 80vh; overflow-y: auto; }
  .zoom-view { height: 250px; border-right: none; border-bottom: 1px solid var(--border-subtle); }
  .lore-view { flex: none; padding: 20px; }
}

/* --- Fullscreen Btn & Modal --- */
.fullscreen-btn {
  background: transparent;
  color: #a48e65;
  border: 1px solid #a48e65;
  border-radius: 4px;
  cursor: pointer;
  padding: 4px 10px;
  margin-left: 10px;
  transition: all 0.3s;
}

.fullscreen-btn:hover {
  background: var(--gold-glow);
  color: #fff;
  border-color: var(--gold-primary);
}

.image-wrapper.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1000000; /* Slightly lower than bbox-modal-overlay */
  border-radius: 0;
  border: none;
  background-color: #030101; /* Solid background to cover everything */
  margin: 0;
  padding: 0;
  max-width: none;
  max-height: none;
  box-sizing: border-box;
}

.close-fullscreen-btn {
  position: absolute;
  top: 20px;
  right: 30px;
  background: rgba(10, 5, 2, 0.5);
  border: 1px solid rgba(222, 184, 135, 0.5);
  color: var(--gold-primary);
  font-size: 30px;
  width: 45px;
  height: 45px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  backdrop-filter: blur(5px);
}

.close-fullscreen-btn:hover {
  color: #fff;
  border-color: #fff;
  transform: scale(1.1);
  background: var(--gold-glow);
}

/* Global override when fullscreen is active to collapse layouts */
body.fullscreen-mode-active {
  overflow: hidden;
}
body.fullscreen-mode-active .app-header {
  display: none !important;
}
body.fullscreen-mode-active .app-main {
  padding: 0 !important;
  z-index: 0 !important;
}

/* ============================================================ */
/* Premium Processing Overlay Animations                        */
/* ============================================================ */
.processing-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(6, 3, 12, 0.85);
  backdrop-filter: blur(8px);
  border-radius: inherit;
}

.process-effect {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
}

.process-label {
  font-size: 16px;
  color: #e8dbb0;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(201, 162, 39, 0.3);
  animation: labelPulse 2s ease-in-out infinite;
}

@keyframes labelPulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

.process-progress {
  width: 200px;
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  animation: progressGrow linear forwards;
}

/* Scan Progress — 5s, blue-purple */
.scan-fill {
  background: linear-gradient(90deg, #4a90d9, #8b5cf6);
  animation-duration: 5s;
}

/* Purify Progress — 3.5s, cyan-blue */
.purify-fill {
  background: linear-gradient(90deg, #22d3ee, #3b82f6);
  animation-duration: 3.5s;
}

/* Restore Progress — 4.5s, gold */
.restore-fill {
  background: linear-gradient(90deg, #c9a227, #f59e0b);
  animation-duration: 4.5s;
}

@keyframes progressGrow {
  from { width: 0%; }
  to { width: 100%; }
}

/* --- Scan: Rune Rings --- */
.scan-rune-ring {
  width: 100px;
  height: 100px;
  border: 2px dashed rgba(138, 92, 246, 0.5);
  border-radius: 50%;
  animation: runeRingSpin 3s linear infinite;
}

.scan-rune-ring.delay2 {
  position: absolute;
  width: 70px;
  height: 70px;
  border-color: rgba(74, 144, 217, 0.4);
  animation-direction: reverse;
  animation-duration: 2s;
}

@keyframes runeRingSpin {
  100% { transform: rotate(360deg); }
}

/* --- Purify: Water Ripples --- */
.water-ripple {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(34, 211, 238, 0.6);
  border-radius: 50%;
  animation: rippleExpand 2.5s ease-out infinite;
}

.water-ripple.r2 { animation-delay: 0.8s; }
.water-ripple.r3 { animation-delay: 1.6s; }

@keyframes rippleExpand {
  0% { width: 20px; height: 20px; opacity: 1; border-width: 2px; }
  100% { width: 200px; height: 200px; opacity: 0; border-width: 0.5px; transform: translate(-90px, -90px); }
}

.purify-sweep {
  position: absolute;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.6), transparent);
  animation: sweepDown 3.5s ease-in-out;
  top: 0;
}

@keyframes sweepDown {
  0% { top: 0; opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* --- Restore: Golden Burst + Particles --- */
.golden-burst {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: radial-gradient(circle, #c9a227, transparent);
  animation: burstExpand 4s ease-out;
  box-shadow: 0 0 30px rgba(201, 162, 39, 0.5);
}

@keyframes burstExpand {
  0% { width: 24px; height: 24px; opacity: 1; box-shadow: 0 0 30px rgba(201, 162, 39, 0.5); }
  50% { width: 120px; height: 120px; opacity: 0.6; }
  100% { width: 200px; height: 200px; opacity: 0; box-shadow: 0 0 80px rgba(201, 162, 39, 0); }
}

.golden-particles {
  position: absolute;
  top: 50%;
  left: 50%;
}

.g-particle {
  position: absolute;
  width: var(--size);
  height: var(--size);
  background: #c9a227;
  border-radius: 50%;
  animation: particleFly 3s ease-out var(--delay) infinite;
  box-shadow: 0 0 6px rgba(201, 162, 39, 0.6);
}

@keyframes particleFly {
  0% { transform: translate(0, 0) scale(1); opacity: 1; }
  100% { transform: rotate(var(--angle)) translateX(var(--dist)) scale(0); opacity: 0; }
}

/* Ambient Dust Particles */
.global-dust-container {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.dust-particle {
  position: absolute;
  width: var(--size);
  height: var(--size);
  background: var(--gold-primary);
  border-radius: 50%;
  filter: blur(var(--blur)) drop-shadow(0 0 4px var(--gold-glow-intense));
  opacity: 0;
  animation: 
    dustDrift var(--duration) linear infinite var(--delay),
    dustTwinkle calc(var(--duration) / 3) ease-in-out infinite var(--delay);
}

@keyframes dustDrift {
  0% { transform: translate(var(--startX), var(--startY)) rotate(0deg); }
  100% { transform: translate(var(--endX), var(--endY)) rotate(360deg); }
}

@keyframes dustTwinkle {
  0%, 100% { opacity: 0; }
  50% { opacity: var(--opacity); }
}

</style>
