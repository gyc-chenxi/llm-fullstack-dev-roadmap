# 🎤 面试深度解析笔记

## 核心面试问题 & 推荐回答框架

---

### Q1: SAM 2 与 SAM 1 的核心区别是什么？

**不同点：**
| 维度 | SAM 1 | SAM 2 |
|------|-------|-------|
| 输入模态 | 仅图像 | 图像 + 视频 |
| 记忆机制 | 无 | Memory Attention + Memory Encoder |
| 视频处理 | 逐帧独立 | 时序传播（propagate_in_video） |
| 架构 | ViT + Prompt Encoder + Mask Decoder | 同上 + Memory Bank（跨帧上下文） |
| 交互方式 | 每帧独立 prompt | 首帧 prompt → 自动追踪全视频 |

**同：** 都遵循 Promptable Segmentation 范式（Point/Box/Mask Prompt → Mask Output）。

---

### Q2: 为什么选择 Hiera 而不是 ViT 作为图像编码器？

1. **效率**: Hiera 是层级化的 Vision Transformer，通过稀疏注意力减少计算量
2. **多尺度**: 天然输出多尺度特征图，利于分割任务
3. **SAM 2 验证**: Meta 在 SAM 2 论文中系统比较了 Hiera-T/S/B+/L 的性能/效率权衡

---

### Q3: Multimask Output 的三个 mask 分别是什么？

SAM2 的 `multimask_output=True` 返回 3 个 mask：
- **整体 mask (whole)**: 完整物体
- **部分 mask (part)**: 物体的子部分（如人的手臂而非全身）
- **子部分 mask (subpart)**: 更精细的子部分（如手指）

**选择策略**: 取最高 IoU 预测得分的 mask（`np.argmax(scores)`）。

---

### Q4: 视频追踪中的 "记忆" 机制是如何工作的？

1. **Memory Encoder**: 将已分割帧的 mask 编码为 memory feature
2. **Memory Attention**: 当前帧通过 cross-attention 查询相邻帧的 memory
3. **Memory Bank**: 维护一个固定大小的 FIFO 队列，存储最近 N 帧的 memory
4. **传播方向**: 支持前向/后向/双向传播

**实际效果**: 即使目标短暂被遮挡，SAM 2 也能通过 memory 恢复追踪。

---

### Q5: MPS vs CUDA 的兼容性问题与应对策略

**已知 MPS 问题:**
1. 部分 `torch.float16` 算子未实现 → 强制 float32
2. 某些 `interpolate` 模式不支持 → CPU fallback
3. attention 算子内存占用较高 → attention_slicing

**工程化防御:**
- `device.py`: 自动检测 + float32 默认
- `inpaint/pipeline.py`: MPS → float32 + enable_attention_slicing + safety_checker=None
- 根据模型尺寸灵活选择 checkpoint (tiny/small/base_plus/large)

---

### Q6: 这个项目的工程化亮点是什么？

1. **模块化分层**: scripts → src → api/app，每层可独立运行
2. **MPS 全链路适配**: 从模型加载到推理到 Inpaint，全流程 Apple Silicon 兼容
3. **生产级可观测性**: JSONL Manifest + 质量报告 + 环境自检
4. **一键式工具链**: Makefile 15+ target (install/download/segment/inpaint/video/test/lint)
5. **标准化 Python 工程**: pyproject.toml + pytest + ruff + src 布局

---

### Q7: 如果让你改进这个项目，你会做什么？

1. **性能**: 添加 `torch.compile()` 支持（PyTorch 2.x）（但 SAM2 的 dynamism 可能限制了 compile 的收益）
2. **多目标追踪**: 扩展 VideoTracker 支持同时追踪多个对象
3. **流式推理**: 用 WebSocket 推送视频追踪进度
4. **量化部署**: ONNX/CoreML 导出，降低部署门槛
5. **评估基准**: 在 DAVIS/YouTube-VOS 标准数据集上评估 mask 质量
