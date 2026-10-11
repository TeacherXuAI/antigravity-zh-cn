# Antigravity 简体中文汉化补丁 · Windows 测试版

**测试编号：0.2.0-windows-test.1。目标环境：Windows 11 x64 / Antigravity Desktop 2.22.0。**

本包用于发布前的实机验证，尚未完成 Windows 桌面启动、界面效果和完整使用流程测试。当前正式版仍为 macOS v0.1.1；请勿将本包标注为 Windows 正式版。

## 测试范围

| 项目 | 范围 |
| --- | --- |
| 系统 | Windows 11，Intel / AMD x64 处理器 |
| 应用 | Google Antigravity **Desktop 2.22.0**，仅接受已核对的官方文件指纹 |
| 功能 | 环境检查、完整原版备份、汉化安装、中英文切换、原版还原 |
| 翻译 | 沿用现有 92 条译文，目标为常用设置与固定导航；Windows 实际覆盖待验证 |
| 未覆盖 | Windows 10、Windows Server、ARM64、Antigravity IDE、其他应用版本 |

## 1. 准备测试环境

1. 从 [Google 官网](https://antigravity.google/download) 安装 Antigravity Desktop。请确认是 **2.22.0、Windows x64**；不要选择页面下方的 Antigravity IDE。如果官网版本已更新，本补丁会停止安装，先反馈版本号即可。
2. 先打开原版，完成必要的登录和初始化，确认能够正常进入设置。汉化补丁不处理账号资格、登录失败、模型权限或额度问题。
3. 完全退出 Antigravity，包括托盘中的应用；关闭其安装、卸载和更新程序。
4. 将测试 ZIP **全部解压到本地磁盘**，不要直接在压缩包内运行，不要放在云盘同步目录、网络盘或 Antigravity 安装目录内。

测试 ZIP 内置来自 [Python 官方](https://www.python.org/downloads/release/python-31316/)的 x64 运行环境及许可证，无需另外安装 Python、Node.js 或 npm。使用 Git 源码目录时，可自行安装 Python 3.9+ x64，并通过命令行运行。

## 2. 检查应用状态

双击 **`Windows-Start.cmd`**，选择 **「1. 检查环境与备份」**。

工具会查找常见安装位置和注册表中的安装路径。如果未找到或检测到多个目录，请选择或输入含有 `Antigravity.exe` 的文件夹。

首次检查应显示 `application_state: original`、`patched: false`。`native_ui_tested: false` 表示本测试版本尚未完成实机验收，不是检查失败。

检查命令只读取应用和已有备份，不会安装补丁。运行中如果提示版本或文件指纹不匹配，请保留提示，不要修改校验值强行安装。

## 3. 备份原版

选择 **「2. 备份原版」**。工具将复制整个应用安装目录，记录所有文件的 SHA-256、大小和目录结构，并复核源文件在复制过程中没有变化。

备份位于安装目录旁，例如：

```text
C:\Users\你的用户名\AppData\Local\Programs\Antigravity
C:\Users\你的用户名\AppData\Local\Programs\Antigravity.zh-cn-backup
```

备份目录中的 `original` 是原版应用，`manifest.json` 是校验和恢复记录。请保留整个备份目录，不要移动、编辑或启动其中的程序。重复备份会校验已有备份，不会覆盖它。

请预留至少原应用大小两倍的剩余磁盘空间。应用旁可能保留 `Antigravity.zh-cn.lock`，它只用于防止两个工具同时操作；程序退出后系统会释放锁。

## 4. 安装汉化补丁

选择 **「3. 安装汉化」**，阅读提示后输入 **`INSTALL`**。

未手动备份时，安装器会先完成同样的完整备份。然后在临时文件中构建、校验汉化资源，最后替换 `resources/app.asar`。如果文件被占用、权限不足或应用在准备期间发生变化，安装会停止。

安装器不自动提权。如果应用装在需要管理员权限的目录中，请先记录权限提示；首轮测试建议使用当前用户可写的安装目录。不要通过关闭 Defender、SmartScreen 或单位安全策略来继续测试。

## 5. 验证实际效果

从原来的快捷方式启动 Antigravity，依次检查：

1. 应用能正常打开，登录状态和已有会话保留。
2. 设置中的通用、应用、外观、模型与用量页面显示目标中文译文。
3. 右下角 **「中文 · 开」** 可以关闭汉化，重新点击可以恢复中文。
4. 退出再打开后，中文默认开启。
5. 项目名称、账号、输入框、聊天内容和代码没有被误译。

第一次启动时请记录任何错误提示。截图或录像应展示真实 Windows 窗口，公开前遮住账号区域。验收表见 `docs/WINDOWS-TEST-RECORD.md`。

## 6. 还原原版

完全退出 Antigravity，重新运行 `Windows-Start.cmd`，选择 **「4. 还原原版」**，输入 **`RESTORE`**。

还原会先校验完整备份，再确认应用除汉化资源之外没有其他变化，最后恢复原资源并逐文件核对。整个应用目录缺失时，也可从完整备份恢复。原版备份在还原成功后仍会保留，以便核验和再次测试。

**如果应用已自动更新或文件发生其他变化，还原会停止，避免用旧版覆盖现有文件。** 请保留备份和报错；不要把旧备份直接覆盖到新版上。账号和聊天数据不在本工具的备份范围内，它们不会被本工具修改。

如果安装过程中意外关闭工具，重新打开后先执行检查，再执行还原。只有原版或已记录的汉化文件会被识别；无法确认的文件状态会停止操作并保留备份。

## 文件与安全说明

- 安装只修改 `resources/app.asar` 中的翻译入口，主程序、DLL 和其他应用文件保持原样。
- 不修改 Electron fuses，不关闭系统安全检查，不修改注册表，不启用调试端口，不读取账号凭据或上传数据。
- 已核对的官方 Windows 2.22.0 包没有启用 Electron 的嵌入式 ASAR 完整性验证，本工具保持原配置不变。未来版本若开启该校验，会停止适配，不会自动关闭它。
- 本次下载的官方安装 EXE 带签名，但解包后的 `Antigravity.exe` 没有内嵌 Authenticode 证书表。因此 Windows 安装器以已核对的主程序及资源 SHA-256 严格匹配，不声称对原应用做了 Windows 信任链验证。补丁也不会添加或替换签名。
- 原子替换及恢复记录用于减少中断影响；突然断电、磁盘故障和安全软件隔离仍需要单独排查，不能由自动化测试保证。
- 测试包包含本项目代码、文档和带原许可证的 Python 运行环境，不包含 Google 应用文件或其解包源码。

## 命令行用法

在解压目录打开 PowerShell，以实际安装路径替换示例：

```powershell
.\runtime\python.exe -I -X utf8 .\tools\windows_patcher.py doctor --app "C:\Users\你的用户名\AppData\Local\Programs\Antigravity"
.\runtime\python.exe -I -X utf8 .\tools\windows_patcher.py backup --app "C:\Users\你的用户名\AppData\Local\Programs\Antigravity"
.\runtime\python.exe -I -X utf8 .\tools\windows_patcher.py install --accept-test-build --app "C:\Users\你的用户名\AppData\Local\Programs\Antigravity"
.\runtime\python.exe -I -X utf8 .\tools\windows_patcher.py restore --app "C:\Users\你的用户名\AppData\Local\Programs\Antigravity"
```

Git 源码目录中没有 `runtime`，可将命令开头替换为 `py -3 -X utf8`，并去掉 `-I`。

## 问题反馈

请记录 Windows 版本、CPU 架构、Antigravity 版本、执行步骤和完整报错。不需要提供账号密码、登录令牌或聊天记录。路径中如包含真实姓名，公开反馈前可自行遮挡。

项目：[TeacherXuAI/antigravity-zh-cn](https://github.com/TeacherXuAI/antigravity-zh-cn)。维护者：徐老师AI。
