# AI 数智化进阶版封面 Skill

`shuzhihua202611` 是用于制作 9:16 培训封面的 Codex Skill。提供封面标题和下方配图，即可按双讲师蓝紫霓虹模板生成 1080 × 1920 PNG。长标题可按语义分行，默认使用亮金色书法主标题与金色黑体副标题。

- [Skill 入口与参数](SKILL.md)
- [封面制作 SOP](references/cover-sop.md)
- [标准交付参考图](assets/reference.png)

## 使用

将仓库目录 `shuzhihua202611` 放入个人 Skill 目录。在 Codex 中调用 `$shuzhihua202611`，附上标题与下方配图。多人合照需要去除会场背景时，先按 SOP 准备透明 PNG。

本地渲染需要 Python、Pillow、NumPy 以及 Noto Sans SC 可变字体、Arial 粗斜体、字魂武林江湖体。字体按本机安装获取。命令行用法见 [SKILL.md](SKILL.md)。

## 标准交付参考图

![AI赋能培训封面标准参考图](assets/reference.png)
