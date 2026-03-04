import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000'

// Define the core stages of the game
export const GameStages = {
    GALLERY: 'GALLERY',           // 图鉴选择库状态，展示待修复残卷
    START: 'START',               // (可选兼容) 初始状态
    IMAGE_LOADED: 'IMAGE_LOADED', // 图片已选择，进入工作台，等待扫描
    SCANNING: 'SCANNING',         // 正在使用 YOLO 扫描
    SCANNED: 'SCANNED',           // 扫描完成，显示标签，等待修复
    PURIFYING: 'PURIFYING',       // 正在降噪 (tk_noise)
    PURIFIED: 'PURIFIED',         // 降噪完成，等待超分
    RESTORING: 'RESTORING',       // 正在超分辨率 (Real-ESRGAN)
    FINISHED: 'FINISHED'          // 修复完成，展示对比和成就
}

export const useGameStore = defineStore('game', () => {
    const currentStage = ref(GameStages.GALLERY)
    const uploadedImage = ref(null)
    const processedImage = ref(null)
    const scanResults = ref([])
    const achievements = ref([])

    // 运行模式: preset（预设）/ real（真实算法）
    const processingMode = ref('preset')

    // 从后端动态加载的画廊数据
    const galleryItems = ref([])
    const galleryLoaded = ref(false)

    // Load restored state from localStorage
    const getRestoredState = () => {
        try {
            return JSON.parse(localStorage.getItem('thangka_restored_state')) || {}
        } catch (e) {
            return {}
        }
    }

    // 从后端 API 加载画廊数据和运行模式
    async function fetchGallery() {
        try {
            const res = await axios.get(`${API_BASE}/api/v1/gallery`)
            const data = res.data
            processingMode.value = data.mode || 'preset'

            const restoredState = getRestoredState()
            galleryItems.value = data.items.map(item => ({
                ...item,
                isRestored: item.isRestored || !!restoredState[item.id]
            }))
            galleryLoaded.value = true
            console.log(`[Gallery] 加载了 ${galleryItems.value.length} 张唐卡, 模式: ${processingMode.value}`)
        } catch (e) {
            console.error('[Gallery] 后端 API 不可用，使用内置画廊数据', e)
            // 回退到内置画廊数据（无预设图片支持）
            loadFallbackGallery()
        }
    }

    // 全部13幅唐卡的备用数据（API不可用时使用）
    function loadFallbackGallery() {
        const restoredState = getRestoredState()
        const makeItem = (id, title, desc, filename) => {
            const stem = filename.replace(/\.[^.]+$/, '')
            const suffix = filename.match(/\.[^.]+$/)?.[0] || '.jpg'
            return { id, title, desc, url: `/gallery/${filename}`, damagedUrl: `/gallery/${stem}_damaged${suffix}`, purifiedUrl: `/gallery/${stem}_purified${suffix}`, restoredUrl: `/gallery/${filename}`, isRestored: !!restoredState[id] }
        }
        galleryItems.value = [
            makeItem(1, '佛陀释迦牟尼', '14世纪精美壁画残片', '佛陀释迦牟尼.jpg'),
            makeItem(2, '药师佛', '神秘的蓝色身相琉璃光如来', '药师佛.jpg'),
            makeItem(3, '大威德金刚', '极具震慑力的忿怒相本尊', '大威德金刚.jpg'),
            makeItem(4, '阿弥陀佛', '西方极乐世界教主红身曼荼罗', '阿弥陀佛.jpg'),
            makeItem(5, '空行母坛城', '繁复神秘的曼荼罗中心', '空行母坛城.jpg'),
            makeItem(6, '古老坛城', '几何与信仰交织的宇宙模型', '坛城.jpg'),
            makeItem(7, '夏鲁寺五方佛', '夏鲁风经典曼荼罗残片', '夏鲁寺五方佛-5.jpg'),
            makeItem(8, '古格佛传故事', '阿里古格遗址红殿壁画', '古格红殿壁画佛传故事.jpg'),
            makeItem(9, '托林寺白殿残卷', '西藏西部艺术的高峰', '托林寺白殿壁画-12.jpg'),
            makeItem(10, '如意宝', '象征满足一切愿望的珍宝', '如意宝.jpg'),
            makeItem(11, '界火', '燃烧于坛城最外围的保护火焰', '界火.jpg'),
            makeItem(12, '神秘佛首', '斑驳却依然宁静的面庞', 'A0004975.jpg'),
            makeItem(13, '古格护法神', '充满力量的怒相神灵', '1576-2246-14.jpg'),
        ]
        galleryLoaded.value = true
    }

    const currentSelectedThangka = ref(null)

    const markCurrentAsRestored = () => {
        if (currentSelectedThangka.value) {
            currentSelectedThangka.value.isRestored = true
            const state = getRestoredState()
            state[currentSelectedThangka.value.id] = true
            localStorage.setItem('thangka_restored_state', JSON.stringify(state))
        }
    }

    // Tashi's dialogue state
    const tashiMessage = ref("尊贵的旅者，欢迎来到『时空修复图鉴』✨ 这里收藏着蒙尘的西藏瑰宝。请从卷轴中选择一幅残卷，我们一起唤醒它的力量吧！")

    // --- Actions to progress the game state ---

    function loadImage(imageUrl, itemObject) {
        // 确保 item 始终有预设 URL（即使从旧缓存加载也能工作）
        if (itemObject.url && !itemObject.purifiedUrl) {
            const stem = itemObject.url.replace(/\.[^.]+$/, '')
            const suffix = itemObject.url.match(/\.[^.]+$/)?.[0] || '.jpg'
            itemObject.damagedUrl = `/gallery/${stem}_damaged${suffix}`
            itemObject.purifiedUrl = `/gallery/${stem}_purified${suffix}`
            itemObject.restoredUrl = itemObject.url
        }

        // 展示从前端传来的决定性 URL（已根据 isRestored 计算好）
        uploadedImage.value = imageUrl

        currentSelectedThangka.value = itemObject
        currentStage.value = GameStages.IMAGE_LOADED
        if (itemObject && itemObject.isRestored) {
            tashiMessage.value = "这份瑰宝已经被我们成功修复过啦！它现在散发着完美的光辉。您依然可以随时在此端详它，或重新施放法术。"
        } else {
            tashiMessage.value = "这是极其珍贵的卷宗！虽然岁月掩盖了它的辉煌，但我感到了强大的气场。下方是您的『修复法器』，请随意施展！✨"
        }
    }

    function startScan() {
        currentStage.value = GameStages.SCANNING
        tashiMessage.value = "『全息慧眼』已启动！🔍 正在扫描隐藏在岁月中的秘密标记..."
    }

    function completeScan(results) {
        scanResults.value = results
        currentStage.value = GameStages.SCANNED

        if (results.length > 0) {
            const topResult = results[0]
            let lore = ""
            if (topResult.class_zh === "莲花") {
                lore = "在唐卡世界里，莲花代表着出淤泥而不染的纯洁与智慧哦！"
            } else if (topResult.class_zh === "金刚杵") {
                lore = "金刚杵象征着无坚不摧的智慧，能破除一切烦恼！"
            } else if (topResult.class_zh === "佛陀") {
                lore = "慧眼洞悉到了佛陀的尊严，无畏印象征着安定与破除恐惧。"
            } else {
                lore = `它可是非常珍贵的元素哦！`
            }
            tashiMessage.value = `『慧眼』发出了共鸣！识别出了『${topResult.class_zh}』🎯。${lore} 时机已到，请施加『净水拂尘』吧！`
        } else {
            tashiMessage.value = "残存的迷雾太浓重，慧眼未能直接锁定位格元素。不过没关系，请先降下『净水拂尘』洗礼它！💪"
        }
    }

    function startPurify() {
        currentStage.value = GameStages.PURIFYING
        tashiMessage.value = "『净水拂尘』启动！💧 AI 降噪算法正在施展魔法，一点点洗去画面的噪点和灰尘..."
    }

    function completePurify(imageUrl) {
        processedImage.value = imageUrl
        currentStage.value = GameStages.PURIFIED
        tashiMessage.value = "净水拂尘起效了！✨ 画面的杂质被清除了很多。但是颜色和细节还有点模糊，快启动『时光重塑』魔法吧！"
    }

    function startRestore() {
        currentStage.value = GameStages.RESTORING
        tashiMessage.value = "『时光回流』启动！⏳ AI 正在重构丢失的细节，让唐卡的色彩再次绽放..."
    }

    function completeRestore(imageUrl) {
        processedImage.value = imageUrl
        currentStage.value = GameStages.FINISHED
        markCurrentAsRestored()

        const tags = ['#时光大能', '#文物守护者']
        if (scanResults.value.length > 0) {
            tags.unshift(`#慧眼识${scanResults.value[0].class_zh}`)
        }
        achievements.value = tags

        tashiMessage.value = `太不可思议了！这幅唐卡在你的手中重铸了昔日的荣光！它的灵性已被记录在『珍宝阁』档案中。您的成就标签：${tags.join(' ')}。🎉`
    }

    function resetGame() {
        currentStage.value = GameStages.GALLERY
        uploadedImage.value = null
        processedImage.value = null
        scanResults.value = []
        achievements.value = []
        currentSelectedThangka.value = null
        tashiMessage.value = "尊贵的旅者，欢迎回到『时空修复图鉴』✨ 请再选择一幅亟待唤醒的卷轴吧！"
    }

    return {
        currentStage,
        uploadedImage,
        processedImage,
        scanResults,
        tashiMessage,
        achievements,
        galleryItems,
        galleryLoaded,
        processingMode,
        currentSelectedThangka,
        fetchGallery,
        loadImage,
        startScan,
        completeScan,
        startPurify,
        completePurify,
        startRestore,
        completeRestore,
        resetGame
    }
})
