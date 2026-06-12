# 📊 Mask 质量指标体系

## 指标总览

| 指标 | 函数 | 含义 | 优秀值 |
|------|------|------|--------|
| **area_px** | `mask.sum()` | mask 前景像素总数 | 取决于物体大小 |
| **connected_components** | `cv2.connectedComponentsWithStats` | 连通域数量（碎片化程度） | 1（理想） |
| **largest_component_area_px** | `stats[CC_STAT_AREA]` | 最大连通域面积 | 接近 total_area |
| **largest_area_ratio** | `largest / total` | 最大连通域占比 | >0.95 |
| **hole_count** | `cv2.RETR_CCOMP` 层级分析 | mask 内部孔洞数量 | 0（理想） |
| **edge_points** | `cv2.findContours` 轮廓点数 | 边缘平滑度（点数越少越平滑） | 取决于分辨率 |
| **compactness** | `4π·area / perimeter²` | 形状紧凑度（圆形=1） | 0.5~1.0 |
| **centroid** | `cv2.moments` | 几何质心 (cx, cy) | — |

## 质量评估流程

```
原始 mask (bool ndarray)
    │
    ├──→ 质量报告 (mask_quality_report)
    │      ├── 面积 + 连通域 + 孔洞 + 边缘复杂度
    │      └──→ JSON 报告
    │
    ├──→ 后处理 (postprocess_mask)
    │      ├── 二值化 → 开运算(去噪) → 闭运算(填孔) → 连通域过滤
    │      └──→ 干净 mask
    │
    └──→ 几何分析 (geometry)
           ├── 质心 → 用于位置追踪
           ├── 边界框 → 用于裁剪
           └── 紧凑度 → 形状合理性判断
```

## 阈值调优指南

| 参数 | 默认值 | 调整建议 |
|------|--------|----------|
| `min_area` (后处理) | 500 | 小物体场景降低到 100，大场景提高到 1000 |
| `kernel_size` (形态学) | 5 | 噪声多→增大，细节多→减小 |
| `pred_iou_thresh` (自动分割) | 0.88 | 更多 mask→降低，更准→提高 |
| `stability_score_thresh` | 0.92 | 同上 |
| `min_mask_region_area` | 500 | 取决于目标物体最小尺寸 |

## 使用示例

```bash
# CLI 工具
python scripts/05_mask_quality_report.py \
  --mask outputs/masks/sample_01_point_mask.png \
  --output outputs/reports/quality.json

# Python API
from sam2_lab.mask.quality import mask_quality_report
from sam2_lab.mask.geometry import mask_centroid, mask_compactness

report = mask_quality_report(mask)
cx, cy = mask_centroid(mask)
compact = mask_compactness(mask)
```
