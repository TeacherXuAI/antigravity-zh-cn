/* TeacherXuAI Antigravity Chinese UI, MIT. No network or application API access. */
(function () {
  'use strict';
  const dictionary = {"Accent": "强调色", "Advanced Settings": "高级设置", "Agent Behavior": "智能体行为", "Always Ask": "始终询问", "App version": "应用版本", "Appearance": "外观", "Application": "应用", "Automatic Check for Updates": "自动检查更新", "Automatically prompt you to restart the app when a new update is available. When disabled, you can check for updates manually from the app menu.": "发现新版本时，自动提示重启应用。关闭后，可从应用菜单手动检查更新。", "Automations": "自动化", "Background": "背景", "Browser": "浏览器", "Browser Actuation Rules": "浏览器操作规则", "Browser Javascript Execution Policy": "浏览器 JavaScript 执行策略", "Chat Settings": "聊天设置", "Claude and GPT models": "Claude 和 GPT 模型", "Close": "关闭", "Configure agent execution, queued message delivery, and permissions.": "配置智能体执行、排队消息的发送方式和权限。", "Configure allowed and denied URLs for browser actuation.": "配置允许和禁止浏览器操作的网址。", "Configure allowed and denied URLs for reading.": "配置允许和禁止读取的网址。", "Configure global allowed and denied resource permissions.": "配置全局允许和禁止访问的资源。", "Configure the agent's visual theme and display preferences.": "配置智能体界面的主题和显示偏好。", "Configure the browser subagent. It requires": "配置浏览器子智能体，需要安装", "Configure the maximum width of the conversation panel.": "设置对话面板的最大宽度。", "Configure when follow-up messages are sent.": "设置后续消息何时发送。", "Contrast": "对比度", "Controls the actions the agent can take.": "控制智能体可以执行的操作。", "Controls whether the agent can run custom JavaScript to automate complex browser actions.": "控制智能体是否可以运行自定义 JavaScript 来自动完成复杂的浏览器操作。", "Conversation History": "对话历史", "Conversation Width": "对话宽度", "Conversations": "对话", "Customizations": "自定义配置", "Dark Theme": "深色主题", "Default": "默认", "Default Dark": "默认深色", "Default Light": "默认浅色", "Display and preserve intermediate thinking steps.": "显示并保留中间思考步骤。", "Edit": "编辑", "Enable AI Credit Overages": "配额用尽后允许使用 AI 点数", "Enable Remote Control": "启用远程控制", "Execution": "执行", "Five Hour Limit Remaining": "五小时剩余额度", "Foreground": "前景", "Gemini Models": "Gemini 模型", "General": "通用", "Global Permissions": "全局权限", "Keep In Menu Bar": "保留在菜单栏", "Keep the app accessible from the menu bar and running in the background when all windows are closed.": "关闭所有窗口后，应用仍在后台运行，可从菜单栏访问。", "Keyboard shortcuts": "键盘快捷键", "Learn more": "了解更多", "Light Theme": "浅色主题", "Manage Antigravity app settings.": "管理 Antigravity 应用设置。", "Manage your model quota and credits.": "管理模型配额和点数。", "Model Credits": "模型点数", "Models": "模型", "Models & Usage": "模型与用量", "Modify permissions for file, terminal, and MCP tools.": "修改文件、终端和 MCP 工具的权限。", "Narrow": "窄", "Network Access Rules": "网络访问规则", "New Conversation": "新建对话", "Not in Project": "未选择项目", "Notification Settings": "通知设置", "Notifications": "通知", "Open": "打开", "Open System Preferences": "打开系统设置", "Permission Preset": "权限预设", "Plan": "订阅套餐", "Plan Review Policy": "计划审核策略", "Preset": "预设", "Prevent Sleep": "防止休眠", "Prevent the computer from sleeping while the app is running.": "应用运行时，防止电脑进入休眠。", "Provide Feedback": "提交反馈", "Queued Messages": "排队消息", "Remote Control": "远程控制", "Request Review": "请求审核", "Settings": "设置", "Shortcuts": "快捷键", "Strong": "高对比度", "Theme": "主题", "To modify notification settings, open your operating system's system preferences.": "要修改通知设置，请打开操作系统的系统设置。", "Tool Permissions": "工具权限", "Upgrade": "升级", "Verbose Agent Chat": "显示详细执行过程", "Version": "版本", "Weekly Limit Remaining": "本周剩余额度", "When toggled on, Antigravity will use your AI credits to fulfill model requests once you're out of model quota. Antigravity will always use your model quota first before using AI credits.": "开启后，模型配额用尽时，Antigravity 会使用你的 AI 点数继续处理请求。始终优先使用模型配额，再使用 AI 点数。", "Whether the agent asks you to review its documents.": "设置智能体是否请你审核其文档。", "Wide": "宽", "Work with local agents from another device.": "从其他设备使用本机智能体。", "You can upgrade to a Google AI Ultra plan to receive higher rate limits.": "升级到 Google AI Ultra 套餐可获得更高的使用额度。", "Your Plan:": "当前套餐：", "to be installed. The browser subagent can be invoked by typing /browser in the conversation input box.": "。在对话输入框中输入 /browser 可调用浏览器子智能体。"};
  const VERSION = '0.1.1';
  const KEY = '__teacherxu_antigravity_zh__';
  if (window[KEY]) return;
  // The native application serves its UI locally. Never translate sign-in sites.
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const SKIP = 'script,style,pre,code,textarea,input,[contenteditable],iframe,webview,' +
    '[data-no-translate],[translate="no"],[data-antigravity-zh-control],.monaco-editor';
  const records = new Map();
  let enabled = true;
  let scheduled = false;
  let disposed = false;
  let control;
  let observer;
  let settingsRoot;
  const normalize = value => value.trim().replace(/\s+/g, ' ');
  const english = node => {
    const record = records.get(node);
    return record && node.nodeValue === record.translated ? record.original : node.nodeValue;
  };
  function originalText(element) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    let result = '', node;
    while ((node = walker.nextNode())) result += english(node);
    return normalize(result);
  }
  function protectedNode(node) {
    const element = node.nodeType === 1 ? node : node.parentElement;
    if (!element || element.closest(SKIP)) return true;
    // Settings' account button contains user data and is not UI copy.
    const button = element.closest('button');
    return !!(button && /[^\s]+@[^\s]+/.test(button.textContent));
  }
  function translateNode(node) {
    if (protectedNode(node)) return;
    const current = node.nodeValue;
    const previous = records.get(node);
    if (previous && current === previous.translated) return;
    records.delete(node); // React may reuse a text node for a new label.
    const key = normalize(current);
    if (!Object.hasOwn(dictionary, key)) return;
    const translated = current.replace(/\S[\s\S]*\S|\S/, dictionary[key]);
    records.set(node, { original: current, translated });
    node.nodeValue = translated;
  }
  function translateTree(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) translateNode(node);
  }
  function findSettings() {
    if (settingsRoot?.isConnected) return settingsRoot;
    // Require the distinctive navigation tabs AND a settings heading. Fail closed.
    const roots = [...document.querySelectorAll('[aria-label="Settings"], [role="dialog"]')];
    for (const heading of document.querySelectorAll('h1')) {
      if (originalText(heading) !== 'Settings') continue;
      let ancestor = heading.parentElement;
      for (let i = 0; ancestor && i < 6; i++, ancestor = ancestor.parentElement) {
        if (ancestor === document.body) break;
        roots.push(ancestor);
      }
    }
    settingsRoot = roots.find(root => {
      const names = [...root.querySelectorAll('button')].map(originalText);
      return ['General', 'Application', 'Appearance'].every(name => names.includes(name)) &&
        [...root.querySelectorAll('h1,h2')].some(h => originalText(h) === 'Settings');
    });
    return settingsRoot;
  }
  const navigation = new Set(['New Conversation', 'Conversation History', 'Automations',
    'Customizations', 'Settings']);
  function scan() {
    if (disposed || !enabled || !document.body) return;
    observer.disconnect();
    try {
      for (const node of records.keys()) if (!node.isConnected) records.delete(node);
      const root = findSettings();
      if (root) {
        const supported = ['General', 'Application', 'Appearance', 'Models & Usage'];
        const headings = [...root.querySelectorAll('h2')].map(originalText);
        if (headings.some(name => supported.includes(name))) translateTree(root);
        else {
          // Other settings screens can contain user-authored skills and project names.
          for (const el of root.querySelectorAll('button,h1')) {
            if (['Settings', 'General', 'Application', 'Appearance', 'Models',
              'Conversations', 'Shortcuts', 'Provide Feedback'].includes(originalText(el))) translateTree(el);
          }
        }
      }
      // Only explicitly named global navigation controls; never project names/history.
      const sidebar = document.querySelector('[aria-label="Sidebar"]');
      if (sidebar) {
        for (const el of sidebar.querySelectorAll('button,a')) {
          const label = el.getAttribute('aria-label');
          const href = el.getAttribute('href');
          const knownLink = el.tagName === 'A' && ['/', '/history', '/customizations'].includes(href);
          if ((label && navigation.has(label)) || (knownLink && navigation.has(originalText(el)))) translateTree(el);
        }
      }
    } finally {
      observe();
    }
  }
  function observe() {
    if (!disposed && enabled && document.body) observer.observe(document.body, {
      childList: true, subtree: true, characterData: true
    });
  }
  function schedule() {
    if (scheduled || disposed || !enabled) return;
    scheduled = true;
    window.requestAnimationFrame(() => { scheduled = false; scan(); });
  }
  function restore() {
    observer?.disconnect();
    for (const [node, record] of records) {
      // Do not revert text updated by the application after our last scan.
      if (node.isConnected && node.nodeValue === record.translated) node.nodeValue = record.original;
    }
    records.clear();
  }
  function setEnabled(value) {
    enabled = !!value;
    if (enabled) { scan(); observe(); } else restore();
    if (control) {
      control.textContent = enabled ? '中文 · 开' : '中文 · 关';
      control.setAttribute('aria-pressed', String(enabled));
    }
  }
  function init() {
    if (disposed || !document.body) return;
    observer = new MutationObserver(schedule);
    control = document.createElement('button');
    control.type = 'button';
    control.dataset.antigravityZhControl = VERSION;
    control.title = '徐老师AI 汉化：点击切换中英文；重启默认开启';
    control.setAttribute('aria-label', '切换界面汉化');
    control.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483647;' +
      'font:12px system-ui;padding:6px 10px;border:1px solid #aaa;border-radius:20px;' +
      'background:#fff;color:#222;cursor:pointer;box-shadow:0 2px 8px #0002';
    control.addEventListener('click', () => setEnabled(!enabled));
    document.body.appendChild(control);
    setEnabled(true);
  }
  window[KEY] = Object.freeze({
    version: VERSION,
    setEnabled,
    refresh: scan,
    dispose() {
      disposed = true;
      restore();
      control?.remove();
      document.removeEventListener('DOMContentLoaded', init);
      delete window[KEY];
    }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
