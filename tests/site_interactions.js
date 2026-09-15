/* Exercise the shipped enhancement with controlled browser capabilities. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const script = fs.readFileSync(path.join(__dirname, '../site/assets/site.js'), 'utf8');
const baseline = fs.readFileSync(path.join(__dirname, '../templates/baseline.md'), 'utf8');

function scenario(clipboard, rule = 'context') {
  const events = {};
  const source = {
    value: baseline,
    focus() { this.focused = true; },
    select() { this.selected = true; },
  };
  const fallback = { hidden: true, querySelector: () => source };
  const status = { textContent: '' };
  const section = { querySelector: name => name === '[data-copy-status]' ? status : fallback };
  const button = {
    hidden: true,
    addEventListener(name, callback) { events[name] = callback; },
    closest() { return { parentElement: section }; },
  };
  const locale = { href: `https://example.test/agents-md-lab/ko/rules/${rule}/index.html#${rule}` };
  const location = { hash: '#why' };
  const context = {
    document: {
      body: { dataset: { copySuccess: 'Copied.', copyFailure: 'Select or download.' } },
      querySelectorAll: () => [button],
      querySelector: () => locale,
    },
    navigator: { clipboard },
    window: { addEventListener(name, callback) { events[name] = callback; } },
    location,
    URL,
  };
  vm.runInNewContext(script, context);
  return { events, source, fallback, status, button, locale, location };
}

(async () => {
  let copied;
  const success = scenario({ writeText: async value => { copied = value; } });
  assert.equal(success.button.hidden, false);
  await success.events.click();
  assert.equal(copied, baseline, 'Copy preserves the entire canonical English file.');
  assert.equal(success.status.textContent, 'Copied.');
  assert.equal(success.fallback.hidden, true);

  for (const clipboard of [undefined, { writeText: async () => { throw new Error('denied'); } }]) {
    const failed = scenario(clipboard);
    await failed.events.click();
    assert.equal(failed.status.textContent, 'Select or download.');
    assert.equal(failed.fallback.hidden, false);
    assert.equal(failed.source.focused, true);
    assert.equal(failed.source.selected, true);
    assert.equal(failed.source.value, baseline);
  }

  for (const [state, rule] of [[success, 'context'], [scenario(undefined, 'r1'), 'r1']]) {
    assert.equal(new URL(state.locale.href).hash, '#why');
    state.location.hash = '#example';
    state.events.hashchange();
    assert.equal(new URL(state.locale.href).hash, '#example');
    state.location.hash = '';
    state.events.hashchange();
    assert.equal(new URL(state.locale.href).hash, '');
    assert.equal(new URL(state.locale.href).pathname, `/agents-md-lab/ko/rules/${rule}/index.html`);
  }
  console.log('PASSED: exact clipboard content, denial/unavailable fallback, live locale anchors.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
