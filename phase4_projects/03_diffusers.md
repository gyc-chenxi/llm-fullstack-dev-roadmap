# P3: Diffusers 图像生成（Day 51-53，3天）

> 核心价值：理解扩散模型 Pipeline 工程（txt2img → img2img → inpaint）

---

## 学习目标

- 理解 SD/SDXL 架构组件：Text Encoder、UNet、VAE、Scheduler
- 跑通 txt2img、img2img、inpaint 三种 Pipeline
- 尝试加载 LoRA 插件 + ControlNet
- 了解生成任务 Schema 设计（seed、steps、cfg_scale）

## 技术栈

```
diffusers / transformers / torch / PIL
```

## 产出物

- [ ] `diffusers_demo.ipynb`：文生图 + 图生图 Demo
- [ ] 生成任务 manifest JSON（记录 seed/steps/cfg_scale/结果）
- [ ] 至少 1 个 LoRA 或 ControlNet 实验

## 参考资料

- HuggingFace Diffusers 官方文档
- 项目路线详见 `phase4_projects/PROJECTS_SUMMARY.md`
