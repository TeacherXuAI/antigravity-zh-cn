# Windows 版本开发验证记录

测试版本：**0.2.0-windows-test.1**。记录日期：2026-10-11。

## 当前结论

已实现 Windows 安装、完整备份、资源还原与冲突检测。Windows 桌面应用启动、账号流程、翻译效果和真实录屏仍待实机验收；本记录不代表 Windows 正式支持声明。

## 官方安装包静态核对

从 [Google 官方下载页](https://antigravity.google/download)取得 Windows x64 Desktop 2.22.0 安装包，仅在开发工作目录中解包检查，未将 Google 程序加入本项目分发包。

| 项目 | 核对结果 |
| --- | --- |
| 安装包 | `Antigravity-x64.exe`，2.22.0 |
| 安装包 SHA-256 | `970c8180dde41ccb67b944eda9755a35d5ce669f6db5b501399dc069d73f667d` |
| 主程序 SHA-256 | `df5030f1f8e1fb6b1b732629e802455d1ff4bd2eeae5f38eb733163e92ad2dfa` |
| 原版 app.asar SHA-256 | `259c83ffa266088dda6ede520a601bbf06cc5c34985cdf56c5d68549c98dbb0e` |
| preload SHA-256 | `81d220de63447d27db95adf67d9711b59ee317b2338ba538f419b354a54b1f60` |
| 可执行文件架构 | PE AMD64 (`0x8664`) |
| Electron fuse V1 | `101100011`，嵌入式 ASAR 校验为关闭；工具不修改任何 fuse |
| 主程序证书表 | 原包解出的 EXE 证书表为空；不据此声称有效 Google Authenticode 签名 |

Electron 配置解释依据 [ASAR Integrity 文档](https://www.electronjs.org/docs/latest/tutorial/asar-integrity)及 [官方 FuseV1Options 定义](https://github.com/electron/fuses/blob/main/src/config.ts)。静态核对不等于 Windows 启动成功。

## 自动化验证范围

- 沿用现有 DOM 翻译、切换、账号与代码保护、ASAR 重建和 macOS 回归测试。
- Windows 安装器覆盖：只读检查、完整备份、安装 / 还原往返、重复操作、版本与架构拒绝、备份损坏、应用更新、文件占用、空间不足、复制与替换失败、替换后中断、资源缺失及应用目录缺失恢复。
- 验证中文与空格路径、硬链接、符号链接及并发操作保护。
- Windows 主机额外执行实际进程枚举、目录联接拒绝、内置 Python 和启动脚本检查。
- 在 macOS 上用官方 Windows 解包文件进行资源修改及逐文件还原验证；操作系统与进程检查在这项测试中被替代，不能视作 Windows 原生验证。

官方文件往返验证结果：423 个应用文件中仅 `resources/app.asar` 发生变化，ASAR 内另外 737 个已打包文件内容不变；还原后所有应用文件的大小与 SHA-256 均与原版一致，主程序 SHA-256 始终不变。

2026-10-11 [GitHub Actions 验证](https://github.com/TeacherXuAI/antigravity-zh-cn/actions/runs/38135086832)已通过，代码提交为 `cb936364709aa14ac37fd3d3bcc58232df0d0326`：

| 环境 | 结果 |
| --- | --- |
| Windows 托管主机 | 8 项 DOM 测试、41 项 Python 测试全部通过 |
| Windows 测试 ZIP | 内置 Python 执行 30 项 Windows 测试通过；含中文、空格和 `&` 的路径中启动脚本检查通过 |
| macOS / Ubuntu 托管主机 | 各 45 项测试通过；4 项 Windows 原生检查按平台跳过 |
| 构建一致性 | 三个平台构建的翻译脚本一致，未改变已发布翻译内容 |

CI 的 Windows 执行环境是 GitHub 托管主机，不能代替普通用户的 Windows 11 桌面实测，也不能验证 SmartScreen、账号登录或界面效果。

## 待实机验证

详见 [Windows 实机验收记录](WINDOWS-TEST-RECORD.md)。正式发布前必须补充真实 Windows 环境、原版与汉化对比、启动和还原结果；不使用 macOS 截图代替 Windows 证据。
