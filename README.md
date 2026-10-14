# Antigravity 简体中文汉化补丁

[![Version](https://img.shields.io/badge/version-v0.1.1-blue)](https://github.com/TeacherXuAI/antigravity-zh-cn/releases/tag/v0.1.1)
[![Tests](https://github.com/TeacherXuAI/antigravity-zh-cn/actions/workflows/test.yml/badge.svg)](https://github.com/TeacherXuAI/antigravity-zh-cn/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

适用于 **Google Antigravity（反重力）Desktop** 的简体中文本地化补丁，提供常用设置翻译、中英文切换，以及原版应用的备份与还原。

本项目由 **[徐老师AI / TeacherXuAI](https://github.com/TeacherXuAI)** 开发维护，采用 MIT 许可证开源，为非 Google 官方的社区项目。当前适配 **macOS 上的 Antigravity Desktop 2.22.0 / 2.23.0**，已在 Apple Silicon 设备上完成实机验证。

**[下载最新版本](https://github.com/TeacherXuAI/antigravity-zh-cn/releases/latest) · [安装指南](#install) · [更新日志](CHANGELOG.md) · [问题反馈](https://github.com/TeacherXuAI/antigravity-zh-cn/issues)**

## 功能特性

- **设置本地化**：提供 92 条简体中文译文，覆盖通用、应用、外观、模型与用量设置页中的主要标签和说明，以及部分固定导航。
- **中英文切换**：通过主界面右下角的开关启用或关闭汉化，关闭后恢复英文原文。
- **安装校验**：安装前核对应用版本、入口文件指纹、文件完整性及原版签名。
- **备份与还原**：保留完整原版应用及恢复记录，提供原版还原命令。

汉化仅作用于指定界面区域，不翻译聊天内容、代码、输入框、项目名称或账号信息。当前版本尚未覆盖整个应用。

## 汉化效果

以下为同一版本应用中关闭与开启汉化的实机对比。左侧为英文原文，右侧为中文显示，页面设置值保持一致。

[![应用设置中英文对比](docs/images/application-comparison.png)](docs/images/application-comparison.png)

<details>
<summary>查看中文界面及更多对比</summary>

### 应用设置

![中文应用设置完整窗口](docs/images/application-zh.png)

### 通用设置

![通用设置中英文对比](docs/images/general-comparison.png)

### 外观设置

![外观设置中英文对比](docs/images/appearance-comparison.png)

</details>

截图采集于 2026-10-11，环境为 macOS 26.5.2 / Apple Silicon / Antigravity Desktop 2.22.0。完整窗口仅遮挡账号区域，未重绘或修改界面文字。v0.1.1 沿用 v0.1.0 的翻译范围与界面效果。

[查看完整图集与采集说明](docs/SCREENSHOTS.md) · [查看测试记录](docs/VALIDATION.md)

## 兼容性

| 项目 | 支持情况 |
| --- | --- |
| 应用 | Google Antigravity Desktop **2.22.0 / 2.23.0** |
| 操作系统 | macOS |
| 处理器 | Apple Silicon 已实测；Intel Mac 尚未实测 |
| 安装环境 | Python **3.9+**，无需 Node.js 或 npm 依赖 |
| Windows / Linux | 暂无安装器 |
| Antigravity IDE / VS Code | 不支持 |

安装器同时核对版本号与入口文件指纹。应用版本不受支持时，安装将停止，请勿通过修改版本号或指纹强行安装。

## 安全说明

**安装会修改应用文件，将修改版的外层签名替换为本地 ad-hoc 签名，并放宽这一份应用的动态库签名校验。** 这会降低该应用对所加载动态库的身份校验；修改版不等同于 Google 签名或 Apple 公证的软件，系统策略或后续更新可能阻止其运行。

安装命令中的 `--acknowledge-signature-change` 和 `--allow-local-library-loading` 分别用于确认上述两项变化。安装前请阅读并确认接受这些变化。

原版应用和恢复记录保存在应用旁边：

- `Antigravity.app.zh-cn-original`：完整原版备份。
- `Antigravity.app.zh-cn-state.json`：安装及恢复记录。

请保留这两个文件。若系统阻止修改版运行，应先还原原版。

<details>
<summary>签名与权限详情</summary>

本地签名不包含 Apple Team ID，因此修改版需要 `com.apple.security.cs.disable-library-validation` 权限，以加载原有 Google 框架。安装器不关闭系统 Gatekeeper 或 Hardened Runtime，不删除隔离属性，不修改 Electron 安全开关，也不启用远程调试端口。

安装前会检查原版 Google 签名、macOS 公证、ASAR 完整性及 preload 指纹；遇到已有备份或冲突状态时停止。完整还原会恢复备份中的原始文件和签名。

</details>

补丁不读取账号凭据、不上传对话、不收集遥测，翻译代码不发起网络请求。分发包仅包含本项目源码、词库、文档和截图，不包含 Google 应用或其解包源码。

<a id="install"></a>

## 安装指南

### 1. 下载补丁

请先从 [Google 官网](https://antigravity.google/download) 安装受支持版本的 Antigravity。

打开 [v0.1.1 发布页](https://github.com/TeacherXuAI/antigravity-zh-cn/releases/tag/v0.1.1)，在 **Assets** 中下载 **antigravity-zh-cn-v0.1.1.zip**。解压后，在终端进入解压目录，后续命令均在该目录执行。

若文件位于默认下载目录，可执行：

```bash
cd ~/Downloads/antigravity-zh-cn-v0.1.1
```

<details>
<summary>通过 Git 获取指定版本</summary>

```bash
git clone --branch v0.1.1 --depth 1 https://github.com/TeacherXuAI/antigravity-zh-cn.git
cd antigravity-zh-cn
```

</details>

### 2. 检查应用状态

```bash
python3 tools/patcher.py doctor
```

该命令为只读检查，将显示应用版本、汉化状态、备份位置和文件校验值。请在检查通过后继续。

### 3. 安装汉化补丁

在 Antigravity 中按 `⌘Q` 完全退出应用。确认接受[安全说明](#安全说明)中的签名与权限变化后执行：

```bash
python3 tools/patcher.py install --acknowledge-signature-change --allow-local-library-loading
```

默认应用路径为 `/Applications/Antigravity.app`。如需指定其他路径，在命令后追加 `--app "/完整路径/Antigravity.app"`。路径必须指向真实应用目录，不支持符号链接；无写入权限时应停止操作，不建议使用 `sudo` 强行安装。

### 4. 验证安装结果

重新打开 `/Applications/Antigravity.app`，进入设置，确认通用、应用、外观等页面的目标文字显示为中文。请勿双击应用旁边的原版备份。

## 使用说明

1. 关闭设置面板，返回主界面。
2. 点击右下角的 **「中文 · 开」** 关闭汉化，按钮变为 **「中文 · 关」**。
3. 再次点击可重新开启汉化。应用重启后默认开启中文。

模型名称、版本号、额度数值、颜色值及代码示例保留原样。

## 还原指南

完全退出 Antigravity 后，在补丁目录执行：

```bash
python3 tools/patcher.py restore
```

工具将校验备份并恢复完整原版应用及其签名。自定义路径的应用需使用与安装时相同的 `--app` 参数。

如果应用在安装补丁后已更新，还原操作会停止，以避免旧版备份覆盖新版。此时应保留备份，从官网重新安装，或通过 Issue 提供具体错误信息。

## 已知限制

- 顶部 macOS 原生菜单、部分长说明、下拉选项和工具提示尚未完整汉化。
- 应用更新可能覆盖补丁；新版本需要重新适配和验证。
- 账号登录、地区资格、模型可用性和额度由 Antigravity 本身决定，汉化补丁不改变这些条件。
- Intel Mac、企业受管设备策略及自动更新后的长期行为尚未完成实机验证。完整范围见[测试记录](docs/VALIDATION.md)。

## 开发与测试

开发环境要求 Node.js **20+**、npm 和 Python **3.9+**。

```bash
npm ci --ignore-scripts
npm test
npm run build
```

| 路径 | 用途 |
| --- | --- |
| `locales/zh-CN.json` | 中英文词库 |
| `src/runtime.js` | 界面定位、文本翻译与原文恢复 |
| `tools/patcher.py` | 应用检查、安装与还原 |
| `tools/compatibility.json` | 支持版本与入口文件指纹 |
| `dist/antigravity-zh-cn.js` | 构建后的运行时代码 |
| `tests/` | DOM、ASAR、安装及还原测试 |

运行时在指定区域使用完整词条匹配；关闭汉化时，仅恢复仍保持本项目译文的文本。安装器在应用副本中追加翻译代码、更新校验和并完成签名校验，然后保存恢复记录、备份原版并替换应用。

修改源码后需重新构建，并一并提交生成文件。适配新版本时，须重新验证界面、安装、重启、语言切换、还原及原版签名。具体要求见[贡献指南](CONTRIBUTING.md)。

## 更新日志

版本变更记录见 [CHANGELOG.md](CHANGELOG.md)。v0.1.1 为文档与版本标识修订，未调整词库、翻译逻辑、安装或还原流程。已安装 v0.1.0 的用户无需为本次文档修订重新安装补丁。

## 问题反馈

请通过 [GitHub Issues](https://github.com/TeacherXuAI/antigravity-zh-cn/issues) 提交安装问题、翻译修正或功能建议，并提供：

- macOS 版本、处理器类型及 Antigravity 版本。
- 补丁版本、操作步骤和完整错误信息。
- 已遮挡个人信息的相关截图。

请勿提交账号凭据、邮箱、登录二维码、私人对话、完整应用文件或个人目录。相同问题优先补充到已有 Issue，便于集中排查。

## 作者与交流

维护者：**[徐老师AI / TeacherXuAI](https://github.com/TeacherXuAI)**。

我平时分享 AI 模型测评、教程和各种好玩的智能产品，也会把自己做的小工具开源出来。抖音、视频号、小红书全平台同名，搜索 **「徐老师AI」** 即可找到。

**微信：`XLSbenren`**。工具交流、使用体验或合作联系，添加时请备注「GitHub + 来意」。安装与翻译问题建议优先提交 Issue，方便其他用户查阅。

如果项目对你有帮助，欢迎通过 **Star** 支持维护。版本通知可在 **Watch → Custom → Releases** 中订阅。项目可以直接下载使用，无需关注或添加微信。

## 许可证

本项目原创代码采用 [MIT License](LICENSE)。Google Antigravity 的名称、图标、软件及相关权利归各自权利方所有。本项目由徐老师AI独立维护，不代表 Google。
