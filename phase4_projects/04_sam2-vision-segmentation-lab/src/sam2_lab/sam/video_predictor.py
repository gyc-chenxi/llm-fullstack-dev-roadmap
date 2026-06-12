"""
SAM 2 视频预测器封装
-------------------
封装 SAM2VideoPredictor，提供简化的视频目标追踪接口：
初始化 → 添加 prompt → 传播 → 导出结果，四步完成。
"""
from __future__ import annotations

import cv2
import numpy as np
from sam2.build_sam import build_sam2_video_predictor


class VideoTracker:
    """SAM 2 视频目标追踪器。

    用法:
        tracker = VideoTracker(checkpoint, model_cfg, device)
        tracker.init_video("video.mp4")
        tracker.add_prompt(frame_idx=0, points=[(300, 250)], labels=[1])
        tracker.propagate()
        masks = tracker.get_all_masks()
    """

    def __init__(
        self,
        checkpoint: str = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt",
        model_cfg: str = "configs/sam2.1/sam2.1_hiera_t.yaml",
        device: str | None = None,
    ):
        if device is None:
            import torch
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

        self.device = device
        self._predictor = build_sam2_video_predictor(
            config_file=model_cfg,
            ckpt_path=checkpoint,
            device=device,
        )
        self._inference_state = None
        self._out_obj_ids = None
        self._out_mask_logits = None
        self._total_frames = 0
        self._video_width = 0
        self._video_height = 0
        self._frame_images = []

    def init_video(self, video_path: str) -> dict:
        """初始化视频推理状态。

        Args:
            video_path: 视频文件路径。

        Returns:
            包含 num_frames, width, height 的字典。
        """
        self._inference_state = self._predictor.init_state(video_path=video_path)
        self._total_frames = self._inference_state["num_frames"]
        self._video_width = self._inference_state["video_width"]
        self._video_height = self._inference_state["video_height"]

        # 缓存原始帧用于后续可视化
        self._frame_images = []
        cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self._frame_images.append(frame)
        cap.release()

        print(
            f"[VideoTracker] 视频已加载: {self._total_frames} 帧, "
            f"{self._video_width}x{self._video_height}"
        )
        return {
            "num_frames": self._total_frames,
            "width": self._video_width,
            "height": self._video_height,
        }

    def add_prompt(
        self,
        frame_idx: int = 0,
        points: list[tuple[int, int]] | None = None,
        labels: list[int] | None = None,
        obj_id: int = 1,
    ) -> list[int]:
        """在指定帧上添加点击 Prompt。

        Args:
            frame_idx: 添加 prompt 的帧索引。
            points: [(x, y), ...] 点击坐标列表。
            labels: [1/0, ...] 对应的前景/背景标签。
            obj_id: 目标 ID（多目标追踪时区分不同对象）。

        Returns:
            注册的目标 ID 列表。
        """
        if self._inference_state is None:
            raise RuntimeError("请先调用 init_video() 初始化视频")

        pts = np.array(points, dtype=np.float32) if points else None
        lbs = np.array(labels, dtype=np.int32) if labels else None

        _, out_obj_ids, out_mask_logits = self._predictor.add_new_points_or_box(
            inference_state=self._inference_state,
            frame_idx=frame_idx,
            obj_id=obj_id,
            points=pts,
            labels=lbs,
        )
        self._out_obj_ids = out_obj_ids
        self._out_mask_logits = out_mask_logits

        print(f"[VideoTracker] Prompt 已添加 @ frame {frame_idx}, obj_ids={out_obj_ids}")
        return list(out_obj_ids)

    def propagate(self, progress_callback=None) -> None:
        """将 mask 从 prompt 帧传播到所有帧。

        Args:
            progress_callback: 可选的回调函数 callback(frame_idx, total_frames)。
        """
        if self._inference_state is None:
            raise RuntimeError("请先调用 init_video() 初始化视频")

        for out_frame_idx, out_obj_ids, out_mask_logits in self._predictor.propagate_in_video(
            self._inference_state
        ):
            self._out_obj_ids = out_obj_ids
            self._out_mask_logits = out_mask_logits
            if progress_callback:
                progress_callback(out_frame_idx, self._total_frames)

        print(f"[VideoTracker] 传播完成，共 {self._total_frames} 帧")

    def get_mask(self, frame_idx: int) -> np.ndarray:
        """获取指定帧的分割 mask。

        Args:
            frame_idx: 帧索引。

        Returns:
            bool 类型的 numpy 数组 (H, W)。
        """
        if self._out_mask_logits is None:
            raise RuntimeError("请先调用 add_prompt() 和 propagate()")

        out = self._predictor._get_orig_video_res_output(
            self._inference_state,
            {
                "out_obj_ids": self._out_obj_ids,
                "out_mask_logits": self._out_mask_logits[frame_idx : frame_idx + 1],
            },
        )
        return out["masks"][0]

    def get_all_masks(self) -> list[np.ndarray]:
        """获取所有帧的分割 mask。

        Returns:
            [(mask, frame_idx), ...] 列表。
        """
        results = []
        for idx in range(self._total_frames):
            mask = self.get_mask(idx)
            results.append((mask, idx))
        return results

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def frame_images(self) -> list:
        return self._frame_images
