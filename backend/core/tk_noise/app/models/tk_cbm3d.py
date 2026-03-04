# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
from scipy import signal
from skimage import img_as_float
from sklearn.decomposition import PCA
import pywt
from scipy.linalg import hadamard
import gc

from pathlib import Path

class TK_CBM3D:
    """基于改进BM3D的唐卡图像去噪算法实现"""
    
    def __init__(self):
        self.block_size = 8
        self.search_window = 39
        self.similar_blocks_basic = 32  # 增加基础估计阶段相似块数量，提高去噪效果
        self.similar_blocks_final = 48  # 增加最终估计阶段相似块数量，强化去噪
        
        # Calculate absolute path to the "pic" directory dynamically
        # This prevents absolute path breakage and removes the need for `os.chdir()`
        current_script_dir = Path(__file__).resolve().parent
        self.noise_free_dir = str(current_script_dir / "pic")
        
        self.hash_size = 8
        self.hamming_threshold = 25     # 降低hamming阈值，要求更相似的块
        self.step_size = 2              # 大幅减小步长，增加块重叠以消除块效应
        self.distance_threshold_basic = 6000   # 放宽基础估计阶段阈值，找到更多相似块
        self.distance_threshold_final = 1200    # 放宽最终估计阶段阈值，增强去噪
        self._hash_cache = {}

    def _adjust_parameters_for_image_size(self, height, width):
        """
        🔧 新增：根据图像大小自适应调整参数
        大图片使用更激进的优化，小图片保持更高质量
        """
        total_pixels = height * width

        if total_pixels > 1000000:  # 大于1MP的大图片
            print(f"🔧 检测到大图片 ({width}x{height})，使用速度优化参数")
            self.search_window = 25
            self.similar_blocks_basic = 20
            self.similar_blocks_final = 30
            self.step_size = 4
        elif total_pixels > 500000:  # 0.5-1MP的中等图片
            print(f"🔧 检测到中等图片 ({width}x{height})，使用平衡参数")
            self.search_window = 31
            self.similar_blocks_basic = 24
            self.similar_blocks_final = 36
            self.step_size = 3
        else:  # 小于0.5MP的小图片
            print(f"🔧 检测到小图片 ({width}x{height})，使用质量优先参数")
            self.search_window = 39
            self.similar_blocks_basic = 32
            self.similar_blocks_final = 48
            self.step_size = 2

        print(f"📊 调整后参数: 搜索窗口={self.search_window}, 相似块={self.similar_blocks_basic}/{self.similar_blocks_final}, 步长={self.step_size}")
    
    def _get_block_id(self, img, x, y):
        return (id(img), x, y)
    
    def _cache_block_hash(self, img, x, y, block):
        block_id = self._get_block_id(img, x, y)
        self._hash_cache[block_id] = self.perceptual_hash(block, is_block=True)
    
    def _get_cached_hash(self, img, x, y, block):
        block_id = self._get_block_id(img, x, y)
        if block_id not in self._hash_cache:
            self._cache_block_hash(img, x, y, block)
        return self._hash_cache[block_id]
    
    def clear_hash_cache(self):
        self._hash_cache.clear()
        gc.collect()

    def add_gaussian_noise(self, img, noise_level=25):
        """
        为图像添加高斯噪声
        Args:
            img: 输入图像 (BGR格式)
            noise_level: 噪声水平 (标准差)
        Returns:
            添加噪声后的图像
        """
        # 转换为float32以避免数值溢出
        img_float = img.astype(np.float32)

        # 生成高斯噪声
        noise = np.random.normal(0, noise_level, img_float.shape).astype(np.float32)

        # 添加噪声
        noisy_img = img_float + noise

        # 限制像素值范围并转换回uint8
        noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)

        return noisy_img
    
    def estimate_noise_level(self, img):
        img_float = img_as_float(img).astype(np.float32)
        h, w = img_float.shape[:2]
        blocks = []
        step = self.block_size // 2
        for i in range(0, h - self.block_size + 1, step):
            for j in range(0, w - self.block_size + 1, step):
                block = img_float[i:i+self.block_size, j:j+self.block_size].flatten()
                blocks.append(block)
        if len(blocks) < 2:
            return 0.01
        try:
            pca = PCA()
            pca.fit(blocks)
            eigenvalues = pca.explained_variance_
        except Exception as e:
            print(f"PCA 失败: {str(e)}")
            return 0.01
        if len(eigenvalues) == 0 or np.any(np.isnan(eigenvalues)):
            return 0.01
        eigenvalues_sorted = np.sort(eigenvalues)[::-1]
        selected_eigenvalues = None
        for i in range(len(eigenvalues_sorted)):
            current_subset = eigenvalues_sorted[i:]
            if len(current_subset) == 0:
                continue
            mean_subset = np.mean(current_subset)
            median_subset = np.median(current_subset)
            if mean_subset <= median_subset:
                selected_eigenvalues = current_subset
                break
        if selected_eigenvalues is None:
            k = max(1, len(eigenvalues_sorted) // 10)
            selected_eigenvalues = np.sort(eigenvalues_sorted)[-k:]
        noise_variance = np.median(selected_eigenvalues)
        noise_std = np.sqrt(max(noise_variance, 1e-6))
        print(f"Estimated sigma: {noise_std}")
        return noise_std
    
    def bgr_to_yuv(self, img):
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y, u, v = cv2.split(yuv)
        print(f"Original Y range: {y.min()} to {y.max()}, U range: {u.min()} to {u.max()}, V range: {v.min()} to {v.max()}")
        return y.astype(np.float32), u.astype(np.float32), v.astype(np.float32)
    
    def yuv_to_rgb(self, y, u, v):
        # 去除Y通道的缩放处理，直接使用原始值
        y = np.round(y.clip(0, 255)).astype(np.uint8)
        u = np.round(u.clip(0, 255)).astype(np.uint8)
        v = np.round(v.clip(0, 255)).astype(np.uint8)
        yuv = cv2.merge([y, u, v])
        rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
        print(f"YUV to RGB - Y range: {y.min()} to {y.max()}, U range: {u.min()} to {u.max()}, V range: {v.min()} to {v.max()}")
        print(f"RGB range: {rgb.min()} to {rgb.max()}")
        return rgb
    
    def perceptual_hash(self, img, is_block=False):
        if is_block:
            img_gray = img
        else:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_resized = cv2.resize(img_gray, (self.hash_size, self.hash_size), interpolation=cv2.INTER_AREA)
        dct = cv2.dct(np.float32(img_resized))
        dct_low = dct[:8, :8]
        mean = np.mean(dct_low)
        hash_str = ''.join(['1' if pixel > mean else '0' for row in dct_low for pixel in row])
        return hash_str
    
    def hamming_distance(self, hash1, hash2):
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def cosine_similarity(self, img1, img2):
        hist1 = cv2.calcHist([cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
        hist1 = hist1.flatten() / np.linalg.norm(hist1)
        hist2 = hist2.flatten() / np.linalg.norm(hist2)
        return np.dot(hist1, hist2)
    
    def search_similar_thangka(self, noise_img):
        noise_hash = self.perceptual_hash(noise_img, is_block=False)
        similar_candidates = []
        for filename in os.listdir(self.noise_free_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(self.noise_free_dir, filename)
                noise_free_img = cv2.imread(img_path)
                if noise_free_img is None:
                    continue
                candidate_hash = self.perceptual_hash(noise_free_img, is_block=False)
                hamming_dist = self.hamming_distance(noise_hash, candidate_hash)
                if hamming_dist <= self.hamming_threshold:
                    cos_sim = self.cosine_similarity(noise_img, noise_free_img)
                    similar_candidates.append((hamming_dist, cos_sim, noise_free_img))
        similar_candidates.sort(key=lambda x: (-x[1], x[0]))
        return [img for (_, _, img) in similar_candidates[:3]]
    
    def precompute_block_hashes(self, img):
        h, w = img.shape
        for x in range(0, h - self.block_size + 1, self.step_size):
            for y in range(0, w - self.block_size + 1, self.step_size):
                block = img[x:x+self.block_size, y:y+self.block_size]
                if block.shape == (self.block_size, self.block_size):
                    self._cache_block_hash(img, x, y, block)
    
    def block_matching(self, img, i, j, block_size, search_window, similar_imgs=None, use_phash=True, is_final=False):
        if not isinstance(img, np.ndarray) or len(img.shape) != 2:
            raise ValueError("输入必须为二维图像")
        h, w = img.shape
        ref_block = img[i:i+block_size, j:j+block_size]
        if ref_block.shape != (block_size, block_size):
            return [(i, j, ref_block)]

        # 根据阶段选择相似块数量和距离阈值（优化版）
        max_similar_blocks = self.similar_blocks_final if is_final else self.similar_blocks_basic
        base_threshold = self.distance_threshold_final if is_final else self.distance_threshold_basic

        # 根据噪声水平自适应调整阈值
        if hasattr(self, '_current_sigma'):
            sigma_factor = min(self._current_sigma / 25.0, 2.0)  # 噪声越大，阈值适当放宽
            distance_threshold = base_threshold * (0.7 + 0.3 * sigma_factor)
        else:
            distance_threshold = base_threshold

        similar_blocks = []
        ref_hash = self._get_cached_hash(img, i, j, ref_block) if use_phash else None

        search_start_i = max(0, i - search_window // 2)
        search_end_i = min(h - block_size, i + search_window // 2)
        search_start_j = max(0, j - search_window // 2)
        search_end_j = min(w - block_size, j + search_window // 2)
        for x in range(search_start_i, search_end_i, 2):
            for y in range(search_start_j, search_end_j, 2):
                curr_block = img[x:x+block_size, y:y+block_size]
                if curr_block.shape != (block_size, block_size):
                    continue
                if use_phash:
                    curr_hash = self._get_cached_hash(img, x, y, curr_block)
                    if self.hamming_distance(ref_hash, curr_hash) > self.hamming_threshold:
                        continue

                # 计算欧式距离
                dist = np.linalg.norm(ref_block - curr_block) ** 2  # 平方欧式距离

                # 只保留距离小于阈值的块
                if dist < distance_threshold:
                    similar_blocks.append((dist, x, y, curr_block))

        similar_blocks.sort(key=lambda x: x[0])
        valid_blocks = [(x, y, block) for dist, x, y, block in similar_blocks if block.shape == (block_size, block_size)]

        # 确保至少包含参考块本身
        if len(valid_blocks) < 3:
            valid_blocks.append((i, j, ref_block))

        # 限制相似块数量
        valid_blocks = valid_blocks[:max_similar_blocks]
        stage_name = "最终估计" if is_final else "基础估计"
        print(f"{stage_name} - Block ({i}, {j}) matched {len(valid_blocks)} blocks, threshold: {distance_threshold}")
        return valid_blocks
    
    def collaborative_filtering(self, blocks, sigma, is_final=False):
        """
        3D协同滤波：使用小波变换+Hadamard变换的真正3D变换方法
        """
        if not blocks:
            return [], []

        num_blocks = len(blocks)
        block_size = blocks[0].shape[0]

        # 步骤1：构建3D块组
        block_3d = np.zeros((num_blocks, block_size, block_size), dtype=np.float32)
        for i, block in enumerate(blocks):
            block_3d[i] = np.float32(block)

        print(f"构建3D块组: {block_3d.shape}")

        if not is_final:
            # 基础估计阶段：硬阈值处理
            return self._basic_estimation_3d(block_3d, sigma)
        else:
            # 最终估计阶段：Wiener滤波
            return self._final_estimation_3d(block_3d, sigma)

    def _basic_estimation_3d(self, block_3d, sigma):
        """基础估计阶段的3D变换处理"""
        num_blocks, block_size, _ = block_3d.shape

        # 步骤2：对每个2D块进行小波变换（Bior1.5）
        # 存储小波系数的原始形式，而不是重构到8x8矩阵
        wavelet_coeffs_list = []
        for i in range(num_blocks):
            # 使用Bior1.5小波进行2D变换
            coeffs = pywt.dwt2(block_3d[i], 'bior1.5', mode='periodization')
            wavelet_coeffs_list.append(coeffs)

        # 为了进行3D变换，我们需要将系数组织成3D数组
        # 提取各个子带的尺寸
        cA, (cH, cV, cD) = wavelet_coeffs_list[0]
        h, w = cA.shape

        # 创建4个3D数组分别存储各子带
        cA_3d = np.zeros((num_blocks, h, w))
        cH_3d = np.zeros((num_blocks, h, w))
        cV_3d = np.zeros((num_blocks, h, w))
        cD_3d = np.zeros((num_blocks, h, w))

        for i in range(num_blocks):
            cA, (cH, cV, cD) = wavelet_coeffs_list[i]
            cA_3d[i] = cA
            cH_3d[i] = cH
            cV_3d[i] = cV
            cD_3d[i] = cD

        print(f"2D小波变换完成，各子带尺寸: {h}x{w}")

        # 步骤3：2D阈值预处理（去噪优先版，确保有效去噪）
        # 使用有效的阈值强度，优先去噪效果
        base_threshold_2d = sigma * 1.5  # 提高基础阈值，确保去噪效果

        # 根据相似块数量调整阈值强度（去噪优先）
        if num_blocks >= 12:
            threshold_multiplier = 1.5  # 有足够相似块时使用强阈值
        elif num_blocks >= 6:
            threshold_multiplier = 1.3
        else:
            threshold_multiplier = 1.1  # 即使相似块少也要保证去噪

        threshold_2d = base_threshold_2d * threshold_multiplier

        if threshold_2d > 0:
            # 对不同频率子带使用有效的阈值策略
            cA_3d[np.abs(cA_3d) < threshold_2d * 0.5] = 0   # 低频适度处理
            cH_3d[np.abs(cH_3d) < threshold_2d * 1.5] = 0   # 水平高频正常强度
            cV_3d[np.abs(cV_3d) < threshold_2d * 1.5] = 0   # 垂直高频正常强度
            cD_3d[np.abs(cD_3d) < threshold_2d * 2.0] = 0   # 对角高频更强，去除噪声
            print(f"2D阈值处理完成，基础阈值: {base_threshold_2d:.2f}, 调整后: {threshold_2d:.2f}")

        # 步骤4：沿第三维进行Hadamard变换
        # 确保块数量是2的幂次，如果不是则填充
        padded_num = self._next_power_of_2(num_blocks)

        def apply_hadamard_3d(coeff_3d):
            """对3D系数数组应用Hadamard变换"""
            if padded_num != num_blocks:
                padded_coeffs = np.zeros((padded_num, h, w))
                padded_coeffs[:num_blocks] = coeff_3d
            else:
                padded_coeffs = coeff_3d

            # 生成Hadamard矩阵
            H = hadamard(padded_num, dtype=np.float32) / np.sqrt(padded_num)

            # 对每个像素位置进行1D Hadamard变换
            hadamard_coeffs = np.zeros_like(padded_coeffs)
            for i in range(h):
                for j in range(w):
                    vector = padded_coeffs[:, i, j]
                    hadamard_coeffs[:, i, j] = H @ vector

            return hadamard_coeffs, H

        # 对各个子带分别进行Hadamard变换
        cA_hadamard, H = apply_hadamard_3d(cA_3d)
        cH_hadamard, _ = apply_hadamard_3d(cH_3d)
        cV_hadamard, _ = apply_hadamard_3d(cV_3d)
        cD_hadamard, _ = apply_hadamard_3d(cD_3d)

        print(f"3D Hadamard变换完成")

        # 步骤5：3D硬阈值收缩（去噪优先版，确保有效去噪）
        # 使用有效的阈值强度，优先去噪效果
        base_threshold = 4.0 * sigma / np.sqrt(max(num_blocks, 1))  # 提高基础系数，确保去噪

        # 根据块数量调整阈值强度（去噪优先策略）
        if num_blocks >= 8:
            threshold_multiplier = 1.6  # 有足够相似块时使用强阈值
        elif num_blocks >= 4:
            threshold_multiplier = 1.4
        else:
            threshold_multiplier = 1.2  # 即使相似块少也要保证去噪

        # 对不同频率子带使用有效的阈值
        threshold_low = base_threshold * threshold_multiplier * 0.5   # 低频适度处理
        threshold_high = base_threshold * threshold_multiplier * 1.3  # 高频正常强度
        threshold_diag = base_threshold * threshold_multiplier * 1.8  # 对角更强，有效去噪

        cA_hadamard[np.abs(cA_hadamard) < threshold_low] = 0
        cH_hadamard[np.abs(cH_hadamard) < threshold_high] = 0
        cV_hadamard[np.abs(cV_hadamard) < threshold_high] = 0
        cD_hadamard[np.abs(cD_hadamard) < threshold_diag] = 0

        print(f"3D硬阈值处理完成 - 低频: {threshold_low:.4f}, 高频: {threshold_high:.4f}, 对角: {threshold_diag:.4f}")
        print(f"保留系数比例 - cA: {np.count_nonzero(cA_hadamard)/cA_hadamard.size:.3f}, "
              f"cH: {np.count_nonzero(cH_hadamard)/cH_hadamard.size:.3f}, "
              f"cV: {np.count_nonzero(cV_hadamard)/cV_hadamard.size:.3f}, "
              f"cD: {np.count_nonzero(cD_hadamard)/cD_hadamard.size:.3f}")

        # 步骤7：一维逆Hadamard变换
        def apply_inverse_hadamard_3d(hadamard_coeffs, H):
            """应用逆Hadamard变换"""
            H_inv = H.T  # Hadamard矩阵的逆矩阵是其转置
            inverse_coeffs = np.zeros_like(hadamard_coeffs)
            coeff_h, coeff_w = hadamard_coeffs.shape[1], hadamard_coeffs.shape[2]

            for i in range(coeff_h):
                for j in range(coeff_w):
                    vector = hadamard_coeffs[:, i, j]
                    inverse_coeffs[:, i, j] = H_inv @ vector

            # 恢复原始块数量
            if padded_num != num_blocks:
                inverse_coeffs = inverse_coeffs[:num_blocks]

            return inverse_coeffs

        # 对各个子带分别进行逆Hadamard变换
        cA_inverse = apply_inverse_hadamard_3d(cA_hadamard, H)
        cH_inverse = apply_inverse_hadamard_3d(cH_hadamard, H)
        cV_inverse = apply_inverse_hadamard_3d(cV_hadamard, H)
        cD_inverse = apply_inverse_hadamard_3d(cD_hadamard, H)

        print(f"1D逆Hadamard变换完成")

        # 步骤6：权重计算（基于保留的非零系数数量）
        weights = []
        for i in range(num_blocks):
            non_zero_count = (np.count_nonzero(cA_inverse[i]) +
                            np.count_nonzero(cH_inverse[i]) +
                            np.count_nonzero(cV_inverse[i]) +
                            np.count_nonzero(cD_inverse[i]))
            if non_zero_count > 0:
                weight = 1.0 / non_zero_count
            else:
                weight = 1.0
            weights.append(weight)

        # 步骤8：二维逆小波变换
        filtered_blocks = []
        for i in range(num_blocks):
            # 重构小波系数
            coeffs = (cA_inverse[i], (cH_inverse[i], cV_inverse[i], cD_inverse[i]))
            reconstructed = pywt.idwt2(coeffs, 'bior1.5', mode='periodization')

            # 确保尺寸正确
            if reconstructed.shape != (block_size, block_size):
                reconstructed = cv2.resize(reconstructed, (block_size, block_size))

            filtered_blocks.append(reconstructed)

        print(f"2D逆小波变换完成")
        print(f"基础估计 - 权重范围: {min(weights):.6f} - {max(weights):.6f}")

        return filtered_blocks, weights

    def _final_estimation_3d(self, block_3d, sigma):
        """最终估计阶段：改进的Wiener滤波"""
        num_blocks, block_size, _ = block_3d.shape

        # 估计基础估计后的残余噪声水平（根据原始噪声水平自适应调整）
        if sigma <= 15:
            residual_sigma = sigma * 0.2  # 低噪声时保守一些
        elif sigma <= 30:
            residual_sigma = sigma * 0.2  # 中等噪声
        else:
            residual_sigma = sigma * 0.2  # 高噪声时基础估计效果更好

        filtered_blocks = []
        weights = []

        for i in range(num_blocks):
            block = block_3d[i]

            # 计算块的能量（而不是方差）
            block_energy = np.mean(block ** 2)
            noise_power = residual_sigma ** 2

            # 改进的Wiener滤波系数（去噪优先版本，有效抑制噪声）
            if block_energy > noise_power * 3.0:
                # 当信号能量明显大于噪声功率时，保留大部分信号但要去噪
                wiener_factor = (block_energy - noise_power) / block_energy
                wiener_factor = max(wiener_factor, 0.7)  # 至少保留70%，允许更多去噪
            elif block_energy > noise_power * 1.5:
                # 当信号能量略大于噪声功率时，适度抑制噪声
                wiener_factor = 0.6  # 保留75%，有效去噪
            else:
                # 当信号能量小于噪声功率时，更多抑制噪声
                wiener_factor = 0.5   # 保留80%，强力去噪

            # 应用Wiener滤波
            filtered_block = block * wiener_factor
            filtered_blocks.append(filtered_block)

            # 权重计算：去噪优先策略，基于去噪效果分配权重
            block_std = np.std(block)
            block_mean = np.mean(np.abs(block))

            # 根据去噪效果分配权重
            if block_std > 12 and block_mean > 15:  # 高质量结构块
                weight = 1.0
            elif block_std > 6 and block_mean > 8:  # 中等质量块
                weight = 0.8   # 适中权重
            elif block_std >3:  # 低质量但有结构的块
                weight = 0.6   # 中等权重
            else:  # 平滑区域，可能是噪声
                weight = 0.4   # 较低权重，允许更多去噪

            # 让Wiener系数影响权重，促进去噪
            weight *= wiener_factor  # 直接使用Wiener系数
            weights.append(weight)

        # 计算实际的Wiener系数范围用于调试
        wiener_factors = []
        for block in block_3d:
            block_energy = np.mean(block ** 2)
            if block_energy > residual_sigma ** 2:
                wf = max((block_energy - residual_sigma ** 2) / block_energy, 0.7)
            else:
                wf = 0.8
            wiener_factors.append(wf)

        print(f"最终估计 - Wiener系数范围: {min(wiener_factors):.4f} - {max(wiener_factors):.4f}")
        print(f"最终估计 - 权重范围: {min(weights):.6f} - {max(weights):.6f}")
        return filtered_blocks, weights



    def _next_power_of_2(self, n):
        """计算大于等于n的最小2的幂次"""
        if n <= 0:
            return 1
        if n & (n - 1) == 0:  # 如果n已经是2的幂次
            return n
        power = 1
        while power < n:
            power <<= 1
        return power
    
    def aggregate(self, img, blocks, weights):
        if not blocks:
            return np.zeros_like(img, dtype=np.float32)
        h, w = img.shape
        result = np.zeros_like(img, dtype=np.float32)
        count = np.zeros_like(img, dtype=np.float32)

        # 计算权重统计信息用于归一化
        max_weight = max(weights) if weights else 1.0
        min_weight = min(weights) if weights else 1.0

        # 创建窗口函数以减少块边界效应
        window = self._create_window_function(self.block_size)

        for (x, y, block), weight in zip(blocks, weights):
            x_start = max(0, x)
            x_end = min(x + self.block_size, h)
            y_start = max(0, y)
            y_end = min(y + self.block_size, w)
            if x_start >= x_end or y_start >= y_end:
                continue

            valid_block = block[:x_end - x_start, :y_end - y_start]
            valid_window = window[:x_end - x_start, :y_end - y_start]

            # 使用更合理的权重策略
            normalized_weight = max(weight, 0.3)  # 提高最小权重，避免过暗

            # 应用窗口函数减少块边界效应
            weighted_block = valid_block * valid_window * normalized_weight
            weighted_window = valid_window * normalized_weight

            result[x_start:x_end, y_start:y_end] += weighted_block
            count[x_start:x_end, y_start:y_end] += weighted_window

        # 避免除零，使用更合理的默认值
        count[count < 0.1] = 1.0
        result = result / count

        print(f"Aggregate result range: {result.min():.2f} to {result.max():.2f}, "
              f"Count range: {count.min():.2f} to {count.max():.2f}, "
              f"Weight range: {min_weight:.3f} to {max_weight:.3f}")
        return result

    def _create_window_function(self, size):
        """创建窗口函数以减少块边界效应"""
        # 使用汉宁窗口
        window_1d = np.hanning(size)
        window_2d = np.outer(window_1d, window_1d)

        # 归一化窗口，使中心区域权重接近1
        window_2d = window_2d / np.max(window_2d)

        # 调整窗口形状，减少边界衰减
        window_2d = np.power(window_2d, 0.5)  # 使衰减更平缓

        return window_2d

    def adaptive_brightness_correction(self, original, denoised):
        """自适应亮度校正（保护细节区域）"""
    # 计算原始图像的梯度幅值（识别细节区域）
        grad_x = cv2.Sobel(original, cv2.CV_32F, 1, 0, ksize=3)  # 从Scharr改为Sobel
        grad_y = cv2.Sobel(original, cv2.CV_32F, 0, 1, ksize=3) 
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # 创建细节区域掩模（梯度大的区域）
        detail_mask =1.0 - np.exp( grad_mag / -12.0)  # 0-1之间，细节区域接近1
    
        global_ratio = np.mean(original) / (np.mean(denoised) + 1e-7)
        global_ratio = np.clip(global_ratio, 0.9, 1.1)
        
        # 减少细节区域的影响
        result = denoised * (1 - detail_mask*0.7) + denoised * global_ratio * detail_mask*0.7
    
        return result

    def _post_process_smoothing(self, img, sigma):
        """后处理平滑，进一步减少残留噪点"""
        # 使用自适应的双边滤波
        # 根据噪声水平调整滤波强度
        
        
        
    # 对平滑区域进行滤波
        ksize = int(max(5, sigma // 2)) * 2 + 1  # 奇数内核
        grad_x = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)  # 从Scharr改为Sobel
        grad_y = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)  # 从Scharr改为Sobel
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        detail_mask = np.tanh(grad_mag / 15.0)  # 从8.0改为15.0（减少细节保留）
    
        # 应用更强的高斯模糊
        smoothed = cv2.GaussianBlur(img, (ksize, ksize), sigmaX=sigma*0.8)  # 从0.4提高到0.8
    
        # 混合处理：减少细节保留
        result = img * detail_mask*0.6 + smoothed * (1 - detail_mask*0.6)
        return result

    def calculate_psnr(self, original, denoised):
        """
        计算PSNR (Peak Signal-to-Noise Ratio)
        使用numpy实现，不需要外部包
        """
        # 确保数据类型一致
        original = original.astype(np.float64)
        denoised = denoised.astype(np.float64)

        # 计算均方误差
        mse = np.mean((original - denoised) ** 2)

        # 如果MSE为0，说明图像完全相同
        if mse == 0:
            return float('inf')

        # 计算PSNR
        max_pixel_value = 255.0
        psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))

        return psnr

    def calculate_ssim(self, original, denoised):
        """
        计算SSIM (Structural Similarity Index)
        简化版本，使用numpy实现
        """
        # 确保数据类型一致
        original = original.astype(np.float64)
        denoised = denoised.astype(np.float64)

        # SSIM参数
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        # 计算均值
        mu1 = np.mean(original)
        mu2 = np.mean(denoised)

        # 计算方差和协方差
        sigma1_sq = np.var(original)
        sigma2_sq = np.var(denoised)
        sigma12 = np.mean((original - mu1) * (denoised - mu2))

        # 计算SSIM
        numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)

        ssim = numerator / denominator

        return ssim

    def print_quality_metrics(self, input_img, denoised_img):
        """
        打印图像质量评估指标（直接去噪模式）
        """
        print("\n" + "="*60)
        print("📊 直接去噪模式 - 图像质量评估结果")
        print("="*60)

        # 计算输入图像和去噪图像的差异指标
        psnr_value = self.calculate_psnr(input_img, denoised_img)
        ssim_value = self.calculate_ssim(input_img, denoised_img)

        print(f"📷 输入图像尺寸: {input_img.shape}")
        print(f"📷 输出图像尺寸: {denoised_img.shape}")
        print("-" * 40)
        print(f"📊 输入vs输出 PSNR: {psnr_value:.2f} dB")
        print(f"📊 输入vs输出 SSIM: {ssim_value:.4f}")
        print("-" * 40)

        # 计算图像统计信息
        input_mean = np.mean(input_img)
        output_mean = np.mean(denoised_img)
        input_std = np.std(input_img)
        output_std = np.std(denoised_img)

        print(f"� 输入图像 - 均值: {input_mean:.2f}, 标准差: {input_std:.2f}")
        print(f"� 输出图像 - 均值: {output_mean:.2f}, 标准差: {output_std:.2f}")
        print(f"� 亮度变化: {((output_mean - input_mean) / input_mean * 100):+.1f}%")
        print(f"� 对比度变化: {((output_std - input_std) / input_std * 100):+.1f}%")

        print("-" * 40)
        print("� 说明:")
        print("   - PSNR值反映去噪前后的像素差异")
        print("   - SSIM值反映结构相似性保持程度")
        print("   - 较高的PSNR和SSIM表示去噪过程保持了更多原始信息")
        print("   - 标准差降低通常表示噪声被有效去除")
        print("="*60)


    
    def denoise_channel(self, channel, sigma, similar_imgs=None, block_matches=None, channel_name="Y"):
        """
        对单个通道进行去噪处理
        Args:
            channel: 要处理的通道
            sigma: 噪声标准差
            similar_imgs: 相似参考图像
            block_matches: 预定义的块匹配结果（用于U、V通道）
            channel_name: 通道名称，用于调试输出
        """
        # 设置当前噪声水平供块匹配使用
        self._current_sigma = sigma

        # 记录原始图像的亮度统计信息
        original_mean = np.mean(channel)
        original_std = np.std(channel)
        h, w = channel.shape
        result = np.zeros_like(channel, dtype=np.float32)
        count = np.zeros_like(channel, dtype=np.float32)  # 改为0初始化

        # 第一步：基础估计
        if block_matches is None:
            block_matches_step1 = {}
            for i in range(0, h - self.block_size + 1, self.step_size):
                for j in range(0, w - self.block_size + 1, self.step_size):
                    similar_blocks = self.block_matching(channel, i, j, self.block_size, self.search_window, similar_imgs, use_phash=True, is_final=False)
                    if not similar_blocks:
                        continue
                    block_matches_step1[(i, j)] = similar_blocks
                    blocks = [b[2] for b in similar_blocks]
                    filtered_blocks, weights = self.collaborative_filtering(blocks, sigma, is_final=False)
                    
                    # 直接累加，不使用aggregate的重复处理
                    for (x, y, _), filtered_block, weight in zip(similar_blocks, filtered_blocks, weights):
                        x_start, x_end = max(0, x), min(x + self.block_size, h)
                        y_start, y_end = max(0, y), min(y + self.block_size, w)
                        if x_start < x_end and y_start < y_end:
                            valid_block = filtered_block[:x_end - x_start, :y_end - y_start]
                            result[x_start:x_end, y_start:y_end] += valid_block * weight
                            count[x_start:x_end, y_start:y_end] += weight
                    
                    del similar_blocks, filtered_blocks

        count[count < 1 ] = 1
        result = result / count

        # 暂时禁用亮度校正，专注于去噪效果评估
        result_mean = np.mean(result)
        brightness_ratio = 1.0
        if result_mean > 0:  # 避免除零
            brightness_ratio = original_mean / result_mean
            brightness_ratio = np.clip(brightness_ratio, 0.95, 1.05)
            result = result * brightness_ratio
        
        result = self.adaptive_brightness_correction(channel, result)
        print(f"[{channel_name}通道] 第二步：基础估计完成. 估计范围: {result.min():.2f} to {result.max():.2f}, "
              f"亮度比: {brightness_ratio:.3f}", flush=True)
        if channel_name == "Y":
            cv2.imwrite("y_basic.jpg", result.clip(0, 255))

        # 第二步：最终估计 - 同样修复
        final_result = np.zeros_like(channel, dtype=np.float32)
        final_count = np.zeros_like(channel, dtype=np.float32)
        
        if block_matches is None:
            # Y通道：重新进行块匹配
            self.clear_hash_cache()
            self.precompute_block_hashes(result)
            block_matches_step2 = {}
            for i in range(0, h - self.block_size + 1, self.step_size):
                for j in range(0, w - self.block_size + 1, self.step_size):
                    similar_blocks = self.block_matching(result, i, j, self.block_size, self.search_window, similar_imgs, use_phash=True, is_final=True)
                    if not similar_blocks:
                        continue
                    block_matches_step2[(i, j)] = similar_blocks
                    # 最终估计应该使用基础估计的结果，而不是原始噪声块
                    blocks_basic = [result[b[0]:b[0]+self.block_size, b[1]:b[1]+self.block_size] for b in similar_blocks]
                    filtered_blocks, weights = self.collaborative_filtering(blocks_basic, sigma, is_final=True)
                    
                    # 直接累加，不使用aggregate的重复处理
                    for (x, y, _), filtered_block, weight in zip(similar_blocks, filtered_blocks, weights):
                        x_start, x_end = max(0, x), min(x + self.block_size, h)
                        y_start, y_end = max(0, y), min(y + self.block_size, w)
                        if x_start < x_end and y_start < y_end:
                            valid_block = filtered_block[:x_end - x_start, :y_end - y_start]
                            final_result[x_start:x_end, y_start:y_end] += valid_block * weight
                            final_count[x_start:x_end, y_start:y_end] += weight
                    
                    del similar_blocks, blocks_basic, filtered_blocks
            # 返回Y通道结果和块匹配信息
            final_count[final_count < 1 ] = 1
            final_result = final_result / final_count

            # 暂时禁用最终估计的亮度校正
            # final_mean = np.mean(final_result)
            # if final_mean > 0:
            #     final_brightness_ratio = original_mean / final_mean
            #     final_brightness_ratio = np.clip(final_brightness_ratio, 0.98, 1.02)
            #     final_result = final_result * final_brightness_ratio
            final_brightness_ratio = 1.0  # 不进行亮度校正

            # 添加轻微的后处理平滑，进一步减少残留噪点
            final_result = self._post_process_smoothing(final_result, sigma)

            print(f"[{channel_name}通道] 第三步：最终估计完成. 估计范围: {final_result.min():.2f} to {final_result.max():.2f}, "
                  f"亮度比: {final_brightness_ratio:.3f}", flush=True)
            cv2.imwrite("y_final.jpg", final_result.clip(0, 255))
            return final_result.clip(0, 255), (block_matches_step1, block_matches_step2)
        else:
            # U、V通道：使用Y通道第二步的块匹配结果
            block_matches_step1, block_matches_step2 = block_matches
            for (i, j), y_similar_blocks in block_matches_step2.items():
                similar_blocks = []
                for y_x, y_y, _ in y_similar_blocks:
                    if (y_x + self.block_size <= h and y_y + self.block_size <= w and
                        y_x >= 0 and y_y >= 0):
                        uv_block = channel[y_x:y_x+self.block_size, y_y:y_y+self.block_size]
                        if uv_block.shape == (self.block_size, self.block_size):
                            similar_blocks.append((y_x, y_y, uv_block))

                if not similar_blocks:
                    continue

                blocks_noisy = [b[2] for b in similar_blocks]
                filtered_blocks, weights = self.collaborative_filtering(blocks_noisy, sigma, is_final=True)
                
                # 直接累加，不使用aggregate的重复处理
                for (x, y, _), filtered_block, weight in zip(similar_blocks, filtered_blocks, weights):
                    x_start, x_end = max(0, x), min(x + self.block_size, h)
                    y_start, y_end = max(0, y), min(y + self.block_size, w)
                    if x_start < x_end and y_start < y_end:
                        valid_block = filtered_block[:x_end - x_start, :y_end - y_start]
                        final_result[x_start:x_end, y_start:y_end] += valid_block * weight
                        final_count[x_start:x_end, y_start:y_end] += weight
                
                del similar_blocks, blocks_noisy, filtered_blocks

            final_count[final_count < 1 ] = 1
            final_result = final_result / final_count
            print(f"{channel_name} Final estimate range: {final_result.min()} to {final_result.max()}")
            return final_result.clip(0, 255)
    
    def denoise(self, img_path, output_path, strength=0):
        # 读取原始图像（直接处理，不添加噪声）
        input_img = cv2.imread(img_path)
        if input_img is None:
            raise ValueError(f"无法读取图像: {img_path}")
        

        #input_img = self.add_gaussian_noise(original_img, noise_level=25)


        # 搜索相似的无噪声唐卡图像
        similar_imgs = self.search_similar_thangka(input_img)
        #print(f"检索到 {len(similar_imgs)} 张相似无噪声唐卡图像")

        # 转换到YUV色彩空间
        y, u, v = self.bgr_to_yuv(input_img)

        # 估计噪声水平
        sigma = self.estimate_noise_level(y)
        print(f"[TK_CBM3D] 📉 估计的噪声水平 (Sigma): {sigma:.2f}\n[TK_CBM3D] 第一步：块匹配特征提取中...", flush=True)

        # 保存输入图像的Y通道
        cv2.imwrite("y_input_channel.jpg", y.clip(0, 255))
        cv2.imwrite("noise_test1.jpg", input_img)
        # 处理Y通道并获取块匹配信息
        self.clear_hash_cache()
        self.precompute_block_hashes(y)
        y_denoised, y_block_matches = self.denoise_channel(y, sigma, similar_imgs, channel_name="Y")

        # 使用Y通道的块匹配结果处理U、V通道
        print("[TK_CBM3D] 跳过 U, V 通道处理以加速实验...", flush=True)
        #u_denoised = self.denoise_channel(u, sigma * 0.5, similar_imgs, y_block_matches, channel_name="U")
        #v_denoised = self.denoise_channel(v, sigma * 0.5, similar_imgs, y_block_matches, channel_name="V")

        result_rgb = self.yuv_to_rgb(y_denoised, u, v)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, result_bgr)

        # 计算并输出图像质量评估指标
        print(f"\n[TK_CBM3D] ✨ 去噪完成！结果已安全存至临时缓存通道。", flush=True)
        self.print_quality_metrics(input_img, result_bgr)

        self.clear_hash_cache()
        return output_path
