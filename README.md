# Illustrator Local Artwork

一个用于 Adobe Illustrator 局部图案替换的 Codex Skill。

它会根据 Illustrator 文档中的现有风格一次生成一张透明背景图，默认匹配原图色调，并在原 AI 文件中创建空的同级 `aicreate-*` 图层，仅放入替换对象。原图层保持可见，只隐藏被替换的旧对象和同一页面或目标范围的较早版本，因此可以随时在 Illustrator 中恢复任意版本。

> 当前版本：`v0.2.0-rc.4`。这是候选发布版，建议先在可恢复的 Illustrator 文件上完成实际测试。该版本会原地保存传入的 AI 文件。

## 主要能力

- 根据参考画面和创意要求生成透明 PNG 图案。
- 每轮只生成一张图；用户不满意时再生成下一版。
- 默认从被替换图案提取色调，对生成图执行受限色调匹配，同时保护浅色低饱和材质。
- 用户明确要求保持外形、纹样或更换色调时，用户要求优先于默认规则。
- 定位指定对象及其所在图层，在同层级创建空的 `aicreate-*` 图层，仅放置替换图案，不复制整层内容。
- 新图层按目标范围命名为 `aicreate-<原图层名>-<scope_id>`；同一范围重名时自动追加 `-02`、`-03`。
- 原图层保持可见，只隐藏被替换对象和同一目标范围的旧生成层。
- 默认嵌入最终素材，避免外链图片丢失。
- 使用快速校验替代全量文档审计，减少大型 AI 文件的处理时间。
- 最终只向用户交付更新后的 AI 文件和替换后预览图。

## 适用场景

- 替换日历、包装、海报或版式中的局部装饰图案。
- 根据现有设计风格生成新的器物、花卉、纹样或插画元素。
- 在不删除旧设计的前提下，为 Illustrator 文件增加一版 AI 生成图案。

不适合处理文字、日期、完整页面排版或从零生成整份 Illustrator 设计稿。

## 工作流程

```text
读取原 AI 和目标区域
        ↓
生成并检查一张透明图片
        ↓
匹配原图色调（用户指定新色调时跳过）
        ↓
在目标层同级新建空的 aicreate-* 图层
        ↓
只把替换图案放入新图层，并隐藏原对象
        ↓
隐藏原对象和同范围旧版本、嵌入素材并原地保存
        ↓
快速校验并导出最终预览
```

任务配置、生成图、调色中间图、临时 JSX 和诊断信息保存在项目的 `.aicreate/<job-id>/` 目录中，不作为对话交付物展示。

## 安装

将仓库克隆到 Codex skills 目录：

```powershell
git clone https://github.com/Colla-Define-X/illustrator-local-artwork.git `
  "$env:USERPROFILE\.codex\skills\illustrator-local-artwork"
```

安装 Python 依赖：

```powershell
python -m pip install -r "$env:USERPROFILE\.codex\skills\illustrator-local-artwork\requirements.txt"
```

该 Skill 还需要可用的 Illustrator MCP，用于读取文档、执行 JSX、保存 AI 和导出预览。

如需使用候选发布版：

```powershell
git -C "$env:USERPROFILE\.codex\skills\illustrator-local-artwork" checkout v0.2.0-rc.4
```

## 使用方式

在 Codex 中调用：

```text
使用 $illustrator-local-artwork，把这个 AI 文件中指定位置的旧图案替换成一只青绿色手绘花瓶，保持现有版式风格。
```

建议同时提供：

- AI 文件的绝对路径。
- 需要替换的图层、对象或大致页面位置。
- 新图案的主体、风格和色彩要求。
- 必须保留或避免的视觉元素。

如果目标区域无法可靠定位，Skill 会先给出映射建议，不会猜测并修改文件。

## 最终产出

成功执行后，对话中只返回：

1. 原地更新后的 `.ai` 文件。
2. 替换完成后的预览 `.png`。

以下内容仅保留在内部工作目录，不会作为交付物返回：

- 生成图片、调色中间图和色调评分。
- Job JSON 与提示词。
- 生成的 JSX。
- 操作日志和失败诊断。

## 图层与回退

假设原目标图层名为 `印刷`，第一次执行后的结构为：

```text
✓ aicreate-印刷-p19    第 19 页新版本，可见
✓ aicreate-印刷-p26    第 26 页新版本，可见
✓ 印刷                 原图层，可见；旧对象单独隐藏
```

用户不满意并再次生成时，新层会依次命名，旧生成层自动隐藏：

```text
aicreate-印刷-p19-02
aicreate-印刷-p19-03
```

不同页面或替换区域使用独立的 `scope_id`，互不隐藏。需要恢复旧版本时，在 Illustrator 图层面板中切换同一范围的 `aicreate-*` 图层，并重新显示对应的原对象即可。

## 快速校验

执行完成前会确认：

- Illustrator 当前打开的是指定 AI 文件。
- `aicreate-*` 新图层存在且可见。
- 原目标图层保持可见，且仅映射的旧对象被隐藏。
- `contain` 模式下新素材位于目标区域内。
- 最终素材已执行嵌入。
- AI 文件原地保存成功。
- 最终预览 PNG 已成功生成。

如果 Illustrator 返回未知执行结果，Skill 不会直接重试，而会先检查文档中是否已经出现 `aicreate-*` 图层，避免重复放置或重复隐藏。

## 开发与验证

运行测试：

```powershell
python -m unittest discover -s tests -v
```

验证 Skill 结构：

```powershell
python path\to\skill-creator\scripts\quick_validate.py .
```

版本号同时维护在 `VERSION` 和 `SKILL.md` 的 `metadata.version` 中。版本历史参见 [CHANGELOG.md](CHANGELOG.md)，发布步骤参见 [RELEASING.md](RELEASING.md)。

## 版本状态

- `v0.1.0`：AI 副本输出、人工候选确认、完整审计。
- `v0.2.0-rc.1`：原地保存、自动选图、`aicreate-*` 可回退图层、快速校验。
- `v0.2.0-rc.2`：单图生成、用户要求优先、原图色调匹配、递增版本图层。
- `v0.2.0-rc.3`：不再复制整个印刷层，只创建同级替换层并隐藏被替换对象。
- `v0.2.0-rc.4`：按页面或目标范围隔离生成图层，只隐藏同范围旧版本。

仓库地址：<https://github.com/Colla-Define-X/illustrator-local-artwork>
