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
