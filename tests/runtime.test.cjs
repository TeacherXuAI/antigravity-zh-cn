const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('jsdom');
const dictionary = JSON.parse(fs.readFileSync('locales/zh-CN.json','utf8'));
const source = fs.readFileSync('src/runtime.js','utf8').replace('/*__DICTIONARY__*/ {}',JSON.stringify(dictionary));
const html = `<aside aria-label="Sidebar"><a href="/">New Conversation</a><button aria-label="Settings">Settings</button><button>General</button></aside>
<main><div id="chat">Settings</div><pre>General</pre><textarea>Appearance</textarea></main>
<section aria-label="Settings"><h1>Settings</h1><nav><button>General</button><button>Application</button><button>Appearance</button></nav><article><h2>General</h2><p id="copy">Global Permissions</p><button id="account"><span>General</span><span>person@example.invalid</span></button><pre>Settings</pre><code>Default</code><input value="General"><div contenteditable="true">Settings</div><div translate="no">General</div><div data-no-translate>Settings</div></article></section>`;
function create(body=html,url='http://127.0.0.1:12345/') {
 const dom=new JSDOM(body,{url,runScripts:'outside-only',pretendToBeVisual:true});
 dom.window.eval(source);
 dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
 const close = dom.window.close.bind(dom.window);
 dom.window.close = () => { dom.window.__teacherxu_antigravity_zh__?.dispose(); close(); };
 return dom;
}
const wait = () => new Promise(r=>setTimeout(r,60));
test('translates settings and named navigation but leaves chat, code, account and input untouched',()=>{
 const dom=create(), d=dom.window.document;
 assert.equal(d.querySelector('h1').textContent,'设置');
 assert.equal(d.querySelector('#copy').textContent,'全局权限');
 assert.equal(d.querySelector('aside a').textContent,'新建对话');
 assert.equal(d.querySelector('aside button:last-child').textContent,'General');
 assert.equal(d.querySelector('#chat').textContent,'Settings');
 assert.equal(d.querySelector('#account span').textContent,'General');
 assert.equal(d.querySelector('article pre').textContent,'Settings');
 assert.equal(d.querySelector('article code').textContent,'Default');
 assert.equal(d.querySelector('input').value,'General');
 assert.equal(d.querySelector('[contenteditable]').textContent,'Settings');
 assert.equal(d.querySelector('[translate="no"]').textContent,'General');
 dom.window.close();
});
test('toggle and dispose restore exact whitespace and all original text',()=>{
 const dom=create(html.replace('id="copy">Global Permissions','id="copy">  Global Permissions  ')), w=dom.window,d=w.document;
 assert.equal(d.querySelector('#copy').textContent,'  全局权限  ');
 w.__teacherxu_antigravity_zh__.setEnabled(false);
 assert.equal(d.querySelector('#copy').textContent,'  Global Permissions  ');
 w.__teacherxu_antigravity_zh__.setEnabled(true);
 assert.equal(d.querySelector('#copy').textContent,'  全局权限  ');
 w.__teacherxu_antigravity_zh__.dispose();
 assert.equal(d.querySelector('h1').textContent,'Settings');
 assert.equal(d.querySelector('[data-antigravity-zh-control]'),null);
 dom.window.close();
});
test('handles React text updates, new nodes, and removed settings panels', async()=>{
 const dom=create(), w=dom.window,d=w.document;
 d.querySelector('#copy').firstChild.nodeValue='Remote Control';
 await wait();
 assert.equal(d.querySelector('#copy').textContent,'远程控制');
 const p=d.createElement('p');p.textContent='Prevent Sleep';d.querySelector('article').append(p);
 await wait();assert.equal(p.textContent,'防止休眠');
 d.querySelector('section').remove();
 d.querySelector('#chat').textContent='Global Permissions';
 await wait();assert.equal(d.querySelector('#chat').textContent,'Global Permissions');
 dom.window.close();
});
test('does not restore stale data when the app updates text before toggle',()=>{
 const dom=create(),w=dom.window,d=w.document;
 d.querySelector('#copy').textContent='New server value';
 w.__teacherxu_antigravity_zh__.setEnabled(false);
 assert.equal(d.querySelector('#copy').textContent,'New server value');dom.window.close();
});
test('does not translate unrelated dialogs or sign-in websites',()=>{
 const dom=create('<div role="dialog"><h1>Settings</h1><p>General</p></div>');
 assert.equal(dom.window.document.querySelector('p').textContent,'General');dom.window.close();
 const auth=create(html,'https://accounts.google.com/');
 assert.equal(auth.window.document.querySelector('h1').textContent,'Settings');
 assert.equal(auth.window.__teacherxu_antigravity_zh__,undefined);auth.window.close();
});
test('does not translate custom skill names on Conversations settings screen',()=>{
 const dom=create(html.replace('<h2>General</h2>','<h2>Conversations</h2>').replace('id="copy">Global Permissions','id="copy">Default'));
 assert.equal(dom.window.document.querySelector('#copy').textContent,'Default');dom.window.close();
});
test('installing payload twice creates only one switch',()=>{
 const dom=create();dom.window.eval(source);
 assert.equal(dom.window.document.querySelectorAll('[data-antigravity-zh-control]').length,1);dom.window.close();
});
test('translation dictionary is plain exact-match strings with no markup',()=>{
 for (const [en,zh] of Object.entries(dictionary)) {
  assert.equal(en.trim(),en);assert.equal(typeof zh,'string');assert.ok(zh.length);assert.ok(!/[<>]/.test(zh));
 }
});
test('translates 2.23.0 sidebar sections, testid buttons, project selector, and placeholders while protecting user names',()=>{
 const dom=create(`<aside aria-label="Sidebar">
  <button data-testid="automations-button"><span>Automations</span></button>
  <button data-testid="settings-button"><span>Settings</span></button>
  <div data-testid="section-header"><h2>Projects</h2></div>
  <div data-testid="section-header"><h2>Conversations</h2></div>
  <span>No conversations yet</span>
  <div data-sidebar-row-id="conv-1"><span>No conversations yet</span></div>
 </aside>
 <main>
  <button data-testid="project-selector-trigger"><span>No Project</span></button>
  <button data-testid="project-selector-trigger"><span>General</span></button>
  <p class="pointer-events-none">Ask anything, @ to mention, / for actions</p>
  <div class="max-w-2xl">
   <h1>Conversation History</h1>
   <input placeholder="Search conversations...">
   <div role="button"><span>Conversation History</span></div>
  </div>
 </main>`);
 const w=dom.window,d=w.document;
 assert.equal(d.querySelector('[data-testid="automations-button"]').textContent,'自动化');
 assert.equal(d.querySelector('[data-testid="settings-button"]').textContent,'设置');
 assert.deepEqual([...d.querySelectorAll('[data-testid="section-header"] h2')].map(e=>e.textContent),['项目','对话']);
 assert.equal(d.querySelector('aside > span').textContent,'暂无对话');
 assert.equal(d.querySelector('[data-sidebar-row-id] span').textContent,'No conversations yet');
 const triggers=d.querySelectorAll('[data-testid="project-selector-trigger"]');
 assert.equal(triggers[0].textContent,'未选择项目');
 assert.equal(triggers[1].textContent,'General');
 assert.equal(d.querySelector('p.pointer-events-none').textContent,'尽管提问，输入 @ 引用内容，输入 / 执行操作');
 assert.equal(d.querySelector('main h1').textContent,'对话历史');
 assert.equal(d.querySelector('main input').getAttribute('placeholder'),'搜索对话...');
 assert.equal(d.querySelector('main [role="button"] span').textContent,'Conversation History');
 w.__teacherxu_antigravity_zh__.setEnabled(false);
 assert.equal(d.querySelector('main input').getAttribute('placeholder'),'Search conversations...');
 dom.window.close();
});
test('translates dynamic quota refresh strings, plan description, chat toolbar, and overview panel',()=>{
 const dom=create(`<section aria-label="Settings"><h1>Settings</h1><nav><button>General</button><button>Application</button><button>Appearance</button></nav><article><h2>Models &amp; Usage</h2>
  <p id="plan-desc">You are subscribed to the best Google AI plan.</p>
  <p id="q1">You have used some of your weekly limit, it will fully refresh in 3 days, 20 hours.</p>
  <p id="q2">You have used some of your 5-hour limit, it will fully refresh in 1 hour, 47 minutes.</p>
 </article></section>
 <div data-testid="agent-input-box">
  <div contenteditable="true">Medium</div>
  <button data-testid="model-selector-trigger"><span>Gemini 4 Argon<span class="opacity-70"> Medium</span></span></button>
  <button><span id="mode-turbo">Turbo</span></button>
 </div>
 <div data-testid="overview-panel"><span id="ov-title">Overview</span><span id="ov-file">main.js</span></div>`);
 const w=dom.window,d=w.document;
 assert.equal(d.querySelector('#plan-desc').textContent,'你已订阅最高等级的 Google AI 套餐。');
 assert.equal(d.querySelector('#q1').textContent,'你已使用部分本周额度，将于 3 天 20 小时后完全恢复。');
 assert.equal(d.querySelector('#q2').textContent,'你已使用部分 5 小时额度，将于 1 小时 47 分钟后完全恢复。');
 assert.equal(d.querySelector('[contenteditable]').textContent,'Medium');
 assert.equal(d.querySelector('[data-testid="model-selector-trigger"]').textContent,'Gemini 4 Argon 中');
 assert.equal(d.querySelector('#mode-turbo').textContent,'极速模式（Turbo）');
 assert.equal(d.querySelector('#ov-title').textContent,'概览');
 assert.equal(d.querySelector('#ov-file').textContent,'main.js');
 w.__teacherxu_antigravity_zh__.setEnabled(false);
 assert.equal(d.querySelector('#q1').textContent,'You have used some of your weekly limit, it will fully refresh in 3 days, 20 hours.');
 dom.window.close();
});
test('translates portal dropdown menus and changed files bar while protecting project and model names',()=>{
 const dom=create(`<div class="files-changed-header"><span id="fc-count">1 file changed</span><button class="review-button"><span>Review</span></button></div>
  <div class="z-[6000]">
   <div role="menu">
    <div data-testid="permissions-project-options"><span>Request Review</span><span>Every command requires approval.</span></div>
    <div data-testid="project-selector-item" data-project-name="General"><span>General</span></div>
    <span data-model-base="Default">Default</span>
   </div>
  </div>`);
 const w=dom.window,d=w.document;
 assert.equal(d.querySelector('#fc-count').textContent,'1 个文件已修改');
 assert.equal(d.querySelector('.review-button').textContent,'审查变更');
 assert.equal(d.querySelector('[data-testid="permissions-project-options"]').textContent,'请求审核每条命令都需要你的批准。');
 assert.equal(d.querySelector('[data-testid="project-selector-item"]').textContent,'General');
 assert.equal(d.querySelector('[data-model-base]').textContent,'Default');
 w.__teacherxu_antigravity_zh__.setEnabled(false);
 assert.equal(d.querySelector('#fc-count').textContent,'1 file changed');
 dom.window.close();
});


