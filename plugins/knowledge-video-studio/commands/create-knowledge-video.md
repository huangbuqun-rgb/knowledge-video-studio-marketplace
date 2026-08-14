---
description: 从知识类脚本自动完成视觉规划、版权安全素材匹配、动画制作、装配与审计
argument-hint: "脚本文本或路径；可附平台、画幅、旁白、字幕、品牌和输出目录"
---

<user_input>
$ARGUMENTS
</user_input>

必须调用 `knowledge-video-director` skill 并按其中的 Step 1–8 执行。除非用户明确要求快速草稿，默认设置 `quality_profile: editorial-premium`。把 `video-plan.json` 作为唯一时间线来源；素材只能通过 `rights-safe-media` 流程进入项目；每个动画段必须使用其匹配技能。默认使用一条连续旁白和一个固定音色，定义一个跨段视觉母题和一个重点高潮镜头；每段标注证据角色。除非用户明确要求，不得逐段换声音或逐段换模板。HyperFrames 最终高质量渲染前保留一次 Studio 预览确认，其余步骤可自动推进。没有通过项目验证、全片联系表人工检查、Premium 质量门槛和素材账本审计时，不得把输出称为可发布成片。
