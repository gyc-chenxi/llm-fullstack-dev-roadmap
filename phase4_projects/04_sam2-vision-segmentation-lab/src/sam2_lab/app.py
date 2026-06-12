"""
SAM 2 Vision Lab — Gradio Web UI
================================
提供拖拽式图像分割交互界面：
  - Tab 1: Point Prompt 分割（点击坐标 + 滑块微调）
  - Tab 2: Box Prompt 分割（手动输入四个坐标）
  - Tab 3: Inpaint 修复（分割 + 提示词描述背景）
  - Tab 4: 视频追踪（上传视频 + 点击目标 → 输出追踪视频）

启动方式:
  PYTHONPATH=src python -m sam2_lab.app
  或 make ui
"""
from __future__ import annotations

import argparse
import os
import sys

import cv2
import gradio as gr
import numpy as np
from PIL import Image

# 确保 src/ 在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sam2_lab.inpaint.pipeline import InpaintPipeline
from sam2_lab.mask.postprocess import postprocess_mask
from sam2_lab.mask.quality import mask_quality_report
from sam2_lab.sam.image_predictor import ImagePredictor
from sam2_lab.sam.loader import load_image_predictor
from sam2_lab.sam.video_predictor import VideoTracker

# ── 全局模型（懒加载）─────────────────────────────────────

_predictor: ImagePredictor | None = None
_inpaint: InpaintPipeline | None = None
_video_tracker: VideoTracker | None = None


def get_predictor() -> ImagePredictor:
    global _predictor
    if _predictor is None:
        print("[UI] Loading SAM2 model (first use)...")
        sam2 = load_image_predictor()
        _predictor = ImagePredictor(sam2)
    return _predictor


def get_inpaint() -> InpaintPipeline:
    global _inpaint
    if _inpaint is None:
        print("[UI] Loading Inpaint model (first use)...")
        _inpaint = InpaintPipeline()
    return _inpaint


def get_video_tracker() -> VideoTracker:
    global _video_tracker
    if _video_tracker is None:
        print("[UI] Loading SAM2 Video Tracker (first use)...")
        _video_tracker = VideoTracker()
    return _video_tracker


# ── 回调函数 ──────────────────────────────────────────────


def _cv2_to_pil(img_bgr: np.ndarray) -> Image.Image:
    """cv2 BGR → PIL RGB"""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _mask_to_pil(mask: np.ndarray) -> Image.Image:
    """bool mask → PIL grayscale"""
    u8 = (mask.astype(np.uint8)) * 255
    return Image.fromarray(u8)


def _overlay_mask(image_bgr: np.ndarray, mask: np.ndarray, color=(0, 255, 0)) -> np.ndarray:
    """在原图 BGR 上叠加彩色半透明 mask。"""
    overlay = image_bgr.copy()
    mask_bool = mask > 0 if mask.dtype != bool else mask
    overlay[mask_bool] = overlay[mask_bool] * 0.5 + np.array(color, dtype=np.uint8) * 0.5
    return overlay


def tab_point_segment(
    image: np.ndarray | None,
    x: int,
    y: int,
    label: str,
    apply_postprocess: bool,
) -> tuple[Image.Image | None, Image.Image | None, str]:
    """Point 分割回调。"""
    if image is None:
        return None, None, "⚠️ 请先上传图片"

    label_int = 1 if "前景" in str(label) else 0  # Gradio 5.x Radio 返回选项字符串

    predictor = get_predictor()
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    predictor.set_image(img_rgb)

    try:
        mask, score = predictor.predict_from_point(x, y, label_int)
    except Exception as e:
        return None, None, f"❌ 分割失败: {e}"

    if apply_postprocess:
        mask = postprocess_mask(mask)

    report = mask_quality_report(mask)
    info = (
        f"**Point ({x}, {y})** | label={label_int}\n\n"
        f"Score: **{score:.3f}**\n"
        f"Area: {report['area_px']} px\n"
        f"Components: {report['connected_components']}\n"
        f"Holes: {report['hole_count']}"
    )

    mask_pil = _mask_to_pil(mask)
    overlay = _overlay_mask(image, mask)
    # 在叠加图上标记点击位置
    cv2.circle(overlay, (x, y), 8, (0, 0, 255), -1)
    cv2.circle(overlay, (x, y), 9, (255, 255, 255), 2)
    overlay_pil = _cv2_to_pil(overlay)

    return mask_pil, overlay_pil, info


def tab_box_segment(
    image: np.ndarray | None,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    apply_postprocess: bool,
) -> tuple[Image.Image | None, Image.Image | None, str]:
    """Box 分割回调。"""
    if image is None:
        return None, None, "⚠️ 请先上传图片"

    predictor = get_predictor()
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    predictor.set_image(img_rgb)

    try:
        mask, score = predictor.predict_from_box(x1, y1, x2, y2)
    except Exception as e:
        return None, None, f"❌ 分割失败: {e}"

    if apply_postprocess:
        mask = postprocess_mask(mask)

    report = mask_quality_report(mask)
    info = (
        f"**Box ({x1},{y1}) → ({x2},{y2})**\n\n"
        f"Score: **{score:.3f}**\n"
        f"Area: {report['area_px']} px\n"
        f"Components: {report['connected_components']}\n"
        f"Holes: {report['hole_count']}"
    )

    mask_pil = _mask_to_pil(mask)
    overlay = _overlay_mask(image, mask)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), 2)
    overlay_pil = _cv2_to_pil(overlay)

    return mask_pil, overlay_pil, info


def tab_inpaint(
    image: np.ndarray | None,
    x: int,
    y: int,
    prompt: str,
    steps: int,
    guidance: float,
    seed: int,
) -> tuple[Image.Image | None, str]:
    """分割 + Inpaint 回调。"""
    if image is None:
        return None, "⚠️ 请先上传图片"

    try:
        pipe = get_inpaint()
        predictor = get_predictor()

        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        predictor.set_image(img_rgb)

        # Step 1: SAM2 分割
        mask, score = predictor.predict_from_point(x, y)
        mask_processed = postprocess_mask(mask)

        # Step 2: Inpaint
        pil_image = Image.fromarray(img_rgb)
        pil_mask = _mask_to_pil(mask_processed).convert("RGB")

        result = pipe.run(
            image=pil_image,
            mask=pil_mask,
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            seed=seed,
        )

        info = (
            f"**Inpaint 完成**\n\n"
            f"Prompt: _{prompt}_\n"
            f"Seg score: {score:.3f}\n"
            f"Steps: {steps} | CFG: {guidance} | Seed: {seed}"
        )
        return result, info

    except Exception as e:
        return None, f"❌ Inpaint 失败: {e}"


def tab_video_track(
    video_path: str | None,
    x: int,
    y: int,
    frame_idx: int,
) -> tuple[str | None, str]:
    """视频追踪回调：上传视频 + 点击目标 → 输出追踪视频。

    边传播边渲染，直接操作 propagate_in_video 返回的 GPU tensor，
    不绕行私有 API，与 scripts/07_video_track.py 保持一致的稳健策略。
    """
    if video_path is None:
        return None, "⚠️ 请先上传视频"

    try:
        import time

        tracker = get_video_tracker()
        info = tracker.init_video(video_path)
        total_frames = info["num_frames"]
        width, height = info["width"], info["height"]

        tracker.add_prompt(
            frame_idx=frame_idx,
            points=[(x, y)],
            labels=[1],
        )

        # 准备输出视频写入器（优先 H.264，浏览器兼容最好）
        output_dir = "outputs/video"
        os.makedirs(output_dir, exist_ok=True)
        out_video_path = os.path.join(
            output_dir,
            f"gradio_tracked_{int(time.time())}.mp4",
        )
        # macOS OpenCV 可能不包含 avc1，逐级回退
        for codec in ["avc1", "h264", "mp4v"]:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out_video = cv2.VideoWriter(
                out_video_path, fourcc, 25.0, (width, height)
            )
            if out_video.isOpened():
                print(f"[video-track] 使用编码: {codec}")
                break
        else:
            return None, "❌ 无法创建视频编码器，请检查 OpenCV 安装"

        # 边传播边渲染：直接迭代 propagate_in_video generator，
        # 对每帧 GPU tensor → CPU numpy → cv2.resize → 叠加 → 写视频
        for out_frame_idx, _obj_ids, out_mask_logits in tracker._predictor.propagate_in_video(
            tracker._inference_state
        ):
            # 取第一个目标 (obj_id=1) 的 mask logit，阈值化为二值 mask
            mask_lowres = (out_mask_logits[0, 0] > 0.0).cpu().numpy().astype(np.uint8)
            mask_full = cv2.resize(
                mask_lowres, (width, height), interpolation=cv2.INTER_NEAREST
            )

            # 绿色半透明叠加到原始帧
            orig = tracker.frame_images[out_frame_idx].copy()
            color = np.array([0, 255, 0], dtype=np.uint8)
            orig[mask_full > 0] = orig[mask_full > 0] * 0.5 + color * 0.5
            out_video.write(orig)

        out_video.release()

        # 校验输出
        file_mb = os.path.getsize(out_video_path) / (1024 * 1024)
        if file_mb < 0.1:
            return None, f"❌ 输出视频过小 ({file_mb:.1f} MB)，编码可能失败"

        info_text = (
            f"**视频追踪完成** ✅\n\n"
            f"总帧数: {total_frames}\n"
            f"追踪点: ({x}, {y}) @ frame {frame_idx}\n"
            f"分辨率: {width}x{height}\n\n"
            f"📁 输出视频: `{out_video_path}`"
        )
        return out_video_path, info_text

    except Exception as e:
        return None, f"❌ 视频追踪失败: {e}"


# ── Gradio UI 构建 ────────────────────────────────────────


def build_ui() -> gr.Blocks:
    head_html = """
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>🔬 SAM 2 Vision Segmentation Lab</h1>
        <p>Meta SAM 2.1 · Point / Box Prompt · Diffusers Inpaint · Apple Silicon</p>
    </div>
    """

    with gr.Blocks(title="SAM 2 Vision Lab") as demo:
        gr.Markdown(head_html)

        with gr.Tabs():
            # ── Tab 1: Point 分割 ──────────────────────────
            with gr.Tab("🎯 Point 分割"):
                with gr.Row():
                    with gr.Column(scale=2):
                        input_img_pt = gr.Image(
                            label="上传图片",
                            type="numpy",
                            sources=["upload", "clipboard"],
                        )
                        with gr.Row():
                            x_slider = gr.Slider(
                                0, 1024, value=400, step=1, label="X 坐标"
                            )
                            y_slider = gr.Slider(
                                0, 1024, value=300, step=1, label="Y 坐标"
                            )
                        with gr.Row():
                            label_radio = gr.Radio(
                                choices=["前景 (positive)", "背景 (negative)"],
                                value="前景 (positive)",
                                label="点标签",
                            )
                            postprocess_chk_pt = gr.Checkbox(
                                value=True, label="后处理 (去噪+填孔)"
                            )
                        btn_pt = gr.Button("🚀 执行 Point 分割", variant="primary")

                    with gr.Column(scale=3):
                        with gr.Row():
                            mask_out_pt = gr.Image(label="分割 Mask", type="pil")
                            overlay_out_pt = gr.Image(label="叠加显示", type="pil")
                        info_text_pt = gr.Markdown("等待操作...")

                # 点击图片自动获取坐标
                def on_image_click(evt: gr.SelectData):
                    return int(evt.index[0]), int(evt.index[1])

                input_img_pt.select(
                    fn=on_image_click,
                    outputs=[x_slider, y_slider],
                ).then(
                    fn=tab_point_segment,
                    inputs=[
                        input_img_pt,
                        x_slider,
                        y_slider,
                        label_radio,
                        postprocess_chk_pt,
                    ],
                    outputs=[mask_out_pt, overlay_out_pt, info_text_pt],
                )

                btn_pt.click(
                    fn=tab_point_segment,
                    inputs=[
                        input_img_pt,
                        x_slider,
                        y_slider,
                        label_radio,
                        postprocess_chk_pt,
                    ],
                    outputs=[mask_out_pt, overlay_out_pt, info_text_pt],
                )

            # ── Tab 2: Box 分割 ────────────────────────────
            with gr.Tab("📦 Box 分割"):
                with gr.Row():
                    with gr.Column(scale=2):
                        input_img_box = gr.Image(
                            label="上传图片",
                            type="numpy",
                            sources=["upload", "clipboard"],
                        )
                        gr.Markdown("**框选坐标 (x1,y1 左上角 → x2,y2 右下角)**")
                        with gr.Row():
                            x1_slider = gr.Slider(
                                0, 1024, value=100, step=1, label="x1"
                            )
                            y1_slider = gr.Slider(
                                0, 1024, value=80, step=1, label="y1"
                            )
                        with gr.Row():
                            x2_slider = gr.Slider(
                                0, 1024, value=700, step=1, label="x2"
                            )
                            y2_slider = gr.Slider(
                                0, 1024, value=600, step=1, label="y2"
                            )
                        postprocess_chk_box = gr.Checkbox(
                            value=True, label="后处理 (去噪+填孔)"
                        )
                        btn_box = gr.Button("🚀 执行 Box 分割", variant="primary")

                    with gr.Column(scale=3):
                        with gr.Row():
                            mask_out_box = gr.Image(label="分割 Mask", type="pil")
                            overlay_out_box = gr.Image(label="叠加显示", type="pil")
                        info_text_box = gr.Markdown("等待操作...")

                btn_box.click(
                    fn=tab_box_segment,
                    inputs=[
                        input_img_box,
                        x1_slider,
                        y1_slider,
                        x2_slider,
                        y2_slider,
                        postprocess_chk_box,
                    ],
                    outputs=[mask_out_box, overlay_out_box, info_text_box],
                )

            # ── Tab 3: Inpaint 修复 ─────────────────────────
            with gr.Tab("🎨 Inpaint 修复"):
                with gr.Row():
                    with gr.Column(scale=2):
                        input_img_inp = gr.Image(
                            label="上传图片",
                            type="numpy",
                            sources=["upload", "clipboard"],
                        )
                        with gr.Row():
                            inp_x = gr.Slider(
                                0, 1024, value=400, step=1, label="分割点 X"
                            )
                            inp_y = gr.Slider(
                                0, 1024, value=300, step=1, label="分割点 Y"
                            )
                        prompt_txt = gr.Textbox(
                            value="a clean futuristic background, soft studio lighting",
                            label="Inpaint 提示词",
                            lines=2,
                        )
                        with gr.Row():
                            inp_steps = gr.Slider(
                                5, 50, value=25, step=1, label="去噪步数"
                            )
                            inp_cfg = gr.Slider(
                                1.0, 15.0, value=7.5, step=0.5, label="CFG 引导强度"
                            )
                            inp_seed = gr.Number(value=42, label="随机种子", precision=0)
                        btn_inp = gr.Button(
                            "🎨 执行分割 + Inpaint 修复", variant="primary"
                        )

                    with gr.Column(scale=3):
                        inpaint_out = gr.Image(label="修复结果", type="pil")
                        inp_info = gr.Markdown("等待操作...")

                # 点击图片自动获取 inpaint 分割点坐标
                def on_inp_image_click(evt: gr.SelectData):
                    return int(evt.index[0]), int(evt.index[1])

                input_img_inp.select(
                    fn=on_inp_image_click,
                    outputs=[inp_x, inp_y],
                ).then(
                    fn=tab_inpaint,
                    inputs=[input_img_inp, inp_x, inp_y, prompt_txt, inp_steps, inp_cfg, inp_seed],
                    outputs=[inpaint_out, inp_info],
                )

                btn_inp.click(
                    fn=tab_inpaint,
                    inputs=[
                        input_img_inp,
                        inp_x,
                        inp_y,
                        prompt_txt,
                        inp_steps,
                        inp_cfg,
                        inp_seed,
                    ],
                    outputs=[inpaint_out, inp_info],
                )

            # ── Tab 4: 视频追踪 ────────────────────────────
            with gr.Tab("🎬 视频追踪"):
                with gr.Row():
                    with gr.Column(scale=2):
                        input_video = gr.Video(
                            label="上传视频",
                            sources=["upload"],
                        )
                        gr.Markdown("**首帧追踪点坐标**")
                        with gr.Row():
                            video_x = gr.Slider(
                                0, 1920, value=300, step=1, label="X 坐标"
                            )
                            video_y = gr.Slider(
                                0, 1080, value=250, step=1, label="Y 坐标"
                            )
                        video_frame_idx = gr.Slider(
                            0, 50, value=0, step=1, label="Prompt 帧索引"
                        )
                        btn_video = gr.Button(
                            "🎬 开始追踪", variant="primary"
                        )

                    with gr.Column(scale=3):
                        video_out = gr.Video(
                            label="追踪结果视频（绿色=追踪 mask）",
                            format="mp4",
                            autoplay=True,
                        )
                        video_info = gr.Markdown(
                            "等待操作...\n\n"
                            "**使用方法：**\n"
                            "1. 上传一段短视频（建议 ≤200 帧）\n"
                            "2. 设置首帧目标点的 X/Y 坐标\n"
                            "3. 点击「开始追踪」\n"
                            "4. 等待处理完成，下载追踪视频"
                        )

                btn_video.click(
                    fn=tab_video_track,
                    inputs=[input_video, video_x, video_y, video_frame_idx],
                    outputs=[video_out, video_info],
                )

        # ── 底部状态栏 ─────────────────────────────────────
        gr.Markdown(
            "<br><hr><p style='text-align:center;color:#888'>"
            "SAM 2.1 Hiera-Tiny · PyTorch · macOS MPS · FastAPI + Gradio · MIT</p>"
        )

    return demo


# ── 入口 ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="SAM 2 Vision Lab — Gradio UI")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址")
    parser.add_argument("--port", type=int, default=7864, help="绑定端口")
    parser.add_argument("--share", action="store_true", help="生成公网分享链接")
    args = parser.parse_args()

    demo = build_ui()
    print(f"\n{'='*55}")
    print("  SAM 2 Vision Lab — Gradio UI")
    print(f"  地址: http://{args.host}:{args.port}")
    print(f"{'='*55}\n")
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
    )


if __name__ == "__main__":
    main()
