# 双平台交付验证记录

本文件只记录已执行的验证，并将脚本检查与实际 Adobe 自动化分开。

| 环境 | 自动检查 | Illustrator 实机 |
|---|---|---|
| Windows x64 | 15 项测试、结构校验、安装和迁移安装通过 | Illustrator 28.6.0 测试副本通过 |
| macOS Intel | 安装脚本静态检查，未在 macOS 运行 | 待验证 |
| macOS Apple Silicon | 安装脚本静态检查，未在 macOS 运行 | 待验证 |

本次以 `08c67ac` 为基线合并双平台交付能力并发布 `v0.2.0-rc.5`，保留 schema v3。
本地使用 Python 3.12.14、Pillow 12.3.0，2026-09-22 验证。
Windows 安装和迁移均使用独立虚拟环境，路径含中文、空格和括号。
交付 ZIP 的 CRC 与逐文件 SHA-256 校验通过，解压后通过 Windows PowerShell 5.1
入口安装到新目录，安装后的 15 项测试再次全部通过。
Illustrator 验证：测试文档连续放置两版、原层可见、原对象隐藏、旧版本隐藏、
其他范围可见、无关对象保留、素材嵌入、保存重开、167 × 167 PNG 可读且显示替换图案。
故意指定错误文档路径返回 mismatch，图层数量不变。没有改动用户设计稿。
实测发现源 AI 路径中的字面 `%20` 会被 Adobe 错报为空格，现已增加前置拒绝；
含 `%20` 的素材路径经过 URI 编码后实际放置成功。Mac 实机尚未验证这一行为。
自动测试不安装 Adobe，因此测试通过不等于 Illustrator 实机通过，也不等于 Codex
生图能力可用。

开发验证：安装 requirements 后执行 `python -m unittest discover -s tests -v`。
路径比较的 JavaScript 行为测试需要 Node.js；它只用于开发测试，不是接收方运行依赖。
结构校验使用 Codex skill-creator 的 `quick_validate.py`。

发布分支：`codex/v0.2-in-place-layer-workflow`。本地自动检查与 Windows Illustrator
实机证据分别记录；macOS 实机仍未验证，不能以静态检查代替。
