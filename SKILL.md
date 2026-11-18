---
name: shuzhihua202611
description: 制作 AI 数智化进阶版封面。用户说“制作 AI 数智化进阶版的封面”“制作 AI 数智化进阶班封面”或调用 $shuzhihua202611 时使用。固定双讲师蓝紫霓虹底图，按确认版排金色书法主标题和金色黑体副标题，抠图合成下方合照，导出 9:16 PNG。
---

# AI 数智化进阶版封面

1. 从本次请求和紧邻上下文取得标题原文与下方原图。只在缺少必要素材时请用户补充。查看[标准交付参考图](assets/reference.png)和[执行 SOP](references/cover-sop.md)，按用户本次指定的例外优先执行。
2. 保留文案原字、大小写、标点及明确指定的换行。辨认主词，尽量让它独立成首行；副句较长时按语义拆成两行。首行用亮金色字魂武林江湖体，ASCII 字母搭配 Arial 粗斜体。后两行用同字号、同字重、同字距的金色 Noto Sans SC 黑体。首行字高要比后两行大，整组在上下配图之间居中铺开。
3. 多人合照先取得真实透明 PNG。已有合格透明图就直接用；否则用 imagegen 按 SOP 去除背景，逐一核对真实人物、姿态和证书等关键物件。保持同一张[固定底图](assets/base.png)上的双讲师与蓝紫装饰，用[渲染器](scripts/render_cover.py)合成。普通照片在需要保留场景时可用 `cover` 或 `contain`。
4. 查看实际输出图，按 SOP 检查文字、层级、人物、红框等效位置和视觉留白。交付带预览和下载链接的 1080 × 1920 PNG。

用带 Pillow 和 NumPy 的 Python，工作区依赖可用时可直接取其中的 Python。系统使用 Noto Sans SC 可变字体、Arial 粗斜体和本机安装的字魂武林江湖体。字体目录不同时用 `--font` 或 `--brush-font` 指定对应字体。示例请求为 UTF-8 JSON，路径换成实际文件。

```json
{
  "title": "AI赋能\n解锁轻松高效的\n营销新方式",
  "photo": "F:/photos/group-cutout.png",
  "fit": "cutout"
}
```

```powershell
& $pythonPath "$skillDir/scripts/render_cover.py" --request "$requestPath" --output "$outputPath"
```

默认样式是 `gold`。仅在用户指定旧款冰青标题时传 `"style": "ice"`。未指定 `fit` 时，透明图片自动用 `cutout`，不透明图片默认 `cover`。保留场景时用 `contain` 显示全图，或用 `cover` 铺满；可传 `"focus": [横向, 纵向]` 控制裁切方向。可选 `"crop": [左, 上, 右, 下]`，坐标为应用 EXIF 方向后的原图比例（0 到 1）。
