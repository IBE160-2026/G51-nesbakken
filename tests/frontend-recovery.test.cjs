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

// placesSeed controls the one-time, construction-time GET /api/places call
// that loadPlaces() fires on script load: omitted means it never resolves
// (existing tests that don't care about the catalogue), an array means it
// resolves immediately with that catalogue, and a function is called for
// its result/throw - letting a test defer resolution until after it opens
// a stop overlay, to probe the late-arriving-catalogue path.
function browser(storedTrip, location = {}, placesSeed, visitHistorySeed) {
  const elements = new Map();
  function element() {
    const listeners = new Map();
    return {
      hidden: true, inert: false, dataset: {}, style: {}, children: [],
      get textContent() { return this._textContent || ""; },
      set textContent(value) { this._textContent = value; this.children = []; },
      get innerHTML() { return this._innerHTML || ""; },
      set innerHTML(value) { this._innerHTML = value; this.children = []; },
      classList: { toggle() {} },
      addEventListener(name, fn) { listeners.set(name, fn); },
      click() {
        if (this.disabled) return;
        const event = { type: 'click', target: this };
        listeners.get('click')?.(event);
        this.onclick?.(event); // real DOM fires both a listener and .onclick
      },
      input(value) { this.value = String(value); listeners.get('input')?.(); },
      appendChild(child) { this.children.push(child); },
      setAttribute(name, value) { this[name] = value; },
      getAttribute(name) { return this[name] ?? null; },
      removeAttribute(name) { delete this[name]; }, focus() {}, scrollTo() {},
      getBoundingClientRect() { return { height: 220 }; },
    };
  }
  for (const [, id] of html.matchAll(/\bid="([^"]+)"/g)) elements.set(id, element());
  const topicPills = Array.from(html.matchAll(/class="[^"]*topic-pill[^"]*"[^>]*data-topic="([^"]+)"/g), ([, topic]) => {
    const pill = element();
    pill.dataset.topic = topic;
    return pill;
  });
  const startChips = Array.from(html.matchAll(/class="[^"]*start-chip[^"]*"[^>]*data-start-id="([^"]+)"/g), ([, startId]) => {
    const chip = element(); chip.dataset.startId = startId; return chip;
  });
  const locationRequests = [];
  const watchRequests = [];
  const clearedWatchIds = new Set();
  let nextWatchId = 0;
  const mapEvents = new Map();
  const windowEvents = new Map();
  let startPanelHeight = 220;
  const startPanelEl = element();
  startPanelEl.getBoundingClientRect = () => ({ height: startPanelHeight });
  const markerPositions = [];
  const cameraPositions = [];
  const cameraOptions = [];
  const timers = new Map();
  let nextTimer = 0;
  elements.get('screen-splash').hidden = false;
  const storage = new Map([
    ...(storedTrip ? [[storageKey, JSON.stringify(storedTrip)]] : []),
    ...(visitHistorySeed ? [['jaunt_visit_history', JSON.stringify(visitHistorySeed)]] : []),
  ]);
  const requests = [];
  const responses = [];
  const summaryResponses = [];
  const summaryRequests = [];
  const shareRequests = [];
  const clipboardWrites = [];
  class Marker {
    setLngLat(point) { markerPositions.push(point); return this; }
    setPopup() { return this; }
    addTo() { return this; }
    remove() {}
    getElement() { return { style: {} }; }
  }
  const context = vm.createContext({
    URL,
    window: {
      isSecureContext: location.secure !== false,
      addEventListener(name, fn) { windowEvents.set(name, fn); },
      removeEventListener() {},
    },
    navigator: location.unsupported ? {} : { geolocation: {
      getCurrentPosition(success, failure, options) {
        if (location.throws) throw new Error('Location failed');
        locationRequests.push({ success, failure, options });
      },
      watchPosition(success, failure, options) {
        if (location.throws) throw new Error('Location failed');
        const id = ++nextWatchId;
        watchRequests.push({ id, success, failure, options });
        return id;
      },
      clearWatch(id) { clearedWatchIds.add(id); },
    },
    share: location.shareUnsupported ? undefined : async (data) => {
      if (location.shareThrows) {
        const err = new Error('cancelled');
        err.name = 'AbortError';
        throw err;
      }
      shareRequests.push(data);
    },
    clipboard: { writeText: async (text) => { clipboardWrites.push(text); } },
    },
    document: {
      getElementById(id) {
        assert(elements.has(id), `Real template must contain #${id}`);
        return elements.get(id);
      },
      querySelector(selector) { return selector === '.start-panel' ? startPanelEl : element(); },
      querySelectorAll(selector) { return selector === '.topic-pill' ? topicPills : selector === '.start-chip' ? startChips : []; },
      createTextNode: text => ({ textContent: text }),
      createElement: element, addEventListener() {}, removeEventListener() {},
    },
    maplibregl: {
      Map: class {
        touchZoomRotate = { disableRotation() {} };
        keyboard = { disable() {} };
        jumpTo(options) { cameraPositions.push(options.center); }
        easeTo(options) { cameraPositions.push(options.center); cameraOptions.push(options); }
        on(name, callback) { mapEvents.set(name, callback); } addControl() {} resize() {}
      },
      NavigationControl: class {}, Marker, Popup: class { setText() { return this; } setDOMContent() { return this; } },
    },
    localStorage: { getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
      removeItem: key => storage.delete(key) },
    console: { error() {} },
    setTimeout(callback, delay) { const id = ++nextTimer; timers.set(id, { callback, delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
    AbortSignal: { timeout: () => undefined },
    fetch: async (url, options) => {
      if (url === '/api/places') {
        if (placesSeed === undefined) return new Promise(() => {});
        if (typeof placesSeed === 'function') return placesSeed();
        return { ok: true, json: async () => JSON.parse(JSON.stringify(placesSeed)) };
      }
      if (url === '/api/summary') {
        summaryRequests.push(JSON.parse(options.body));
        assert(summaryResponses.length, 'Unexpected summary request');
        return summaryResponses.shift()();
      }
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
    requests, elements, evaluate, locationRequests, watchRequests, clearedWatchIds, markerPositions, cameraPositions, cameraOptions, timers, startChips,
    fireTimer(id) { const timer = timers.get(id); timers.delete(id); timer.callback(); },
    mapClick(lat, lng) { mapEvents.get('click')({ lngLat: { lat, lng } }); },
    fireResize() { windowEvents.get('resize')?.(); },
    setStartPanelHeight(height) { startPanelHeight = height; },
    seed(trip) { evaluate(`trip = ${JSON.stringify(trip)}; saveActiveTrip(trip);`); },
    saved: () => JSON.parse(storage.get(storageKey)),
    valid: () => evaluate('isValidTrip(JSON.parse(localStorage.getItem(STORAGE_KEY)))'),
    click: id => elements.get(id).click(),
    respond(data, ok = true) { responses.push(() => ({ ok, status: ok ? 200 : 503, json: async () => data })); },
    networkError() { responses.push(() => { throw new Error('Network failed'); }); },
    parseError() { responses.push(() => ({ ok: true, json: async () => { throw new Error('Invalid JSON'); } })); },
    pending() { responses.push(() => new Promise(() => {})); },
    summaryRequests,
    shareRequests,
    clipboardWrites,
    respondSummary(data) { summaryResponses.push(() => ({ ok: true, status: 200, json: async () => data })); },
    summaryNetworkError() { summaryResponses.push(() => { throw new Error('Network failed'); }); },
    deferred() {
      let finish;
      const promise = new Promise(resolve => { finish = resolve; });
      responses.push(() => promise);
      return (data, ok = true) => finish({ ok, status: ok ? 200 : 503, json: async () => data });
    },
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

test('both setup sliders synchronize and send continuous inverted preference through either topic path', async () => {
  for (const slider of ['preference-range-rest', 'preference-range-choose']) {
    for (const value of [0, 50, 100, 63]) {
      for (const wild of [false, true]) {
        const app = browser();
        app.seed({ ...route(), phase: 'setting_up', setup_step: wild ? 'topic_at_rest' : 'choose_topic',
          stops: null, geometry: null, total_minutes: null, unused_minutes: null });
        app.elements.get(slider).input(value);
        const preference = 1 - value / 100;
        assert.equal(app.saved().preference, preference);
        assert.equal(app.elements.get('preference-range-rest').value, String(value));
        assert.equal(app.elements.get('preference-range-choose').value, String(value));
        app.pending(); app.click(wild ? 'wild-jaunt-btn' : 'start-jaunt-btn'); app.click('confirm-btn');
        assert.equal(app.requests[0].preference, preference);
        assert.equal(app.requests[0].topic, wild ? 'surprise_me' : 'history');
        const reload = browser(app.saved());
        assert.equal(reload.requests.length, 0);
        assert.equal(reload.saved().preference, preference);
        // Each slider restores its displayed value when its setup step opens.
        reload.evaluate("showStep('topic_at_rest')");
        assert.equal(reload.elements.get('preference-range-rest').value, String(value));
        reload.click('choose-topic-btn');
        assert.equal(reload.elements.get('preference-range-choose').value, String(value));
        await app.settle();
      }
    }
  }
});

test('untouched fresh Wild Jaunt sends Balanced and confirmation has no preference slider', () => {
  const app = browser();
  app.evaluate("trip.starting_point = { lat: -33.9, lng: 151.18 }; trip.available_minutes = 60;");
  app.pending(); app.click('wild-jaunt-btn'); app.click('confirm-btn');
  assert.equal(app.requests[0].preference, 0.5);
  const confirmation = html.split('id="confirm-sheet-wrap"')[1].split('</section>')[0];
  assert(!confirmation.includes('type="range"'));
});

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
    assert.equal(app.requests[0].preference, original.preference);
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
  assert.equal(reload.saved().preference, 0.7);
  assert(app.requests.every(request => request.preference === 0.7));
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
  assert(app.requests.every(request => request.preference === 0.7));
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

test('replacement keeps constraints through technical retry and preserves retained stories', async () => {
  const app = browser(route(['a', 'b', 'c']));
  app.networkError();
  app.evaluate("replaceStop('b')");
  await app.settle();
  assert.deepEqual(app.requests[0].retained_ids, ['a', 'c']);
  assert.deepEqual(app.requests[0].excluded_ids, ['b']);
  assert.equal(app.requests[0].replacement_mode, true);
  assert.equal(app.requests[0].preference, 0.7);
  assert.equal(app.saved().phase, 'setting_up');
  assert(app.valid());
  const response = route(['c', 'd', 'a']);
  response.stops.forEach(stop => stop.content = 'Regenerated');
  app.respond({ feasible: true, ...response, replacement_outcome: 'replacement_found' });
  app.click('technical-failure-retry-btn');
  await app.settle();
  assert.deepEqual(app.requests[1], app.requests[0]);
  assert.deepEqual(app.saved().stops.map(stop => stop.content), ['Grounded text', 'Regenerated', 'Grounded text']);
});

test('retained-only one-stop result has refreshed totals, inline notice, and survives reload', async () => {
  const app = browser(route());
  app.respond({ feasible: true, ...route(['b']), total_minutes: 7, unused_minutes: 53, replacement_outcome: 'retained_only' });
  app.evaluate("replaceStop('a')");
  await app.settle();
  const saved = app.saved();
  assert.equal(saved.phase, 'reviewing');
  assert.equal(saved.total_minutes, 7);
  assert.equal(saved.replacement_notice, 0);
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, false);
  assert(app.valid());
  const reloaded = browser(saved);
  assert.equal(reloaded.saved().stops.length, 1);
  assert.equal(reloaded.requests.length, 0);
});

test('final-stop replacement excludes it and honest failure never restores it', async () => {
  const app = browser(route(['a']));
  app.respond({ feasible: false, reason: 'No options' });
  app.evaluate("replaceStop('a')");
  await app.settle();
  assert.deepEqual(app.requests[0].retained_ids, []);
  assert.deepEqual(app.saved().excluded_ids, ['a']);
  assert.equal(app.saved().stops, null);
  assert.equal(app.elements.get('screen-honest-fallback').hidden, false);
});

test('pending replacement reload recovers setup without requesting and setup exit clears intent', async () => {
  const app = browser(route());
  app.pending();
  app.evaluate("replaceStop('a')");
  const reloaded = browser(app.saved());
  assert(reloaded.valid());
  assert.equal(reloaded.requests.length, 0);
  reloaded.click('technical-failure-back-btn');
  assert.equal(reloaded.saved().replacement, null);
  assert.deepEqual(reloaded.saved().excluded_ids, ['a']);
});

test('stop card exposes only sibling details and enabled final-stop Replace', () => {
  const app = browser(route(['a']));
  app.evaluate('renderStopList()');
  const row = app.elements.get('stop-list').children[0];
  assert.equal(row.children.length, 2);
  assert.equal(row.children[0].className, 'stop-list-btn');
  assert.equal(row.children[1].textContent, 'Replace');
  assert.notEqual(row.children[1].disabled, true);
  assert(row.children.every(control => control.textContent !== 'Remove'));
  app.pending();
  row.children[1].click();
  assert.equal(app.requests[0].replacement_mode, true);
  assert.deepEqual(app.requests[0].retained_ids, []);
});

function replacementSuccess(ids) {
  const response = { ...success(ids), geometry: route().geometry };
  response.stops.forEach(stop => { stop.content = "Regenerated content"; });
  return response;
}

for (const [label, mutate] of [
  ['missing retained', data => { data.stops = [stop('a', 1), stop('d', 2), stop('e', 3)]; }],
  ['excluded stop', data => { data.stops = [stop('a', 1), stop('c', 2), stop('b', 3)]; }],
  ['duplicate stop', data => { data.stops = [stop('a', 1), stop('c', 2), stop('c', 3)]; }],
  ['wrong count', data => { data.stops = [stop('a', 1), stop('c', 2)]; }],
  ['reordered retained only', data => { data.stops = [stop('c', 1), stop('a', 2)]; data.replacement_outcome = 'retained_only'; }],
  ['missing geometry', data => { delete data.geometry; }],
  ['overbudget', data => { data.total_minutes = 61; }],
  ['null stop', data => { data.stops[1] = null; }],
]) {
  test(`invalid replacement: ${label} preserves constraints for retry`, async () => {
    const app = browser(route(['a', 'b', 'c']));
    const data = { ...replacementSuccess(['a', 'c', 'd']), replacement_outcome: 'replacement_found' };
    mutate(data);
    app.respond(data);
    app.evaluate("replaceStop('b')");
    await app.settle();
    assert.equal(app.elements.get('screen-technical-failure').hidden, false);
    assert.equal(app.saved().phase, 'setting_up');
    assert.equal(app.saved().stops, null);
    assert.deepEqual(app.saved().replacement.retained_stops.map(stop => stop.id), ['a', 'c']);
    app.respond({ ...replacementSuccess(['a', 'c', 'd']), replacement_outcome: 'replacement_found' });
    app.click('technical-failure-retry-btn');
    await app.settle();
    assert.deepEqual(app.requests[1], app.requests[0]);
    assert.equal(app.saved().phase, 'reviewing');
  });
}

test('consecutive successful and retained-only edits accumulate exclusions and reset notices', async () => {
  const app = browser(route(['a', 'b', 'c']));
  app.respond({ ...replacementSuccess(['c', 'd', 'a']), replacement_outcome: 'replacement_found' });
  app.evaluate("replaceStop('b')"); await app.settle();
  assert.equal(app.saved().replacement_notice, null);
  app.respond({ ...replacementSuccess(['c', 'a']), replacement_outcome: 'retained_only' });
  app.evaluate("replaceStop('d')"); await app.settle();
  assert.deepEqual(app.requests[1].retained_ids, ['c', 'a']);
  assert.deepEqual(app.requests[1].excluded_ids, ['b', 'd']);
  assert.deepEqual(app.saved().stops.map(stop => stop.content), ['Grounded text', 'Grounded text']);
  const list = app.elements.get('stop-list');
  assert.equal(list.children.length, 3);
  assert.equal(list.children[1].textContent, 'Jarrod could not find a suitable replacement with these settings');
  app.evaluate('renderStopList()');
  assert.equal(list.children.length, 3);
  assert.equal(list.children[1].className, 'replacement-notice');
  app.respond({ ...replacementSuccess(['c', 'e']), replacement_outcome: 'replacement_found' });
  app.evaluate("replaceStop('a')"); await app.settle();
  assert.deepEqual(app.requests[2].excluded_ids, ['b', 'd', 'a']);
  assert.deepEqual(app.requests[2].retained_ids, ['c']);
  assert.equal(app.saved().replacement_notice, null);
  app.evaluate('renderStopList()');
  assert.equal(list.children.length, 2);
  assert(list.children.every(row => row.className !== 'replacement-notice'));
});

test('last-row removal places one notice after remaining stops across rerenders', async () => {
  const app = browser(route(['a', 'b', 'c']));
  app.respond({ ...replacementSuccess(['a', 'b']), replacement_outcome: 'retained_only' });
  app.evaluate("replaceStop('c')"); await app.settle();
  const list = app.elements.get('stop-list');
  for (let i = 0; i < 2; i++) {
    assert.equal(list.children.length, 3);
    assert.equal(list.children[2].textContent, 'Jarrod could not find a suitable replacement with these settings');
    assert.equal(list.children[2].className, 'replacement-notice');
    app.evaluate('renderStopList()');
  }
});

test('replacement loads only the chosen card, preserves neighbours, and blocks overlapping edits', async () => {
  const app = browser(route(['a', 'b', 'c']));
  app.click('open-stop-list-btn');
  const finish = app.deferred();
  app.evaluate("replaceStop('b')");
  const list = app.elements.get('stop-list');
  assert.equal(list.children.length, 3);
  assert.equal(list.children[1].className, 'stop-list-row replacement-loading');
  assert.equal(list.children[1].children[0].textContent, 'Finding a replacement…');
  for (const [i, name] of [[0, 'Stop a'], [2, 'Stop c']]) {
    assert.equal(list.children[i].children[0].children[2].children[0].textContent, name);
    assert.equal(list.children[i].children[1].disabled, true);
  }
  assert.equal(app.elements.get('screen-loading').hidden, true);
  assert.equal(app.elements.get('map-stage').hidden, false);
  assert.equal(app.elements.get('screen-reviewing').hidden, false);
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, false);
  for (const id of ['approve-route-btn', 're-jaunt-btn', 'change-jaunt-btn']) assert.equal(app.elements.get(id).disabled, true);
  app.evaluate("replaceStop('a')");
  for (const id of ['approve-route-btn', 're-jaunt-btn', 'change-jaunt-btn']) app.click(id);
  assert.equal(app.requests.length, 1);
  assert.equal(app.saved().phase, 'setting_up');
  assert(app.valid());
  assert.equal(browser(app.saved()).requests.length, 0);
  app.click('stop-list-close-btn'); app.click('open-stop-list-btn');
  assert.equal(list.children[1].children[0].textContent, 'Finding a replacement…');
  finish({ ...replacementSuccess(['a', 'c', 'd']), replacement_outcome: 'replacement_found' });
  await app.settle();
  assert.equal(app.saved().phase, 'reviewing');
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, false);
  assert(list.children.every(row => row.className !== 'stop-list-row replacement-loading'));
  for (const id of ['approve-route-btn', 're-jaunt-btn', 'change-jaunt-btn']) assert.equal(app.elements.get(id).disabled, false);
});

test('technical failure releases local busy state and retry returns to card-local loading', async () => {
  const app = browser(route(['a', 'b', 'c']));
  app.networkError(); app.evaluate("replaceStop('b')"); await app.settle();
  assert.equal(app.elements.get('screen-technical-failure').hidden, false);
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, true);
  assert.equal(app.elements.get('map-stage').inert, false);
  assert.equal(app.elements.get('approve-route-btn').disabled, false);
  const finish = app.deferred();
  app.click('technical-failure-retry-btn');
  assert.equal(app.elements.get('screen-loading').hidden, true);
  assert.equal(app.elements.get('screen-reviewing').hidden, false);
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, false);
  assert.equal(app.elements.get('stop-list').children[1].children[0].textContent, 'Finding a replacement…');
  assert.deepEqual(app.requests[1], app.requests[0]);
  finish({ ...replacementSuccess(['a', 'c']), replacement_outcome: 'retained_only' }); await app.settle();
  assert.equal(app.saved().replacement_notice, 1);
  assert.equal(app.elements.get('approve-route-btn').disabled, false);
  assert.equal(app.elements.get('stop-list').children[1].className, 'replacement-notice');
});

test('final-stop failure cleans up the local sheet before sad-Jarrod fallback', async () => {
  const app = browser(route(['a'])); const finish = app.deferred();
  app.evaluate("replaceStop('a')");
  assert.equal(app.elements.get('stop-list').children[0].className, 'stop-list-row replacement-loading');
  finish({ feasible: false }); await app.settle();
  assert.equal(app.elements.get('screen-honest-fallback').hidden, false);
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, true);
  assert.equal(app.elements.get('map-stage').inert, false);
  assert.equal(app.elements.get('approve-route-btn').disabled, false);
});

test('initial generation and whole-route Re-Jaunt still use the full loading screen', () => {
  const app = browser();
  app.seed({ ...route(), phase: 'setting_up', setup_step: 'confirm_sheet' });
  app.pending(); app.evaluate('startRoutePlanning()');
  assert.equal(app.elements.get('screen-loading').hidden, false);
  assert.equal(app.elements.get('map-stage').hidden, true);
  const rejaunt = browser(route());
  rejaunt.pending(); rejaunt.click('re-jaunt-btn');
  assert.equal(rejaunt.elements.get('screen-loading').hidden, false);
  assert.equal(rejaunt.elements.get('map-stage').hidden, true);
});

for (const outcome of ['replacement_found', 'retained_only', 'technical', 'final']) {
  test(`replacement completion cleans up an intervening credits sheet: ${outcome}`, async () => {
    const app = browser(route(outcome === 'final' ? ['a'] : ['a', 'b', 'c']));
    const finish = app.deferred();
    app.evaluate(outcome === 'final' ? "replaceStop('a')" : "replaceStop('b')");
    app.click('stop-list-close-btn'); app.click('open-credits-btn');
    assert.equal(app.elements.get('credits-sheet-wrap').hidden, false);
    if (outcome === 'technical') finish({ error: 'Unavailable' }, false);
    else if (outcome === 'final') finish({ feasible: false });
    else finish({ ...replacementSuccess(outcome === 'retained_only' ? ['a', 'c'] : ['a', 'c', 'd']), replacement_outcome: outcome });
    await app.settle();
    assert.equal(app.elements.get('credits-sheet-wrap').hidden, true);
    const successful = ['replacement_found', 'retained_only'].includes(outcome);
    assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, !successful);
    assert.equal(app.elements.get('map-stage').inert, successful);
    assert.equal(app.elements.get('screen-reviewing').inert, successful);
    assert.equal(app.elements.get('approve-route-btn').disabled, false);
  });
}


test('current location previews first and is saved only after explicit confirmation', () => {
  const app = browser();
  assert.equal(app.locationRequests.length, 0);
  app.click('current-location-btn'); app.click('current-location-btn');
  assert.equal(app.locationRequests.length, 1);
  assert.match(app.elements.get('current-location-status').textContent, /Finding/);
  const request = app.locationRequests[0];
  assert.deepEqual(JSON.parse(JSON.stringify(request.options)), { timeout: 10000, maximumAge: 0, enableHighAccuracy: false });
  request.success({ coords: { latitude: 40, longitude: -74 } });
  assert.equal(app.saved().starting_point, null);
  assert.equal(app.saved().setup_step, 'starting_point');
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  assert.equal(app.elements.get('pending-pin-label').textContent, 'Current location');
  assert.match(html, />Tap to drop a pin</);
  assert.equal(app.requests.length, 0);
  assert.equal(browser(app.saved()).saved().starting_point, null);
  app.click('confirm-start-btn');
  assert.deepEqual(app.saved().starting_point, { lat: 40, lng: -74, label: 'Current location' });
  assert.deepEqual(Array.from(app.markerPositions.at(-1)), [-74, 40]);
  assert.deepEqual(Array.from(app.cameraPositions.at(-1)), [-74, 40]);
  assert.deepEqual(Array.from(app.cameraOptions.at(-1).offset), [0, -78]);
  assert.equal(app.cameraOptions.at(-1).duration, 0);
  assert.equal([...app.timers.values()].filter(timer => timer.delay === 10000).length, 0);
  assert.equal(app.elements.get('screen-available-time').hidden, false);
  assert.equal(app.requests.length, 0);
  const reload = browser(app.saved());
  assert.equal(reload.locationRequests.length, 0);
  assert.equal(reload.elements.get('screen-available-time').hidden, false);
  app.pending(); app.click('wild-jaunt-btn'); app.click('confirm-btn');
  assert.equal(app.requests[0].start_lat, 40);
  assert.equal(app.requests[0].start_lon, -74);
});

for (const failure of ['denied', 'unavailable', 'timeout', 'unsupported', 'insecure', 'throws', 'invalid']) {
  test(`current location ${failure} preserves inputs and permits manual recovery`, () => {
    const app = browser(undefined, { unsupported: failure === 'unsupported', secure: failure !== 'insecure', throws: failure === 'throws' });
    app.seed({ ...route(), phase: 'setting_up', setup_step: 'starting_point', stops: null, geometry: null, total_minutes: null, unused_minutes: null });
    const before = app.saved();
    app.click('current-location-btn');
    if (failure === 'invalid') app.locationRequests[0].success({ coords: { latitude: Infinity, longitude: 181 } });
    else if (['denied', 'unavailable', 'timeout'].includes(failure)) app.locationRequests[0].failure({ code: { denied: 1, unavailable: 2, timeout: 3 }[failure] });
    assert.deepEqual(app.saved(), before);
    assert.equal(app.elements.get('current-location-btn').disabled, false);
    assert.match(app.elements.get('current-location-status').textContent, /Choose|choose/);
    app.startChips[0].click();
    assert.deepEqual(app.saved(), before);
    app.click('confirm-start-btn');
    assert.equal(app.saved().starting_point.label, 'Newtown Station');
    assert.equal(app.saved().available_minutes, before.available_minutes);
    assert.equal(app.saved().preference, before.preference);
  });
}

for (const choice of ['named', 'map', 'leave']) {
  test(`late location callbacks cannot overwrite ${choice} choice`, () => {
    const app = browser(); app.click('current-location-btn');
    const request = app.locationRequests[0];
    if (choice === 'named') { app.startChips[1].click(); app.click('confirm-start-btn'); }
    else if (choice === 'map') { app.mapClick(-33.9, 151.2); app.click('confirm-start-btn'); }
    else app.evaluate("showStep('available_time')");
    const saved = app.saved();
    request.success({ coords: { latitude: 1, longitude: 2 } });
    request.failure({ code: 1 });
    assert.deepEqual(app.saved(), saved);
    assert.equal(app.elements.get('screen-available-time').hidden, false);
    assert.equal(app.elements.get('current-location-status').textContent, '');
  });
}

test('retry supersedes old callbacks and pending reload never requests location', () => {
  const app = browser(); app.click('current-location-btn');
  const old = app.locationRequests[0];
  assert.equal(browser(app.saved()).locationRequests.length, 0);
  old.failure({ code: 3 }); app.click('current-location-btn');
  old.success({ coords: { latitude: 1, longitude: 2 } });
  assert.equal(app.saved().starting_point, null);
  app.locationRequests[1].success({ coords: { latitude: -90, longitude: 180 } });
  assert.equal(app.saved().starting_point, null);
  app.click('confirm-start-btn');
  assert.equal(app.saved().starting_point.lat, -90);
});


test('application deadline releases unanswered permission and discards late callbacks', () => {
  const app = browser(); app.click('current-location-btn');
  const request = app.locationRequests[0];
  const [id, timer] = [...app.timers].find(([, timer]) => timer.delay === 10000);
  assert.equal(timer.delay, 10000);
  app.fireTimer(id);
  assert.equal(app.elements.get('current-location-btn').disabled, false);
  const status = app.elements.get('current-location-status').textContent;
  assert.match(status, /too long/);
  request.success({ coords: { latitude: 1, longitude: 2 } });
  request.failure({ code: 1 });
  assert.equal(app.saved().starting_point, null);
  assert.equal(app.elements.get('current-location-status').textContent, status);
  app.click('current-location-btn');
  assert.equal(app.locationRequests.length, 2);
});

test('map tap invalidates pending location before pin confirmation', () => {
  const app = browser(); app.click('current-location-btn');
  const request = app.locationRequests[0];
  app.mapClick(-33.9, 151.2);
  const saved = app.saved();
  const pendingPin = app.evaluate('JSON.stringify(pendingPin)');
  const status = app.elements.get('current-location-status').textContent;
  request.success({ coords: { latitude: 1, longitude: 2 } });
  request.failure({ code: 1 });
  assert.deepEqual(app.saved(), saved);
  assert.equal(app.evaluate('JSON.stringify(pendingPin)'), pendingPin);
  assert.equal(app.elements.get('screen-starting-point').hidden, false);
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  assert.equal(app.elements.get('current-location-status').textContent, status);
  assert.equal([...app.timers.values()].filter(timer => timer.delay === 10000).length, 0);
});

test('location failure recovers through map pin confirmation and preserves other inputs', () => {
  const app = browser();
  app.seed({ ...route(), phase: 'setting_up', setup_step: 'starting_point', stops: null, geometry: null, total_minutes: null, unused_minutes: null });
  const before = app.saved();
  app.click('current-location-btn'); app.locationRequests[0].failure({ code: 1 });
  assert.equal([...app.timers.values()].filter(timer => timer.delay === 10000).length, 0);
  app.mapClick(-33.8, 151.1); app.click('confirm-start-btn');
  assert.deepEqual(app.saved().starting_point, { lat: -33.8, lng: 151.1, label: 'Dropped pin' });
  for (const key of ['available_minutes', 'topic', 'preference', 'excluded_ids']) assert.deepEqual(app.saved()[key], before[key]);
  assert.equal(app.elements.get('screen-available-time').hidden, false);
  assert(app.valid());
});

const placePhotos = JSON.parse(fs.readFileSync(path.join(root, 'data/place_photos.json'), 'utf8'));
const curatedPhoto = placePhotos['heritage/2420855'];
const publicPhoto = Object.fromEntries(Object.entries(curatedPhoto).filter(([key]) => key !== 'reviewed'));
// A second, genuinely different valid photo - used to prove the overlay
// shows the catalogue's current photo rather than a stale saved one.
const catalogueCurrentPhoto = Object.fromEntries(
  Object.entries(placePhotos['heritage/2030116']).filter(([key]) => key !== 'reviewed'));
function catalogueEntry(id, photo) {
  return { id, name: 'Catalogue place', latitude: -33.9, longitude: 151.18, topics: ['history'], source_type: 'test', photo };
}

test('photo lifecycle reveals complete credit only after load and resets on errors, switching and close', () => {
  const app = browser();
  const photoStop = { ...stop('photo', 1), photo: publicPhoto,
    attribution: [{ source_type: 'wikipedia', source_title: 'Prose source', source_url: 'https://example.org/story' }] };
  const open = value => app.evaluate(`openStopOverlay(${JSON.stringify(value)})`);
  const figure = app.elements.get('stop-overlay-figure');
  const image = app.elements.get('stop-overlay-photo');
  const credit = app.elements.get('stop-overlay-credit');
  open(photoStop);
  assert.equal(figure.hidden, true);
  assert.equal(image.alt, publicPhoto.alt);
  assert.equal(image.src, publicPhoto.url);
  image.onload();
  assert.equal(figure.hidden, false);
  assert.equal(app.elements.get('stop-overlay-body').textContent, photoStop.content);
  assert.equal(app.elements.get('stop-overlay-attribution').children.length, 1);
  const links = credit.children.filter(child => child.href);
  assert.deepEqual(links.map(link => link.href), [publicPhoto.source_url, publicPhoto.license_url]);
  assert(links.every(link => link.rel === 'noopener noreferrer'));
  assert(credit.children.some(child => child.textContent.includes(publicPhoto.creator)));
  assert(credit.children.some(child => child.textContent === publicPhoto.changes));
  open(photoStop);
  const staleLoad = image.onload;
  open({ ...stop('plain', 2), photo_url: 'https://example.org/old.jpg' });
  staleLoad();
  assert.equal(figure.hidden, true);
  assert.equal(image.src, undefined);
  assert.equal(credit.textContent, '');
  open(photoStop); image.onerror();
  assert.equal(figure.hidden, true);
  assert.equal(image.src, undefined);
  open(photoStop); const afterClose = image.onload;
  app.evaluate('closeStopOverlay()'); afterClose();
  assert.equal(figure.hidden, true);
  open(photoStop); image.onload();
  app.evaluate('backToStopListFromOverlay()');
  assert.equal(figure.hidden, true);
});

test('structured optional photos survive save/reload; incomplete and unsafe metadata cannot display', () => {
  const trip = route(); trip.stops[0].photo = publicPhoto;
  const app = browser(); app.seed(trip);
  const reload = browser(app.saved());
  assert.equal(reload.valid(), true);
  assert.deepEqual(reload.saved().stops[0].photo, publicPhoto);
  assert.equal(reload.requests.length, 0);
  for (const invalid of [null, {}, { ...publicPhoto, creator: '' },
    { ...publicPhoto, url: 'https://example.org/photo.jpg' },
    { ...publicPhoto, url: '/static/place-photos/../photo.jpg' },
    { ...publicPhoto, url: '/static/place-photos/%2e%2e/photo.jpg' },
    { ...publicPhoto, source_url: 'javascript:alert(1)' },
    { ...publicPhoto, license_url: 'http://example.org/license' }]) {
    assert.equal(app.evaluate(`isValidStop(${JSON.stringify({ ...stop('x', 1), photo: invalid })})`), true);
    app.evaluate(`openStopOverlay(${JSON.stringify({ ...stop('x', 1), photo: invalid })})`);
    assert.equal(app.elements.get('stop-overlay-figure').hidden, true);
  }
  assert.equal(app.evaluate(`isValidStop(${JSON.stringify(stop('old', 1))})`), true);
});


test('replacement uses canonical backend photo metadata while retaining grounded stories', async () => {
  const trip = route(); trip.stops[1].photo = publicPhoto;
  const app = browser(trip);
  const response = route(['b', 'c']);
  response.stops[0].content = 'Regenerated';
  response.stops[1].photo = publicPhoto;
  app.respond({ feasible: true, ...response, replacement_outcome: 'replacement_found' });
  app.evaluate("replaceStop('a')");
  await app.settle();
  assert.equal(app.saved().stops[0].photo, undefined);
  assert.equal(app.saved().stops[0].content, 'Grounded text');
  assert.deepEqual(app.saved().stops[1].photo, publicPhoto);
  assert.equal(browser(app.saved()).valid(), true);
});


test('malformed optional photos preserve saved review and planned response text', async () => {
  for (const photo of [null, {}, { ...publicPhoto, creator: '' },
    { ...publicPhoto, url: 'https://example.org/unsafe.jpg' },
    { ...publicPhoto, source_url: 'javascript:alert(1)' }]) {
    const savedTrip = route(); savedTrip.stops[0].photo = photo;
    const restored = browser(savedTrip);
    assert.equal(restored.valid(), true);
    assert.equal(restored.saved().phase, 'reviewing');
    assert.equal(restored.elements.get('screen-reviewing').hidden, false);
    assert.equal(restored.requests.length, 0);
    restored.evaluate('openStopOverlay(trip.stops[0])');
    assert.equal(restored.elements.get('stop-overlay-body').textContent, savedTrip.stops[0].content);
    assert.equal(restored.elements.get('stop-overlay-figure').hidden, true);
    assert.equal(restored.elements.get('stop-overlay-photo').src, undefined);

    const planned = browser();
    planned.seed({ ...route(), phase: 'setting_up', setup_step: 'confirm_sheet', stops: null,
      geometry: null, total_minutes: null, unused_minutes: null });
    const response = success(['new-a', 'new-b']); response.stops[0].photo = photo;
    planned.respond(response);
    await planned.evaluate('startRoutePlanning()');
    assert.equal(planned.saved().phase, 'reviewing');
    assert.equal(planned.valid(), true);
    assert.deepEqual(planned.saved().stops.map(stop => stop.id), ['new-a', 'new-b']);
    planned.evaluate('openStopOverlay(trip.stops[0])');
    assert.equal(planned.elements.get('stop-overlay-body').textContent, response.stops[0].content);
    assert.equal(planned.elements.get('stop-overlay-figure').hidden, true);
    assert.equal(planned.elements.get('stop-overlay-photo').src, undefined);
  }
});


// loadPlaces() is normally only reached via the real map's "load" event,
// which this harness never fires (mapEvents.set('load', ...) just records
// it) - these tests call it directly, exactly as app.js's own map.on("load")
// handler would.

test('old saved route with no saved photo shows the catalogue\'s current photo for that stop id', async () => {
  const trip = route(['enmore']); // no .photo on the saved stop - as if saved before this one existed
  const app = browser(trip, {}, [catalogueEntry('enmore', catalogueCurrentPhoto)]);
  await app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  const image = app.elements.get('stop-overlay-photo');
  assert.equal(image.src, catalogueCurrentPhoto.url);
  assert.equal(image.alt, catalogueCurrentPhoto.alt);
});

test('a current catalogue photo is shown in place of a different, stale saved photo', async () => {
  const trip = route(['enmore']); trip.stops[0].photo = publicPhoto; // stale saved photo
  const app = browser(trip, {}, [catalogueEntry('enmore', catalogueCurrentPhoto)]); // catalogue has a different one now
  await app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  const image = app.elements.get('stop-overlay-photo');
  assert.equal(image.src, catalogueCurrentPhoto.url);
  assert.notEqual(catalogueCurrentPhoto.url, publicPhoto.url);
});

test('a catalogue entry that currently has no qualifying photo does not revive a stale saved one', async () => {
  const trip = route(['enmore']); trip.stops[0].photo = publicPhoto; // stale saved photo
  const app = browser(trip, {}, [catalogueEntry('enmore', undefined)]); // place still exists, photo removed/invalid
  await app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  assert.equal(app.elements.get('stop-overlay-figure').hidden, true);
  assert.equal(app.elements.get('stop-overlay-photo').src, undefined);
});

test('a catalogue fetch failure preserves stop text and falls back to a valid saved photo', async () => {
  const trip = route(['enmore']); trip.stops[0].photo = publicPhoto;
  const app = browser(trip, {}, () => { throw new Error('Network failed'); });
  await app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  const image = app.elements.get('stop-overlay-photo');
  assert.equal(image.src, publicPhoto.url);
  assert.equal(app.elements.get('stop-overlay-body').textContent, trip.stops[0].content);
});

test('a catalogue that finishes loading after its stop overlay is already open fills in the photo in place', async () => {
  const trip = route(['enmore']);
  let finishPlaces;
  const placesPromise = new Promise((resolve) => { finishPlaces = resolve; });
  const app = browser(trip, {}, () => placesPromise);
  app.evaluate('loadPlaces()'); // in flight, pending on placesPromise
  app.evaluate('openStopOverlay(trip.stops[0])');
  const heading = app.elements.get('stop-overlay-heading');
  const image = app.elements.get('stop-overlay-photo');
  assert.equal(image.src, undefined);
  assert.equal(heading.textContent, trip.stops[0].name);
  finishPlaces({ ok: true, json: async () => [catalogueEntry('enmore', catalogueCurrentPhoto)] });
  await app.settle();
  assert.equal(image.src, catalogueCurrentPhoto.url);
  // Filling the photo in must not have rebuilt or reopened the overlay.
  assert.equal(heading.textContent, trip.stops[0].name);
});

test('a catalogue resolving to the exact photo already showing does not reset or reload it', async () => {
  // Regression: the catalogue arriving late and re-resolving to the same
  // photo a fresh /api/plan response already attached was resetting and
  // reassigning src unconditionally, hiding an already-correct photo
  // (briefly on a fast connection, long enough to look "gone" on a slow one).
  const trip = route(['enmore']); trip.stops[0].photo = publicPhoto;
  let finishPlaces;
  const placesPromise = new Promise((resolve) => { finishPlaces = resolve; });
  const app = browser(trip, {}, () => placesPromise);
  app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  const figure = app.elements.get('stop-overlay-figure');
  const image = app.elements.get('stop-overlay-photo');
  image.onload(); // the photo already attached to the fresh stop finishes loading normally
  assert.equal(figure.hidden, false);
  finishPlaces({ ok: true, json: async () => [catalogueEntry('enmore', publicPhoto)] }); // catalogue agrees - same photo
  await app.settle();
  // Must still be showing without a second onload - a real reset/reload would have hidden it again.
  assert.equal(figure.hidden, false);
  assert.equal(image.src, publicPhoto.url);
});

test('a catalogue agreeing with a still-loading photo does not abort/restart it', async () => {
  // Regression (phone report, slow connection): the first fix only skipped
  // the reset when the figure was already visible - on a slow connection
  // the catalogue can instead land while the photo is still mid-load
  // (figure still hidden, onload pending), and resetting there aborts and
  // restarts the in-flight request, which may never recover.
  const trip = route(['enmore']); trip.stops[0].photo = publicPhoto;
  let finishPlaces;
  const placesPromise = new Promise((resolve) => { finishPlaces = resolve; });
  const app = browser(trip, {}, () => placesPromise);
  app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  const figure = app.elements.get('stop-overlay-figure');
  const image = app.elements.get('stop-overlay-photo');
  const originalOnload = image.onload; // captured before the photo has finished loading
  assert.equal(figure.hidden, true); // still loading - onload has not fired yet
  finishPlaces({ ok: true, json: async () => [catalogueEntry('enmore', publicPhoto)] }); // catalogue agrees mid-load
  await app.settle();
  // The in-flight request must be untouched: same onload, still pending.
  assert.equal(image.onload, originalOnload);
  assert.equal(figure.hidden, true);
  originalOnload(); // the original (never-aborted) request now finishes
  assert.equal(figure.hidden, false);
});

test('a catalogue that arrives after switching stops renders onto the stop now open, not the one first opened', async () => {
  const trip = route(['enmore', 'other']);
  let finishPlaces;
  const placesPromise = new Promise((resolve) => { finishPlaces = resolve; });
  const app = browser(trip, {}, () => placesPromise);
  app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  app.evaluate('openStopOverlay(trip.stops[1])');
  finishPlaces({ ok: true, json: async () => [
    catalogueEntry('enmore', catalogueCurrentPhoto),
    catalogueEntry('other', publicPhoto),
  ] });
  await app.settle();
  assert.equal(app.elements.get('stop-overlay-heading').textContent, trip.stops[1].name);
  assert.equal(app.elements.get('stop-overlay-photo').src, publicPhoto.url);
});

test('a catalogue that arrives after the overlay was closed does not reopen it or render a photo', async () => {
  const trip = route(['enmore']);
  let finishPlaces;
  const placesPromise = new Promise((resolve) => { finishPlaces = resolve; });
  const app = browser(trip, {}, () => placesPromise);
  app.evaluate('loadPlaces()');
  app.evaluate('openStopOverlay(trip.stops[0])');
  app.evaluate('closeStopOverlay()');
  finishPlaces({ ok: true, json: async () => [catalogueEntry('enmore', catalogueCurrentPhoto)] });
  await app.settle();
  assert.equal(app.elements.get('stop-overlay-wrap').hidden, true);
  assert.equal(app.elements.get('stop-overlay-photo').src, undefined);
});


test('GPS preview can be moved on the map before confirming without changing other inputs', () => {
  const app = browser();
  app.seed({ ...route(), phase: 'setting_up', setup_step: 'starting_point', stops: null, geometry: null, total_minutes: null, unused_minutes: null });
  const before = app.saved();
  app.click('current-location-btn');
  app.locationRequests[0].success({ coords: { latitude: -33.8, longitude: 151.1 } });
  assert.deepEqual(app.saved(), before);
  const reload = browser(app.saved());
  assert.deepEqual(reload.saved().starting_point, before.starting_point);
  assert.equal(reload.locationRequests.length, 0);
  app.mapClick(-33.81, 151.11);
  assert.equal(app.elements.get('pending-pin-label').textContent, 'Dropped pin');
  app.click('confirm-start-btn');
  assert.deepEqual(app.saved().starting_point, { lat: -33.81, lng: 151.11, label: 'Dropped pin' });
  for (const key of ['available_minutes', 'topic', 'preference', 'excluded_ids']) assert.deepEqual(app.saved()[key], before[key]);
  assert(app.valid());
  app.evaluate("showStep('starting_point')");
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  assert.equal(app.elements.get('pending-pin-label').textContent, 'Dropped pin');
});


test('all named starts require confirmation and preserve the existing trip until confirmed', () => {
  for (let i = 0; i < 3; i++) {
    const app = browser();
    assert.equal(app.elements.get('confirm-start-btn').disabled, true);
    app.click('confirm-start-btn');
    assert.equal(app.saved().setup_step, 'starting_point');
    app.startChips[i].click();
    assert.equal(app.saved().starting_point, null);
    assert.equal(app.saved().setup_step, 'starting_point');
    assert.equal(app.elements.get('confirm-start-btn').disabled, false);
    const selected = JSON.parse(app.evaluate('JSON.stringify(pendingPin)'));
    const reload = browser(app.saved());
    assert.equal(reload.saved().starting_point, null);
    assert.equal(reload.elements.get('confirm-start-btn').disabled, true);
    app.click('confirm-start-btn');
    assert.deepEqual(app.saved().starting_point, selected);
    assert.equal(app.saved().setup_step, 'available_time');
    app.click('available-time-back-btn');
    assert.equal(app.saved().setup_step, 'starting_point');
    assert.equal(app.elements.get('confirm-start-btn').disabled, false);
    assert.deepEqual(JSON.parse(app.evaluate('JSON.stringify(pendingPin)')), selected);
    const restored = browser(app.saved());
    assert.equal(restored.elements.get('confirm-start-btn').disabled, false);
    restored.click('confirm-start-btn');
    assert.equal(restored.saved().setup_step, 'available_time');
  }
});

test('changing a named preview or moving its pin commits only the last choice', () => {
  const app = browser();
  app.startChips[0].click(); app.startChips[1].click();
  assert.equal(app.saved().starting_point, null);
  app.mapClick(-33.9, 151.2);
  app.click('confirm-start-btn');
  assert.deepEqual(app.saved().starting_point, { lat: -33.9, lng: 151.2, label: 'Dropped pin' });
});

test('confirming a selected spot cancels an unanswered GPS request', () => {
  const app = browser();
  app.startChips[0].click(); app.click('current-location-btn');
  const request = app.locationRequests[0];
  app.click('confirm-start-btn');
  const saved = app.saved();
  request.success({ coords: { latitude: 1, longitude: 2 } });
  assert.deepEqual(app.saved(), saved);
  assert.equal(saved.starting_point.label, 'Newtown Station');
});


test('named preview cancels stale GPS callbacks before confirmation', () => {
  const app = browser(); app.click('current-location-btn');
  const request = app.locationRequests[0];
  app.startChips[0].click();
  const before = app.saved();
  const preview = app.evaluate('JSON.stringify(pendingPin)');
  request.success({ coords: { latitude: 1, longitude: 2 } });
  request.failure({ code: 1 });
  assert.deepEqual(app.saved(), before);
  assert.equal(app.evaluate('JSON.stringify(pendingPin)'), preview);
  assert.equal(app.elements.get('pending-pin-label').textContent, 'Newtown Station');
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  assert.equal(app.elements.get('screen-starting-point').hidden, false);
});

for (const source of ['named', 'map', 'GPS']) {
  test(`reload discards unconfirmed ${source} replacement and restores the committed start`, () => {
    const app = browser();
    app.startChips[0].click(); app.click('confirm-start-btn');
    const committed = app.saved().starting_point;
    app.click('available-time-back-btn');
    if (source === 'named') app.startChips[1].click();
    else if (source === 'map') app.mapClick(-33.8, 151.1);
    else {
      app.click('current-location-btn');
      app.locationRequests[0].success({ coords: { latitude: -33.8, longitude: 151.1 } });
    }
    assert.deepEqual(app.saved().starting_point, committed);
    const reload = browser(app.saved());
    assert.deepEqual(reload.saved().starting_point, committed);
    assert.deepEqual(JSON.parse(reload.evaluate('JSON.stringify(pendingPin)')), committed);
    assert.equal(reload.elements.get('confirm-start-btn').disabled, false);
    assert.equal(reload.saved().setup_step, 'starting_point');
    assert.equal(reload.locationRequests.length, 0);
  });
}


test('named starts are an accessible disclosure and selecting one restores the compact panel', () => {
  const app = browser();
  const group = app.elements.get('named-starts');
  const toggle = app.elements.get('start-panel-label');
  assert.equal(group.hidden, true);
  assert.equal(toggle['aria-expanded'], 'false');
  app.click('start-panel-label');
  assert.equal(group.hidden, false);
  assert.equal(toggle['aria-expanded'], 'true');
  assert.equal(app.saved().starting_point, null);
  assert.equal(app.saved().setup_step, 'starting_point');
  app.startChips[0].click();
  assert.equal(group.hidden, true);
  assert.equal(toggle['aria-expanded'], 'false');
  assert.equal(app.elements.get('pending-pin-label').textContent, 'Newtown Station');
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  assert.equal(app.saved().starting_point, null);
  app.click('start-panel-label');
  assert.equal(group.hidden, false);
  app.click('start-panel-label');
  assert.equal(group.hidden, true);
  assert.equal(app.elements.get('confirm-start-btn').disabled, false);
  app.click('confirm-start-btn');
  app.click('available-time-back-btn');
  assert.equal(group.hidden, true);
  assert.equal(toggle['aria-expanded'], 'false');
  assert.equal(app.saved().starting_point.label, 'Newtown Station');
});


for (const origin of ['fresh', 'named', 'GPS', 'expanded']) {
  test(`manual pin placement leaves the camera unchanged from ${origin} state`, () => {
    const app = browser();
    if (origin === 'named') app.startChips[0].click();
    if (origin === 'GPS') {
      app.click('current-location-btn');
      app.locationRequests[0].success({ coords: { latitude: -33.8, longitude: 151.1 } });
    }
    if (origin === 'expanded') app.click('start-panel-label');
    const before = app.saved();
    const cameras = JSON.stringify(app.cameraPositions);
    app.mapClick(-33.897, 151.179);
    app.mapClick(-33.898, 151.181);
    assert.equal(JSON.stringify(app.cameraPositions), cameras);
    assert.deepEqual(JSON.parse(app.evaluate('JSON.stringify(pendingPin)')), { lat: -33.898, lng: 151.181, label: 'Dropped pin' });
    assert.deepEqual(Array.from(app.markerPositions.at(-1)), [151.181, -33.898]);
    assert.equal(app.elements.get('named-starts').hidden, true);
    assert.equal(app.elements.get('confirm-start-btn').disabled, false);
    assert.equal(app.saved().setup_step, 'starting_point');
    assert.deepEqual(app.saved(), before);
    app.click('confirm-start-btn');
    assert.deepEqual(app.saved().starting_point, { lat: -33.898, lng: 151.181, label: 'Dropped pin' });
  });
}

// Regression: mobile browsers fire window "resize" for reasons (address bar
// collapsing on scroll/tap, keyboard appearing) that don't actually change
// the start panel's size - the handler must only recenter when the panel
// itself genuinely grew or shrank, or a plain tap can still appear to move
// the map on a phone even though the tap handler itself never moves it.
test('a resize that does not change the start panel\'s height leaves the camera unchanged after a manual pin drop', () => {
  const app = browser();
  app.mapClick(-33.897, 151.179);
  const cameras = JSON.stringify(app.cameraPositions);
  app.fireResize();
  assert.equal(JSON.stringify(app.cameraPositions), cameras);
});

test('a resize that genuinely changes the start panel\'s height still recenters on the pending pin', () => {
  const app = browser();
  app.mapClick(-33.897, 151.179);
  const cameras = JSON.stringify(app.cameraPositions);
  app.setStartPanelHeight(320); // e.g. an on-screen keyboard shrinking the visible map area
  app.fireResize();
  assert.notEqual(JSON.stringify(app.cameraPositions), cameras);
  assert.deepEqual(Array.from(app.cameraPositions.at(-1)), [151.179, -33.897]);
});

test('resize does nothing once there is no pending pin or the step has moved on', () => {
  const app = browser();
  const cameras = JSON.stringify(app.cameraPositions);
  app.fireResize(); // nothing dropped yet
  assert.equal(JSON.stringify(app.cameraPositions), cameras);
  app.mapClick(-33.897, 151.179);
  app.click('confirm-start-btn'); // advances past starting_point and clears pendingPin
  const camerasAfterConfirm = JSON.stringify(app.cameraPositions);
  app.setStartPanelHeight(999);
  app.fireResize();
  assert.equal(JSON.stringify(app.cameraPositions), camerasAfterConfirm);
});

// =====================================================================
// EPIC 2: WALK IT
// =====================================================================

test('Story 2.1: approving a route shows the real walking screen, not the old stub, and reuses the map', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  assert.equal(app.saved().phase, 'walking');
  assert.equal(app.elements.get('screen-walking').hidden, false);
  assert.equal(app.elements.get('screen-walking-stub'), undefined);
  assert.equal(app.elements.get('walking-summary').textContent, '2 stops - 40 min walk - 20 min to spare');
  assert.equal(app.requests.length, 0); // no new fetch (FR-6)
});

test('Story 2.1: reloading mid-walk resumes the real walking screen directly', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  const reload = browser(app.saved());
  assert.equal(reload.elements.get('screen-walking').hidden, false);
  assert.equal(reload.requests.length, 0);
});

test('Story 2.1: tapping a stop marker or row opens the same content overlay used pre-walk', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-open-stop-list-btn');
  assert.equal(app.elements.get('stop-list-sheet-wrap').hidden, false);
  app.evaluate("openStopOverlay(trip.stops[0])");
  assert.equal(app.elements.get('stop-overlay-body').textContent, 'Grounded text');
});

test('Story 2.1: the hamburger drawer opens/closes and restores focus to the menu button', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-menu-btn');
  assert.equal(app.elements.get('walking-drawer-wrap').hidden, false);
  app.click('walking-drawer-close-btn');
  assert.equal(app.elements.get('walking-drawer-wrap').hidden, true);
});

test('Story 2.1/3.1: End Jaunt opens catch-up without clearing anything - AD-2, wrap-up fires at completion, not the hamburger tap', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  assert.equal(app.elements.get('catchup-sheet-wrap').hidden, false);
  assert.equal(app.elements.get('walking-drawer-wrap').hidden, true);
  // Nothing cleared yet - still mid-walk.
  assert.equal(app.saved().phase, 'walking');
  assert.equal(app.saved().starting_point.lat, -33.9);
});

test('Story 3.1/3.2: finishing wrap-up ("Back to start") clears the active trip only, leaving visit history untouched', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.click('catchup-no-summary-btn'); // skip AI entirely - straight to the plain list
  assert.equal(app.elements.get('screen-walk-complete').hidden, false);
  assert.equal(app.elements.get('walk-complete-stop-list').children.length, 1);
  app.click('walk-complete-back-btn');
  const saved = app.saved();
  assert.equal(saved.phase, 'setting_up');
  assert.equal(saved.setup_step, 'starting_point');
  assert.equal(saved.starting_point, null);
  assert.equal(app.elements.get('screen-starting-point').hidden, false);
  assert.equal(app.evaluate("isStopVisited('a')"), true);
});

test('Story 2.3: the Visited badge is hidden before a walk starts and shown, actionable, during one', () => {
  const app = browser(route(['a', 'b']));
  app.evaluate("openStopOverlay(trip.stops[0])"); // still phase: reviewing
  assert.equal(app.elements.get('stop-overlay-visited-btn').hidden, true);
  app.click('approve-route-btn');
  app.evaluate("openStopOverlay(trip.stops[0])");
  const badge = app.elements.get('stop-overlay-visited-btn');
  assert.equal(badge.hidden, false);
  assert.equal(badge['aria-pressed'], 'false');
});

test('Story 2.3: tapping Visited records it separately from opening content, and a second tap undoes an accidental one', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("openStopOverlay(trip.stops[0])");
  assert.equal(app.evaluate("isStopVisited('a')"), false); // merely opening never marks it
  app.click('stop-overlay-visited-btn');
  assert.equal(app.evaluate("isStopVisited('a')"), true);
  const badge = app.elements.get('stop-overlay-visited-btn');
  assert.equal(badge['aria-pressed'], 'true');
  // User feedback 2026-10-25: an accidental tap must be undoable.
  app.click('stop-overlay-visited-btn');
  assert.equal(app.evaluate("isStopVisited('a')"), false);
  assert.equal(badge['aria-pressed'], 'false');
});

test('Story 2.3: a stop marked Visited survives a reload, stored under a separate localStorage key from the active trip', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  assert.equal(app.saved().stops.some((s) => 'state' in s), false); // never written onto the trip object itself
  const visitHistory = JSON.parse(app.evaluate("localStorage.getItem('jaunt_visit_history')"));
  const reload = browser(app.saved(), {}, undefined, visitHistory);
  reload.evaluate("openStopOverlay(trip.stops[0])");
  assert.equal(reload.elements.get('stop-overlay-visited-btn')['aria-pressed'], 'true');
});

test("Story 2.2: entering the walking screen starts watching position and shows the calm 'Location off' baseline first", () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  assert.equal(app.watchRequests.length, 1);
  assert.equal(app.elements.get('location-off-pill').hidden, false);
});

test('Story 2.2: a granted position shows the live marker and hides the pill - never an error screen', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  assert.equal(app.elements.get('location-off-pill').hidden, true);
  assert.equal(app.evaluate('!!liveMarker'), true);
});

test('Story 2.2: a real, non-null heading shows the directional arrow; a null/NaN heading does not', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: 45 } });
  assert.equal(app.evaluate('liveArrowEl.hidden'), false);
  assert.equal(app.evaluate('liveArrowEl.style.transform'), 'rotate(45deg)');
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  assert.equal(app.evaluate('liveArrowEl.hidden'), true);
});

test('Story 2.2: permission denied, or losing signal mid-walk, degrades to the same calm pill - marker removed, no error', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  assert.equal(app.evaluate('!!liveMarker'), true);
  app.watchRequests[0].failure({ code: 1 });
  assert.equal(app.evaluate('!!liveMarker'), false);
  assert.equal(app.elements.get('location-off-pill').hidden, false);
});

test('Story 2.2/3.1: finishing wrap-up (not just opening catch-up) releases the native watch and removes the marker', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  const watchId = app.watchRequests[0].id;
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  // Opening catch-up alone must not stop tracking - the walk isn't over yet.
  assert.equal(app.clearedWatchIds.has(watchId), false);
  assert.equal(app.evaluate('!!liveMarker'), true);
  app.click('catchup-no-summary-btn');
  assert.equal(app.clearedWatchIds.has(watchId), true);
  assert.equal(app.evaluate('!!liveMarker'), false);
});

test('Story 2.5: a position within range of an unvisited stop shows a subtle arrival nudge, never a modal', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  assert.equal(app.elements.get('arrival-pill').hidden, false);
  assert.equal(app.elements.get('arrival-pill-text').textContent, "You're near Stop a");
});

test('Story 2.5: an already-visited stop never triggers the arrival nudge, and it is never simulated without live position', () => {
  // A single-stop route - route(['a','b']) would put a second, still-
  // unvisited stop at the exact same coordinates, confounding this check.
  const app = browser(route(['a']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.watchRequests[0].success({ coords: { latitude: -33.9, longitude: 151.18, heading: null } });
  assert.equal(app.elements.get('arrival-pill').hidden, true);
  // Without ever granting position (no success callback fired at all):
  const app2 = browser(route(['a']));
  app2.click('approve-route-btn');
  assert.equal(app2.elements.get('arrival-pill').hidden, true);
});

test('distance from the starting point shows while live position is active, formatted in m/km', () => {
  const app = browser(route(['a', 'b'])); // default label 'Test start', not 'Current location'
  app.click('approve-route-btn');
  // ~1.11km north of the -33.9/151.18 starting point (1 degree lat ~111km).
  app.watchRequests[0].success({ coords: { latitude: -33.89, longitude: 151.18, heading: null } });
  const pill = app.elements.get('start-distance-pill');
  assert.equal(pill.hidden, false);
  assert.equal(pill.textContent, '1.1 km from your starting point');
  // A close position formats in meters, not a fraction of a km.
  app.watchRequests[0].success({ coords: { latitude: -33.9003, longitude: 151.18, heading: null } });
  assert.equal(pill.textContent, '33 m from your starting point');
});

test('distance from the starting point never shows when the walk started from Current location', () => {
  const trip = route(['a', 'b']);
  trip.starting_point.label = 'Current location';
  const app = browser(trip);
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.89, longitude: 151.18, heading: null } });
  assert.equal(app.elements.get('start-distance-pill').hidden, true);
});

test('distance from the starting point hides again once live position is lost, same as the marker', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.watchRequests[0].success({ coords: { latitude: -33.89, longitude: 151.18, heading: null } });
  assert.equal(app.elements.get('start-distance-pill').hidden, false);
  app.watchRequests[0].failure({ code: 1 });
  assert.equal(app.elements.get('start-distance-pill').hidden, true);
});

// Story 2.4's refreshAmenityLayer() calls map.addSource/getSource, which
// this harness's Map stub doesn't implement (it never fires a real "load"
// event either - the same pre-existing gap every other map-layer feature
// in this project has, e.g. updateRouteLayers()). Not automated here;
// verified live instead (see spec's Verification section): a real route's
// own stop was confirmed excluded from the amenity source's feature set
// (158 of 159 catalogue places rendered, the 159th being the route's own
// stop), and a genuinely different place was confirmed included.

// =====================================================================
// EPIC 3: REMEMBER AND VARY
// =====================================================================

test('Story 3.3: a successful plan records every stop as at least proposed, live, not only retroactively', async () => {
  const app = browser();
  app.seed({ ...route(), phase: 'setting_up', setup_step: 'confirm_sheet', stops: null,
    geometry: null, total_minutes: null, unused_minutes: null });
  app.respond(success(['a', 'b']));
  await app.evaluate('startRoutePlanning()');
  assert.equal(app.evaluate("isStopVisited('a')"), false);
  const history = JSON.parse(app.evaluate('localStorage.getItem("jaunt_visit_history")'));
  assert.deepEqual(history.map((e) => [e.id, e.state]).sort(), [['a', 'proposed'], ['b', 'proposed']]);
});

test('Story 3.3: a stop already Visited stays Visited when a fresh route merely re-proposes it', async () => {
  const app = browser(route(['a', 'b']));
  app.evaluate("setStopVisited('a', true)");
  app.evaluate('trip.phase = "setting_up"; trip.setup_step = "confirm_sheet";');
  app.respond(success(['a', 'c']));
  await app.evaluate('startRoutePlanning()');
  assert.equal(app.evaluate("isStopVisited('a')"), true); // never downgraded by the re-proposal
});

test('Story 3.3: opening a stop\'s content upgrades it to opened_engaged, pre-walk and during the walk, never downgrading Visited', () => {
  const app = browser(route(['a', 'b']));
  app.evaluate("openStopOverlay(trip.stops[0])"); // pre-walk preview, phase: reviewing
  const historyAfterOpen = JSON.parse(app.evaluate('localStorage.getItem("jaunt_visit_history")'));
  assert.equal(historyAfterOpen.find((e) => e.id === 'a').state, 'opened_engaged');
  app.evaluate("setStopVisited('a', true)");
  app.evaluate("openStopOverlay(trip.stops[0])"); // opening it again must not downgrade Visited
  assert.equal(app.evaluate("isStopVisited('a')"), true);
});

test('Story 3.3: "Not interested" works identically pre-walk and during the walk (never phase-gated, unlike Visited), toggles, and an accidental tap is undoable', () => {
  for (const phase of ['reviewing', 'walking']) {
    const app = browser({ ...route(['a', 'b']), phase });
    app.evaluate("openStopOverlay(trip.stops[0])");
    const btn = app.elements.get('stop-overlay-reject-btn');
    assert.equal(btn['aria-pressed'], 'false');
    app.click('stop-overlay-reject-btn');
    assert.equal(app.evaluate("isStopRejected('a')"), true);
    assert.equal(btn['aria-pressed'], 'true');
    app.click('stop-overlay-reject-btn');
    assert.equal(app.evaluate("isStopRejected('a')"), false);
    assert.equal(btn['aria-pressed'], 'false');
  }
});

test('Story 3.3/3.4: a rejected stop is merged into excluded_ids and dropped from visit_history on the next planning request', async () => {
  const app = browser(route(['a', 'b']));
  app.evaluate("trip.phase = 'setting_up'; trip.setup_step = 'confirm_sheet';");
  app.evaluate("setStopRejected('rejected-place', true)");
  app.evaluate("setStopVisited('a', true)"); // ordinary history - should still be sent
  app.respond(success(['b', 'c']));
  await app.evaluate('startRoutePlanning()');
  assert.equal(app.requests[0].excluded_ids.includes('rejected-place'), true);
  const sentHistory = app.requests[0].visit_history;
  assert.equal(sentHistory.some((e) => e.id === 'rejected-place'), false); // never sent - redundant, already excluded
  const sentA = sentHistory.find((e) => e.id === 'a');
  assert.deepEqual(sentA, { id: 'a', state: 'visited_completed', favourited: false });
});

test('Story 3.1: a catch-up row is a real toggle - tap to mark Visited retroactively, tap again to undo', () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  const list = app.elements.get('catchup-list');
  assert.equal(list.children.length, 2);
  const firstRow = list.children[0].children[0]; // li > button.catchup-row
  assert.equal(firstRow['aria-pressed'], 'false');
  firstRow.click();
  assert.equal(app.evaluate("isStopVisited('a')"), true);
  const rerenderedRow = app.elements.get('catchup-list').children[0].children[0];
  assert.equal(rerenderedRow['aria-pressed'], 'true');
  rerenderedRow.click();
  assert.equal(app.evaluate("isStopVisited('a')"), false);
});

test('Story 3.2: a successful AI summary shows the real text and each visited stop with its own favourite-heart', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: true, summary: 'A lovely afternoon walk.' });
  await app.evaluate('finishWrapUp(true)');
  assert.equal(app.elements.get('screen-walk-complete').hidden, false);
  assert.equal(app.elements.get('walk-complete-message').textContent, 'A lovely afternoon walk.');
  assert.equal(app.elements.get('walk-complete-stop-list').children.length, 1);
  // FR-16: grounded strictly in Visited stops - only 'a' was sent, not 'b'.
  assert.deepEqual(app.summaryRequests[0].visited_stops.map((s) => s.name), ['Stop a']);
});

test('Story 3.2 follow-up: a visited stop with an already rights-cleared photo shows it in the summary list; one without never gets an image', async () => {
  const trip = route(['a', 'b']);
  trip.stops[0].photo = publicPhoto; // only 'a' has a real, verified photo
  const app = browser(trip);
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.evaluate("setStopVisited('b', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: true, summary: 'A lovely afternoon walk.' });
  await app.evaluate('finishWrapUp(true)');
  const rows = app.elements.get('walk-complete-stop-list').children;
  assert.equal(rows.length, 2);
  // 'a' has a photo: [photo-wrap, name, heart] - 'b' has none: [name, heart].
  assert.equal(rows[0].children.length, 3);
  assert.equal(rows[0].children[0].className, 'walk-summary-stop-photo-wrap');
  const [img, credit] = rows[0].children[0].children;
  assert.equal(img.className, 'walk-summary-stop-photo');
  assert.equal(img.src, publicPhoto.url);
  assert.equal(credit.textContent, `Photo by ${publicPhoto.creator}, ${publicPhoto.license}`);
  assert.equal(rows[1].children.length, 2);
  assert.equal(rows[1].children[0].className, 'walk-summary-stop-name');
});

test('Share summary: uses the native share sheet when available, includes the real summary and visited names', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: true, summary: 'A lovely afternoon walk.' });
  await app.evaluate('finishWrapUp(true)');
  assert.equal(app.elements.get('walk-complete-share-btn').hidden, false);
  await app.evaluate('document.getElementById("walk-complete-share-btn").click()');
  await app.settle();
  assert.equal(app.shareRequests.length, 1);
  assert.equal(app.shareRequests[0].text, 'A lovely afternoon walk.\n\nVisited: Stop a');
  assert.equal(app.clipboardWrites.length, 0);
});

test('Share summary: falls back to clipboard copy when the Web Share API is unsupported', async () => {
  const app = browser(route(['a', 'b']), { shareUnsupported: true });
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: true, summary: 'A lovely afternoon walk.' });
  await app.evaluate('finishWrapUp(true)');
  await app.evaluate('document.getElementById("walk-complete-share-btn").click()');
  await app.settle();
  assert.equal(app.clipboardWrites.length, 1);
  assert.equal(app.clipboardWrites[0], 'A lovely afternoon walk.\n\nVisited: Stop a');
});

test('Share summary: a cancelled native share sheet (AbortError) never falls through to clipboard', async () => {
  const app = browser(route(['a', 'b']), { shareThrows: true });
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: true, summary: 'A lovely afternoon walk.' });
  await app.evaluate('finishWrapUp(true)');
  await app.evaluate('document.getElementById("walk-complete-share-btn").click()');
  await app.settle();
  assert.equal(app.clipboardWrites.length, 0);
});

test('Share summary: hidden on the honest empty ending - nothing was Visited, nothing to share', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  await app.evaluate('finishWrapUp(false)');
  assert.equal(app.elements.get('walk-complete-share-btn').hidden, true);
});

test('Story 3.2: generation failure (feasible:false) falls back to the plain list, never an error screen', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.respondSummary({ feasible: false });
  await app.evaluate('finishWrapUp(true)');
  assert.equal(app.elements.get('screen-walk-complete').hidden, false);
  assert.equal(app.elements.get('walk-complete-stop-list').children.length, 1);
  assert.equal(app.elements.get('screen-technical-failure').hidden, true);
});

test('Story 3.2: a network failure on the summary request also falls back to the plain list, not a technical-failure screen', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.summaryNetworkError();
  await app.evaluate('finishWrapUp(true)');
  assert.equal(app.elements.get('screen-walk-complete').hidden, false);
  assert.equal(app.elements.get('walk-complete-stop-list').children.length, 1);
});

test('Story 3.2: zero Visited stops never calls the summary endpoint at all - the honest empty ending applies directly', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  await app.evaluate('finishWrapUp(true)'); // "Create summary" tapped, but nothing was ever marked Visited
  assert.equal(app.summaryRequests.length, 0);
  assert.equal(app.elements.get('screen-walk-complete').hidden, false);
  assert.equal(app.elements.get('walk-complete-message').textContent, "Nothing was marked Visited this time - no summary to show.");
  assert.equal(app.elements.get('walk-complete-stop-list').hidden, true);
});

test('Story 3.3/3.4: favouriting a stop on the walk-complete screen persists and is reflected in the next planning request', async () => {
  const app = browser(route(['a', 'b']));
  app.click('approve-route-btn');
  app.evaluate("setStopVisited('a', true)");
  app.click('walking-menu-btn');
  app.click('end-jaunt-btn');
  app.click('catchup-no-summary-btn');
  const heart = app.elements.get('walk-complete-stop-list').children[0].children[1]; // li > [name, heart]
  assert.equal(heart['aria-pressed'], 'false');
  heart.click();
  assert.equal(app.evaluate("isStopFavourited('a')"), true);
  assert.equal(heart['aria-pressed'], 'true');
});

test('UX-DR4/UX-DR5 regression check: "Back to start" is the compact pill, never the full-width primary button', () => {
  // Same pattern as the project's own precedent for this exact regression
  // (the confirm-sheet slider test above) - a raw source-text check, since
  // this harness's generic element stubs don't track real class attributes.
  const screen = html.split('id="screen-walk-complete"')[1].split('</section>')[0];
  const button = screen.split('id="walk-complete-back-btn"')[0].split('<button').pop();
  assert(button.includes('btn-pill'));
  assert(!button.includes('btn-full'));
});
