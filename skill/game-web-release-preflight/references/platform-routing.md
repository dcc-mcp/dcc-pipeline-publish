# Small platform routing matrix

Checked 2026-10-24. Recheck changing platform rules before a real release.
This is a technical preparation guide, not a legal eligibility determination.

| Route | Actual artifact and automation | Account/cost/review boundary |
| --- | --- | --- |
| itch.io HTML5 | Complete browser export: ZIP with index.html at its root, or a standalone self-contained HTML file. Butler supports incremental uploads; after the first push, the owner must set the page to HTML and mark the channel as HTML5 / playable in browser. | Officially free upload/hosting; account/project and visibility choices still needed. Commercial payments have separate terms/fees. Content/quality rules still apply; uploading does not guarantee discovery. |
| WeChat mini game | Actual supported mini-game build, not arbitrary HTML5. Official miniprogram-ci handles compilation, preview, and upload. | AppID and administrator-provisioned upload key/IP allowlist are prerequisites. Upload is not approval or publication. Current account-specific qualification, verification fees, privacy obligations, and package limits remain to be verified. |
| Douyin mini game | Dedicated mini-game project. Official tt-minigame-ide-cli exposes developer-tool commands including upload-backed preview. | Official onboarding requires subject verification before game creation. Submission/review/publication follow upload. Account-specific fees and qualifications must be checked; no blanket zero-cost claim. |

## Engine boundary

Cocos Creator 3.8 documents distinct WeChat Game and Douyin build targets.
The WeChat build produces game.json/project.config.json and uses the game's
AppID. LayaAir's official release documentation likewise distinguishes Web,
WeChat, and Douyin targets. These capabilities apply to projects in those
engines, not an automatic converter for Godot projects.

Godot Web export targets browser technologies. No official Godot-to-WeChat or
Godot-to-Douyin adapter was verified in this research. Do not promise support
from a generic WebAssembly/HTML artifact. Evaluate a real maintained adapter
separately if a mini-game release becomes the goal; do not port existing games
or add unreviewed SDKs during this preparation slice.

## Platform-specific work still required

For mini games, confirm the exact engine adapter, platform runtime/base-library
version, main/subpackage budgets, remote-resource rules, touch/keyboard targets,
orientation/safe areas, suspension/resume, audio lifecycle, and platform storage
APIs. Browser IndexedDB evidence does not prove wx/tt storage works. Test the
actual client/device. Check required identity/age/privacy/content and SDK
obligations for the particular account and game, with owner review of relevant
agreements. Do not embed identity documents or secrets in reports.

Do not copy old hard-coded package/fee numbers across platforms: the Cocos
Douyin page lists default main/total limits, while eligibility can differ by
platform channel and newer policy. Treat those as leads requiring current
platform verification, not universal release gates. The direct WeChat CI page
was inaccessible during this research; its official GitHub distribution README
independently verifies CI and key/IP prerequisites. No workaround was used to
enter an account or bypass access restrictions.

## Minimum next slice

Prepare one existing game's supported browser export and evidence bundle first.
Keep its current playable slice rather than expanding content for distribution.
Verify progression persistence, input, combat responsiveness where relevant,
audio and restart on the intended browser/device before adding a mobile claim.
This guide does not establish that any project's Web build already works.

Sources:
- https://itch.io/developers
- https://itch.io/docs/butler/pushing.html
- https://github.com/wechat-miniprogram/miniprogram-ci-dist/blob/master/README.md
- https://partner.open-douyin.com/docs/resource/zh-CN/mini-game/develop/dev-tools/development-assistance/ide-cli
- https://partner.open-douyin.com/docs/resource/zh-CN/mini-game/guide/minigame/register
- https://partner.open-douyin.com/docs/resource/zh-CN/mini-game/guide/minigame/develop
- https://docs.cocos.com/creator/3.8/manual/en/editor/publish/publish-wechatgame.html
- https://docs.cocos.com/creator/3.8/manual/en/editor/publish/publish-bytedance-mini-game.html
- https://layaair.com/3.3/doc/released/generalSetting/readme.html
