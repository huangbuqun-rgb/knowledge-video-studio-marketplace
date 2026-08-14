---
description: 根据知识类脚本生成逐段视觉计划，自动决定素材、HyperFrames、Remotion 或编辑纸拼贴
argument-hint: "脚本文本、脚本文件路径，以及可选的平台/画幅/品牌要求"
---

<user_input>
$ARGUMENTS
</user_input>

调用 `knowledge-video-director` skill，只完成素材语义分析、分段、视觉路由和 `video-plan.json` 验证。默认规划为 `editorial-premium`，必须明确连续旁白策略、跨段视觉母题、重点高潮镜头、证据角色和克制音频策略。不要下载素材，不要渲染，不要声称项目已经完成。向用户总结各视觉模式所占时长、需要的素材密钥，以及任何事实/版权风险。
