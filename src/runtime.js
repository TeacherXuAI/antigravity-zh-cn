/* TeacherXuAI Antigravity Chinese UI, MIT. No network or application API access. */
(function () {
  'use strict';
  const dictionary = /*__DICTIONARY__*/ {};
  const VERSION = '0.1.1';
  const KEY = '__teacherxu_antigravity_zh__';
  if (window[KEY]) return;
  // The native application serves its UI locally. Never translate sign-in sites.
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const SKIP = 'script,style,pre,code,textarea,input,[contenteditable],iframe,webview,' +
    '[data-no-translate],[translate="no"],[data-antigravity-zh-control],.monaco-editor,' +
    '[data-sidebar-row-id],[data-tooltip-id$="-name"],[data-testid^="automation-card-"],' +
    '[data-testid="project-selector-item"],[data-model-base],[data-harness],[data-mention-menu]';
  const records = new Map();
  const placeholderRecords = new Map();
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
  function formatLimitName(raw) {
    const lower = raw.trim().toLowerCase();
    if (lower === 'weekly' || lower === 'weekly limit') return '本周额度';
    if (lower === '5-hour' || lower === '5 hour' || lower === 'five-hour' || lower === 'five hour') return ' 5 小时额度';
    if (lower === 'daily' || lower === 'daily limit') return '今日额度';
    if (lower === 'hourly' || lower === 'hourly limit') return '每小时额度';
    if (lower === 'monthly' || lower === 'monthly limit') return '本月额度';
    return `${raw.trim()}额度`;
  }
  function formatDuration(raw) {
    return raw.trim()
      .replace(/less than a minute|<1m/gi, '不到 1 分钟')
      .replace(/(\d+)\s*days?/gi, '$1 天')
      .replace(/(\d+)\s*hours?/gi, '$1 小时')
      .replace(/(\d+)\s*(?:minutes?|mins?)/gi, '$1 分钟')
      .replace(/(\d+)\s*(?:seconds?|secs?)/gi, '$1 秒')
      .replace(/(\d+)d\b/gi, '$1 天')
      .replace(/(\d+)h\b/gi, '$1 小时')
      .replace(/(\d+)m\b/gi, '$1 分钟')
      .replace(/,\s*and\s+|\s+and\s+|,\s*/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function translateDynamic(key) {
    // Dynamic quota refresh text in Models & Usage:
    // e.g. "You have used some of your weekly limit, it will fully refresh in 3 days, 20 hours."
    // e.g. "You have used some of your 5-hour limit, it will fully refresh in 1 hour, 47 minutes."
    let match = key.match(
      /^You(?:'ve| have) used (some|all|most|\d+%) of your ([^,]+?)(?: limit)?,\s*(?:and )?it will (?:fully )?refresh in (.+?)\.?$/i
    );
    if (match) {
      const amountMap = { some: '部分', all: '全部', most: '大部分' };
      const amount = amountMap[match[1].toLowerCase()] || ` ${match[1]} 的`;
      const limit = formatLimitName(match[2]);
      const duration = formatDuration(match[3]);
      return `你已使用${amount}${limit}，将于 ${duration}后完全恢复。`;
    }
    match = key.match(
      /^You(?:'ve| have) reached your ([^,]+?)(?: limit)?,\s*(?:and )?it will (?:fully )?refresh in (.+?)\.?$/i
    );
    if (match) {
      return `你已达到${formatLimitName(match[1])}上限，将于 ${formatDuration(match[2])}后完全恢复。`;
    }
    match = key.match(/^You (?:have not|haven't) used any of your ([^.]+?)(?: limit)?\.?$/i);
    if (match) {
      return `你尚未使用${formatLimitName(match[1])}。`;
    }
    match = key.match(/^Resets in (.+)$/i);
    if (match) {
      return `将于 ${formatDuration(match[1])}后重置`;
    }
    match = key.match(/^Available AI Credits:\s*(.+)$/i);
    if (match) {
      return `可用 AI 点数：${match[1]}`;
    }
    match = key.match(/^Shared with:\s*(.+)$/i);
    if (match) {
      return `共享配额模型：${match[1]}`;
    }
    match = key.match(/^Show more \((\d+)\)$/i);
    if (match) {
      return `显示更多 (${match[1]})`;
    }
    match = key.match(/^Send feedback as (.+)$/i);
    if (match) {
      return `以 ${match[1]} 的身份发送反馈`;
    }
    match = key.match(/^Show (\d+) breakdowns?$/i);
    if (match) {
      return `展开 ${match[1]} 项明细`;
    }
    match = key.match(/^(\d+) tools?$/i);
    if (match) {
      return `${match[1]} 个工具`;
    }
    match = key.match(/^(\d+) demoted$/i);
    if (match) {
      return `${match[1]} 项已降级`;
    }
    match = key.match(/^(\d+) excluded$/i);
    if (match) {
      return `${match[1]} 项已排除`;
    }
    match = key.match(/^(\d+) tools? excluded$/i);
    if (match) {
      return `已排除 ${match[1]} 个工具`;
    }
    match = key.match(/^(\d+) active conversations?(?: and (\d+) archived conversations?)?$/i);
    if (match) {
      return match[2]
        ? `${match[1]} 个进行中对话和 ${match[2]} 个已归档对话`
        : `${match[1]} 个进行中对话`;
    }
    match = key.match(/^(\d+) archived conversations?$/i);
    if (match) {
      return `${match[1]} 个已归档对话`;
    }
    match = key.match(/^(\d+) models? selected$/i);
    if (match) {
      return `已选择 ${match[1]} 个模型`;
    }
    match = key.match(/^(\d+) active modes?$/i);
    if (match) {
      return `已启用 ${match[1]} 个模式`;
    }
    match = key.match(/^(\d+) files? changed$/i);
    if (match) {
      return `${match[1]} 个文件已修改`;
    }
    return null;
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
    const target = Object.hasOwn(dictionary, key) ? dictionary[key] : translateDynamic(key);
    if (!target) return;
    const translated = current.replace(/\S[\s\S]*\S|\S/, target);
    records.set(node, { original: current, translated });
    node.nodeValue = translated;
  }
  function translatePlaceholder(el) {
    if (!el || el.closest('[data-no-translate],[translate="no"],.monaco-editor')) return;
    const current = el.getAttribute('placeholder');
    if (!current) return;
    const previous = placeholderRecords.get(el);
    if (previous && current === previous.translated) return;
    placeholderRecords.delete(el);
    const key = normalize(current);
    if (!Object.hasOwn(dictionary, key)) return;
    const translated = current.replace(/\S[\s\S]*\S|\S/, dictionary[key]);
    placeholderRecords.set(el, { original: current, translated });
    el.setAttribute('placeholder', translated);
  }
  function translateTree(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) translateNode(node);
    if (root.nodeType === 1) {
      if (root.matches?.('input[placeholder],textarea[placeholder]')) translatePlaceholder(root);
      for (const el of root.querySelectorAll('input[placeholder],textarea[placeholder]')) {
        translatePlaceholder(el);
      }
    }
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
    'Scheduled Tasks', 'Customizations', 'Settings', 'Provide Feedback']);
  const sidebarTestIds = new Set(['automations-button', 'settings-button',
    'new-conversation-button', 'history-button', 'customizations-button']);
  const sidebarPlaceholders = new Set(['No conversations yet', 'No pinned conversations',
    'Drop to add to group', 'See all']);
  const projectTriggerLabels = new Set(['No Project', 'Select Project', 'Select Workspace',
    'New Workspace', 'No Workspace']);
  const chatInputPlaceholders = new Set(['Ask anything, @ to mention, / for actions', 'Ask anything']);
  const historySafeTexts = new Set(['Conversation History',
    'Manage and revisit your past agent sessions.', 'Active', 'Archived', 'Select', 'Done',
    'Select all', 'Deselect all', 'Archive', 'Unarchive', 'Delete', 'Show more',
    'No matching conversations.', 'No archived conversations.', 'No conversations yet.']);
  const overviewSafeTexts = new Set(['Overview', 'Review', 'Files', 'Terminal', 'Plugins',
    'Subagents', 'Background Tasks', 'Goals', 'Documents', 'Artifacts', 'Links',
    'Modified Files', 'Uploads', 'Extensions', 'No subagents', 'No links', 'No uploads',
    'No plugins available', 'Needs attention', 'Approve', 'Deny', 'Blocked, needs input']);
  function scan() {
    if (disposed || !enabled || !document.body) return;
    observer.disconnect();
    try {
      for (const node of records.keys()) if (!node.isConnected) records.delete(node);
      for (const el of placeholderRecords.keys()) if (!el.isConnected) placeholderRecords.delete(el);
      const root = findSettings();
      if (root) {
        const supported = ['General', 'Application', 'Appearance', 'Models & Usage',
          'Shortcuts', 'Account', 'Provide Feedback', 'Customizations',
          'Workspaces', 'Projects', 'Not in Project'];
        const headings = [...root.querySelectorAll('h2')].map(originalText);
        if (headings.some(name => supported.includes(name))) translateTree(root);
        else {
          // Other settings screens can contain user-authored skills and project names.
          for (const el of root.querySelectorAll('button,h1,h2')) {
            if (['Settings', 'General', 'Application', 'Appearance', 'Models',
              'Conversations', 'Shortcuts', 'Provide Feedback', 'Account',
              'Customizations', 'Workspaces', 'Projects', 'Not in Project'].includes(originalText(el))) translateTree(el);
          }
        }
      }
      // Only explicitly named global navigation controls; never project names/history.
      const sidebar = document.querySelector('[aria-label="Sidebar"]');
      if (sidebar) {
        for (const el of sidebar.querySelectorAll('button,a')) {
          const label = el.getAttribute('aria-label');
          const href = el.getAttribute('href');
          const testId = el.getAttribute('data-testid');
          const text = originalText(el);
          const knownLink = el.tagName === 'A' && ['/', '/history', '/customizations'].includes(href);
          if ((label && navigation.has(label)) || (knownLink && navigation.has(text)) ||
            (testId && sidebarTestIds.has(testId)) || text === 'Provide Feedback') translateTree(el);
        }
        for (const el of sidebar.querySelectorAll('[data-testid="section-header"] h2')) {
          translateTree(el);
        }
        for (const el of sidebar.querySelectorAll('span')) {
          if (!el.closest('[data-sidebar-row-id]') && sidebarPlaceholders.has(originalText(el))) {
            translateTree(el);
          }
        }
      }
      // Project selector trigger on home / chat view (only UI placeholder states, never project names).
      for (const el of document.querySelectorAll('[data-testid="project-selector-trigger"]')) {
        if (projectTriggerLabels.has(originalText(el))) translateTree(el);
      }
      // Chat input box (Lexical editor content is protected by [contenteditable] in SKIP).
      for (const el of document.querySelectorAll('[data-testid="agent-input-box"]')) {
        translateTree(el);
      }
      for (const el of document.querySelectorAll('p.pointer-events-none')) {
        if (chatInputPlaceholders.has(originalText(el))) translateTree(el);
      }
      // Changed files summary bar in conversation view (only the header bar, never expanded file paths).
      for (const el of document.querySelectorAll('.files-changed-header,[data-testid="cleared-step-notice"]')) {
        translateTree(el);
      }
      // Portal dropdown menus, select popups, popovers, and tooltips (e.g. Permission preset menu, Model selector, Add Context menu, Select dropdowns).
      for (const el of document.querySelectorAll('.z-\\[6000\\],[role="menu"],[data-select-popup],[role="tooltip"]')) {
        translateTree(el);
      }
      // Right-side Overview panel (only known UI labels, never file/artifact names).
      for (const panel of document.querySelectorAll('[data-testid="overview-panel"]')) {
        for (const el of panel.querySelectorAll('span,button,div')) {
          if (el.children.length === 0 && overviewSafeTexts.has(originalText(el))) {
            translateTree(el);
          }
        }
      }
      // Automations view in main pane.
      for (const el of document.querySelectorAll(
        '[data-testid="cloud-triggers-view"],[data-testid="trigger-InlineCreator"],[data-testid="automation-detail-view"]'
      )) {
        translateTree(el);
      }
      // Standalone Customizations view in main pane (/customizations).
      if (location.pathname === '/customizations') {
        for (const h2 of document.querySelectorAll('h2')) {
          if (originalText(h2) === 'Customizations') {
            const panel = h2.closest('.max-w-2xl')?.parentElement || h2.parentElement;
            if (panel) translateTree(panel);
          }
        }
      }
      // Conversation History view (/history and home history section), excluding conversation rows.
      for (const input of document.querySelectorAll('input[placeholder]')) {
        const record = placeholderRecords.get(input);
        const rawPlaceholder = record ? record.original : input.getAttribute('placeholder');
        if (rawPlaceholder && normalize(rawPlaceholder) === 'Search conversations...') {
          translatePlaceholder(input);
          const container = input.closest('.max-w-3xl,.max-w-2xl') || input.parentElement?.parentElement?.parentElement;
          if (container) {
            for (const el of container.querySelectorAll('h1,p,button,span')) {
              if (!el.closest('[role="button"]') && historySafeTexts.has(originalText(el))) {
                translateTree(el);
              }
            }
          }
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
    for (const [el, record] of placeholderRecords) {
      if (el.isConnected && el.getAttribute('placeholder') === record.translated) {
        el.setAttribute('placeholder', record.original);
      }
    }
    placeholderRecords.clear();
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
