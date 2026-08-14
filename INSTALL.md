# Install in WorkBuddy

Public marketplace source: `huangbuqun-rgb/knowledge-video-studio-marketplace`

## Graphical installation

1. Open WorkBuddy.
2. Open **专家·技能·连接器**.
3. Choose **技能 → 套件 → 添加市场**.
4. Add `huangbuqun-rgb/knowledge-video-studio-marketplace` as the Git marketplace source.
5. Install **knowledge-video-studio** from the new market.
6. Start a new task and run `/plan-knowledge-video` or `/create-knowledge-video`.

Do not select the inner plugin directory as the market. The selected root is the directory that contains `.codebuddy-plugin/marketplace.json`.

## Optional stock providers

Set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` in the environment used to launch WorkBuddy. Without them, Wikimedia Commons and user-owned local media remain available.

## Verify before installation

```bash
/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy \
  plugin validate ./plugins/knowledge-video-studio

/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy \
  plugin validate .
```
