# 🐛 常见失败案例与排查指南

## 1. SAM2 模型加载失败

### 症状
```
ModuleNotFoundError: No module named 'sam2'
```

### 原因 & 解决
- **原因**: SAM2 未安装到当前 Python 环境。
- **解决**: `cd external/sam2 && SAM2_BUILD_CUDA=0 pip install -e .`
- **备选**: 运行 `make setup` 一键安装。

---

## 2. MPS 后端算子不支持

### 症状
```
RuntimeError: MPS does not support...
NotImplementedError: The operator '...' is not currently implemented for MPS
```

### 原因
- SAM2 的某些操作（如 `torch.nn.functional.interpolate` 的特定模式）在 MPS 上未完全实现。

### 解决
- **已内建防御**: `device.py` 中 MPS 默认使用 `float32`。
- **备选方案**:
  ```python
  # 强制使用 CPU
  predictor = build_sam2(cfg, ckpt, device="cpu")
  ```
- **权衡**: CPU 推理速度慢 3-5x，但稳定性最高。

---

## 3. CUDA Out of Memory

### 症状
```
torch.cuda.OutOfMemoryError: CUDA out of memory.
```

### 解决
1. 使用 Tiny 模型（`sam2.1_hiera_tiny.pt`，~39M 参数）
2. 降低 `points_per_side`（如 16 或 8）
3. 设置 `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5`（MPS 等效方案）

---

## 4. 视频追踪 mask 全黑

### 症状
- `propagate_in_video` 返回的 mask 全为零

### 排查步骤
1. 确认首帧 prompt 点确实在目标物体上
2. 检查坐标是否超出了视频分辨率范围
3. 视频画面变化太快时，可以多点几个帧作为 prompt：
   ```python
   tracker.add_prompt(frame_idx=0, points=[(x,y)], labels=[1])
   tracker.add_prompt(frame_idx=10, points=[(x,y)], labels=[1])
   tracker.propagate()
   ```

---

## 5. Diffusers Inpaint 生成黑图

### 症状
- StableDiffusionInpaintPipeline 输出全黑或噪声图

### 原因
1. MPS 下 `torch.float16` 数值精度问题
2. `safety_checker` 误判（关闭后恢复正常）

### 解决
- `InpaintPipeline.__init__` 已内建 MPS → float32 + safety_checker=None
- 手动检查: `pipe = StableDiffusionInpaintPipeline.from_pretrained(..., torch_dtype=torch.float32, safety_checker=None)`

---

## 6. FastAPI TestClient 无法触发 lifespan

### 症状
- `TestClient.get("/health")` 返回 `RuntimeError: SAM2 模型尚未加载`

### 原因
- TestClient 默认不会自动触发 lifespan 事件

### 解决
```python
# 使用 with 上下文触发 lifespan
from sam2_lab.api.server import app
with TestClient(app) as client:
    response = client.get("/health")
```

---

## 7. Gradio 图片上传后坐标系偏移

### 症状
- 点击图片获取的坐标与实际目标位置不符

### 原因
- Gradio 可能对图片做了缩放，坐标需要反算到原始分辨率

### 解决
- 当前 `app.py` 使用 `gr.Image(type="numpy")` 保证原始尺寸一致性
- 如果仍有偏差，在回调函数中打印 `image.shape` 确认
