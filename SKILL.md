---
name: shuzhihua202611
description: 制作 AI 数智化进阶版封面。用户说“制作 AI 数智化进阶版的封面”“制作 AI 数智化进阶班封面”或调用 $shuzhihua202611 时使用。固定双讲师蓝紫霓虹底图，按确认版排金色书法主标题和金色黑体副标题，抠图合成下方合照，导出 9:16 PNG。
---

# AI 数智化进阶版封面

1. 从本次请求和紧邻上下文取得标题原文与下方原图。查看[标准交付参考图](assets/reference.png)和[结构化执行指南](references/cover-sop.md)。只换配图时沿用已确认的标题和[固定双讲师底图](assets/base.png)。
2. 保留原字、标点和明确指定的换行。主标题用金色武林江湖体，ASCII 字母用 Arial 粗斜体，副标题用金色 Noto Sans SC 黑体。副标题可排一至两行，具体用能读清又能为全身照留出空间的排法。
3. 对合照去背景并核对人物身份、顺序、姿势和关键物件。按整组完整边界等比放大到接近配图区，**每个人的腿和鞋完整入画优先**。原图已截腿时按指南补足全身素材。逐脸检查清晰度，亮度、暖色高光与皮肤质感参考标题上方的讲师照。
4. 用[渲染器](scripts/render_cover.py)合成。先看缩略图占幅，再在成图原尺寸核对头脚、脸部和接缝。交付可打开的 1080 × 1920 竖屏 PNG，附成图预览和下载链接。

用带 Pillow 和 NumPy 的 Python，工作区依赖可用时可直接取其中的 Python。系统使用 Noto Sans SC 可变字体、Arial 粗斜体和本机安装的字魂武林江湖体。字体目录不同时用 `--font` 或 `--brush-font` 指定对应字体。示例请求为 UTF-8 JSON，路径换成实际文件。

```json
{
  "title": "AI 赋能\n让工作与生活更从容",
  "photo": "F:/photos/group-cutout.png",
  "fit": "cutout"
}
```

```powershell
& $pythonPath "$skillDir/scripts/render_cover.py" --request "$requestPath" --output "$outputPath"
```

默认样式是 `gold`。仅在用户指定旧款冰青标题时传 `"style": "ice"`。未指定 `fit` 时，透明图片自动用 `cutout`，不透明图片默认 `cover`。保留场景时用 `contain` 显示全图，或用 `cover` 铺满；可传 `"focus": [横向, 纵向]` 控制裁切方向。可选 `"crop": [左, 上, 右, 下]`，坐标为应用 EXIF 方向后的原图比例（0 到 1）。
