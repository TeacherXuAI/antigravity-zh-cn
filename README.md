# Google Antigravity 中文汉化补丁 · 徐老师AI

[![Tests](https://github.com/TeacherXuAI/antigravity-zh-cn/actions/workflows/test.yml/badge.svg)](https://github.com/TeacherXuAI/antigravity-zh-cn/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

看 Antigravity 的英文设置有些费劲？这个补丁可以把常用设置换成简体中文，想看原文时也能切回去。

由 **徐老师AI** 制作并开源。目前支持 **Google Antigravity（反重力）Desktop 2.22.0 的 macOS 版本**，已在 Apple Silicon Mac 上测试。这是社区汉化补丁，与 Google 官方无关。

**v0.1.0 正式版**收录了 92 条译文，主要用于「通用、应用、外观、模型与用量」四个设置页，以及部分导航。**还不是全界面汉化**，没翻译的地方会保留英文；可以先看下面的实机截图。

**[下载 v0.1.0](https://github.com/TeacherXuAI/antigravity-zh-cn/releases/tag/v0.1.0) · [安装与还原](#install) · [测试记录](docs/VALIDATION.md) · [反馈问题](https://github.com/TeacherXuAI/antigravity-zh-cn/issues)**

用着有帮助的话，欢迎点一下右上角的 **⭐ Star**。想收到后续版本通知，可以在 **Watch → Custom → Releases** 中订阅。

## 实机效果

下面是在同一台 Mac、同一份应用中切换中英文后的截图。左边关闭汉化，右边开启汉化，页面里的设置值没有改动。

拍摄于 **2026-10-11**，环境为 macOS 26.5.2 / Apple Silicon / Antigravity Desktop 2.22.0。图片保留完整窗口，只遮住左下角账号，没有重绘界面或补写中文。

[![应用设置：汉化关闭与开启的实机对比](docs/images/application-comparison.png)](docs/images/application-comparison.png)

点击图片可以放大。[这里还有三组对比和六张完整窗口截图](docs/SCREENSHOTS.md)。

<details>
<summary>展开查看中文应用设置、通用页和外观页</summary>

### 中文应用设置

![中文应用设置完整窗口，账号已遮挡](docs/images/application-zh.png)

### 通用设置

![通用设置前后对比，部分说明仍为英文](docs/images/general-comparison.png)

### 外观设置

![外观设置前后对比，颜色值和代码示例保留原样](docs/images/appearance-comparison.png)

</details>

## 这一版能做什么

- 把常用设置标签和说明换成中文，模型名称、版本号、额度数值保留原样。
- 在主界面点击右下角「中文 · 开 / 关」切换语言。切换前先关掉设置面板；重启后默认开启中文。
- 安装前检查版本和原版文件，安装时保留完整备份，不想用了可以还原。

聊天内容、代码、输入框、项目名和账号信息不在翻译范围内。

## 支持范围

| 项目 | 目前情况 |
| --- | --- |
| 应用版本 | Antigravity Desktop **2.22.0**，安装时还会核对入口文件指纹 |
| macOS | 提供安装器，已在 Apple Silicon 上实测；Intel Mac 尚未实测 |
| Windows / Linux | 暂无安装器 |
| Antigravity IDE / VS Code | 不支持，本项目不是编辑器语言包 |
| 顶部 macOS 原生菜单 | 暂未汉化 |
| 下拉菜单、工具提示及部分长说明 | 还没有完整覆盖 |
| 应用更新 | 更新可能覆盖补丁；遇到未知版本会停止安装 |
| 账号登录、地区资格、模型和额度 | 由 Antigravity 本身决定，汉化补丁不改变这些 |

已在上述 Mac 环境验证安装、设置页显示、中英切换、重启和完整还原。[测试记录](docs/VALIDATION.md)中列出了具体结果和还没测到的情况。

## 安装前请看一下

这类补丁需要修改应用文件，不能像普通语言设置那样直接启用。**安装后，修改版会改用本地 ad-hoc 签名，并为这一份应用放宽动态库签名校验。** 这会降低它对所加载动态库的身份校验，不等同于 Google 签名或 Apple 公证；系统策略或后续更新也可能阻止修改版运行。

安装命令中的两个参数分别表示你接受这两项变化。完整原版保存在应用旁边的 `Antigravity.app.zh-cn-original`，请连同 `.zh-cn-state.json` 恢复记录一起保留。如果系统阻止运行，请先还原原版。

补丁不读取账号凭据、不上传对话、不收集遥测，翻译代码也不发起网络请求。下载包只有补丁源码、词库、说明和截图，不包含 Google 应用。

<details>
<summary>签名与系统设置细节</summary>

本地签名没有 Apple Team ID，因此修改版需要增加 `com.apple.security.cs.disable-library-validation` 权限，才能加载原有 Google 框架。安装器不会关闭系统 Gatekeeper 或 Hardened Runtime，不删除隔离属性，不改 Electron 安全开关，也不启用远程调试端口。

安装前会核对版本、原始 preload 指纹、ASAR 完整性、Google 签名和 macOS 公证；遇到未知版本或已有备份会停止。完整还原会恢复备份中的原有文件和签名。

</details>

<a id="install"></a>

## 下载、安装和还原

需要 Python **3.9+**。安装不需要 Node.js 或 npm 依赖。请先从 [Google 官网](https://antigravity.google/download) 安装受支持版本的 Antigravity。

在 [v0.1.0 发布页](https://github.com/TeacherXuAI/antigravity-zh-cn/releases/tag/v0.1.0)展开 **Assets**，下载 **antigravity-zh-cn-v0.1.0.zip**。解压后，在终端进入解压出来的文件夹，再运行下面的命令。也可以用 Git 下载：

```bash
git clone https://github.com/TeacherXuAI/antigravity-zh-cn.git
cd antigravity-zh-cn
```

### 1. 检查是否支持

```bash
python3 tools/patcher.py doctor
```

这个命令只检查，不修改应用。它会显示版本、汉化状态、备份位置和校验值。如果提示版本不支持，请先等适配，不要改版本号或指纹强行安装。

### 2. 退出应用，再安装

先在 Antigravity 中按 `⌘Q` 完全退出。确认接受前面说明的签名变化后，运行：

```bash
python3 tools/patcher.py install --acknowledge-signature-change --allow-local-library-loading
```

安装完成后，打开 `/Applications/Antigravity.app`，进入设置查看中文效果。主界面右下角可以切回英文；设置面板打开时，先关闭它再切换。不要双击旁边的原版备份。

如果应用不在默认位置，可使用 `--app "/完整路径/Antigravity.app"` 指定真实目录，暂不支持符号链接。没有写入权限时请先停止，不建议加 `sudo` 强行安装。

### 3. 想换回原版

完全退出应用，然后运行：

```bash
python3 tools/patcher.py restore
```

工具会校验备份，恢复完整原版及其签名。如果应用在安装补丁后更新过，还原会停止，避免用旧备份覆盖新版。此时请保留备份，从官网重新安装，或在仓库反馈具体情况。

## 给想参与开发的朋友

词库在 `locales/zh-CN.json`，翻译逻辑在 `src/runtime.js`，安装和还原工具在 `tools/patcher.py`。

运行时只处理识别到的设置区域和固定导航，词条需要完整匹配。关闭汉化时，只恢复仍保持本工具译文的文本，避免覆盖应用后来更新的内容。

安装器会准备完整应用副本，把翻译代码追加到 preload，再更新 ASAR 和 Info.plist 中的校验和。完成签名与校验后，再次检查应用已退出、原版未变化，最后保存恢复记录并替换应用。

开发测试需要 Node.js 20+、npm 和 Python 3.9+：

```bash
npm ci --ignore-scripts
npm test
npm run build
```

`dist/antigravity-zh-cn.js` 是生成后的运行时代码，修改源码后请一并更新。`tools/compatibility.json` 记录支持版本和入口文件指纹。适配新版本需要重新检查界面、签名、安装和还原流程，不能只改版本号。

欢迎补译文、报问题或提 PR，具体见 [贡献指南](CONTRIBUTING.md)。反馈时带上系统版本、应用版本、操作步骤和打码后的截图，会更容易排查。请勿上传邮箱、登录二维码、对话内容或完整应用文件。

## 作者与交流

我是 **[徐老师AI](https://github.com/TeacherXuAI)**，平时做 AI 模型测评与教程，也分享机器人、好玩的智能产品和自己做的开源小工具。

抖音、视频号、小红书都叫 **「徐老师AI」**，直接搜名字就能找到我。

**微信：`XLSbenren`**。聊 AI 工具、使用体验或合作都可以，添加时备注「GitHub + 来意」就好。安装报错或译文问题，尽量发到 [Issue](https://github.com/TeacherXuAI/antigravity-zh-cn/issues)，这样其他人遇到同样的问题也能找到答案。

项目可以直接下载使用，不需要先关注或加微信。想看看我后面做了什么，也欢迎在 GitHub [关注我](https://github.com/TeacherXuAI)。

## 许可

本项目的原创代码使用 [MIT License](LICENSE)。Google Antigravity 的名称、图标、软件及相关权利归各自权利方所有。本项目由徐老师AI独立维护，不代表 Google。
