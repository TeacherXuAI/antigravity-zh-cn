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
