# Knowledge Video Studio Marketplace

面向知识类创作者的 WorkBuddy / CodeBuddy 视频制作插件市场。输入一段脚本，插件会先判断每个语义节拍应该使用可追溯素材、HyperFrames、Remotion、编辑纸拼贴或混合画面，再生成旁白、字幕、成片和素材授权账本。

## 1.1.0：Editorial Premium

完整制作默认执行一套可复用的高质量流程：

- 全片一次生成同一位讲述者，不逐段随机换声音；
- 用一个视觉母题贯穿相邻镜头，并指定一个重点高潮镜头；
- 区分证据素材、背景语境、机制图解和纯氛围素材；
- 中文旁白目标为每秒 4.2–5.2 个汉字；
- 音乐至少比旁白低 18 dB，每 40 秒最多三个语义音效；
- 发布前必须通过素材授权、整片解码、联系表人工检查和至少 85 分的可测质量门槛。

## 安装

在 WorkBuddy 中运行：

```text
/plugin marketplace add huangbuqun-rgb/knowledge-video-studio-marketplace
/plugin install knowledge-video-studio@knowledge-video-studio-marketplace
/reload-plugins
```

也可以在“专家·技能·连接器 → 技能 → 套件 → 添加市场”中填写本仓库地址。

安装后运行：

```text
/knowledge-video-studio:create-knowledge-video <你的知识视频脚本>
```

详细依赖、API Key 配置和本地验证方式见 [INSTALL.md](./INSTALL.md) 与插件内的 [README](./plugins/knowledge-video-studio/README.md)。Pexels/Pixabay Key 采用 BYOK，严禁写入公开仓库；没有 Key 时仍可使用 Wikimedia Commons 和用户自有素材。

## 授权与风险

插件代码采用 MIT License。外部素材沿用各自许可证，并记录来源页、作者、授权链接、文件哈希和使用段落。自动审计不替代法律意见，也不能自动消除肖像权、商标和敏感语境风险。
