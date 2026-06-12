# 🧠 模型卡片

## SAM 2.1 (Meta, 2024)

| 属性 | 值 |
|------|-----|
| **全称** | Segment Anything Model 2.1 |
| **开发者** | Meta AI (FAIR) |
| **许可证** | Apache 2.0 |
| **架构** | Hiera 层级化视觉编码器 + Prompt 编码器 + Mask 解码器 + Memory 模块 |
| **输入** | 图像 (H×W×3) 或 视频 (T×H×W×3) + Point/Box/Mask Prompt |
| **输出** | 分割 mask + IoU 分数 + 稳定性分数 |

### 模型规格

| 变体 | 参数量 | 编码器 | 推荐场景 |
|------|--------|--------|----------|
| **Tiny** ⭐ (本项目默认) | ~38.9M | Hiera-T | 开发/学习/快速实验 |
| Small | ~46M | Hiera-S | 精度要求较高 |
| Base+ | ~80.8M | Hiera-B+ | 生产/高质量 |
| Large | ~224M | Hiera-L | 研究/最佳精度 |

### 下载

```bash
# 自动下载
make download-sam2
# 手动下载
python scripts/01_download_sam2.py --model-size tiny
```

### 配置

见 `configs/sam2.yaml`：
- `image.max_long_side`: 1024（长边 resize 上限）
- `auto_mask.points_per_side`: 32（采样密度）
- `auto_mask.pred_iou_thresh`: 0.88

---

## Stable Diffusion Inpainting (RunwayML, 2022)

| 属性 | 值 |
|------|-----|
| **全称** | Stable Diffusion Inpainting v1.5 |
| **开发者** | RunwayML (基于 Stability AI SD 1.2) |
| **许可证** | CreativeML Open RAIL++-M |
| **架构** | 基于 Latent Diffusion Model (LDM)，UNet + VAE + CLIP Text Encoder |
| **输入** | 图片 (512×512) + Mask (512×512) + Prompt (text) |
| **输出** | 修复后的图片 (512×512) |

### 下载

```bash
make download-diffusers
# 模型缓存于 models/diffusers/stable-diffusion-inpainting/
```

### 配置

见 `configs/inpaint.yaml`：
- `generation.steps`: 25（去噪步数，越大越精细但越慢）
- `generation.guidance_scale`: 7.5（CFG 强度，越大越贴近 prompt）
- `generation.seed`: 42（随机种子，固定可复现）

### MPS 注意事项

- 强制 `torch_dtype=float32`（float16 在 MPS 上不稳定）
- `attention_slicing=True`（降低显存峰值）
- `safety_checker=None`（学习环境可关闭，加速推理）

---

## 引用

```bibtex
@article{ravi2024sam2,
  title={SAM 2: Segment Anything in Images and Videos},
  author={Ravi, Nikhila and Gabeur, Valentin and Hu, Yuan-Ting and Hu, Ronghang and
          Ryali, Chaitanya and Ma, Tengyu and Khedr, Haitham and R{\"a}dle, Roman and
          Rolland, Chloe and Gustafson, Laura and Mintun, Eric and Pan, Junting and
          Alwala, Kalyan Vasudev and Carion, Nicolas and Wu, Chao-Yuan and Girshick,
          Ross and Doll{\'a}r, Piotr and Feichtenhofer, Christoph},
  journal={arXiv preprint arXiv:2408.00714},
  year={2024}
}

@article{rombach2022high,
  title={High-Resolution Image Synthesis with Latent Diffusion Models},
  author={Rombach, Robin and Blattmann, Andreas and Lorenz, Dominik and Esser, Patrick and Ommer, Bj{\"o}rn},
  booktitle={CVPR},
  year={2022}
}
```
