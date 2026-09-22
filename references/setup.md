# Windows / macOS 安装与交付

适用 Windows x64、macOS Intel 和 Apple Silicon。需要接收方自己的 Codex、
可用的内置图像生成工具、Adobe Illustrator 和 Python 3.12 或以上。
安装时需要联网下载 Pillow；本包不含 Python、Adobe、Codex 或 MCP 服务端。
Apple Silicon 推荐使用原生 arm64 Python。实际验证状态见 [TESTING.md](../TESTING.md)。

## 1. 安装 Skill

解压 ZIP，进入含 `SKILL.md` 的 `illustrator-local-artwork` 文件夹。
默认安装位置为 `$CODEX_HOME/skills/illustrator-local-artwork`，未设置
`CODEX_HOME` 时为用户主目录下 `.codex/skills/illustrator-local-artwork`。
安装入口根据自身位置找脚本，不依赖当前工作目录。

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install-windows.ps1
# 指定已有 Python 和自定义安装位置：
.\install-windows.ps1 -Python 'C:\Python312\python.exe' -Destination 'D:\工具\illustrator-local-artwork'
```

`ExecutionPolicy Bypass` 只应用于这一次进程，不改变系统执行策略。
未指定 Python 时先尝试 `py -3`，否则尝试 `python`；低于 3.12 会停止并说明原因。

macOS Terminal：

```bash
bash ./install-macos.sh
# 指定原生 Python 或自定义安装位置：
PYTHON_BIN=/opt/homebrew/bin/python3 bash ./install-macos.sh --destination "$HOME/工具/illustrator-local-artwork"
```

自定义位置不会自动注册到 Codex；在 Codex 中明确提供该位置的 `SKILL.md`，
或使用默认 skills 目录让宿主发现它。完成安装后重新加载技能。
已有不同内容的目标文件会阻止覆盖；升级时先自行保留旧版，再使用新目录，
或在已经更新代码的技能目录原地安装（destination 指向自身）。
重复安装相同版本可复用环境。迁移时只搬源文件或 ZIP，不搬 `.venv`；
在新位置重新安装。Job 的绝对路径和 MCP 配置也需要按新机器重新填写。

后续始终使用安装输出的 Python 路径，不依赖终端是否激活虚拟环境：

```powershell
& 'D:\工具\illustrator-local-artwork\.venv\Scripts\python.exe' 'D:\工具\illustrator-local-artwork\scripts\doctor.py'
```

```bash
"$HOME/工具/illustrator-local-artwork/.venv/bin/python" "$HOME/工具/illustrator-local-artwork/scripts/doctor.py"
```

## 2. 配置 Illustrator MCP

已有能调用 `get_state` 和 `run(code, target_path)` 的 Illustrator MCP 可继续使用。
没有时可安装项目使用的 [Illustrator MCP Fork](https://github.com/scort1213/illustrator-mcp)，
其 Windows 使用 COM，Mac 使用 AppleScript/osascript。以下固定到本次检查过的源码提交，
不表示该 MCP 的 Mac 实机已经认证：

```text
01f1e0decf82466e54ba0736709f9e7573441b5c
```

安装示例需先有 Git；MCP 使用自己的虚拟环境，不和 Skill 环境混用。
Windows：

```powershell
git clone https://github.com/scort1213/illustrator-mcp.git "$env:USERPROFILE\illustrator-mcp"
git -C "$env:USERPROFILE\illustrator-mcp" checkout 01f1e0decf82466e54ba0736709f9e7573441b5c
py -3.12 -m venv "$env:USERPROFILE\illustrator-mcp\.venv"
& "$env:USERPROFILE\illustrator-mcp\.venv\Scripts\python.exe" -m pip install "$env:USERPROFILE\illustrator-mcp"
```

macOS：

```bash
git clone https://github.com/scort1213/illustrator-mcp.git "$HOME/illustrator-mcp"
git -C "$HOME/illustrator-mcp" checkout 01f1e0decf82466e54ba0736709f9e7573441b5c
python3 -m venv "$HOME/illustrator-mcp/.venv"
"$HOME/illustrator-mcp/.venv/bin/python" -m pip install "$HOME/illustrator-mcp"
```

将下面一段合并到 Codex 的 `config.toml`（通常在用户目录 `.codex` 下），
将 `<用户名>` 替换为接收方的真实路径；已有 `[mcp_servers.illustrator]` 时编辑它，
不要重复添加，也不要覆盖整个配置文件。

Windows TOML 示例（单引号保留反斜杠）：

```toml
[mcp_servers.illustrator]
command = 'C:\Users\<用户名>\illustrator-mcp\.venv\Scripts\python.exe'
args = ['-m', 'illustrator']
```

macOS TOML 示例：

```toml
[mcp_servers.illustrator]
command = '/Users/<用户名>/illustrator-mcp/.venv/bin/python'
args = ['-m', 'illustrator']
```

配置格式依据 [OpenAI 官方 MCP 文档](https://developers.openai.com/zh-Hans/docs/extend/mcp)。
重新加载 MCP 后先调用 `get_state`，确认实际 Illustrator 版本和打开的文档路径。
Mac 首次可能要求允许启动 MCP 的宿主控制 Illustrator；到系统设置 → 隐私与安全性
→ 自动化检查对应宿主权限。必要时先手动启动 Illustrator，再重新连接。
不要通过反复执行写入脚本排查权限。

## 3. 环境检查的含义

`doctor.py` 输出 JSON；可用 `--config /absolute/config.toml` 和 `--server-name 名称`
指定配置来源。它不启动 Adobe、不执行 MCP 命令、不输出配置中的参数或密钥。

- `runtime_ready: true`：当前 Python、Pillow 与操作系统检查通过，退出码为 0。
- `mcp_config.status: configured_unverified`：只找到配置及可执行命令，尚未连接。
- `not_configured` / `disabled` / `command_not_found`：按上述说明补齐配置。
- `illustrator_connection`、`image_generation` 始终为 `unverified`，须在 Codex 内另验。
- 缺少或损坏 Pillow、Python 太旧、平台不支持时退出码为 1。安装中断可修复网络或 Python 后重跑。

生图工具不能由 Python 安装器提供；当前宿主没有图像生成能力时流程停在生成前。
不能以本地图片转换或安装通过来声称生图成功。

## 4. 首次实际验收

用可丢弃的 AI 测试副本执行一次，再在同一目标执行第二版：确认只隐藏指定旧对象，
原图层可见，新图层嵌入素材，同范围旧版本隐藏，其他范围保持原状态。
保存后重开，检查图层及预览 PNG。Job 仍为 schema v3，路径填写本机绝对路径，
Mac 保留准确大小写。含 `%` 的路径不要手工 URL 编码。

已知限制：AI 源文件的完整路径不能含 `%` 后接两位十六进制字符（如 `%20`、`%AB`）。
Windows Illustrator 28.6 实测会把这类字面路径错误报告为解码后的路径，因此校验器和
JSX 构建器会在写入前返回 `source_path_contains_percent_escape`。先将测试副本移动或
改名到没有这类片段的目录，再重新指定路径。素材 PNG 的这类路径通过 URI 编码处理。

遇到 `target_document_path_mismatch`，核对 MCP 指向和 Job 路径；不要取消保护。
所引用的 MCP 自身按不区分大小写选择文档，因此 Mac 同时打开仅大小写不同的两个文件时
可能拒绝为歧义；关闭无关副本再操作，Skill 自身仍会在写入前严格校验实际路径。
发生超时或 `outcome_unknown`，先检查真实文档和图层状态，不能直接重试。
