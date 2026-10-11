# 实机截图与前后对比

日期：2026-10-11。环境：macOS 26.5.2，Apple Silicon，Google Antigravity Desktop 2.22.0，汉化补丁 v0.1.0。

## 截图采集方法

1. 在本机已安装的 Antigravity 原生窗口中，打开通用、应用、外观设置，分别截取中文状态。
2. 关闭设置弹窗，点击右下角「中文 · 开」关闭汉化，再进入相同页面截取英文状态。
3. 采集过程中不改变页面中的设置值；完成后恢复中文开启。
4. 公开单图保留完整 1400 × 900 窗口，只在左下角账号区域加实色块。单图经解码后的 RGB 像素逐一检查，遮挡区域外差异为 0；导出 PNG 时移除截图元数据。
5. 对比图将两张处理后的截图按原尺寸并排放置，标题与说明位于截图之外。没有 AI 重绘、文字补画或界面复刻。

**“前后”表示同一份已打补丁的应用中，汉化开关关闭与开启的状态。** 此次未为了拍图重新卸载补丁；安装、重启、完整还原的测试证据另见 [验证记录](VALIDATION.md)。截图只证明这些页面在该环境中的实际显示，不代表完整界面、其他版本或其他操作系统均已支持。

v0.1.1 仅修订文档与版本标识，沿用以下 v0.1.0 实机截图。翻译范围与界面显示逻辑未变。

## 应用设置

版本号 2.22.0、菜单栏开关开启、防止休眠和远程控制关闭，前后保持一致。

[![应用设置实机对比](images/application-comparison.png)](images/application-comparison.png)

[英文完整窗口](images/application-en.png) · [中文完整窗口](images/application-zh.png)

## 通用设置

执行、权限和计划审核的词库命中项显示中文。Queue、Send Immediately 及部分浏览器说明仍为英文，图片保留实际结果。

[![通用设置实机对比](images/general-comparison.png)](images/general-comparison.png)

[英文完整窗口](images/general-en.png) · [中文完整窗口](images/general-zh.png)

## 外观设置

主题标签与说明显示中文；颜色值与原有英文代码示例保留原样。这里只翻译界面文本，不翻译代码内容。

[![外观设置实机对比](images/appearance-comparison.png)](images/appearance-comparison.png)

[英文完整窗口](images/appearance-en.png) · [中文完整窗口](images/appearance-zh.png)

## 图片文件与处理记录

共 6 张账号已遮挡的单图与 3 张并排对比图。公开图片的 SHA-256、遮挡矩形和逐像素检查结果见 [manifest.json](images/manifest.json)。含账号的原始截图不公开分发。

截图中的 Antigravity 界面归其权利方所有，仅用于说明社区补丁的实际效果。
