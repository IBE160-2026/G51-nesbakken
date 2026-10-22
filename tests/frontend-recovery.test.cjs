// Run with: node --test tests/frontend-recovery.test.cjs
// Execute the real application script. Only browser/map/network boundaries are
// stubbed: these tests cover state and request behaviour, not rendered layout.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'static/app.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'templates/index.html'), 'utf8');
const storageKey = 'jaunt_active_trip';

function browser(storedTrip) {
  const elements = new Map();
  function element() {
    const listeners = new Map();
    return {
      hidden: true, inert: false, dataset: {}, style: {}, children: [],
      classList: { toggle() {} },
      addEventListener(name, fn) { listeners.set(name, fn); },
      click() { listeners.get('click')?.(); },
      appendChild(child) { this.children.push(child); },
      setAttribute() {}, removeAttribute() {}, focus() {}, scrollTo() {},
      getBoundingClientRect() { return { height: 220 }; },
    };
  }
  for (const [, id] of html.matchAll(/\bid="([^"]+)"/g)) elements.set(id, element());
  const topicPills = Array.from(html.matchAll(/class="[^"]*topic-pill[^"]*"[^>]*data-topic="([^"]+)"/g), ([, topic]) => {
    const pill = element();
    pill.dataset.topic = topic;
    return pill;
  });
  elements.get('screen-splash').hidden = false;
  const storage = new Map(storedTrip ? [[storageKey, JSON.stringify(storedTrip)]] : []);
  const requests = [];
  const responses = [];
  class Marker {
    setLngLat() { return this; }
    setPopup() { return this; }
    addTo() { return this; }
    remove() {}
  }
  const context = vm.createContext({
    document: {
      getElementById(id) {
        assert(elements.has(id), `Real template must contain #${id}`);
        return elements.get(id);
      },
      querySelector() { return element(); },
      querySelectorAll(selector) { return selector === '.topic-pill' ? topicPills : []; },
      createElement: element, addEventListener() {}, removeEventListener() {},
    },
    maplibregl: {
      Map: class {
        touchZoomRotate = { disableRotation() {} };
        keyboard = { disable() {} };
        on() {} addControl() {} resize() {}
      },
      NavigationControl: class {}, Marker, Popup: class { setText() { return this; } },
    },
    localStorage: { getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value) },
    console: { error() {} }, setTimeout() {}, clearTimeout() {},
    AbortSignal: { timeout: () => undefined },
    fetch: async (url, options) => {
      assert.equal(url, '/api/plan');
      requests.push(JSON.parse(options.body));
      assert(responses.length, 'Unexpected planning request');
      return responses.shift()();
    },
  });
  vm.runInContext(source, context, { filename: 'static/app.js' });
  const evaluate = code => vm.runInContext(code, context);
  evaluate('dismissSplash()');
  return {
    requests, elements, evaluate,
    seed(trip) { evaluate(`trip = ${JSON.stringify(trip)}; saveActiveTrip(trip);`); },
    saved: () => JSON.parse(storage.get(storageKey)),
    valid: () => evaluate('isValidTrip(JSON.parse(localStorage.getItem(STORAGE_KEY)))'),
    click: id => elements.get(id).click(),
    respond(data, ok = true) { responses.push(() => ({ ok, status: ok ? 200 : 503, json: async () => data })); },
    networkError() { responses.push(() => { throw new Error('Network failed'); }); },
    parseError() { responses.push(() => ({ ok: true, json: async () => { throw new Error('Invalid JSON'); } })); },
    pending() { responses.push(() => new Promise(() => {})); },
    settle: () => new Promise(resolve => setImmediate(resolve)),
  };
}

function stop(id, order) {
  return { id, order, name: `Stop ${id}`, latitude: -33.9, longitude: 151.18,
    topics: ['history'], content: 'Grounded text', attribution: [] };
}
function route(ids = ['a', 'b']) {
  return { schema_version: 1, phase: 'reviewing', setup_step: null,
    starting_point: { lat: -33.9, lng: 151.18, label: 'Test start' },
    available_minutes: 60, topic: 'history', preference: 0.7,
    stops: ids.map((id, index) => stop(id, index + 1)), geometry: [[151.18, -33.9], [151.181, -33.901]],
    total_minutes: 40, unused_minutes: 20, excluded_ids: [] };
}
function success(ids) {
  return { feasible: true, stops: ids.map((id, index) => stop(id, index + 1)), geometry: null,
    total_minutes: 35, unused_minutes: 25 };
}

test('reload during Re-Jaunt keeps inputs/exclusions and never restores rejected stops or fetches', () => {
  for (const topic of ['history', 'surprise_me']) {
    const app = browser();
    const original = { ...route(), topic };
    app.seed(original);
    app.pending();
    app.click('re-jaunt-btn');
    const saved = app.saved();
    assert.equal(saved.phase, 'setting_up');
    assert.equal(saved.setup_step, topic === 'surprise_me' ? 'topic_at_rest' : 'choose_topic');
    for (const key of ['stops', 'geometry', 'total_minutes', 'unused_minutes']) assert.equal(saved[key], null);
    assert.deepEqual(saved.starting_point, original.starting_point);
    assert.equal(saved.preference, original.preference);
    assert.equal(saved.topic, original.topic);
    assert.equal(saved.available_minutes, original.available_minutes);
    assert.deepEqual(saved.excluded_ids, ['a', 'b']);
    assert(app.valid());
    const reload = browser(saved);
    assert.equal(reload.requests.length, 0);
    assert.equal(reload.saved().topic, original.topic);
    assert.equal(reload.elements.get(`screen-${saved.setup_step.replaceAll('_', '-')}`).hidden, false);
  }
});

for (const outcome of ['honest', 'technical', 'network', 'parse']) {
  const buttons = outcome === 'honest'
    ? ['honest-fallback-back-btn', 'fallback-topic-chip'] : ['technical-failure-back-btn'];
  for (const button of buttons) {
    test(`${outcome} Re-Jaunt recovery via ${button} survives reload`, async () => {
      const app = browser(); app.seed(route());
      if (outcome === 'network') app.networkError();
      else if (outcome === 'parse') app.parseError();
      else app.respond({ feasible: false }, outcome !== 'technical');
      app.click('re-jaunt-btn'); await app.settle();
      const screen = outcome === 'honest' ? 'screen-honest-fallback' : 'screen-technical-failure';
      assert.equal(app.elements.get(screen).hidden, false);
      const beforeNavigation = browser(app.saved());
      assert.equal(beforeNavigation.requests.length, 0);
      assert.equal(beforeNavigation.elements.get('screen-reviewing').hidden, true);
      app.click(button);
      assert(app.valid());
      assert.equal(app.saved().phase, 'setting_up');
      assert.deepEqual(app.saved().excluded_ids, ['a', 'b']);
      assert.equal(app.saved().topic, button === 'fallback-topic-chip' ? null : 'history');
      assert.equal(browser(app.saved()).elements.get('screen-choose-topic').hidden, false);
    });
  }
}

test('two successful Re-Jaunts resend every excluded id and restore a valid review', async () => {
  const app = browser(); app.seed(route());
  app.respond(success(['c', 'd'])); app.click('re-jaunt-btn'); await app.settle();
  assert(app.valid()); assert.equal(app.saved().phase, 'reviewing');
  app.respond(success(['e', 'f'])); app.click('re-jaunt-btn'); await app.settle();
  assert.deepEqual(app.requests.map(r => r.excluded_ids), [['a', 'b'], ['a', 'b', 'c', 'd']]);
  assert.deepEqual(app.saved().stops.map(s => s.id), ['e', 'f']);
  assert(app.valid());
  const reload = browser(app.saved());
  assert.equal(reload.elements.get('screen-reviewing').hidden, false);
  assert.deepEqual(reload.saved().stops.map(s => s.id), ['e', 'f']);
  assert.equal(reload.requests.length, 0);
});

test('user can explicitly submit again after recovery reload with original inputs and exclusions', async () => {
  const app = browser(); app.seed(route()); app.pending(); app.click('re-jaunt-btn');
  const reload = browser(app.saved());
  assert.equal(reload.elements.get('start-jaunt-btn').disabled, false);
  reload.respond(success(['c', 'd']));
  reload.click('start-jaunt-btn');
  assert.equal(reload.elements.get('confirm-sheet-wrap').hidden, false);
  reload.click('confirm-btn'); await reload.settle();
  assert.deepEqual(reload.requests[0], app.requests[0]);
  assert.equal(reload.saved().phase, 'reviewing');
  assert(reload.valid());
});

test('reload during an adjusted-time retry preserves the new budget without fetching', async () => {
  const app = browser(); app.seed({ ...route(), available_minutes: 115 });
  app.respond({ feasible: false }); app.click('re-jaunt-btn'); await app.settle();
  app.pending(); app.click('fallback-time-chip');
  const reload = browser(app.saved());
  assert.equal(reload.saved().available_minutes, 120);
  assert.deepEqual(reload.saved().excluded_ids, ['a', 'b']);
  assert.equal(reload.saved().topic, 'history');
  assert.equal(reload.elements.get('screen-choose-topic').hidden, false);
  assert.equal(reload.requests.length, 0);
  assert(reload.valid());
});

test('fallback navigation repairs a reviewing origin as well as an initial setup attempt', () => {
  for (const phase of ['setting_up', 'reviewing']) {
    for (const topic of ['history', 'surprise_me']) {
      for (const button of ['honest-fallback-back-btn', 'technical-failure-back-btn', 'fallback-topic-chip']) {
        const app = browser();
        app.seed({ ...route(), phase, topic,
          setup_step: phase === 'reviewing' ? null : 'confirm_sheet', excluded_ids: ['earlier-stop'] });
        app.click(button);
        assert(app.valid(), `${phase}/${topic}/${button} must persist a valid trip`);
        assert.equal(app.saved().phase, 'setting_up');
        assert.equal(app.saved().setup_step, topic === 'surprise_me' ? 'topic_at_rest' : 'choose_topic');
        assert.equal(app.saved().topic, button === 'fallback-topic-chip' ? null : topic);
        assert.deepEqual(app.saved().excluded_ids, ['earlier-stop']);
        assert.equal(app.saved().stops, null);
        assert.equal(browser(app.saved()).requests.length, 0);
      }
    }
  }
});

test('time cap and technical retry keep the adjusted request and exclusions', async () => {
  const app = browser(); app.seed({ ...route(), available_minutes: 115 });
  app.respond({ feasible: false }); app.click('re-jaunt-btn'); await app.settle();
  assert.equal(app.elements.get('fallback-time-chip').textContent, 'Try 120 minutes');
  app.respond({ error: 'Unavailable' }, false);
  app.click('fallback-time-chip'); await app.settle();
  assert(app.valid());
  app.respond(success(['c', 'd']));
  app.click('technical-failure-retry-btn'); await app.settle();
  assert.equal(app.requests[1].requested_minutes, 120);
  assert.deepEqual(app.requests[2], app.requests[1]);
  assert.equal(app.saved().phase, 'reviewing'); assert(app.valid());
  app.respond({ feasible: false }); app.click('re-jaunt-btn'); await app.settle();
  assert.equal(app.elements.get('fallback-time-chip').hidden, true);
});

test('initial planning still reaches review without adding exclusions', async () => {
  const app = browser();
  app.seed({ ...route(), phase: 'setting_up', setup_step: 'confirm_sheet', stops: null,
    geometry: null, total_minutes: null, unused_minutes: null });
  app.respond(success(['a', 'b']));
  await app.evaluate('startRoutePlanning()');
  assert.deepEqual(app.requests[0].excluded_ids, []);
  assert.equal(app.saved().phase, 'reviewing'); assert(app.valid());
});
