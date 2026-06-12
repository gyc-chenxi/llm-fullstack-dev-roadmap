#!/usr/bin/env python3
"""
SAM 2 视频目标追踪脚本 (兼容 SAM 2.1)
----------------------
使用 build_sam2_video_predictor 实现对视频中指定目标的时序分割追踪。
边推断边渲染，抛弃内部私有函数，直接输出追踪视频和关键帧 Mask。

用法示例:
  python scripts/07_video_track.py \
    --video data/videos/sample_video.mp4 \
    --x 300 --y 250
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cv2
import numpy as np
import torch
from sam2.build_sam import build_sam2_video_predictor


def main():
    parser = argparse.ArgumentParser(description="SAM 2 Video Object Tracking")
    parser.add_argument("--video", required=True, help="输入视频路径")
    parser.add_argument("--x", type=int, required=True, help="首帧目标点 X 坐标")
    parser.add_argument("--y", type=int, required=True, help="首帧目标点 Y 坐标")
    parser.add_argument(
        "--frame-idx", type=int, default=0, help="添加 prompt 的帧索引（默认第 0 帧）"
    )
    parser.add_argument(
        "--label", type=int, default=1, help="1=正样本(目标), 0=负样本(背景)"
    )
    parser.add_argument(
        "--checkpoint",
        default="models/sam2/checkpoints/sam2.1_hiera_tiny.pt",
        help="SAM 2 模型权重路径",
    )
    parser.add_argument(
        "--model-cfg",
        default="configs/sam2.1/sam2.1_hiera_t.yaml",
        help="SAM 2 模型配置文件",
    )
    parser.add_argument(
        "--output-dir", default="outputs/video", help="追踪结果输出目录"
    )
    parser.add_argument(
        "--vis-frame-stride",
        type=int,
        default=5,
        help="每隔多少帧保存一张可视化叠加图（控制输出量）",
    )
    args = parser.parse_args()

    # ── 1. 设备检测 ────────────────────────────────────────────
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[video-track] 设备: {device}")
    print(f"[video-track] 视频: {args.video}")
    print(f"[video-track] 追踪点: ({args.x}, {args.y})  @ frame {args.frame_idx}")

    if not os.path.exists(args.video):
        print(f"❌ 错误: 视频文件不存在: {args.video}")
        return

    # ── 2. 加载 SAM 2 视频预测器 ──────────────────────────────
    print("[video-track] 正在加载 SAM 2 视频预测器...")
    predictor = build_sam2_video_predictor(
        config_file=args.model_cfg,
        ckpt_path=args.checkpoint,
        device=device,
    )
    print("[video-track] 模型加载完成 ✓")

    # ── 3. 初始化推理状态 ─────────────────────────────────────
    print("[video-track] 正在初始化视频推理状态（提取帧 + 编码特征）...")
    inference_state = predictor.init_state(video_path=args.video)
    total_frames = inference_state["num_frames"]
    video_height = inference_state["video_height"]
    video_width = inference_state["video_width"]
    print(f"[video-track] 视频信息: {total_frames} 帧, {video_width}x{video_height}")

    # ── 4. 读取原始视频帧到内存 (用于后续画图) ────────────────
    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps):
        fps = 25.0
        
    frame_images = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_images.append(frame)
    cap.release()

    # ── 5. 在指定帧上添加点击 prompt ──────────────────────────
    obj_id = 1
    points = np.array([[args.x, args.y]], dtype=np.float32)
    labels = np.array([args.label], dtype=np.int32)

    print(f"[video-track] 在 frame {args.frame_idx} 添加 prompt...")
    _, out_obj_ids, _ = predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=args.frame_idx,
        obj_id=obj_id,
        points=points,
        labels=labels,
    )
    print(f"[video-track] 已注册追踪目标 ID: {out_obj_ids} ✓")

    # ── 6. 准备输出目录和 VideoWriter ─────────────────────────
    os.makedirs(args.output_dir, exist_ok=True)
    video_name = Path(args.video).stem
    frame_dir = os.path.join(args.output_dir, f"{video_name}_frames")
    os.makedirs(frame_dir, exist_ok=True)

    out_video_path = os.path.join(args.output_dir, f"{video_name}_tracked.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(out_video_path, fourcc, fps, (video_width, video_height))

    manifest_records = []
    saved_mask_count = 0

    # ── 7. 边传播边渲染 (核心重构逻辑) ────────────────────────
    print("[video-track] 正在传播 Mask 并渲染视频...")
    
    for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
        if out_frame_idx % 10 == 0:
            print(f"\r[video-track] 处理进度: {out_frame_idx + 1}/{total_frames} 帧", end="")

        # 将 GPU 上的低分辨率 Tensor 转换为 CPU NumPy 数组 (取第一个物体)
        mask_tensor_np = (out_mask_logits[0, 0] > 0.0).cpu().numpy().astype(np.uint8)
        
        # 使用 OpenCV 将低分辨率 Mask 插值放大到原视频尺寸 (INTER_NEAREST 保持清晰边界)
        mask_resized = cv2.resize(mask_tensor_np, (video_width, video_height), interpolation=cv2.INTER_NEAREST)

        # 保存纯黑白 Mask PNG
        mask_u8 = mask_resized * 255
        mask_filename = f"{video_name}_frame_{out_frame_idx:04d}_mask.png"
        mask_path = os.path.join(frame_dir, mask_filename)
        cv2.imwrite(mask_path, mask_u8)
        saved_mask_count += 1

        # 在原图上画绿色半透明遮罩
        orig_frame = frame_images[out_frame_idx].copy()
        color = np.array([0, 255, 0], dtype=np.uint8)
        orig_frame[mask_resized > 0] = orig_frame[mask_resized > 0] * 0.5 + color * 0.5

        # 写入合成视频流
        out_video.write(orig_frame)

        # 按照步长单独保存 Overlay 预览图
        if out_frame_idx % args.vis_frame_stride == 0:
            vis_path = os.path.join(frame_dir, f"{video_name}_frame_{out_frame_idx:04d}_overlay.png")
            cv2.imwrite(vis_path, orig_frame)

        # 记录数据
        manifest_records.append({
            "frame_idx": out_frame_idx,
            "mask_path": mask_path,
            "mask_area_px": int(mask_resized.sum()),
        })

    out_video.release()
    print("\n[video-track] 视频渲染完成 ✓")

    # ── 8. 保存 manifest ───────────────────────────────────────
    manifest_path = os.path.join(args.output_dir, f"{video_name}_manifest.jsonl")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for rec in manifest_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ── 9. 汇总输出 ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print("[video-track] ✅ 视频追踪全部完成!")
    print(f"[video-track] 导出视频:   {out_video_path}")
    print(f"[video-track] 保存 mask 数: {saved_mask_count}")
    print(f"[video-track] mask 目录:    {frame_dir}")
    print(f"[video-track] manifest:     {manifest_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()