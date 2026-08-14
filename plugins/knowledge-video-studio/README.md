# Knowledge Video Studio

一个可安装到 WorkBuddy 的完整视频制作套件。输入知识类视频脚本后，它先生成逐段视觉计划，再自动调用以下四种画面路径：

从 1.1.0 起，完整制作默认使用 `editorial-premium` 质量档：一条连续旁白、一个跨段视觉母题、一个重点高潮镜头、逐段证据角色、克制混音、全片联系表和自动交付门槛。只有创作者明确要求时才使用多角色配音、分段风格切换或快速草稿档。

- `stock`：Pexels、Pixabay、Wikimedia Commons 或本地版权明确的素材。
- `hyperframes`：抽象概念、流程、关系、地图、数据解释。
- `remotion`：可参数化图表、UI、代码、数字和动效排版。
- `editorial_collage`：强钩子、历史转折、对比和隐喻的编辑纸拼贴动画。

套件不会把“可免费使用”误称为“无版权”。每次下载都会写入 `asset-ledger.json`，记录来源页、作者、许可证、文件哈希和使用段落；最终审计仍不能替代法律意见，也不能自动消除肖像权、商标或敏感语境风险。

## 安装

1. 在 WorkBuddy 打开“专家·技能·连接器”。
2. 进入“技能”中的“套件”，选择“添加市场”。
3. 选择本市场目录，或填写托管该目录的 Git 仓库地址。
4. 从市场中安装 `knowledge-video-studio`。
5. 运行 `/reload-plugins`，然后使用 `/knowledge-video-studio:create-knowledge-video`。

市场目录必须保留 `.codebuddy-plugin/marketplace.json` 和 `plugins/knowledge-video-studio/` 的相对结构。

## 可选环境变量

不要把 API Key 写进公开插件包或项目仓库。每个使用者可在自己的用户级
`~/.codebuddy/settings.json` 中配置：

```json
{
  "env": {
    "PEXELS_API_KEY": "用户自己的 Pexels Key",
    "PIXABAY_API_KEY": "用户自己的 Pixabay Key"
  }
}
```

也可以在启动 WorkBuddy 前设置同名环境变量。公开分发时推荐 BYOK（每位用户
使用自己的 Key）；如果希望用户免配置，需要另建带鉴权、限流和用量隔离的服务端代理，
不能把开发者 Key 内嵌在插件中。

没有密钥时，连接器仍可检索 Wikimedia Commons。Pexels 和 Pixabay 使用各自的内容许可证，不是公共领域；Commons 结果默认只允许公共领域、CC0、CC BY 和 CC BY-SA，并保留署名字段。

## 本机依赖

- Python 3.10+
- FFmpeg 与 ffprobe
- Node.js 22+、npm/npx（Remotion 与 HyperFrames）
- HyperFrames CLI 仅在计划实际包含 HyperFrames 段落时需要

检查环境：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/doctor.py"
```

## 命令

- `/knowledge-video-studio:plan-knowledge-video <脚本或脚本路径>`：只生成和验证视觉计划。
- `/knowledge-video-studio:create-knowledge-video <脚本或脚本路径>`：从计划、素材、动画到成片的完整流程。
- `/knowledge-video-studio:audit-knowledge-video <项目目录>`：校验计划、片段和素材许可证账本。

完整制作默认走 Premium。明确要求“快速草稿”时才降为 `standard`。Premium 计划必须达到至少 85 分的可测合规分且没有错误；分数检查时间线、中文语速、停顿、解码、音频峰值和联系表是否存在，最终审美仍由创作者查看联系表后确认。

## 给其他用户安装

把完整市场目录推送到 GitHub 或其他 Git 仓库，并保留
`.codebuddy-plugin/marketplace.json`。其他用户先添加市场，再安装插件：

```text
/plugin marketplace add owner/repo
/plugin install knowledge-video-studio@knowledge-video-studio-marketplace
/reload-plugins
```

本地目录适合开发测试；公开或团队分发推荐 Git 市场，便于版本更新。项目作用域可以把
插件启用信息写入 `.codebuddy/settings.json` 与协作者共享，但每位用户仍应保管自己的素材
API Key。

HyperFrames 有一个统一的最终预览确认点：`check` 通过后先打开 Studio，创作者确认再做高质量最终渲染。其他段落可以先自动产出草稿。

## 项目产物

```text
project/
├── source/                 # 原稿、旁白、字幕源
├── video-plan.json         # 唯一时间线与路由来源
├── asset-ledger.json       # 素材许可账本
├── media/                  # 下载或用户提供的素材
├── scenes/                 # 各渲染器工程
├── segments/               # 统一规格的片段 MP4
├── audit/                  # 检查结果与预览帧
└── output/final.mp4        # 成片
```

## 设计依据

素材检索链路参考 MoneyPrinterTurbo 的“脚本 → 搜索词 → Pexels/Pixabay → 时长拼接”，但把随机素材拼接升级为逐段视觉路由和许可证审计。Pexels、Pixabay、Wikimedia、Remotion 与 WorkBuddy 的链接都记录在 `references/upstream.md`。
