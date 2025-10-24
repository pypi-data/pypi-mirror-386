var fr = Object.defineProperty;
var dr = (e, t, n) => t in e ? fr(e, t, { enumerable: !0, configurable: !0, writable: !0, value: n }) : e[t] = n;
var Y = (e, t, n) => dr(e, typeof t != "symbol" ? t + "" : t, n);
import * as hr from "vue";
import { toRaw as hn, toValue as be, normalizeClass as ut, normalizeStyle as pr, cloneVNode as se, vModelDynamic as mr, vShow as gr, withDirectives as pn, h as G, toDisplayString as mn, withModifiers as yr, resolveDynamicComponent as vr, normalizeProps as wr, TransitionGroup as _r, createTextVNode as Er, unref as K, toRef as me, readonly as kt, customRef as ye, ref as U, onBeforeUnmount as br, onMounted as gn, nextTick as Se, getCurrentScope as Sr, onScopeDispose as kr, getCurrentInstance as Ke, watch as q, isRef as Rt, shallowRef as ae, watchEffect as Ot, computed as L, inject as ce, shallowReactive as Rr, defineComponent as Z, reactive as Or, provide as H, onUnmounted as Nr, onErrorCaptured as Pr, openBlock as fe, createElementBlock as Ee, createElementVNode as yn, createVNode as Vr, createCommentVNode as ft, mergeProps as de, createBlock as vn, Teleport as Cr, renderSlot as Ar, useAttrs as xr, Fragment as $r, useSlots as Me, KeepAlive as Tr } from "vue";
let wn;
function Ir(e) {
  wn = e;
}
function dt() {
  return wn;
}
function Ue() {
  const { queryPath: e, pathParams: t, queryParams: n } = dt();
  return {
    path: e,
    ...t === void 0 ? {} : { params: t },
    ...n === void 0 ? {} : { queryParams: n }
  };
}
function Dt(e, t) {
  Object.entries(e).forEach(([n, r]) => t(r, n));
}
function Ge(e, t) {
  return _n(e, {
    valueFn: t
  });
}
function _n(e, t) {
  const { valueFn: n, keyFn: r } = t;
  return Object.fromEntries(
    Object.entries(e).map(([s, o], i) => [
      r ? r(s, o) : s,
      n(o, s, i)
    ])
  );
}
function Dr(e, t, n) {
  if (Array.isArray(t)) {
    const [s, ...o] = t;
    switch (s) {
      case "!":
        return !e;
      case "+":
        return e + o[0];
      case "~+":
        return o[0] + e;
    }
  }
  const r = Mr(t);
  return e[r];
}
function Mr(e, t) {
  if (typeof e == "string" || typeof e == "number")
    return e;
  if (!Array.isArray(e))
    throw new Error(`Invalid path ${e}`);
  const [n, ...r] = e;
  switch (n) {
    case "bind":
      throw new Error("No bindable function provided");
    default:
      throw new Error(`Invalid flag ${n} in array at ${e}`);
  }
}
function jr(e, t, n) {
  return t.reduce(
    (r, s) => Dr(r, s),
    e
  );
}
function Lr(e, t) {
  return t ? t.reduce((n, r) => n[r], e) : e;
}
const Br = window.structuredClone || ((e) => JSON.parse(JSON.stringify(e)));
function En(e) {
  if (typeof e == "function")
    return e;
  try {
    return Br(hn(be(e)));
  } catch {
    return e;
  }
}
function Fr(e, t) {
  const n = e.classes;
  if (!n)
    return null;
  if (typeof n == "string")
    return ut(n);
  const { str: r, map: s, bind: o } = n, { bindingGetter: i } = t, a = [];
  return r && a.push(r), s && a.push(
    Ge(
      s,
      (c) => i.getValue(c)
    )
  ), o && a.push(...o.map((c) => i.getValue(c))), ut(a);
}
function Wr(e, t) {
  const n = [], { bindingGetter: r } = t, { dStyle: s = {}, sStyle: o = [] } = e;
  n.push(
    Ge(
      s || {},
      (c) => r.getValue(c)
    )
  ), n.push(
    ...o.map((c) => r.getValue(c))
  );
  const i = pr([e.style || {}, n]);
  return {
    hasStyle: i && Object.keys(i).length > 0,
    styles: i
  };
}
function Ur(e, t, n) {
  const r = [], { dir: s = [] } = t, { bindingGetter: o } = n;
  return s.forEach((i) => {
    const { sys: a, name: c, arg: h, value: u, mf: l } = i;
    if (c === "vmodel") {
      const f = o.getRef(u);
      if (e = se(e, {
        [`onUpdate:${h}`]: (d) => {
          f.value = d;
        }
      }), a === 1) {
        const d = l ? Object.fromEntries(l.map((p) => [p, !0])) : {};
        r.push([mr, f.value, void 0, d]);
      } else
        e = se(e, {
          [h]: f.value
        });
    } else if (c === "vshow") {
      const f = o.getValue(u);
      r.push([gr, f]);
    } else
      console.warn(`Directive ${c} is not supported yet`);
  }), r.length > 0 ? pn(e, r) : e;
}
function Te(e, t) {
  return G(ir, {
    config: e,
    vforSetting: t == null ? void 0 : t.vforSetting,
    slotSetting: t == null ? void 0 : t.slotSetting
  });
}
function Hr(e, t, n) {
  if (!e.slots)
    return;
  const r = e.slots ?? {};
  if (t) {
    const a = r[":"];
    if (!a)
      return;
    const { scope: c, items: h } = a;
    return c ? Te(c, {
      buildOptions: n
    }) : h == null ? void 0 : h.map((u) => ve(u, n));
  }
  return _n(r, { keyFn: (a) => a === ":" ? "default" : a, valueFn: (a) => {
    const { usePropId: c, scope: h } = a;
    return h ? (u) => Te(h, {
      buildOptions: n,
      slotSetting: c ? {
        id: c,
        value: u
      } : void 0
    }) : () => {
      var u;
      return (u = a.items) == null ? void 0 : u.map((l) => ve(l, n));
    };
  } });
}
function J(e, t) {
  t = t || {};
  const n = [...Object.keys(t), "__Vue"], r = [...Object.values(t), hr];
  try {
    return new Function(...n, `return (${e})`)(...r);
  } catch (s) {
    throw new Error(s + " in function code: " + e);
  }
}
function He(e, t = !0) {
  if (!(typeof e != "object" || e === null)) {
    if (Array.isArray(e)) {
      t && e.forEach((n) => He(n, !0));
      return;
    }
    for (const [n, r] of Object.entries(e))
      if (n.startsWith(":"))
        try {
          e[n.slice(1)] = new Function(`return (${r})`)(), delete e[n];
        } catch (s) {
          console.error(
            `Error while converting ${n} attribute to function:`,
            s
          );
        }
      else
        t && He(r, !0);
  }
}
function zr(e, t) {
  const n = e.startsWith(":");
  return n && (e = e.slice(1), t = J(t)), { name: e, value: t, isFunc: n };
}
class Kr {
  toString() {
    return "";
  }
}
const Ie = new Kr();
function ke(e) {
  return hn(e) === Ie;
}
function Gr(e, t) {
  var o;
  const n = {}, r = e.props ?? {}, { bindingGetter: s } = t;
  return He(r), Dt(e.bProps || {}, (i, a) => {
    const c = s.getValue(i);
    ke(c) || (He(c), n[a] = qr(c, a));
  }), (o = e.proxyProps) == null || o.forEach((i) => {
    const a = s.getValue(i);
    typeof a == "object" && Dt(a, (c, h) => {
      const { name: u, value: l } = zr(h, c);
      n[u] = l;
    });
  }), { ...r, ...n };
}
function qr(e, t) {
  return t === "innerText" ? mn(e) : e;
}
function Nt(e) {
  return e !== null && typeof e == "object" && e.nodeType === 1 && typeof e.nodeName == "string";
}
class Jr {
  async eventSend(t, n) {
    const { fType: r, hKey: s, key: o } = t, i = dt().webServerInfo, a = o !== void 0 ? { key: o } : {}, c = r === "sync" ? i.event_url : i.event_async_url;
    let h = {};
    const u = await fetch(c, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        bind: n,
        hKey: s,
        ...a,
        page: Ue(),
        ...h
      })
    });
    if (!u.ok)
      throw new Error(`HTTP error! status: ${u.status}`);
    return await u.json();
  }
  async watchSend(t) {
    const { fType: n, key: r } = t.watchConfig, s = dt().webServerInfo, o = n === "sync" ? s.watch_url : s.watch_async_url, i = t.getServerInputs(), a = {
      key: r,
      input: i,
      page: Ue()
    };
    return await (await fetch(o, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(a)
    })).json();
  }
}
class Qr {
  async eventSend(t, n) {
    const { fType: r, hKey: s, key: o } = t, i = o !== void 0 ? { key: o } : {};
    let a = {};
    const c = {
      bind: n,
      fType: r,
      hKey: s,
      ...i,
      page: Ue(),
      ...a
    };
    return await window.pywebview.api.event_call(c);
  }
  async watchSend(t) {
    const { fType: n, key: r } = t.watchConfig, s = t.getServerInputs(), o = {
      key: r,
      input: s,
      fType: n,
      page: Ue()
    };
    return await window.pywebview.api.watch_call(o);
  }
}
let ht;
function Yr(e) {
  switch (e) {
    case "web":
      ht = new Jr();
      break;
    case "webview":
      ht = new Qr();
      break;
  }
}
function bn() {
  return ht;
}
function Sn(e) {
  const { config: t, bindingGetter: n } = e;
  if (!t)
    return {
      run: () => {
      },
      tryReset: () => {
      }
    };
  const r = t.map((i) => {
    const [a, c, h] = i, u = n.getRef(a);
    function l(f, d) {
      const { type: p, value: m } = d;
      if (p === "const") {
        f.value = m;
        return;
      }
      if (p === "action") {
        const y = Xr(m, n);
        f.value = y;
        return;
      }
    }
    return {
      run: () => l(u, c),
      reset: () => l(u, h)
    };
  });
  return {
    run: () => {
      r.forEach((i) => i.run());
    },
    tryReset: () => {
      r.forEach((i) => i.reset());
    }
  };
}
function Xr(e, t) {
  const { inputs: n = [], code: r } = e, s = J(r), o = n.map((i) => t.getValue(i));
  return s(...o);
}
function Mt(e) {
  return e == null;
}
const re = {
  Ref: 0,
  EventContext: 1,
  Data: 2,
  JsFn: 3,
  ElementRef: 4,
  EventContextDataset: 5
}, jt = {
  const: "c",
  ref: "r",
  range: "n"
}, Ae = {
  Ref: 0,
  RouterAction: 1,
  ElementRefAction: 2,
  JsCode: 3
};
function qe(e, t, n) {
  if (Mt(t) || Mt(e.values))
    return;
  t = t;
  const r = e.values, s = e.types ?? Array.from({ length: t.length }).fill(0);
  t.forEach((o, i) => {
    const a = s[i];
    if (a === 1)
      return;
    if (o.type === Ae.Ref) {
      if (a === 2) {
        r[i].forEach(([u, l]) => {
          const f = o.ref, d = {
            ...f,
            path: [...f.path ?? [], ...u]
          };
          n.updateValue(d, l);
        });
        return;
      }
      n.updateValue(o.ref, r[i]);
      return;
    }
    if (o.type === Ae.RouterAction) {
      const h = r[i], u = n.getRouter(o.ref)[h.fn];
      u(...h.args);
      return;
    }
    if (o.type === Ae.ElementRefAction) {
      const h = o.ref, u = n.getRef(h).value, l = r[i], { method: f, args: d = [] } = l;
      u[f](...d);
      return;
    }
    if (o.type === Ae.JsCode) {
      const h = r[i];
      if (!h)
        return;
      const u = J(h);
      Promise.resolve(u());
      return;
    }
    const c = n.getRef(o.ref);
    c.value = r[i];
  });
}
class Zr extends Map {
  constructor(t) {
    super(), this.factory = t;
  }
  getOrDefault(t) {
    if (!this.has(t)) {
      const n = this.factory();
      return this.set(t, n), n;
    }
    return super.get(t);
  }
}
function kn(e) {
  return new Zr(e);
}
const es = "on:mounted";
function ts(e, t, n) {
  if (!t)
    return e;
  const r = kn(() => []);
  t.map(([a, c]) => {
    const h = ns(c, n), { eventName: u, handleEvent: l } = as({
      eventName: a,
      info: c,
      handleEvent: h
    });
    r.getOrDefault(u).push(l);
  });
  const s = {};
  for (const [a, c] of r) {
    const h = c.length === 1 ? c[0] : (...u) => c.forEach((l) => Promise.resolve().then(() => l(...u)));
    s[a] = h;
  }
  const { [es]: o, ...i } = s;
  return e = se(e, i), o && (e = pn(e, [
    [
      {
        mounted(a) {
          o(a);
        }
      }
    ]
  ])), e;
}
function ns(e, t) {
  if (e.type === "web") {
    const n = rs(e, t);
    return ss(e, n, t);
  } else {
    if (e.type === "vue")
      return is(e, t);
    if (e.type === "js")
      return os(e, t);
  }
  throw new Error(`unknown event type ${e}`);
}
function rs(e, t) {
  const { inputs: n = [] } = e, { bindingGetter: r } = t;
  return (...s) => n.map(({ value: o, type: i }) => {
    if (i === re.EventContext || i === re.EventContextDataset) {
      const { path: a } = o;
      if (a.startsWith(":")) {
        const c = a.slice(1);
        return J(c)(...s);
      }
      return Lr(s[0], a.split("."));
    }
    return i === re.Ref ? r.getValue(o) : o;
  });
}
function ss(e, t, n) {
  const { bindingGetter: r } = n;
  async function s(...o) {
    const i = t(...o), a = Sn({
      config: e.preSetup,
      bindingGetter: r
    });
    try {
      a.run();
      const c = await bn().eventSend(e, i);
      if (!c)
        return;
      qe(c, e.sets, r);
    } finally {
      a.tryReset();
    }
  }
  return s;
}
function os(e, t) {
  const { sets: n, code: r, inputs: s = [] } = e, { bindingGetter: o } = t, i = J(r);
  function a(...c) {
    const h = s.map(({ value: l, type: f }) => {
      const d = f === re.EventContextDataset;
      if (f === re.EventContext || d) {
        if (l.path.startsWith(":")) {
          const p = l.path.slice(1), m = J(p)(...c);
          return m == null ? m : d ? JSON.parse(m) : m;
        }
        return jr(c[0], l.path.split("."));
      }
      if (f === re.Ref)
        return o.getValue(l);
      if (f === re.Data)
        return l;
      if (f === re.ElementRef) {
        const p = o.getValue(l);
        return p && (Nt(p) ? p : p.$el);
      }
      if (f === re.JsFn)
        return o.getValue(l);
      throw new Error(`unknown input type ${f}`);
    }), u = i(...h);
    if (n !== void 0) {
      const f = n.length === 1 ? [u] : u, d = f.map((p) => p === void 0 ? 1 : 0);
      qe(
        { values: f, types: d },
        n,
        o
      );
    }
  }
  return a;
}
function is(e, t) {
  const { code: n, inputs: r = {} } = e, { bindingGetter: s } = t, o = Ge(
    r,
    (c) => c.type !== re.Data ? s.getRef(c.value) : c.value
  ), i = J(n, o);
  function a(...c) {
    i(...c);
  }
  return a;
}
function as(e) {
  const { eventName: t, info: n, handleEvent: r } = e;
  if (n.type === "vue")
    return {
      eventName: t,
      handleEvent: r
    };
  const { modifier: s = [] } = n;
  if (s.length === 0)
    return {
      eventName: t,
      handleEvent: r
    };
  const o = ["passive", "capture", "once"], i = [], a = [];
  for (const u of s)
    o.includes(u) ? i.push(u[0].toUpperCase() + u.slice(1)) : a.push(u);
  const c = i.length > 0 ? t + i.join("") : t, h = a.length > 0 ? yr(r, a) : r;
  return {
    eventName: c,
    handleEvent: h
  };
}
function cs(e, t, n) {
  const { eRef: r } = t, { bindingGetter: s } = n;
  return r ? se(e, { ref: s.getRef(r) }) : e;
}
function ls(e, t) {
  const n = us(e, t), r = vr(n), s = typeof r == "string", o = Fr(e, t), { styles: i, hasStyle: a } = Wr(e, t), c = Hr(e, s, t), h = Gr(e, t), u = wr(h) || {};
  a && (u.style = i), o && (u.class = o);
  let l = G(r, { ...u }, c);
  return l = ts(l, e.events, t), l = cs(l, e, t), Ur(l, e, t);
}
function us(e, t) {
  const { tag: n } = e;
  return typeof n == "string" ? n : t.bindingGetter.getValue(n);
}
function fs(e, t) {
  var l, f, d;
  const { fkey: n, tsGroup: r = {}, scope: s } = e, o = !!((l = e.used) != null && l.item), i = !!((f = e.used) != null && f.index), a = !!((d = e.used) != null && d.key), c = [], { sourceInfo: h, iterSource: u } = ds(e, t);
  for (const [p, m, y] of u) {
    const _ = {};
    o && (_.item = {
      value: m,
      id: e.used.item
    }, h && (_.item.sourceInfo = {
      source: h.source,
      type: h.type,
      index: p,
      key: y
    })), i && (_.index = {
      value: p,
      id: e.used.index
    }), a && (_.key = {
      value: y,
      id: e.used.key
    });
    let w = Te(s, {
      buildOptions: t,
      vforSetting: _
    });
    const k = ms(n, { value: m, index: p });
    w = se(w, { key: k }), c.push(w);
  }
  return r && Object.keys(r).length > 0 ? G(_r, r, {
    default: () => c
  }) : c;
}
function ds(e, t) {
  const { type: n, value: r } = e.array, { bindingGetter: s } = t, o = n === jt.range, i = n === jt.const || o && typeof r == "number";
  if (o) {
    const { start: a = 0, end: c, step: h = 1 } = r, u = typeof a == "number" ? a : s.getValue(a), l = typeof c == "number" ? c : s.getValue(c), f = typeof h == "number" ? h : s.getValue(h);
    return {
      sourceInfo: void 0,
      iterSource: Lt(u, l, f)
    };
  }
  {
    const a = i ? r : s.getValue(e.array.value);
    if (typeof a == "number")
      return {
        sourceInfo: void 0,
        iterSource: Lt(0, a, 1)
      };
    if (Array.isArray(a)) {
      function* c() {
        for (let h = 0; h < a.length; h++)
          yield [h, a[h]];
      }
      return {
        sourceInfo: i ? void 0 : {
          source: s.getRef(e.array.value),
          type: "array"
        },
        iterSource: c()
      };
    }
    if (typeof a == "object" && a !== null) {
      function* c() {
        let h = 0;
        for (const [u, l] of Object.entries(a))
          yield [h++, l, u];
      }
      return {
        sourceInfo: i ? void 0 : {
          source: s.getRef(e.array.value),
          type: "object"
        },
        iterSource: c()
      };
    }
    if (ke(a))
      return a;
  }
  throw new Error("Not implemented yet");
}
function* Lt(e, t, n = 1) {
  if (n === 0)
    throw new Error("Step cannot be 0");
  let r = 0;
  if (n > 0)
    for (let s = e; s < t; s += n)
      yield [r++, s];
  else
    for (let s = e; s > t; s += n)
      yield [r++, s];
}
const hs = (e) => e, ps = (e, t) => t;
function ms(e, t) {
  const { value: n, index: r } = t, s = gs(e ?? "index");
  return typeof s == "function" ? s(n, r) : e === "item" ? hs(n) : ps(n, r);
}
function gs(e) {
  const t = e.trim();
  if (t === "item" || t === "index")
    return;
  if (e.startsWith(":")) {
    e = e.slice(1);
    try {
      return J(e);
    } catch (r) {
      throw new Error(r + " in function code: " + e);
    }
  }
  const n = `(item, index) => { return ${t}; }`;
  try {
    return J(n);
  } catch (r) {
    throw new Error(r + " in function code: " + n);
  }
}
function ys(e, t) {
  const { on: n, items: r } = e;
  return (typeof n == "boolean" ? n : t.bindingGetter.getValue(n)) ? r == null ? void 0 : r.map((o) => ve(o, t)) : void 0;
}
function vs(e, t) {
  const { cond: n, const: r = 0, cases: s, default: o } = e, a = r === 1 ? n : t.bindingGetter.getValue(n), c = [];
  let h = !1;
  for (const { value: u, items: l = [] } of s || [])
    if (u === a) {
      c.push(...l.map((f) => ve(f, t))), h = !0;
      break;
    }
  return !h && o && o.items && c.push(
    ...o.items.map((u) => ve(u, t))
  ), c;
}
function ws(e, t) {
  const { value: n, r = 0 } = e, s = r === 1 ? t.bindingGetter.getValue(n) : n;
  return Er(s);
}
const _s = /* @__PURE__ */ new Map(
  [
    ["vfor", fs],
    ["vif", ys],
    ["match", vs],
    ["content", ws]
  ]
);
function Es(e, t) {
  const n = _s.get(e.tag);
  if (!n)
    throw new Error(`Unknown logic component ${e.tag}`);
  return n(e, t);
}
function ve(e, t) {
  const { type: n } = e;
  if (n === "cp")
    return ls(e, t);
  if (n === "logic")
    return Es(e, t);
  if (n === "scope")
    return Te(e, {
      buildOptions: t
    });
  throw new Error(`Unknown component type ${n}`);
}
function Rn(e) {
  return "r" in e;
}
function Pt(e) {
  return Sr() ? (kr(e), !0) : !1;
}
function te(e) {
  return typeof e == "function" ? e() : K(e);
}
const On = typeof window < "u" && typeof document < "u";
typeof WorkerGlobalScope < "u" && globalThis instanceof WorkerGlobalScope;
const bs = (e) => e != null, Ss = Object.prototype.toString, ks = (e) => Ss.call(e) === "[object Object]", De = () => {
};
function Rs(e, t) {
  function n(...r) {
    return new Promise((s, o) => {
      Promise.resolve(e(() => t.apply(this, r), { fn: t, thisArg: this, args: r })).then(s).catch(o);
    });
  }
  return n;
}
const Nn = (e) => e();
function Os(e = Nn) {
  const t = U(!0);
  function n() {
    t.value = !1;
  }
  function r() {
    t.value = !0;
  }
  const s = (...o) => {
    t.value && e(...o);
  };
  return { isActive: kt(t), pause: n, resume: r, eventFilter: s };
}
function pt(e, t = !1, n = "Timeout") {
  return new Promise((r, s) => {
    setTimeout(t ? () => s(n) : r, e);
  });
}
function Pn(e) {
  return Ke();
}
function Vn(...e) {
  if (e.length !== 1)
    return me(...e);
  const t = e[0];
  return typeof t == "function" ? kt(ye(() => ({ get: t, set: De }))) : U(t);
}
function Ns(e, t, n = {}) {
  const {
    eventFilter: r = Nn,
    ...s
  } = n;
  return q(
    e,
    Rs(
      r,
      t
    ),
    s
  );
}
function Ps(e, t, n = {}) {
  const {
    eventFilter: r,
    ...s
  } = n, { eventFilter: o, pause: i, resume: a, isActive: c } = Os(r);
  return { stop: Ns(
    e,
    t,
    {
      ...s,
      eventFilter: o
    }
  ), pause: i, resume: a, isActive: c };
}
function Vs(e, t) {
  Pn() && br(e, t);
}
function Cn(e, t = !0, n) {
  Pn() ? gn(e, n) : t ? e() : Se(e);
}
function mt(e, t = !1) {
  function n(l, { flush: f = "sync", deep: d = !1, timeout: p, throwOnTimeout: m } = {}) {
    let y = null;
    const w = [new Promise((k) => {
      y = q(
        e,
        (v) => {
          l(v) !== t && (y ? y() : Se(() => y == null ? void 0 : y()), k(v));
        },
        {
          flush: f,
          deep: d,
          immediate: !0
        }
      );
    })];
    return p != null && w.push(
      pt(p, m).then(() => te(e)).finally(() => y == null ? void 0 : y())
    ), Promise.race(w);
  }
  function r(l, f) {
    if (!Rt(l))
      return n((v) => v === l, f);
    const { flush: d = "sync", deep: p = !1, timeout: m, throwOnTimeout: y } = f ?? {};
    let _ = null;
    const k = [new Promise((v) => {
      _ = q(
        [e, l],
        ([R, A]) => {
          t !== (R === A) && (_ ? _() : Se(() => _ == null ? void 0 : _()), v(R));
        },
        {
          flush: d,
          deep: p,
          immediate: !0
        }
      );
    })];
    return m != null && k.push(
      pt(m, y).then(() => te(e)).finally(() => (_ == null || _(), te(e)))
    ), Promise.race(k);
  }
  function s(l) {
    return n((f) => !!f, l);
  }
  function o(l) {
    return r(null, l);
  }
  function i(l) {
    return r(void 0, l);
  }
  function a(l) {
    return n(Number.isNaN, l);
  }
  function c(l, f) {
    return n((d) => {
      const p = Array.from(d);
      return p.includes(l) || p.includes(te(l));
    }, f);
  }
  function h(l) {
    return u(1, l);
  }
  function u(l = 1, f) {
    let d = -1;
    return n(() => (d += 1, d >= l), f);
  }
  return Array.isArray(te(e)) ? {
    toMatch: n,
    toContains: c,
    changed: h,
    changedTimes: u,
    get not() {
      return mt(e, !t);
    }
  } : {
    toMatch: n,
    toBe: r,
    toBeTruthy: s,
    toBeNull: o,
    toBeNaN: a,
    toBeUndefined: i,
    changed: h,
    changedTimes: u,
    get not() {
      return mt(e, !t);
    }
  };
}
function Cs(e) {
  return mt(e);
}
function As(e, t, n) {
  let r;
  Rt(n) ? r = {
    evaluating: n
  } : r = n || {};
  const {
    lazy: s = !1,
    evaluating: o = void 0,
    shallow: i = !0,
    onError: a = De
  } = r, c = U(!s), h = i ? ae(t) : U(t);
  let u = 0;
  return Ot(async (l) => {
    if (!c.value)
      return;
    u++;
    const f = u;
    let d = !1;
    o && Promise.resolve().then(() => {
      o.value = !0;
    });
    try {
      const p = await e((m) => {
        l(() => {
          o && (o.value = !1), d || m();
        });
      });
      f === u && (h.value = p);
    } catch (p) {
      a(p);
    } finally {
      o && f === u && (o.value = !1), d = !0;
    }
  }), s ? L(() => (c.value = !0, h.value)) : h;
}
const Re = On ? window : void 0, xs = On ? window.document : void 0;
function Vt(e) {
  var t;
  const n = te(e);
  return (t = n == null ? void 0 : n.$el) != null ? t : n;
}
function Bt(...e) {
  let t, n, r, s;
  if (typeof e[0] == "string" || Array.isArray(e[0]) ? ([n, r, s] = e, t = Re) : [t, n, r, s] = e, !t)
    return De;
  Array.isArray(n) || (n = [n]), Array.isArray(r) || (r = [r]);
  const o = [], i = () => {
    o.forEach((u) => u()), o.length = 0;
  }, a = (u, l, f, d) => (u.addEventListener(l, f, d), () => u.removeEventListener(l, f, d)), c = q(
    () => [Vt(t), te(s)],
    ([u, l]) => {
      if (i(), !u)
        return;
      const f = ks(l) ? { ...l } : l;
      o.push(
        ...n.flatMap((d) => r.map((p) => a(u, d, p, f)))
      );
    },
    { immediate: !0, flush: "post" }
  ), h = () => {
    c(), i();
  };
  return Pt(h), h;
}
function $s() {
  const e = U(!1), t = Ke();
  return t && gn(() => {
    e.value = !0;
  }, t), e;
}
function An(e) {
  const t = $s();
  return L(() => (t.value, !!e()));
}
function Ts(e, t, n = {}) {
  const { window: r = Re, ...s } = n;
  let o;
  const i = An(() => r && "MutationObserver" in r), a = () => {
    o && (o.disconnect(), o = void 0);
  }, c = L(() => {
    const f = te(e), d = (Array.isArray(f) ? f : [f]).map(Vt).filter(bs);
    return new Set(d);
  }), h = q(
    () => c.value,
    (f) => {
      a(), i.value && f.size && (o = new MutationObserver(t), f.forEach((d) => o.observe(d, s)));
    },
    { immediate: !0, flush: "post" }
  ), u = () => o == null ? void 0 : o.takeRecords(), l = () => {
    h(), a();
  };
  return Pt(l), {
    isSupported: i,
    stop: l,
    takeRecords: u
  };
}
function Is(e, t, n) {
  const {
    immediate: r = !0,
    delay: s = 0,
    onError: o = De,
    onSuccess: i = De,
    resetOnExecute: a = !0,
    shallow: c = !0,
    throwError: h
  } = {}, u = c ? ae(t) : U(t), l = U(!1), f = U(!1), d = ae(void 0);
  async function p(_ = 0, ...w) {
    a && (u.value = t), d.value = void 0, l.value = !1, f.value = !0, _ > 0 && await pt(_);
    const k = typeof e == "function" ? e(...w) : e;
    try {
      const v = await k;
      u.value = v, l.value = !0, i(v);
    } catch (v) {
      if (d.value = v, o(v), h)
        throw v;
    } finally {
      f.value = !1;
    }
    return u.value;
  }
  r && p(s);
  const m = {
    state: u,
    isReady: l,
    isLoading: f,
    error: d,
    execute: p
  };
  function y() {
    return new Promise((_, w) => {
      Cs(f).toBe(!1).then(() => _(m)).catch(w);
    });
  }
  return {
    ...m,
    then(_, w) {
      return y().then(_, w);
    }
  };
}
function Ds(e, t = {}) {
  const { window: n = Re } = t, r = An(() => n && "matchMedia" in n && typeof n.matchMedia == "function");
  let s;
  const o = U(!1), i = (h) => {
    o.value = h.matches;
  }, a = () => {
    s && ("removeEventListener" in s ? s.removeEventListener("change", i) : s.removeListener(i));
  }, c = Ot(() => {
    r.value && (a(), s = n.matchMedia(te(e)), "addEventListener" in s ? s.addEventListener("change", i) : s.addListener(i), o.value = s.matches);
  });
  return Pt(() => {
    c(), a(), s = void 0;
  }), o;
}
const Be = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, Fe = "__vueuse_ssr_handlers__", Ms = /* @__PURE__ */ js();
function js() {
  return Fe in Be || (Be[Fe] = Be[Fe] || {}), Be[Fe];
}
function xn(e, t) {
  return Ms[e] || t;
}
function Ls(e) {
  return Ds("(prefers-color-scheme: dark)", e);
}
function Bs(e) {
  return e == null ? "any" : e instanceof Set ? "set" : e instanceof Map ? "map" : e instanceof Date ? "date" : typeof e == "boolean" ? "boolean" : typeof e == "string" ? "string" : typeof e == "object" ? "object" : Number.isNaN(e) ? "any" : "number";
}
const Fs = {
  boolean: {
    read: (e) => e === "true",
    write: (e) => String(e)
  },
  object: {
    read: (e) => JSON.parse(e),
    write: (e) => JSON.stringify(e)
  },
  number: {
    read: (e) => Number.parseFloat(e),
    write: (e) => String(e)
  },
  any: {
    read: (e) => e,
    write: (e) => String(e)
  },
  string: {
    read: (e) => e,
    write: (e) => String(e)
  },
  map: {
    read: (e) => new Map(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e.entries()))
  },
  set: {
    read: (e) => new Set(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e))
  },
  date: {
    read: (e) => new Date(e),
    write: (e) => e.toISOString()
  }
}, Ft = "vueuse-storage";
function gt(e, t, n, r = {}) {
  var s;
  const {
    flush: o = "pre",
    deep: i = !0,
    listenToStorageChanges: a = !0,
    writeDefaults: c = !0,
    mergeDefaults: h = !1,
    shallow: u,
    window: l = Re,
    eventFilter: f,
    onError: d = (P) => {
      console.error(P);
    },
    initOnMounted: p
  } = r, m = (u ? ae : U)(typeof t == "function" ? t() : t);
  if (!n)
    try {
      n = xn("getDefaultStorage", () => {
        var P;
        return (P = Re) == null ? void 0 : P.localStorage;
      })();
    } catch (P) {
      d(P);
    }
  if (!n)
    return m;
  const y = te(t), _ = Bs(y), w = (s = r.serializer) != null ? s : Fs[_], { pause: k, resume: v } = Ps(
    m,
    () => A(m.value),
    { flush: o, deep: i, eventFilter: f }
  );
  l && a && Cn(() => {
    n instanceof Storage ? Bt(l, "storage", B) : Bt(l, Ft, Q), p && B();
  }), p || B();
  function R(P, I) {
    if (l) {
      const F = {
        key: e,
        oldValue: P,
        newValue: I,
        storageArea: n
      };
      l.dispatchEvent(n instanceof Storage ? new StorageEvent("storage", F) : new CustomEvent(Ft, {
        detail: F
      }));
    }
  }
  function A(P) {
    try {
      const I = n.getItem(e);
      if (P == null)
        R(I, null), n.removeItem(e);
      else {
        const F = w.write(P);
        I !== F && (n.setItem(e, F), R(I, F));
      }
    } catch (I) {
      d(I);
    }
  }
  function T(P) {
    const I = P ? P.newValue : n.getItem(e);
    if (I == null)
      return c && y != null && n.setItem(e, w.write(y)), y;
    if (!P && h) {
      const F = w.read(I);
      return typeof h == "function" ? h(F, y) : _ === "object" && !Array.isArray(F) ? { ...y, ...F } : F;
    } else return typeof I != "string" ? I : w.read(I);
  }
  function B(P) {
    if (!(P && P.storageArea !== n)) {
      if (P && P.key == null) {
        m.value = y;
        return;
      }
      if (!(P && P.key !== e)) {
        k();
        try {
          (P == null ? void 0 : P.newValue) !== w.write(m.value) && (m.value = T(P));
        } catch (I) {
          d(I);
        } finally {
          P ? Se(v) : v();
        }
      }
    }
  }
  function Q(P) {
    B(P.detail);
  }
  return m;
}
const Ws = "*,*::before,*::after{-webkit-transition:none!important;-moz-transition:none!important;-o-transition:none!important;-ms-transition:none!important;transition:none!important}";
function Us(e = {}) {
  const {
    selector: t = "html",
    attribute: n = "class",
    initialValue: r = "auto",
    window: s = Re,
    storage: o,
    storageKey: i = "vueuse-color-scheme",
    listenToStorageChanges: a = !0,
    storageRef: c,
    emitAuto: h,
    disableTransition: u = !0
  } = e, l = {
    auto: "",
    light: "light",
    dark: "dark",
    ...e.modes || {}
  }, f = Ls({ window: s }), d = L(() => f.value ? "dark" : "light"), p = c || (i == null ? Vn(r) : gt(i, r, o, { window: s, listenToStorageChanges: a })), m = L(() => p.value === "auto" ? d.value : p.value), y = xn(
    "updateHTMLAttrs",
    (v, R, A) => {
      const T = typeof v == "string" ? s == null ? void 0 : s.document.querySelector(v) : Vt(v);
      if (!T)
        return;
      const B = /* @__PURE__ */ new Set(), Q = /* @__PURE__ */ new Set();
      let P = null;
      if (R === "class") {
        const F = A.split(/\s/g);
        Object.values(l).flatMap((ee) => (ee || "").split(/\s/g)).filter(Boolean).forEach((ee) => {
          F.includes(ee) ? B.add(ee) : Q.add(ee);
        });
      } else
        P = { key: R, value: A };
      if (B.size === 0 && Q.size === 0 && P === null)
        return;
      let I;
      u && (I = s.document.createElement("style"), I.appendChild(document.createTextNode(Ws)), s.document.head.appendChild(I));
      for (const F of B)
        T.classList.add(F);
      for (const F of Q)
        T.classList.remove(F);
      P && T.setAttribute(P.key, P.value), u && (s.getComputedStyle(I).opacity, document.head.removeChild(I));
    }
  );
  function _(v) {
    var R;
    y(t, n, (R = l[v]) != null ? R : v);
  }
  function w(v) {
    e.onChanged ? e.onChanged(v, _) : _(v);
  }
  q(m, w, { flush: "post", immediate: !0 }), Cn(() => w(m.value));
  const k = L({
    get() {
      return h ? p.value : m.value;
    },
    set(v) {
      p.value = v;
    }
  });
  return Object.assign(k, { store: p, system: d, state: m });
}
function Hs(e = {}) {
  const {
    valueDark: t = "dark",
    valueLight: n = ""
  } = e, r = Us({
    ...e,
    onChanged: (i, a) => {
      var c;
      e.onChanged ? (c = e.onChanged) == null || c.call(e, i === "dark", a, i) : a(i);
    },
    modes: {
      dark: t,
      light: n
    }
  }), s = L(() => r.system.value);
  return L({
    get() {
      return r.value === "dark";
    },
    set(i) {
      const a = i ? "dark" : "light";
      s.value === a ? r.value = "auto" : r.value = a;
    }
  });
}
function zs(e = null, t = {}) {
  var n, r, s;
  const {
    document: o = xs,
    restoreOnUnmount: i = (l) => l
  } = t, a = (n = o == null ? void 0 : o.title) != null ? n : "", c = Vn((r = e ?? (o == null ? void 0 : o.title)) != null ? r : null), h = e && typeof e == "function";
  function u(l) {
    if (!("titleTemplate" in t))
      return l;
    const f = t.titleTemplate || "%s";
    return typeof f == "function" ? f(l) : te(f).replace(/%s/g, l);
  }
  return q(
    c,
    (l, f) => {
      l !== f && o && (o.title = u(typeof l == "string" ? l : ""));
    },
    { immediate: !0 }
  ), t.observe && !t.titleTemplate && o && !h && Ts(
    (s = o.head) == null ? void 0 : s.querySelector("title"),
    () => {
      o && o.title !== c.value && (c.value = u(o.title));
    },
    { childList: !0 }
  ), Vs(() => {
    if (i) {
      const l = i(a, c.value || "");
      l != null && o && (o.title = l);
    }
  }), c;
}
function $n(e) {
  return e.constructor.name === "AsyncFunction";
}
function Tn(e, t, n) {
  const [r] = t;
  switch (r) {
    case "bind":
      return e[ne(t, n)];
    case "!":
      return !e;
    case "+":
      return e + ne(t, n);
    case "~+":
      return ne(t, n) + e;
    case "<":
      return e < ne(t, n);
    case "<=":
      return e <= ne(t, n);
    case ">":
      return e > ne(t, n);
    case ">=":
      return e >= ne(t, n);
    case "==":
      return e == ne(t, n);
    case "!=":
      return e != ne(t, n);
    case "len":
      return e.length;
    default:
      throw new Error(`Invalid flag ${r} in array at ${t}`);
  }
}
function ne(e, t) {
  const [n, r, s] = e, o = () => s && s[0] ? t(r[0]) : r[0];
  switch (n) {
    case "bind":
      return o();
    case "+":
      return o();
    case "~+":
      return o();
    case "<":
      return o();
    case "<=":
      return o();
    case ">":
      return o();
    case ">=":
      return o();
    case "==":
      return o();
    case "!=":
      return o();
    default:
      throw new Error(`Invalid flag ${n} in array at ${e}`);
  }
}
function Ks(e, t, n) {
  return Dn(t).reduce(
    (r, s) => Tn(r, s, n),
    e
  );
}
function In(e, t, n, r) {
  Dn(t).reduce((s, o, i) => {
    if (i === t.length - 1)
      s[ne(o, r)] = n;
    else
      return Tn(s, o, r);
  }, e);
}
function Dn(e) {
  return Gs(e) ? e.map((t) => ["bind", [t]]) : e;
}
function Gs(e) {
  return !Array.isArray(e[0]);
}
function qs(e, t, n) {
  const { paths: r, getBindableValueFn: s } = t, { paths: o, getBindableValueFn: i } = t;
  return r === void 0 || r.length === 0 ? e : ye(() => ({
    get() {
      try {
        return Ks(
          be(e),
          r,
          s
        );
      } catch {
        return;
      }
    },
    set(a) {
      In(
        be(e),
        o || r,
        a,
        i
      );
    }
  }));
}
function Wt(e, t) {
  return !ke(e) && JSON.stringify(t) === JSON.stringify(e);
}
function Ct(e) {
  if (Rt(e)) {
    const t = e;
    return ye(() => ({
      get() {
        return be(t);
      },
      set(n) {
        const r = be(t);
        Wt(r, n) || (t.value = n);
      }
    }));
  }
  return ye((t, n) => ({
    get() {
      return t(), e;
    },
    set(r) {
      Wt(e, r) || (e = r, n());
    }
  }));
}
function Js(e) {
  const { type: t, key: n, value: r } = e.args;
  return t === "local" ? gt(n, r) : gt(n, r, sessionStorage);
}
const Qs = "insta-color-scheme";
function Ys(e) {
  return Hs({
    storageKey: Qs,
    onChanged(n) {
      n ? (document.documentElement.setAttribute("theme-mode", "dark"), document.documentElement.classList.add("insta-dark")) : (document.documentElement.setAttribute("theme-mode", "light"), document.documentElement.classList.remove("insta-dark"));
    }
  });
}
function Xs(e) {
  return zs();
}
const Zs = U("en_US");
function eo() {
  return Zs;
}
const to = /* @__PURE__ */ new Map([
  ["storage", Js],
  ["useDark", Ys],
  ["usePageTitle", Xs],
  ["useLanguage", eo]
]);
function no(e) {
  const { type: t } = e;
  if (!t)
    throw new Error("Invalid ref type");
  const n = to.get(t);
  if (!n)
    throw new Error(`Invalid ref type ${t}`);
  return n(e);
}
function ro(e, t) {
  const { deepCompare: n = !1, type: r } = e;
  if (!r) {
    const { value: s } = e;
    return n ? Ct(s) : U(s);
  }
  return no(e);
}
function so(e, t, n) {
  const { bind: r = {}, code: s, const: o = [] } = e, i = Object.values(r).map((u, l) => o[l] === 1 ? u : t.getRef(u));
  if ($n(new Function(s)))
    return As(
      async () => {
        const u = Object.fromEntries(
          Object.keys(r).map((l, f) => [l, i[f]])
        );
        return await J(s, u)();
      },
      null,
      { lazy: !0 }
    );
  const a = Object.fromEntries(
    Object.keys(r).map((u, l) => [u, i[l]])
  ), c = J(s, a);
  return L(c);
}
function oo(e) {
  const { init: t, deepEqOnInput: n } = e;
  return n === void 0 ? ae(t ?? Ie) : Ct(t ?? Ie);
}
function io(e, t, n) {
  const {
    inputs: r = [],
    code: s,
    slient: o,
    data: i,
    asyncInit: a = null,
    deepEqOnInput: c = 0
  } = e, h = o || Array(r.length).fill(0), u = i || Array(r.length).fill(0), l = r.filter((y, _) => h[_] === 0 && u[_] === 0).map((y) => t.getRef(y));
  function f() {
    return r.map((y, _) => {
      if (u[_] === 1)
        return y;
      const w = t.getValue(y);
      return Nt(w) ? w : En(w);
    });
  }
  const d = J(s), p = c === 0 ? ae(Ie) : Ct(Ie), m = { immediate: !0, deep: !0 };
  return $n(d) ? (p.value = a, q(
    l,
    async () => {
      f().some(ke) || (p.value = await d(...f()));
    },
    m
  )) : q(
    l,
    () => {
      const y = f();
      y.some(ke) || (p.value = d(...y));
    },
    m
  ), kt(p);
}
function ao(e, t, n) {
  const s = {
    ref: {
      r: n.getBindIndex(D(e, t.id))
    },
    type: Ae.Ref
  };
  return {
    ...t,
    immediate: !0,
    outputs: [s, ...t.outputs || []]
  };
}
function co(e) {
  const { watchConfigs: t, computedConfigs: n, bindingGetter: r, sid: s } = e;
  return new lo(t, n, r, s);
}
class lo {
  constructor(t, n, r, s) {
    Y(this, "taskQueue", []);
    Y(this, "id2TaskMap", /* @__PURE__ */ new Map());
    Y(this, "input2TaskIdMap", kn(() => []));
    this.bindingGetter = r;
    const o = [], i = (a) => {
      var h;
      const c = new uo(a, r);
      return this.id2TaskMap.set(c.id, c), (h = a.inputs) == null || h.forEach((u, l) => {
        var d, p;
        if (((d = a.data) == null ? void 0 : d[l]) === 0 && ((p = a.slient) == null ? void 0 : p[l]) === 0) {
          const m = u.r;
          this.input2TaskIdMap.getOrDefault(m).push(c.id);
        }
      }), c;
    };
    t == null || t.forEach((a) => {
      const c = i(a);
      o.push(c);
    }), n == null || n.forEach((a) => {
      const c = i(
        ao(s, a, r)
      );
      o.push(c);
    }), o.forEach((a) => {
      const {
        deep: c = !0,
        once: h,
        flush: u,
        immediate: l = !0
      } = a.watchConfig, f = {
        immediate: l,
        deep: c,
        once: h,
        flush: u
      }, d = this._getWatchTargets(a);
      q(
        d,
        (p) => {
          p.some(ke) || (a.modify = !0, this.taskQueue.push(new fo(a)), this._scheduleNextTick());
        },
        f
      );
    });
  }
  _getWatchTargets(t) {
    if (!t.watchConfig.inputs)
      return [];
    const n = t.slientInputs, r = t.constDataInputs;
    return t.watchConfig.inputs.filter(
      (o, i) => !r[i] && !n[i]
    ).map((o) => this.bindingGetter.getRef(o));
  }
  _scheduleNextTick() {
    Se(() => this._runAllTasks());
  }
  _runAllTasks() {
    const t = this.taskQueue.slice();
    this.taskQueue.length = 0, this._setTaskNodeRelations(t), t.forEach((n) => {
      n.run();
    });
  }
  _setTaskNodeRelations(t) {
    t.forEach((n) => {
      const r = this._findNextNodes(n, t);
      n.appendNextNodes(...r), r.forEach((s) => {
        s.appendPrevNodes(n);
      });
    });
  }
  _findNextNodes(t, n) {
    const r = t.watchTask.watchConfig.outputs;
    if (r && r.length <= 0)
      return [];
    const s = this._getCalculatorTasksByOutput(
      t.watchTask.watchConfig.outputs
    );
    return n.filter(
      (o) => s.has(o.watchTask.id) && o.watchTask.id !== t.watchTask.id
    );
  }
  _getCalculatorTasksByOutput(t) {
    const n = /* @__PURE__ */ new Set();
    return t == null || t.forEach((r) => {
      if (!Rn(r.ref))
        throw new Error("Non-var output bindings are not supported.");
      const s = r.ref.r;
      (this.input2TaskIdMap.get(s) || []).forEach((i) => n.add(i));
    }), n;
  }
}
class uo {
  constructor(t, n) {
    Y(this, "modify", !0);
    Y(this, "_running", !1);
    Y(this, "id");
    Y(this, "_runningPromise", null);
    Y(this, "_runningPromiseResolve", null);
    Y(this, "_inputInfos");
    this.watchConfig = t, this.bindingGetter = n, this.id = Symbol(t.debug), this._inputInfos = this.createInputInfos();
  }
  createInputInfos() {
    const { inputs: t = [] } = this.watchConfig, n = this.watchConfig.data || Array.from({ length: t.length }).fill(0), r = this.watchConfig.slient || Array.from({ length: t.length }).fill(0);
    return {
      const_data: n,
      slients: r
    };
  }
  get slientInputs() {
    return this._inputInfos.slients;
  }
  get constDataInputs() {
    return this._inputInfos.const_data;
  }
  getServerInputs() {
    const { const_data: t } = this._inputInfos;
    return this.watchConfig.inputs ? this.watchConfig.inputs.map((n, r) => t[r] === 0 ? this.bindingGetter.getValue(n) : n) : [];
  }
  get running() {
    return this._running;
  }
  get runningPromise() {
    return this._runningPromise;
  }
  /**
   * setRunning
   */
  setRunning() {
    this._running = !0, this._runningPromise = new Promise((t) => {
      this._runningPromiseResolve = t;
    });
  }
  /**
   * taskDone
   */
  taskDone() {
    this._running = !1, this._runningPromiseResolve && (this._runningPromiseResolve(), this._runningPromiseResolve = null);
  }
}
class fo {
  /**
   *
   */
  constructor(t) {
    Y(this, "prevNodes", []);
    Y(this, "nextNodes", []);
    Y(this, "_runningPrev", !1);
    this.watchTask = t;
  }
  /**
   * appendPrevNodes
   */
  appendPrevNodes(...t) {
    this.prevNodes.push(...t);
  }
  /**
   *
   */
  appendNextNodes(...t) {
    this.nextNodes.push(...t);
  }
  /**
   * hasNextNodes
   */
  hasNextNodes() {
    return this.nextNodes.length > 0;
  }
  /**
   * run
   */
  async run() {
    if (this.prevNodes.length > 0 && !this._runningPrev)
      try {
        this._runningPrev = !0, await Promise.all(this.prevNodes.map((t) => t.run()));
      } finally {
        this._runningPrev = !1;
      }
    if (this.watchTask.running) {
      await this.watchTask.runningPromise;
      return;
    }
    if (this.watchTask.modify) {
      this.watchTask.modify = !1, this.watchTask.setRunning();
      try {
        await ho(this.watchTask);
      } finally {
        this.watchTask.taskDone();
      }
    }
  }
}
async function ho(e) {
  const { bindingGetter: t } = e, { outputs: n, preSetup: r } = e.watchConfig, s = Sn({
    config: r,
    bindingGetter: t
  });
  try {
    s.run(), e.taskDone();
    const o = await bn().watchSend(e);
    if (!o)
      return;
    qe(o, n, t);
  } finally {
    s.tryReset();
  }
}
function po(e, t) {
  const {
    on: n,
    code: r,
    immediate: s,
    deep: o,
    once: i,
    flush: a,
    bind: c = {},
    onData: h,
    bindData: u
  } = e, l = h || Array.from({ length: n.length }).fill(0), f = u || Array.from({ length: Object.keys(c).length }).fill(0), d = Ge(
    c,
    (y, _, w) => f[w] === 0 ? t.getRef(y) : y
  ), p = J(r, d), m = n.length === 1 ? Ut(l[0] === 1, n[0], t) : n.map(
    (y, _) => Ut(l[_] === 1, y, t)
  );
  return q(m, p, { immediate: s, deep: o, once: i, flush: a });
}
function Ut(e, t, n) {
  return e ? () => t : n.getRef(t);
}
function mo(e, t) {
  const {
    inputs: n = [],
    outputs: r,
    slient: s,
    data: o,
    code: i,
    immediate: a = !0,
    deep: c,
    once: h,
    flush: u
  } = e, l = s || Array.from({ length: n.length }).fill(0), f = o || Array.from({ length: n.length }).fill(0), d = J(i), p = n.filter((y, _) => l[_] === 0 && f[_] === 0).map((y) => t.getRef(y));
  function m() {
    return n.map((y, _) => {
      if (f[_] === 0) {
        const w = t.getValue(y);
        return Nt(w) ? w : En(w);
      }
      return y;
    });
  }
  q(
    p,
    () => {
      let y = d(...m());
      if (!r)
        return;
      const w = r.length === 1 ? [y] : y, k = w.map((v) => v === void 0 ? 1 : 0);
      qe(
        {
          values: w,
          types: k
        },
        r,
        t
      );
    },
    { immediate: a, deep: c, once: h, flush: u }
  );
}
function go() {
  return Mn().__VUE_DEVTOOLS_GLOBAL_HOOK__;
}
function Mn() {
  return typeof navigator < "u" && typeof window < "u" ? window : typeof globalThis < "u" ? globalThis : {};
}
const yo = typeof Proxy == "function", vo = "devtools-plugin:setup", wo = "plugin:settings:set";
let _e, yt;
function _o() {
  var e;
  return _e !== void 0 || (typeof window < "u" && window.performance ? (_e = !0, yt = window.performance) : typeof globalThis < "u" && (!((e = globalThis.perf_hooks) === null || e === void 0) && e.performance) ? (_e = !0, yt = globalThis.perf_hooks.performance) : _e = !1), _e;
}
function Eo() {
  return _o() ? yt.now() : Date.now();
}
class bo {
  constructor(t, n) {
    this.target = null, this.targetQueue = [], this.onQueue = [], this.plugin = t, this.hook = n;
    const r = {};
    if (t.settings)
      for (const i in t.settings) {
        const a = t.settings[i];
        r[i] = a.defaultValue;
      }
    const s = `__vue-devtools-plugin-settings__${t.id}`;
    let o = Object.assign({}, r);
    try {
      const i = localStorage.getItem(s), a = JSON.parse(i);
      Object.assign(o, a);
    } catch {
    }
    this.fallbacks = {
      getSettings() {
        return o;
      },
      setSettings(i) {
        try {
          localStorage.setItem(s, JSON.stringify(i));
        } catch {
        }
        o = i;
      },
      now() {
        return Eo();
      }
    }, n && n.on(wo, (i, a) => {
      i === this.plugin.id && this.fallbacks.setSettings(a);
    }), this.proxiedOn = new Proxy({}, {
      get: (i, a) => this.target ? this.target.on[a] : (...c) => {
        this.onQueue.push({
          method: a,
          args: c
        });
      }
    }), this.proxiedTarget = new Proxy({}, {
      get: (i, a) => this.target ? this.target[a] : a === "on" ? this.proxiedOn : Object.keys(this.fallbacks).includes(a) ? (...c) => (this.targetQueue.push({
        method: a,
        args: c,
        resolve: () => {
        }
      }), this.fallbacks[a](...c)) : (...c) => new Promise((h) => {
        this.targetQueue.push({
          method: a,
          args: c,
          resolve: h
        });
      })
    });
  }
  async setRealTarget(t) {
    this.target = t;
    for (const n of this.onQueue)
      this.target.on[n.method](...n.args);
    for (const n of this.targetQueue)
      n.resolve(await this.target[n.method](...n.args));
  }
}
function So(e, t) {
  const n = e, r = Mn(), s = go(), o = yo && n.enableEarlyProxy;
  if (s && (r.__VUE_DEVTOOLS_PLUGIN_API_AVAILABLE__ || !o))
    s.emit(vo, e, t);
  else {
    const i = o ? new bo(n, s) : null;
    (r.__VUE_DEVTOOLS_PLUGINS__ = r.__VUE_DEVTOOLS_PLUGINS__ || []).push({
      pluginDescriptor: n,
      setupFn: t,
      proxy: i
    }), i && t(i.proxiedTarget);
  }
}
var O = {};
const ie = typeof document < "u";
function jn(e) {
  return typeof e == "object" || "displayName" in e || "props" in e || "__vccOpts" in e;
}
function ko(e) {
  return e.__esModule || e[Symbol.toStringTag] === "Module" || // support CF with dynamic imports that do not
  // add the Module string tag
  e.default && jn(e.default);
}
const x = Object.assign;
function it(e, t) {
  const n = {};
  for (const r in t) {
    const s = t[r];
    n[r] = X(s) ? s.map(e) : e(s);
  }
  return n;
}
const xe = () => {
}, X = Array.isArray;
function N(e) {
  const t = Array.from(arguments).slice(1);
  console.warn.apply(console, ["[Vue Router warn]: " + e].concat(t));
}
const Ln = /#/g, Ro = /&/g, Oo = /\//g, No = /=/g, Po = /\?/g, Bn = /\+/g, Vo = /%5B/g, Co = /%5D/g, Fn = /%5E/g, Ao = /%60/g, Wn = /%7B/g, xo = /%7C/g, Un = /%7D/g, $o = /%20/g;
function At(e) {
  return encodeURI("" + e).replace(xo, "|").replace(Vo, "[").replace(Co, "]");
}
function To(e) {
  return At(e).replace(Wn, "{").replace(Un, "}").replace(Fn, "^");
}
function vt(e) {
  return At(e).replace(Bn, "%2B").replace($o, "+").replace(Ln, "%23").replace(Ro, "%26").replace(Ao, "`").replace(Wn, "{").replace(Un, "}").replace(Fn, "^");
}
function Io(e) {
  return vt(e).replace(No, "%3D");
}
function Do(e) {
  return At(e).replace(Ln, "%23").replace(Po, "%3F");
}
function Mo(e) {
  return e == null ? "" : Do(e).replace(Oo, "%2F");
}
function Oe(e) {
  try {
    return decodeURIComponent("" + e);
  } catch {
    O.NODE_ENV !== "production" && N(`Error decoding "${e}". Using original value`);
  }
  return "" + e;
}
const jo = /\/$/, Lo = (e) => e.replace(jo, "");
function at(e, t, n = "/") {
  let r, s = {}, o = "", i = "";
  const a = t.indexOf("#");
  let c = t.indexOf("?");
  return a < c && a >= 0 && (c = -1), c > -1 && (r = t.slice(0, c), o = t.slice(c + 1, a > -1 ? a : t.length), s = e(o)), a > -1 && (r = r || t.slice(0, a), i = t.slice(a, t.length)), r = Wo(r ?? t, n), {
    fullPath: r + (o && "?") + o + i,
    path: r,
    query: s,
    hash: Oe(i)
  };
}
function Bo(e, t) {
  const n = t.query ? e(t.query) : "";
  return t.path + (n && "?") + n + (t.hash || "");
}
function Ht(e, t) {
  return !t || !e.toLowerCase().startsWith(t.toLowerCase()) ? e : e.slice(t.length) || "/";
}
function zt(e, t, n) {
  const r = t.matched.length - 1, s = n.matched.length - 1;
  return r > -1 && r === s && he(t.matched[r], n.matched[s]) && Hn(t.params, n.params) && e(t.query) === e(n.query) && t.hash === n.hash;
}
function he(e, t) {
  return (e.aliasOf || e) === (t.aliasOf || t);
}
function Hn(e, t) {
  if (Object.keys(e).length !== Object.keys(t).length)
    return !1;
  for (const n in e)
    if (!Fo(e[n], t[n]))
      return !1;
  return !0;
}
function Fo(e, t) {
  return X(e) ? Kt(e, t) : X(t) ? Kt(t, e) : e === t;
}
function Kt(e, t) {
  return X(t) ? e.length === t.length && e.every((n, r) => n === t[r]) : e.length === 1 && e[0] === t;
}
function Wo(e, t) {
  if (e.startsWith("/"))
    return e;
  if (O.NODE_ENV !== "production" && !t.startsWith("/"))
    return N(`Cannot resolve a relative location without an absolute path. Trying to resolve "${e}" from "${t}". It should look like "/${t}".`), e;
  if (!e)
    return t;
  const n = t.split("/"), r = e.split("/"), s = r[r.length - 1];
  (s === ".." || s === ".") && r.push("");
  let o = n.length - 1, i, a;
  for (i = 0; i < r.length; i++)
    if (a = r[i], a !== ".")
      if (a === "..")
        o > 1 && o--;
      else
        break;
  return n.slice(0, o).join("/") + "/" + r.slice(i).join("/");
}
const le = {
  path: "/",
  // TODO: could we use a symbol in the future?
  name: void 0,
  params: {},
  query: {},
  hash: "",
  fullPath: "/",
  matched: [],
  meta: {},
  redirectedFrom: void 0
};
var Ne;
(function(e) {
  e.pop = "pop", e.push = "push";
})(Ne || (Ne = {}));
var ge;
(function(e) {
  e.back = "back", e.forward = "forward", e.unknown = "";
})(ge || (ge = {}));
const ct = "";
function zn(e) {
  if (!e)
    if (ie) {
      const t = document.querySelector("base");
      e = t && t.getAttribute("href") || "/", e = e.replace(/^\w+:\/\/[^\/]+/, "");
    } else
      e = "/";
  return e[0] !== "/" && e[0] !== "#" && (e = "/" + e), Lo(e);
}
const Uo = /^[^#]+#/;
function Kn(e, t) {
  return e.replace(Uo, "#") + t;
}
function Ho(e, t) {
  const n = document.documentElement.getBoundingClientRect(), r = e.getBoundingClientRect();
  return {
    behavior: t.behavior,
    left: r.left - n.left - (t.left || 0),
    top: r.top - n.top - (t.top || 0)
  };
}
const Je = () => ({
  left: window.scrollX,
  top: window.scrollY
});
function zo(e) {
  let t;
  if ("el" in e) {
    const n = e.el, r = typeof n == "string" && n.startsWith("#");
    if (O.NODE_ENV !== "production" && typeof e.el == "string" && (!r || !document.getElementById(e.el.slice(1))))
      try {
        const o = document.querySelector(e.el);
        if (r && o) {
          N(`The selector "${e.el}" should be passed as "el: document.querySelector('${e.el}')" because it starts with "#".`);
          return;
        }
      } catch {
        N(`The selector "${e.el}" is invalid. If you are using an id selector, make sure to escape it. You can find more information about escaping characters in selectors at https://mathiasbynens.be/notes/css-escapes or use CSS.escape (https://developer.mozilla.org/en-US/docs/Web/API/CSS/escape).`);
        return;
      }
    const s = typeof n == "string" ? r ? document.getElementById(n.slice(1)) : document.querySelector(n) : n;
    if (!s) {
      O.NODE_ENV !== "production" && N(`Couldn't find element using selector "${e.el}" returned by scrollBehavior.`);
      return;
    }
    t = Ho(s, e);
  } else
    t = e;
  "scrollBehavior" in document.documentElement.style ? window.scrollTo(t) : window.scrollTo(t.left != null ? t.left : window.scrollX, t.top != null ? t.top : window.scrollY);
}
function Gt(e, t) {
  return (history.state ? history.state.position - t : -1) + e;
}
const wt = /* @__PURE__ */ new Map();
function Ko(e, t) {
  wt.set(e, t);
}
function Go(e) {
  const t = wt.get(e);
  return wt.delete(e), t;
}
let qo = () => location.protocol + "//" + location.host;
function Gn(e, t) {
  const { pathname: n, search: r, hash: s } = t, o = e.indexOf("#");
  if (o > -1) {
    let a = s.includes(e.slice(o)) ? e.slice(o).length : 1, c = s.slice(a);
    return c[0] !== "/" && (c = "/" + c), Ht(c, "");
  }
  return Ht(n, e) + r + s;
}
function Jo(e, t, n, r) {
  let s = [], o = [], i = null;
  const a = ({ state: f }) => {
    const d = Gn(e, location), p = n.value, m = t.value;
    let y = 0;
    if (f) {
      if (n.value = d, t.value = f, i && i === p) {
        i = null;
        return;
      }
      y = m ? f.position - m.position : 0;
    } else
      r(d);
    s.forEach((_) => {
      _(n.value, p, {
        delta: y,
        type: Ne.pop,
        direction: y ? y > 0 ? ge.forward : ge.back : ge.unknown
      });
    });
  };
  function c() {
    i = n.value;
  }
  function h(f) {
    s.push(f);
    const d = () => {
      const p = s.indexOf(f);
      p > -1 && s.splice(p, 1);
    };
    return o.push(d), d;
  }
  function u() {
    const { history: f } = window;
    f.state && f.replaceState(x({}, f.state, { scroll: Je() }), "");
  }
  function l() {
    for (const f of o)
      f();
    o = [], window.removeEventListener("popstate", a), window.removeEventListener("beforeunload", u);
  }
  return window.addEventListener("popstate", a), window.addEventListener("beforeunload", u, {
    passive: !0
  }), {
    pauseListeners: c,
    listen: h,
    destroy: l
  };
}
function qt(e, t, n, r = !1, s = !1) {
  return {
    back: e,
    current: t,
    forward: n,
    replaced: r,
    position: window.history.length,
    scroll: s ? Je() : null
  };
}
function Qo(e) {
  const { history: t, location: n } = window, r = {
    value: Gn(e, n)
  }, s = { value: t.state };
  s.value || o(r.value, {
    back: null,
    current: r.value,
    forward: null,
    // the length is off by one, we need to decrease it
    position: t.length - 1,
    replaced: !0,
    // don't add a scroll as the user may have an anchor, and we want
    // scrollBehavior to be triggered without a saved position
    scroll: null
  }, !0);
  function o(c, h, u) {
    const l = e.indexOf("#"), f = l > -1 ? (n.host && document.querySelector("base") ? e : e.slice(l)) + c : qo() + e + c;
    try {
      t[u ? "replaceState" : "pushState"](h, "", f), s.value = h;
    } catch (d) {
      O.NODE_ENV !== "production" ? N("Error with push/replace State", d) : console.error(d), n[u ? "replace" : "assign"](f);
    }
  }
  function i(c, h) {
    const u = x({}, t.state, qt(
      s.value.back,
      // keep back and forward entries but override current position
      c,
      s.value.forward,
      !0
    ), h, { position: s.value.position });
    o(c, u, !0), r.value = c;
  }
  function a(c, h) {
    const u = x(
      {},
      // use current history state to gracefully handle a wrong call to
      // history.replaceState
      // https://github.com/vuejs/router/issues/366
      s.value,
      t.state,
      {
        forward: c,
        scroll: Je()
      }
    );
    O.NODE_ENV !== "production" && !t.state && N(`history.state seems to have been manually replaced without preserving the necessary values. Make sure to preserve existing history state if you are manually calling history.replaceState:

history.replaceState(history.state, '', url)

You can find more information at https://router.vuejs.org/guide/migration/#Usage-of-history-state`), o(u.current, u, !0);
    const l = x({}, qt(r.value, c, null), { position: u.position + 1 }, h);
    o(c, l, !1), r.value = c;
  }
  return {
    location: r,
    state: s,
    push: a,
    replace: i
  };
}
function qn(e) {
  e = zn(e);
  const t = Qo(e), n = Jo(e, t.state, t.location, t.replace);
  function r(o, i = !0) {
    i || n.pauseListeners(), history.go(o);
  }
  const s = x({
    // it's overridden right after
    location: "",
    base: e,
    go: r,
    createHref: Kn.bind(null, e)
  }, t, n);
  return Object.defineProperty(s, "location", {
    enumerable: !0,
    get: () => t.location.value
  }), Object.defineProperty(s, "state", {
    enumerable: !0,
    get: () => t.state.value
  }), s;
}
function Yo(e = "") {
  let t = [], n = [ct], r = 0;
  e = zn(e);
  function s(a) {
    r++, r !== n.length && n.splice(r), n.push(a);
  }
  function o(a, c, { direction: h, delta: u }) {
    const l = {
      direction: h,
      delta: u,
      type: Ne.pop
    };
    for (const f of t)
      f(a, c, l);
  }
  const i = {
    // rewritten by Object.defineProperty
    location: ct,
    // TODO: should be kept in queue
    state: {},
    base: e,
    createHref: Kn.bind(null, e),
    replace(a) {
      n.splice(r--, 1), s(a);
    },
    push(a, c) {
      s(a);
    },
    listen(a) {
      return t.push(a), () => {
        const c = t.indexOf(a);
        c > -1 && t.splice(c, 1);
      };
    },
    destroy() {
      t = [], n = [ct], r = 0;
    },
    go(a, c = !0) {
      const h = this.location, u = (
        // we are considering delta === 0 going forward, but in abstract mode
        // using 0 for the delta doesn't make sense like it does in html5 where
        // it reloads the page
        a < 0 ? ge.back : ge.forward
      );
      r = Math.max(0, Math.min(r + a, n.length - 1)), c && o(this.location, h, {
        direction: u,
        delta: a
      });
    }
  };
  return Object.defineProperty(i, "location", {
    enumerable: !0,
    get: () => n[r]
  }), i;
}
function Xo(e) {
  return e = location.host ? e || location.pathname + location.search : "", e.includes("#") || (e += "#"), O.NODE_ENV !== "production" && !e.endsWith("#/") && !e.endsWith("#") && N(`A hash base must end with a "#":
"${e}" should be "${e.replace(/#.*$/, "#")}".`), qn(e);
}
function ze(e) {
  return typeof e == "string" || e && typeof e == "object";
}
function Jn(e) {
  return typeof e == "string" || typeof e == "symbol";
}
const _t = Symbol(O.NODE_ENV !== "production" ? "navigation failure" : "");
var Jt;
(function(e) {
  e[e.aborted = 4] = "aborted", e[e.cancelled = 8] = "cancelled", e[e.duplicated = 16] = "duplicated";
})(Jt || (Jt = {}));
const Zo = {
  1({ location: e, currentLocation: t }) {
    return `No match for
 ${JSON.stringify(e)}${t ? `
while being at
` + JSON.stringify(t) : ""}`;
  },
  2({ from: e, to: t }) {
    return `Redirected from "${e.fullPath}" to "${ti(t)}" via a navigation guard.`;
  },
  4({ from: e, to: t }) {
    return `Navigation aborted from "${e.fullPath}" to "${t.fullPath}" via a navigation guard.`;
  },
  8({ from: e, to: t }) {
    return `Navigation cancelled from "${e.fullPath}" to "${t.fullPath}" with a new navigation.`;
  },
  16({ from: e, to: t }) {
    return `Avoided redundant navigation to current location: "${e.fullPath}".`;
  }
};
function Pe(e, t) {
  return O.NODE_ENV !== "production" ? x(new Error(Zo[e](t)), {
    type: e,
    [_t]: !0
  }, t) : x(new Error(), {
    type: e,
    [_t]: !0
  }, t);
}
function oe(e, t) {
  return e instanceof Error && _t in e && (t == null || !!(e.type & t));
}
const ei = ["params", "query", "hash"];
function ti(e) {
  if (typeof e == "string")
    return e;
  if (e.path != null)
    return e.path;
  const t = {};
  for (const n of ei)
    n in e && (t[n] = e[n]);
  return JSON.stringify(t, null, 2);
}
const Qt = "[^/]+?", ni = {
  sensitive: !1,
  strict: !1,
  start: !0,
  end: !0
}, ri = /[.+*?^${}()[\]/\\]/g;
function si(e, t) {
  const n = x({}, ni, t), r = [];
  let s = n.start ? "^" : "";
  const o = [];
  for (const h of e) {
    const u = h.length ? [] : [
      90
      /* PathScore.Root */
    ];
    n.strict && !h.length && (s += "/");
    for (let l = 0; l < h.length; l++) {
      const f = h[l];
      let d = 40 + (n.sensitive ? 0.25 : 0);
      if (f.type === 0)
        l || (s += "/"), s += f.value.replace(ri, "\\$&"), d += 40;
      else if (f.type === 1) {
        const { value: p, repeatable: m, optional: y, regexp: _ } = f;
        o.push({
          name: p,
          repeatable: m,
          optional: y
        });
        const w = _ || Qt;
        if (w !== Qt) {
          d += 10;
          try {
            new RegExp(`(${w})`);
          } catch (v) {
            throw new Error(`Invalid custom RegExp for param "${p}" (${w}): ` + v.message);
          }
        }
        let k = m ? `((?:${w})(?:/(?:${w}))*)` : `(${w})`;
        l || (k = // avoid an optional / if there are more segments e.g. /:p?-static
        // or /:p?-:p2
        y && h.length < 2 ? `(?:/${k})` : "/" + k), y && (k += "?"), s += k, d += 20, y && (d += -8), m && (d += -20), w === ".*" && (d += -50);
      }
      u.push(d);
    }
    r.push(u);
  }
  if (n.strict && n.end) {
    const h = r.length - 1;
    r[h][r[h].length - 1] += 0.7000000000000001;
  }
  n.strict || (s += "/?"), n.end ? s += "$" : n.strict && !s.endsWith("/") && (s += "(?:/|$)");
  const i = new RegExp(s, n.sensitive ? "" : "i");
  function a(h) {
    const u = h.match(i), l = {};
    if (!u)
      return null;
    for (let f = 1; f < u.length; f++) {
      const d = u[f] || "", p = o[f - 1];
      l[p.name] = d && p.repeatable ? d.split("/") : d;
    }
    return l;
  }
  function c(h) {
    let u = "", l = !1;
    for (const f of e) {
      (!l || !u.endsWith("/")) && (u += "/"), l = !1;
      for (const d of f)
        if (d.type === 0)
          u += d.value;
        else if (d.type === 1) {
          const { value: p, repeatable: m, optional: y } = d, _ = p in h ? h[p] : "";
          if (X(_) && !m)
            throw new Error(`Provided param "${p}" is an array but it is not repeatable (* or + modifiers)`);
          const w = X(_) ? _.join("/") : _;
          if (!w)
            if (y)
              f.length < 2 && (u.endsWith("/") ? u = u.slice(0, -1) : l = !0);
            else
              throw new Error(`Missing required param "${p}"`);
          u += w;
        }
    }
    return u || "/";
  }
  return {
    re: i,
    score: r,
    keys: o,
    parse: a,
    stringify: c
  };
}
function oi(e, t) {
  let n = 0;
  for (; n < e.length && n < t.length; ) {
    const r = t[n] - e[n];
    if (r)
      return r;
    n++;
  }
  return e.length < t.length ? e.length === 1 && e[0] === 80 ? -1 : 1 : e.length > t.length ? t.length === 1 && t[0] === 80 ? 1 : -1 : 0;
}
function Qn(e, t) {
  let n = 0;
  const r = e.score, s = t.score;
  for (; n < r.length && n < s.length; ) {
    const o = oi(r[n], s[n]);
    if (o)
      return o;
    n++;
  }
  if (Math.abs(s.length - r.length) === 1) {
    if (Yt(r))
      return 1;
    if (Yt(s))
      return -1;
  }
  return s.length - r.length;
}
function Yt(e) {
  const t = e[e.length - 1];
  return e.length > 0 && t[t.length - 1] < 0;
}
const ii = {
  type: 0,
  value: ""
}, ai = /[a-zA-Z0-9_]/;
function ci(e) {
  if (!e)
    return [[]];
  if (e === "/")
    return [[ii]];
  if (!e.startsWith("/"))
    throw new Error(O.NODE_ENV !== "production" ? `Route paths should start with a "/": "${e}" should be "/${e}".` : `Invalid path "${e}"`);
  function t(d) {
    throw new Error(`ERR (${n})/"${h}": ${d}`);
  }
  let n = 0, r = n;
  const s = [];
  let o;
  function i() {
    o && s.push(o), o = [];
  }
  let a = 0, c, h = "", u = "";
  function l() {
    h && (n === 0 ? o.push({
      type: 0,
      value: h
    }) : n === 1 || n === 2 || n === 3 ? (o.length > 1 && (c === "*" || c === "+") && t(`A repeatable param (${h}) must be alone in its segment. eg: '/:ids+.`), o.push({
      type: 1,
      value: h,
      regexp: u,
      repeatable: c === "*" || c === "+",
      optional: c === "*" || c === "?"
    })) : t("Invalid state to consume buffer"), h = "");
  }
  function f() {
    h += c;
  }
  for (; a < e.length; ) {
    if (c = e[a++], c === "\\" && n !== 2) {
      r = n, n = 4;
      continue;
    }
    switch (n) {
      case 0:
        c === "/" ? (h && l(), i()) : c === ":" ? (l(), n = 1) : f();
        break;
      case 4:
        f(), n = r;
        break;
      case 1:
        c === "(" ? n = 2 : ai.test(c) ? f() : (l(), n = 0, c !== "*" && c !== "?" && c !== "+" && a--);
        break;
      case 2:
        c === ")" ? u[u.length - 1] == "\\" ? u = u.slice(0, -1) + c : n = 3 : u += c;
        break;
      case 3:
        l(), n = 0, c !== "*" && c !== "?" && c !== "+" && a--, u = "";
        break;
      default:
        t("Unknown state");
        break;
    }
  }
  return n === 2 && t(`Unfinished custom RegExp for param "${h}"`), l(), i(), s;
}
function li(e, t, n) {
  const r = si(ci(e.path), n);
  if (O.NODE_ENV !== "production") {
    const o = /* @__PURE__ */ new Set();
    for (const i of r.keys)
      o.has(i.name) && N(`Found duplicated params with name "${i.name}" for path "${e.path}". Only the last one will be available on "$route.params".`), o.add(i.name);
  }
  const s = x(r, {
    record: e,
    parent: t,
    // these needs to be populated by the parent
    children: [],
    alias: []
  });
  return t && !s.record.aliasOf == !t.record.aliasOf && t.children.push(s), s;
}
function ui(e, t) {
  const n = [], r = /* @__PURE__ */ new Map();
  t = tn({ strict: !1, end: !0, sensitive: !1 }, t);
  function s(l) {
    return r.get(l);
  }
  function o(l, f, d) {
    const p = !d, m = Zt(l);
    O.NODE_ENV !== "production" && pi(m, f), m.aliasOf = d && d.record;
    const y = tn(t, l), _ = [m];
    if ("alias" in l) {
      const v = typeof l.alias == "string" ? [l.alias] : l.alias;
      for (const R of v)
        _.push(
          // we need to normalize again to ensure the `mods` property
          // being non enumerable
          Zt(x({}, m, {
            // this allows us to hold a copy of the `components` option
            // so that async components cache is hold on the original record
            components: d ? d.record.components : m.components,
            path: R,
            // we might be the child of an alias
            aliasOf: d ? d.record : m
            // the aliases are always of the same kind as the original since they
            // are defined on the same record
          }))
        );
    }
    let w, k;
    for (const v of _) {
      const { path: R } = v;
      if (f && R[0] !== "/") {
        const A = f.record.path, T = A[A.length - 1] === "/" ? "" : "/";
        v.path = f.record.path + (R && T + R);
      }
      if (O.NODE_ENV !== "production" && v.path === "*")
        throw new Error(`Catch all routes ("*") must now be defined using a param with a custom regexp.
See more at https://router.vuejs.org/guide/migration/#Removed-star-or-catch-all-routes.`);
      if (w = li(v, f, y), O.NODE_ENV !== "production" && f && R[0] === "/" && gi(w, f), d ? (d.alias.push(w), O.NODE_ENV !== "production" && hi(d, w)) : (k = k || w, k !== w && k.alias.push(w), p && l.name && !en(w) && (O.NODE_ENV !== "production" && mi(l, f), i(l.name))), Yn(w) && c(w), m.children) {
        const A = m.children;
        for (let T = 0; T < A.length; T++)
          o(A[T], w, d && d.children[T]);
      }
      d = d || w;
    }
    return k ? () => {
      i(k);
    } : xe;
  }
  function i(l) {
    if (Jn(l)) {
      const f = r.get(l);
      f && (r.delete(l), n.splice(n.indexOf(f), 1), f.children.forEach(i), f.alias.forEach(i));
    } else {
      const f = n.indexOf(l);
      f > -1 && (n.splice(f, 1), l.record.name && r.delete(l.record.name), l.children.forEach(i), l.alias.forEach(i));
    }
  }
  function a() {
    return n;
  }
  function c(l) {
    const f = yi(l, n);
    n.splice(f, 0, l), l.record.name && !en(l) && r.set(l.record.name, l);
  }
  function h(l, f) {
    let d, p = {}, m, y;
    if ("name" in l && l.name) {
      if (d = r.get(l.name), !d)
        throw Pe(1, {
          location: l
        });
      if (O.NODE_ENV !== "production") {
        const k = Object.keys(l.params || {}).filter((v) => !d.keys.find((R) => R.name === v));
        k.length && N(`Discarded invalid param(s) "${k.join('", "')}" when navigating. See https://github.com/vuejs/router/blob/main/packages/router/CHANGELOG.md#414-2022-08-22 for more details.`);
      }
      y = d.record.name, p = x(
        // paramsFromLocation is a new object
        Xt(
          f.params,
          // only keep params that exist in the resolved location
          // only keep optional params coming from a parent record
          d.keys.filter((k) => !k.optional).concat(d.parent ? d.parent.keys.filter((k) => k.optional) : []).map((k) => k.name)
        ),
        // discard any existing params in the current location that do not exist here
        // #1497 this ensures better active/exact matching
        l.params && Xt(l.params, d.keys.map((k) => k.name))
      ), m = d.stringify(p);
    } else if (l.path != null)
      m = l.path, O.NODE_ENV !== "production" && !m.startsWith("/") && N(`The Matcher cannot resolve relative paths but received "${m}". Unless you directly called \`matcher.resolve("${m}")\`, this is probably a bug in vue-router. Please open an issue at https://github.com/vuejs/router/issues/new/choose.`), d = n.find((k) => k.re.test(m)), d && (p = d.parse(m), y = d.record.name);
    else {
      if (d = f.name ? r.get(f.name) : n.find((k) => k.re.test(f.path)), !d)
        throw Pe(1, {
          location: l,
          currentLocation: f
        });
      y = d.record.name, p = x({}, f.params, l.params), m = d.stringify(p);
    }
    const _ = [];
    let w = d;
    for (; w; )
      _.unshift(w.record), w = w.parent;
    return {
      name: y,
      path: m,
      params: p,
      matched: _,
      meta: di(_)
    };
  }
  e.forEach((l) => o(l));
  function u() {
    n.length = 0, r.clear();
  }
  return {
    addRoute: o,
    resolve: h,
    removeRoute: i,
    clearRoutes: u,
    getRoutes: a,
    getRecordMatcher: s
  };
}
function Xt(e, t) {
  const n = {};
  for (const r of t)
    r in e && (n[r] = e[r]);
  return n;
}
function Zt(e) {
  const t = {
    path: e.path,
    redirect: e.redirect,
    name: e.name,
    meta: e.meta || {},
    aliasOf: e.aliasOf,
    beforeEnter: e.beforeEnter,
    props: fi(e),
    children: e.children || [],
    instances: {},
    leaveGuards: /* @__PURE__ */ new Set(),
    updateGuards: /* @__PURE__ */ new Set(),
    enterCallbacks: {},
    // must be declared afterwards
    // mods: {},
    components: "components" in e ? e.components || null : e.component && { default: e.component }
  };
  return Object.defineProperty(t, "mods", {
    value: {}
  }), t;
}
function fi(e) {
  const t = {}, n = e.props || !1;
  if ("component" in e)
    t.default = n;
  else
    for (const r in e.components)
      t[r] = typeof n == "object" ? n[r] : n;
  return t;
}
function en(e) {
  for (; e; ) {
    if (e.record.aliasOf)
      return !0;
    e = e.parent;
  }
  return !1;
}
function di(e) {
  return e.reduce((t, n) => x(t, n.meta), {});
}
function tn(e, t) {
  const n = {};
  for (const r in e)
    n[r] = r in t ? t[r] : e[r];
  return n;
}
function Et(e, t) {
  return e.name === t.name && e.optional === t.optional && e.repeatable === t.repeatable;
}
function hi(e, t) {
  for (const n of e.keys)
    if (!n.optional && !t.keys.find(Et.bind(null, n)))
      return N(`Alias "${t.record.path}" and the original record: "${e.record.path}" must have the exact same param named "${n.name}"`);
  for (const n of t.keys)
    if (!n.optional && !e.keys.find(Et.bind(null, n)))
      return N(`Alias "${t.record.path}" and the original record: "${e.record.path}" must have the exact same param named "${n.name}"`);
}
function pi(e, t) {
  t && t.record.name && !e.name && !e.path && N(`The route named "${String(t.record.name)}" has a child without a name and an empty path. Using that name won't render the empty path child so you probably want to move the name to the child instead. If this is intentional, add a name to the child route to remove the warning.`);
}
function mi(e, t) {
  for (let n = t; n; n = n.parent)
    if (n.record.name === e.name)
      throw new Error(`A route named "${String(e.name)}" has been added as a ${t === n ? "child" : "descendant"} of a route with the same name. Route names must be unique and a nested route cannot use the same name as an ancestor.`);
}
function gi(e, t) {
  for (const n of t.keys)
    if (!e.keys.find(Et.bind(null, n)))
      return N(`Absolute path "${e.record.path}" must have the exact same param named "${n.name}" as its parent "${t.record.path}".`);
}
function yi(e, t) {
  let n = 0, r = t.length;
  for (; n !== r; ) {
    const o = n + r >> 1;
    Qn(e, t[o]) < 0 ? r = o : n = o + 1;
  }
  const s = vi(e);
  return s && (r = t.lastIndexOf(s, r - 1), O.NODE_ENV !== "production" && r < 0 && N(`Finding ancestor route "${s.record.path}" failed for "${e.record.path}"`)), r;
}
function vi(e) {
  let t = e;
  for (; t = t.parent; )
    if (Yn(t) && Qn(e, t) === 0)
      return t;
}
function Yn({ record: e }) {
  return !!(e.name || e.components && Object.keys(e.components).length || e.redirect);
}
function wi(e) {
  const t = {};
  if (e === "" || e === "?")
    return t;
  const r = (e[0] === "?" ? e.slice(1) : e).split("&");
  for (let s = 0; s < r.length; ++s) {
    const o = r[s].replace(Bn, " "), i = o.indexOf("="), a = Oe(i < 0 ? o : o.slice(0, i)), c = i < 0 ? null : Oe(o.slice(i + 1));
    if (a in t) {
      let h = t[a];
      X(h) || (h = t[a] = [h]), h.push(c);
    } else
      t[a] = c;
  }
  return t;
}
function nn(e) {
  let t = "";
  for (let n in e) {
    const r = e[n];
    if (n = Io(n), r == null) {
      r !== void 0 && (t += (t.length ? "&" : "") + n);
      continue;
    }
    (X(r) ? r.map((o) => o && vt(o)) : [r && vt(r)]).forEach((o) => {
      o !== void 0 && (t += (t.length ? "&" : "") + n, o != null && (t += "=" + o));
    });
  }
  return t;
}
function _i(e) {
  const t = {};
  for (const n in e) {
    const r = e[n];
    r !== void 0 && (t[n] = X(r) ? r.map((s) => s == null ? null : "" + s) : r == null ? r : "" + r);
  }
  return t;
}
const Ei = Symbol(O.NODE_ENV !== "production" ? "router view location matched" : ""), rn = Symbol(O.NODE_ENV !== "production" ? "router view depth" : ""), Qe = Symbol(O.NODE_ENV !== "production" ? "router" : ""), xt = Symbol(O.NODE_ENV !== "production" ? "route location" : ""), bt = Symbol(O.NODE_ENV !== "production" ? "router view location" : "");
function Ve() {
  let e = [];
  function t(r) {
    return e.push(r), () => {
      const s = e.indexOf(r);
      s > -1 && e.splice(s, 1);
    };
  }
  function n() {
    e = [];
  }
  return {
    add: t,
    list: () => e.slice(),
    reset: n
  };
}
function ue(e, t, n, r, s, o = (i) => i()) {
  const i = r && // name is defined if record is because of the function overload
  (r.enterCallbacks[s] = r.enterCallbacks[s] || []);
  return () => new Promise((a, c) => {
    const h = (f) => {
      f === !1 ? c(Pe(4, {
        from: n,
        to: t
      })) : f instanceof Error ? c(f) : ze(f) ? c(Pe(2, {
        from: t,
        to: f
      })) : (i && // since enterCallbackArray is truthy, both record and name also are
      r.enterCallbacks[s] === i && typeof f == "function" && i.push(f), a());
    }, u = o(() => e.call(r && r.instances[s], t, n, O.NODE_ENV !== "production" ? bi(h, t, n) : h));
    let l = Promise.resolve(u);
    if (e.length < 3 && (l = l.then(h)), O.NODE_ENV !== "production" && e.length > 2) {
      const f = `The "next" callback was never called inside of ${e.name ? '"' + e.name + '"' : ""}:
${e.toString()}
. If you are returning a value instead of calling "next", make sure to remove the "next" parameter from your function.`;
      if (typeof u == "object" && "then" in u)
        l = l.then((d) => h._called ? d : (N(f), Promise.reject(new Error("Invalid navigation guard"))));
      else if (u !== void 0 && !h._called) {
        N(f), c(new Error("Invalid navigation guard"));
        return;
      }
    }
    l.catch((f) => c(f));
  });
}
function bi(e, t, n) {
  let r = 0;
  return function() {
    r++ === 1 && N(`The "next" callback was called more than once in one navigation guard when going from "${n.fullPath}" to "${t.fullPath}". It should be called exactly one time in each navigation guard. This will fail in production.`), e._called = !0, r === 1 && e.apply(null, arguments);
  };
}
function lt(e, t, n, r, s = (o) => o()) {
  const o = [];
  for (const i of e) {
    O.NODE_ENV !== "production" && !i.components && !i.children.length && N(`Record with path "${i.path}" is either missing a "component(s)" or "children" property.`);
    for (const a in i.components) {
      let c = i.components[a];
      if (O.NODE_ENV !== "production") {
        if (!c || typeof c != "object" && typeof c != "function")
          throw N(`Component "${a}" in record with path "${i.path}" is not a valid component. Received "${String(c)}".`), new Error("Invalid route component");
        if ("then" in c) {
          N(`Component "${a}" in record with path "${i.path}" is a Promise instead of a function that returns a Promise. Did you write "import('./MyPage.vue')" instead of "() => import('./MyPage.vue')" ? This will break in production if not fixed.`);
          const h = c;
          c = () => h;
        } else c.__asyncLoader && // warn only once per component
        !c.__warnedDefineAsync && (c.__warnedDefineAsync = !0, N(`Component "${a}" in record with path "${i.path}" is defined using "defineAsyncComponent()". Write "() => import('./MyPage.vue')" instead of "defineAsyncComponent(() => import('./MyPage.vue'))".`));
      }
      if (!(t !== "beforeRouteEnter" && !i.instances[a]))
        if (jn(c)) {
          const u = (c.__vccOpts || c)[t];
          u && o.push(ue(u, n, r, i, a, s));
        } else {
          let h = c();
          O.NODE_ENV !== "production" && !("catch" in h) && (N(`Component "${a}" in record with path "${i.path}" is a function that does not return a Promise. If you were passing a functional component, make sure to add a "displayName" to the component. This will break in production if not fixed.`), h = Promise.resolve(h)), o.push(() => h.then((u) => {
            if (!u)
              throw new Error(`Couldn't resolve component "${a}" at "${i.path}"`);
            const l = ko(u) ? u.default : u;
            i.mods[a] = u, i.components[a] = l;
            const d = (l.__vccOpts || l)[t];
            return d && ue(d, n, r, i, a, s)();
          }));
        }
    }
  }
  return o;
}
function sn(e) {
  const t = ce(Qe), n = ce(xt);
  let r = !1, s = null;
  const o = L(() => {
    const u = K(e.to);
    return O.NODE_ENV !== "production" && (!r || u !== s) && (ze(u) || (r ? N(`Invalid value for prop "to" in useLink()
- to:`, u, `
- previous to:`, s, `
- props:`, e) : N(`Invalid value for prop "to" in useLink()
- to:`, u, `
- props:`, e)), s = u, r = !0), t.resolve(u);
  }), i = L(() => {
    const { matched: u } = o.value, { length: l } = u, f = u[l - 1], d = n.matched;
    if (!f || !d.length)
      return -1;
    const p = d.findIndex(he.bind(null, f));
    if (p > -1)
      return p;
    const m = on(u[l - 2]);
    return (
      // we are dealing with nested routes
      l > 1 && // if the parent and matched route have the same path, this link is
      // referring to the empty child. Or we currently are on a different
      // child of the same parent
      on(f) === m && // avoid comparing the child with its parent
      d[d.length - 1].path !== m ? d.findIndex(he.bind(null, u[l - 2])) : p
    );
  }), a = L(() => i.value > -1 && Ni(n.params, o.value.params)), c = L(() => i.value > -1 && i.value === n.matched.length - 1 && Hn(n.params, o.value.params));
  function h(u = {}) {
    if (Oi(u)) {
      const l = t[K(e.replace) ? "replace" : "push"](
        K(e.to)
        // avoid uncaught errors are they are logged anyway
      ).catch(xe);
      return e.viewTransition && typeof document < "u" && "startViewTransition" in document && document.startViewTransition(() => l), l;
    }
    return Promise.resolve();
  }
  if (O.NODE_ENV !== "production" && ie) {
    const u = Ke();
    if (u) {
      const l = {
        route: o.value,
        isActive: a.value,
        isExactActive: c.value,
        error: null
      };
      u.__vrl_devtools = u.__vrl_devtools || [], u.__vrl_devtools.push(l), Ot(() => {
        l.route = o.value, l.isActive = a.value, l.isExactActive = c.value, l.error = ze(K(e.to)) ? null : 'Invalid "to" value';
      }, { flush: "post" });
    }
  }
  return {
    route: o,
    href: L(() => o.value.href),
    isActive: a,
    isExactActive: c,
    navigate: h
  };
}
function Si(e) {
  return e.length === 1 ? e[0] : e;
}
const ki = /* @__PURE__ */ Z({
  name: "RouterLink",
  compatConfig: { MODE: 3 },
  props: {
    to: {
      type: [String, Object],
      required: !0
    },
    replace: Boolean,
    activeClass: String,
    // inactiveClass: String,
    exactActiveClass: String,
    custom: Boolean,
    ariaCurrentValue: {
      type: String,
      default: "page"
    }
  },
  useLink: sn,
  setup(e, { slots: t }) {
    const n = Or(sn(e)), { options: r } = ce(Qe), s = L(() => ({
      [an(e.activeClass, r.linkActiveClass, "router-link-active")]: n.isActive,
      // [getLinkClass(
      //   props.inactiveClass,
      //   options.linkInactiveClass,
      //   'router-link-inactive'
      // )]: !link.isExactActive,
      [an(e.exactActiveClass, r.linkExactActiveClass, "router-link-exact-active")]: n.isExactActive
    }));
    return () => {
      const o = t.default && Si(t.default(n));
      return e.custom ? o : G("a", {
        "aria-current": n.isExactActive ? e.ariaCurrentValue : null,
        href: n.href,
        // this would override user added attrs but Vue will still add
        // the listener, so we end up triggering both
        onClick: n.navigate,
        class: s.value
      }, o);
    };
  }
}), Ri = ki;
function Oi(e) {
  if (!(e.metaKey || e.altKey || e.ctrlKey || e.shiftKey) && !e.defaultPrevented && !(e.button !== void 0 && e.button !== 0)) {
    if (e.currentTarget && e.currentTarget.getAttribute) {
      const t = e.currentTarget.getAttribute("target");
      if (/\b_blank\b/i.test(t))
        return;
    }
    return e.preventDefault && e.preventDefault(), !0;
  }
}
function Ni(e, t) {
  for (const n in t) {
    const r = t[n], s = e[n];
    if (typeof r == "string") {
      if (r !== s)
        return !1;
    } else if (!X(s) || s.length !== r.length || r.some((o, i) => o !== s[i]))
      return !1;
  }
  return !0;
}
function on(e) {
  return e ? e.aliasOf ? e.aliasOf.path : e.path : "";
}
const an = (e, t, n) => e ?? t ?? n, Pi = /* @__PURE__ */ Z({
  name: "RouterView",
  // #674 we manually inherit them
  inheritAttrs: !1,
  props: {
    name: {
      type: String,
      default: "default"
    },
    route: Object
  },
  // Better compat for @vue/compat users
  // https://github.com/vuejs/router/issues/1315
  compatConfig: { MODE: 3 },
  setup(e, { attrs: t, slots: n }) {
    O.NODE_ENV !== "production" && Ci();
    const r = ce(bt), s = L(() => e.route || r.value), o = ce(rn, 0), i = L(() => {
      let h = K(o);
      const { matched: u } = s.value;
      let l;
      for (; (l = u[h]) && !l.components; )
        h++;
      return h;
    }), a = L(() => s.value.matched[i.value]);
    H(rn, L(() => i.value + 1)), H(Ei, a), H(bt, s);
    const c = U();
    return q(() => [c.value, a.value, e.name], ([h, u, l], [f, d, p]) => {
      u && (u.instances[l] = h, d && d !== u && h && h === f && (u.leaveGuards.size || (u.leaveGuards = d.leaveGuards), u.updateGuards.size || (u.updateGuards = d.updateGuards))), h && u && // if there is no instance but to and from are the same this might be
      // the first visit
      (!d || !he(u, d) || !f) && (u.enterCallbacks[l] || []).forEach((m) => m(h));
    }, { flush: "post" }), () => {
      const h = s.value, u = e.name, l = a.value, f = l && l.components[u];
      if (!f)
        return cn(n.default, { Component: f, route: h });
      const d = l.props[u], p = d ? d === !0 ? h.params : typeof d == "function" ? d(h) : d : null, y = G(f, x({}, p, t, {
        onVnodeUnmounted: (_) => {
          _.component.isUnmounted && (l.instances[u] = null);
        },
        ref: c
      }));
      if (O.NODE_ENV !== "production" && ie && y.ref) {
        const _ = {
          depth: i.value,
          name: l.name,
          path: l.path,
          meta: l.meta
        };
        (X(y.ref) ? y.ref.map((k) => k.i) : [y.ref.i]).forEach((k) => {
          k.__vrv_devtools = _;
        });
      }
      return (
        // pass the vnode to the slot as a prop.
        // h and <component :is="..."> both accept vnodes
        cn(n.default, { Component: y, route: h }) || y
      );
    };
  }
});
function cn(e, t) {
  if (!e)
    return null;
  const n = e(t);
  return n.length === 1 ? n[0] : n;
}
const Vi = Pi;
function Ci() {
  const e = Ke(), t = e.parent && e.parent.type.name, n = e.parent && e.parent.subTree && e.parent.subTree.type;
  if (t && (t === "KeepAlive" || t.includes("Transition")) && typeof n == "object" && n.name === "RouterView") {
    const r = t === "KeepAlive" ? "keep-alive" : "transition";
    N(`<router-view> can no longer be used directly inside <transition> or <keep-alive>.
Use slot props instead:

<router-view v-slot="{ Component }">
  <${r}>
    <component :is="Component" />
  </${r}>
</router-view>`);
  }
}
function Ce(e, t) {
  const n = x({}, e, {
    // remove variables that can contain vue instances
    matched: e.matched.map((r) => Fi(r, ["instances", "children", "aliasOf"]))
  });
  return {
    _custom: {
      type: null,
      readOnly: !0,
      display: e.fullPath,
      tooltip: t,
      value: n
    }
  };
}
function We(e) {
  return {
    _custom: {
      display: e
    }
  };
}
let Ai = 0;
function xi(e, t, n) {
  if (t.__hasDevtools)
    return;
  t.__hasDevtools = !0;
  const r = Ai++;
  So({
    id: "org.vuejs.router" + (r ? "." + r : ""),
    label: "Vue Router",
    packageName: "vue-router",
    homepage: "https://router.vuejs.org",
    logo: "https://router.vuejs.org/logo.png",
    componentStateTypes: ["Routing"],
    app: e
  }, (s) => {
    typeof s.now != "function" && console.warn("[Vue Router]: You seem to be using an outdated version of Vue Devtools. Are you still using the Beta release instead of the stable one? You can find the links at https://devtools.vuejs.org/guide/installation.html."), s.on.inspectComponent((u, l) => {
      u.instanceData && u.instanceData.state.push({
        type: "Routing",
        key: "$route",
        editable: !1,
        value: Ce(t.currentRoute.value, "Current Route")
      });
    }), s.on.visitComponentTree(({ treeNode: u, componentInstance: l }) => {
      if (l.__vrv_devtools) {
        const f = l.__vrv_devtools;
        u.tags.push({
          label: (f.name ? `${f.name.toString()}: ` : "") + f.path,
          textColor: 0,
          tooltip: "This component is rendered by &lt;router-view&gt;",
          backgroundColor: Xn
        });
      }
      X(l.__vrl_devtools) && (l.__devtoolsApi = s, l.__vrl_devtools.forEach((f) => {
        let d = f.route.path, p = tr, m = "", y = 0;
        f.error ? (d = f.error, p = Mi, y = ji) : f.isExactActive ? (p = er, m = "This is exactly active") : f.isActive && (p = Zn, m = "This link is active"), u.tags.push({
          label: d,
          textColor: y,
          tooltip: m,
          backgroundColor: p
        });
      }));
    }), q(t.currentRoute, () => {
      c(), s.notifyComponentUpdate(), s.sendInspectorTree(a), s.sendInspectorState(a);
    });
    const o = "router:navigations:" + r;
    s.addTimelineLayer({
      id: o,
      label: `Router${r ? " " + r : ""} Navigations`,
      color: 4237508
    }), t.onError((u, l) => {
      s.addTimelineEvent({
        layerId: o,
        event: {
          title: "Error during Navigation",
          subtitle: l.fullPath,
          logType: "error",
          time: s.now(),
          data: { error: u },
          groupId: l.meta.__navigationId
        }
      });
    });
    let i = 0;
    t.beforeEach((u, l) => {
      const f = {
        guard: We("beforeEach"),
        from: Ce(l, "Current Location during this navigation"),
        to: Ce(u, "Target location")
      };
      Object.defineProperty(u.meta, "__navigationId", {
        value: i++
      }), s.addTimelineEvent({
        layerId: o,
        event: {
          time: s.now(),
          title: "Start of navigation",
          subtitle: u.fullPath,
          data: f,
          groupId: u.meta.__navigationId
        }
      });
    }), t.afterEach((u, l, f) => {
      const d = {
        guard: We("afterEach")
      };
      f ? (d.failure = {
        _custom: {
          type: Error,
          readOnly: !0,
          display: f ? f.message : "",
          tooltip: "Navigation Failure",
          value: f
        }
      }, d.status = We("❌")) : d.status = We("✅"), d.from = Ce(l, "Current Location during this navigation"), d.to = Ce(u, "Target location"), s.addTimelineEvent({
        layerId: o,
        event: {
          title: "End of navigation",
          subtitle: u.fullPath,
          time: s.now(),
          data: d,
          logType: f ? "warning" : "default",
          groupId: u.meta.__navigationId
        }
      });
    });
    const a = "router-inspector:" + r;
    s.addInspector({
      id: a,
      label: "Routes" + (r ? " " + r : ""),
      icon: "book",
      treeFilterPlaceholder: "Search routes"
    });
    function c() {
      if (!h)
        return;
      const u = h;
      let l = n.getRoutes().filter((f) => !f.parent || // these routes have a parent with no component which will not appear in the view
      // therefore we still need to include them
      !f.parent.record.components);
      l.forEach(sr), u.filter && (l = l.filter((f) => (
        // save matches state based on the payload
        St(f, u.filter.toLowerCase())
      ))), l.forEach((f) => rr(f, t.currentRoute.value)), u.rootNodes = l.map(nr);
    }
    let h;
    s.on.getInspectorTree((u) => {
      h = u, u.app === e && u.inspectorId === a && c();
    }), s.on.getInspectorState((u) => {
      if (u.app === e && u.inspectorId === a) {
        const f = n.getRoutes().find((d) => d.record.__vd_id === u.nodeId);
        f && (u.state = {
          options: Ti(f)
        });
      }
    }), s.sendInspectorTree(a), s.sendInspectorState(a);
  });
}
function $i(e) {
  return e.optional ? e.repeatable ? "*" : "?" : e.repeatable ? "+" : "";
}
function Ti(e) {
  const { record: t } = e, n = [
    { editable: !1, key: "path", value: t.path }
  ];
  return t.name != null && n.push({
    editable: !1,
    key: "name",
    value: t.name
  }), n.push({ editable: !1, key: "regexp", value: e.re }), e.keys.length && n.push({
    editable: !1,
    key: "keys",
    value: {
      _custom: {
        type: null,
        readOnly: !0,
        display: e.keys.map((r) => `${r.name}${$i(r)}`).join(" "),
        tooltip: "Param keys",
        value: e.keys
      }
    }
  }), t.redirect != null && n.push({
    editable: !1,
    key: "redirect",
    value: t.redirect
  }), e.alias.length && n.push({
    editable: !1,
    key: "aliases",
    value: e.alias.map((r) => r.record.path)
  }), Object.keys(e.record.meta).length && n.push({
    editable: !1,
    key: "meta",
    value: e.record.meta
  }), n.push({
    key: "score",
    editable: !1,
    value: {
      _custom: {
        type: null,
        readOnly: !0,
        display: e.score.map((r) => r.join(", ")).join(" | "),
        tooltip: "Score used to sort routes",
        value: e.score
      }
    }
  }), n;
}
const Xn = 15485081, Zn = 2450411, er = 8702998, Ii = 2282478, tr = 16486972, Di = 6710886, Mi = 16704226, ji = 12131356;
function nr(e) {
  const t = [], { record: n } = e;
  n.name != null && t.push({
    label: String(n.name),
    textColor: 0,
    backgroundColor: Ii
  }), n.aliasOf && t.push({
    label: "alias",
    textColor: 0,
    backgroundColor: tr
  }), e.__vd_match && t.push({
    label: "matches",
    textColor: 0,
    backgroundColor: Xn
  }), e.__vd_exactActive && t.push({
    label: "exact",
    textColor: 0,
    backgroundColor: er
  }), e.__vd_active && t.push({
    label: "active",
    textColor: 0,
    backgroundColor: Zn
  }), n.redirect && t.push({
    label: typeof n.redirect == "string" ? `redirect: ${n.redirect}` : "redirects",
    textColor: 16777215,
    backgroundColor: Di
  });
  let r = n.__vd_id;
  return r == null && (r = String(Li++), n.__vd_id = r), {
    id: r,
    label: n.path,
    tags: t,
    children: e.children.map(nr)
  };
}
let Li = 0;
const Bi = /^\/(.*)\/([a-z]*)$/;
function rr(e, t) {
  const n = t.matched.length && he(t.matched[t.matched.length - 1], e.record);
  e.__vd_exactActive = e.__vd_active = n, n || (e.__vd_active = t.matched.some((r) => he(r, e.record))), e.children.forEach((r) => rr(r, t));
}
function sr(e) {
  e.__vd_match = !1, e.children.forEach(sr);
}
function St(e, t) {
  const n = String(e.re).match(Bi);
  if (e.__vd_match = !1, !n || n.length < 3)
    return !1;
  if (new RegExp(n[1].replace(/\$$/, ""), n[2]).test(t))
    return e.children.forEach((i) => St(i, t)), e.record.path !== "/" || t === "/" ? (e.__vd_match = e.re.test(t), !0) : !1;
  const s = e.record.path.toLowerCase(), o = Oe(s);
  return !t.startsWith("/") && (o.includes(t) || s.includes(t)) || o.startsWith(t) || s.startsWith(t) || e.record.name && String(e.record.name).includes(t) ? !0 : e.children.some((i) => St(i, t));
}
function Fi(e, t) {
  const n = {};
  for (const r in e)
    t.includes(r) || (n[r] = e[r]);
  return n;
}
function Wi(e) {
  const t = ui(e.routes, e), n = e.parseQuery || wi, r = e.stringifyQuery || nn, s = e.history;
  if (O.NODE_ENV !== "production" && !s)
    throw new Error('Provide the "history" option when calling "createRouter()": https://router.vuejs.org/api/interfaces/RouterOptions.html#history');
  const o = Ve(), i = Ve(), a = Ve(), c = ae(le);
  let h = le;
  ie && e.scrollBehavior && "scrollRestoration" in history && (history.scrollRestoration = "manual");
  const u = it.bind(null, (g) => "" + g), l = it.bind(null, Mo), f = (
    // @ts-expect-error: intentionally avoid the type check
    it.bind(null, Oe)
  );
  function d(g, b) {
    let E, S;
    return Jn(g) ? (E = t.getRecordMatcher(g), O.NODE_ENV !== "production" && !E && N(`Parent route "${String(g)}" not found when adding child route`, b), S = b) : S = g, t.addRoute(S, E);
  }
  function p(g) {
    const b = t.getRecordMatcher(g);
    b ? t.removeRoute(b) : O.NODE_ENV !== "production" && N(`Cannot remove non-existent route "${String(g)}"`);
  }
  function m() {
    return t.getRoutes().map((g) => g.record);
  }
  function y(g) {
    return !!t.getRecordMatcher(g);
  }
  function _(g, b) {
    if (b = x({}, b || c.value), typeof g == "string") {
      const V = at(n, g, b.path), j = t.resolve({ path: V.path }, b), pe = s.createHref(V.fullPath);
      return O.NODE_ENV !== "production" && (pe.startsWith("//") ? N(`Location "${g}" resolved to "${pe}". A resolved location cannot start with multiple slashes.`) : j.matched.length || N(`No match found for location with path "${g}"`)), x(V, j, {
        params: f(j.params),
        hash: Oe(V.hash),
        redirectedFrom: void 0,
        href: pe
      });
    }
    if (O.NODE_ENV !== "production" && !ze(g))
      return N(`router.resolve() was passed an invalid location. This will fail in production.
- Location:`, g), _({});
    let E;
    if (g.path != null)
      O.NODE_ENV !== "production" && "params" in g && !("name" in g) && // @ts-expect-error: the type is never
      Object.keys(g.params).length && N(`Path "${g.path}" was passed with params but they will be ignored. Use a named route alongside params instead.`), E = x({}, g, {
        path: at(n, g.path, b.path).path
      });
    else {
      const V = x({}, g.params);
      for (const j in V)
        V[j] == null && delete V[j];
      E = x({}, g, {
        params: l(V)
      }), b.params = l(b.params);
    }
    const S = t.resolve(E, b), $ = g.hash || "";
    O.NODE_ENV !== "production" && $ && !$.startsWith("#") && N(`A \`hash\` should always start with the character "#". Replace "${$}" with "#${$}".`), S.params = u(f(S.params));
    const W = Bo(r, x({}, g, {
      hash: To($),
      path: S.path
    })), C = s.createHref(W);
    return O.NODE_ENV !== "production" && (C.startsWith("//") ? N(`Location "${g}" resolved to "${C}". A resolved location cannot start with multiple slashes.`) : S.matched.length || N(`No match found for location with path "${g.path != null ? g.path : g}"`)), x({
      fullPath: W,
      // keep the hash encoded so fullPath is effectively path + encodedQuery +
      // hash
      hash: $,
      query: (
        // if the user is using a custom query lib like qs, we might have
        // nested objects, so we keep the query as is, meaning it can contain
        // numbers at `$route.query`, but at the point, the user will have to
        // use their own type anyway.
        // https://github.com/vuejs/router/issues/328#issuecomment-649481567
        r === nn ? _i(g.query) : g.query || {}
      )
    }, S, {
      redirectedFrom: void 0,
      href: C
    });
  }
  function w(g) {
    return typeof g == "string" ? at(n, g, c.value.path) : x({}, g);
  }
  function k(g, b) {
    if (h !== g)
      return Pe(8, {
        from: b,
        to: g
      });
  }
  function v(g) {
    return T(g);
  }
  function R(g) {
    return v(x(w(g), { replace: !0 }));
  }
  function A(g) {
    const b = g.matched[g.matched.length - 1];
    if (b && b.redirect) {
      const { redirect: E } = b;
      let S = typeof E == "function" ? E(g) : E;
      if (typeof S == "string" && (S = S.includes("?") || S.includes("#") ? S = w(S) : (
        // force empty params
        { path: S }
      ), S.params = {}), O.NODE_ENV !== "production" && S.path == null && !("name" in S))
        throw N(`Invalid redirect found:
${JSON.stringify(S, null, 2)}
 when navigating to "${g.fullPath}". A redirect must contain a name or path. This will break in production.`), new Error("Invalid redirect");
      return x({
        query: g.query,
        hash: g.hash,
        // avoid transferring params if the redirect has a path
        params: S.path != null ? {} : g.params
      }, S);
    }
  }
  function T(g, b) {
    const E = h = _(g), S = c.value, $ = g.state, W = g.force, C = g.replace === !0, V = A(E);
    if (V)
      return T(
        x(w(V), {
          state: typeof V == "object" ? x({}, $, V.state) : $,
          force: W,
          replace: C
        }),
        // keep original redirectedFrom if it exists
        b || E
      );
    const j = E;
    j.redirectedFrom = b;
    let pe;
    return !W && zt(r, S, E) && (pe = Pe(16, { to: j, from: S }), Tt(
      S,
      S,
      // this is a push, the only way for it to be triggered from a
      // history.listen is with a redirect, which makes it become a push
      !0,
      // This cannot be the first navigation because the initial location
      // cannot be manually navigated to
      !1
    )), (pe ? Promise.resolve(pe) : P(j, S)).catch((z) => oe(z) ? (
      // navigation redirects still mark the router as ready
      oe(
        z,
        2
        /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
      ) ? z : rt(z)
    ) : (
      // reject any unknown error
      nt(z, j, S)
    )).then((z) => {
      if (z) {
        if (oe(
          z,
          2
          /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
        ))
          return O.NODE_ENV !== "production" && // we are redirecting to the same location we were already at
          zt(r, _(z.to), j) && // and we have done it a couple of times
          b && // @ts-expect-error: added only in dev
          (b._count = b._count ? (
            // @ts-expect-error
            b._count + 1
          ) : 1) > 30 ? (N(`Detected a possibly infinite redirection in a navigation guard when going from "${S.fullPath}" to "${j.fullPath}". Aborting to avoid a Stack Overflow.
 Are you always returning a new location within a navigation guard? That would lead to this error. Only return when redirecting or aborting, that should fix this. This might break in production if not fixed.`), Promise.reject(new Error("Infinite redirect in navigation guard"))) : T(
            // keep options
            x({
              // preserve an existing replacement but allow the redirect to override it
              replace: C
            }, w(z.to), {
              state: typeof z.to == "object" ? x({}, $, z.to.state) : $,
              force: W
            }),
            // preserve the original redirectedFrom if any
            b || j
          );
      } else
        z = F(j, S, !0, C, $);
      return I(j, S, z), z;
    });
  }
  function B(g, b) {
    const E = k(g, b);
    return E ? Promise.reject(E) : Promise.resolve();
  }
  function Q(g) {
    const b = Le.values().next().value;
    return b && typeof b.runWithContext == "function" ? b.runWithContext(g) : g();
  }
  function P(g, b) {
    let E;
    const [S, $, W] = Ui(g, b);
    E = lt(S.reverse(), "beforeRouteLeave", g, b);
    for (const V of S)
      V.leaveGuards.forEach((j) => {
        E.push(ue(j, g, b));
      });
    const C = B.bind(null, g, b);
    return E.push(C), we(E).then(() => {
      E = [];
      for (const V of o.list())
        E.push(ue(V, g, b));
      return E.push(C), we(E);
    }).then(() => {
      E = lt($, "beforeRouteUpdate", g, b);
      for (const V of $)
        V.updateGuards.forEach((j) => {
          E.push(ue(j, g, b));
        });
      return E.push(C), we(E);
    }).then(() => {
      E = [];
      for (const V of W)
        if (V.beforeEnter)
          if (X(V.beforeEnter))
            for (const j of V.beforeEnter)
              E.push(ue(j, g, b));
          else
            E.push(ue(V.beforeEnter, g, b));
      return E.push(C), we(E);
    }).then(() => (g.matched.forEach((V) => V.enterCallbacks = {}), E = lt(W, "beforeRouteEnter", g, b, Q), E.push(C), we(E))).then(() => {
      E = [];
      for (const V of i.list())
        E.push(ue(V, g, b));
      return E.push(C), we(E);
    }).catch((V) => oe(
      V,
      8
      /* ErrorTypes.NAVIGATION_CANCELLED */
    ) ? V : Promise.reject(V));
  }
  function I(g, b, E) {
    a.list().forEach((S) => Q(() => S(g, b, E)));
  }
  function F(g, b, E, S, $) {
    const W = k(g, b);
    if (W)
      return W;
    const C = b === le, V = ie ? history.state : {};
    E && (S || C ? s.replace(g.fullPath, x({
      scroll: C && V && V.scroll
    }, $)) : s.push(g.fullPath, $)), c.value = g, Tt(g, b, E, C), rt();
  }
  let ee;
  function lr() {
    ee || (ee = s.listen((g, b, E) => {
      if (!It.listening)
        return;
      const S = _(g), $ = A(S);
      if ($) {
        T(x($, { replace: !0, force: !0 }), S).catch(xe);
        return;
      }
      h = S;
      const W = c.value;
      ie && Ko(Gt(W.fullPath, E.delta), Je()), P(S, W).catch((C) => oe(
        C,
        12
        /* ErrorTypes.NAVIGATION_CANCELLED */
      ) ? C : oe(
        C,
        2
        /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
      ) ? (T(
        x(w(C.to), {
          force: !0
        }),
        S
        // avoid an uncaught rejection, let push call triggerError
      ).then((V) => {
        oe(
          V,
          20
          /* ErrorTypes.NAVIGATION_DUPLICATED */
        ) && !E.delta && E.type === Ne.pop && s.go(-1, !1);
      }).catch(xe), Promise.reject()) : (E.delta && s.go(-E.delta, !1), nt(C, S, W))).then((C) => {
        C = C || F(
          // after navigation, all matched components are resolved
          S,
          W,
          !1
        ), C && (E.delta && // a new navigation has been triggered, so we do not want to revert, that will change the current history
        // entry while a different route is displayed
        !oe(
          C,
          8
          /* ErrorTypes.NAVIGATION_CANCELLED */
        ) ? s.go(-E.delta, !1) : E.type === Ne.pop && oe(
          C,
          20
          /* ErrorTypes.NAVIGATION_DUPLICATED */
        ) && s.go(-1, !1)), I(S, W, C);
      }).catch(xe);
    }));
  }
  let tt = Ve(), $t = Ve(), je;
  function nt(g, b, E) {
    rt(g);
    const S = $t.list();
    return S.length ? S.forEach(($) => $(g, b, E)) : (O.NODE_ENV !== "production" && N("uncaught error during route navigation:"), console.error(g)), Promise.reject(g);
  }
  function ur() {
    return je && c.value !== le ? Promise.resolve() : new Promise((g, b) => {
      tt.add([g, b]);
    });
  }
  function rt(g) {
    return je || (je = !g, lr(), tt.list().forEach(([b, E]) => g ? E(g) : b()), tt.reset()), g;
  }
  function Tt(g, b, E, S) {
    const { scrollBehavior: $ } = e;
    if (!ie || !$)
      return Promise.resolve();
    const W = !E && Go(Gt(g.fullPath, 0)) || (S || !E) && history.state && history.state.scroll || null;
    return Se().then(() => $(g, b, W)).then((C) => C && zo(C)).catch((C) => nt(C, g, b));
  }
  const st = (g) => s.go(g);
  let ot;
  const Le = /* @__PURE__ */ new Set(), It = {
    currentRoute: c,
    listening: !0,
    addRoute: d,
    removeRoute: p,
    clearRoutes: t.clearRoutes,
    hasRoute: y,
    getRoutes: m,
    resolve: _,
    options: e,
    push: v,
    replace: R,
    go: st,
    back: () => st(-1),
    forward: () => st(1),
    beforeEach: o.add,
    beforeResolve: i.add,
    afterEach: a.add,
    onError: $t.add,
    isReady: ur,
    install(g) {
      const b = this;
      g.component("RouterLink", Ri), g.component("RouterView", Vi), g.config.globalProperties.$router = b, Object.defineProperty(g.config.globalProperties, "$route", {
        enumerable: !0,
        get: () => K(c)
      }), ie && // used for the initial navigation client side to avoid pushing
      // multiple times when the router is used in multiple apps
      !ot && c.value === le && (ot = !0, v(s.location).catch(($) => {
        O.NODE_ENV !== "production" && N("Unexpected error when starting the router:", $);
      }));
      const E = {};
      for (const $ in le)
        Object.defineProperty(E, $, {
          get: () => c.value[$],
          enumerable: !0
        });
      g.provide(Qe, b), g.provide(xt, Rr(E)), g.provide(bt, c);
      const S = g.unmount;
      Le.add(g), g.unmount = function() {
        Le.delete(g), Le.size < 1 && (h = le, ee && ee(), ee = null, c.value = le, ot = !1, je = !1), S();
      }, O.NODE_ENV !== "production" && ie && xi(g, b, t);
    }
  };
  function we(g) {
    return g.reduce((b, E) => b.then(() => Q(E)), Promise.resolve());
  }
  return It;
}
function Ui(e, t) {
  const n = [], r = [], s = [], o = Math.max(t.matched.length, e.matched.length);
  for (let i = 0; i < o; i++) {
    const a = t.matched[i];
    a && (e.matched.find((h) => he(h, a)) ? r.push(a) : n.push(a));
    const c = e.matched[i];
    c && (t.matched.find((h) => he(h, c)) || s.push(c));
  }
  return [n, r, s];
}
function Hi() {
  return ce(Qe);
}
function zi(e) {
  return ce(xt);
}
const or = Symbol("BINDING_GETTER_KEY");
function Ki(e, t) {
  const n = Qi(e, t);
  return Gi(e, n, t), Nr(() => {
    n._release();
  }), H(or, n), {
    bindingGetter: n
  };
}
function Gi(e, t, n) {
  var s, o, i, a, c, h, u, l, f;
  const { id: r } = e;
  if (qi(n.vforSetting, r, t), Ji(n.slotSetting, r, t), e.routerParam) {
    const d = D(r, e.routerParam), p = zi(), m = L(() => p.params);
    t._registerBinding(d, m), H(d, m);
  }
  if (e.routerAct) {
    const d = D(r, e.routerAct), p = Hi();
    t._registerBinding(d, p), H(d, p);
  }
  (s = e.data) == null || s.forEach((d) => {
    const p = D(r, d.id);
    t._registerBinding(p, d.value), H(p, d.value);
  }), (o = e.jsFn) == null || o.forEach((d) => {
    const p = D(r, d.id), m = Yi(d);
    t._registerBinding(p, m), H(p, m);
  }), (i = e.eRefs) == null || i.forEach((d) => {
    const p = D(r, d.id), m = ae(null);
    t._registerBinding(p, m), H(p, m);
  }), (a = e.refs) == null || a.forEach((d) => {
    const { id: p, constData: m } = d, _ = m !== void 0 ? t.getValue(d.value) : d.value, w = D(r, p), k = ro({ ...d, value: _ });
    t._registerBinding(w, k), H(w, k);
  }), (c = e.web_computed) == null || c.forEach((d) => {
    const p = D(r, d.id), m = oo(d);
    t._registerBinding(p, m), H(p, m);
  }), (h = e.js_computed) == null || h.forEach((d) => {
    const p = D(r, d.id), m = io(
      d,
      t
    );
    t._registerBinding(p, m), H(p, m);
  }), (u = e.vue_computed) == null || u.forEach((d) => {
    const p = D(r, d.id), m = so(
      d,
      t
    );
    t._registerBinding(p, m), H(p, m);
  }), co({
    watchConfigs: e.py_watch || [],
    computedConfigs: e.web_computed || [],
    bindingGetter: t,
    sid: r
  }), (l = e.js_watch) == null || l.forEach((d) => {
    mo(d, t);
  }), (f = e.vue_watch) == null || f.forEach((d) => {
    po(d, t);
  });
}
function qi(e, t, n) {
  if (e != null && e.item) {
    const { id: r } = e.item, s = D(t, r), o = Xi(e.item, n);
    n._registerBinding(s, o), H(s, o);
  }
  if (e != null && e.index) {
    const { id: r, value: s } = e.index, o = D(t, r), i = U(s);
    n._registerBinding(o, i), H(o, i);
  }
  if (e != null && e.key) {
    const { id: r, value: s } = e.key, o = D(t, r), i = U(s);
    n._registerBinding(o, i), H(o, i);
  }
}
function Ji(e, t, n) {
  if (!e)
    return;
  const { id: r, value: s } = e, o = D(t, r), i = ae(s);
  n._registerBinding(o, i), H(o, i);
}
function Qi(e, t) {
  const { binds: n } = e, r = /* @__PURE__ */ new Map(), s = /* @__PURE__ */ new Map();
  let o = null, i = null;
  const a = Zi(
    n,
    e.web_computed,
    e.id,
    t
  );
  a == null || a.forEach((v, R) => {
    const { sid: A, id: T } = v, B = D(A, T);
    if (A !== e.id) {
      const Q = ce(B);
      r.set(R, Q);
    } else
      s.set(B, R);
  });
  function c(v) {
    const R = h(v);
    return qs(R, {
      paths: v.path,
      getBindableValueFn: u
    });
  }
  function h(v) {
    const R = r.get(v.r);
    if (!R)
      throw new Error(`Binding not found: ${JSON.stringify(v)}`);
    return R;
  }
  function u(v) {
    return be(c(v));
  }
  function l(v) {
    const R = r.get(v.r);
    if (!R)
      throw new Error(`Router binding not found: ${JSON.stringify(v)}`);
    return R;
  }
  function f(v, R) {
    if (Rn(v)) {
      const A = h(v);
      if (v.path) {
        In(A.value, v.path, R, u);
        return;
      }
      A.value = R;
      return;
    }
    throw new Error(`Unsupported output binding: ${v}`);
  }
  function d(v) {
    if (v != null && v.item) {
      const { id: R, value: A, sourceInfo: T } = v.item;
      if (T) {
        const { index: P, key: I } = T;
        o && (o.value = P), i && (i.value = I);
      }
      const B = D(e.id, R), Q = c({ r: m(B) });
      Q.value = A;
    }
    if (v != null && v.index) {
      const { id: R, value: A } = v.index, T = D(e.id, R), B = c({ r: m(T) });
      B.value = A;
    }
    if (v != null && v.key) {
      const { id: R, value: A } = v.key, T = D(e.id, R), B = c({ r: m(T) });
      B.value = A;
    }
  }
  function p(v) {
    if (!v)
      return;
    const { id: R, value: A } = v, T = D(e.id, R), B = c({ r: m(T) });
    B.value = A;
  }
  function m(v) {
    return s.get(v);
  }
  function y(v, R) {
    const A = s.get(v);
    A !== void 0 && r.set(A, R);
  }
  function _() {
    r.clear(), s.clear();
  }
  function w(v) {
    return o = U(v), o;
  }
  function k(v) {
    return i = U(v), i;
  }
  return {
    getValue: u,
    getRef: c,
    updateValue: f,
    getBindIndex: m,
    updateVForInfo: d,
    updateSlotInfo: p,
    getRouter: l,
    initVForIndexRef: w,
    initVForKeyRef: k,
    _registerBinding: y,
    _release: _
  };
}
function D(e, t) {
  return `${e}-${t}`;
}
function Yi(e) {
  const { immediately: t = !1, code: n } = e;
  let r = J(n);
  return t && (r = r()), ye(() => ({
    get() {
      return r;
    },
    set() {
      throw new Error("Cannot set value to js function");
    }
  }));
}
function ec() {
  const { getRef: e, getRouter: t, getValue: n } = ce(or);
  return {
    getRef: e,
    getRouter: t,
    getValue: n
  };
}
function Xi(e, t) {
  const { value: n, sourceInfo: r } = e;
  if (r) {
    const { source: s, type: o, index: i, key: a } = r, c = t.initVForIndexRef(i);
    return o === "array" ? ye(() => ({
      get() {
        return s.value[c.value];
      },
      set(h) {
        s.value[c.value] = h;
      }
    })) : ye(() => {
      const h = t.initVForKeyRef(a);
      return {
        get() {
          return s.value[h.value];
        },
        set(u) {
          s.value[h.value] = u;
        }
      };
    });
  }
  return U(n);
}
function Zi(e, t, n, r) {
  const s = new Set(e == null ? void 0 : e.map((c) => D(c.sid, c.id))), o = ea(
    e,
    s,
    t,
    n
  ), i = ta(
    o,
    s,
    n,
    r
  );
  return na(
    i,
    s,
    n,
    r
  );
}
function ea(e, t, n, r) {
  if (!n)
    return e;
  const s = n.filter((o) => !t.has(D(r, o.id))).map((o) => ({ id: o.id, sid: r }));
  return [...e ?? [], ...s];
}
function ta(e, t, n, r) {
  if (!r.vforSetting)
    return e;
  const s = [];
  return r.vforSetting.item && !t.has(D(n, r.vforSetting.item.id)) && s.push({
    id: r.vforSetting.item.id,
    sid: n
  }), r.vforSetting.index && !t.has(D(n, r.vforSetting.index.id)) && s.push({
    id: r.vforSetting.index.id,
    sid: n
  }), r.vforSetting.key && !t.has(D(n, r.vforSetting.key.id)) && s.push({
    id: r.vforSetting.key.id,
    sid: n
  }), [...e ?? [], ...s];
}
function na(e, t, n, r) {
  return !r.slotSetting || t.has(D(n, r.slotSetting.id)) ? e : [
    ...e ?? [],
    { id: r.slotSetting.id, sid: n }
  ];
}
const ir = Z(ra, {
  props: ["config", "vforSetting", "slotSetting"]
});
function ra(e) {
  const { config: t, vforSetting: n, slotSetting: r } = e, { items: s } = t, { bindingGetter: o } = Ki(t, { vforSetting: n, slotSetting: r });
  return () => {
    if (o.updateVForInfo(e.vforSetting), o.updateSlotInfo(e.slotSetting), !s)
      return null;
    if (s.length === 1) {
      const i = s[0];
      return ve(i, { sid: t.id, bindingGetter: o });
    }
    return s == null ? void 0 : s.map(
      (i) => ve(i, { sid: t.id, bindingGetter: o })
    );
  };
}
function sa(e, t) {
  const { state: n, isReady: r, isLoading: s } = Is(async () => {
    let o = e;
    const i = t;
    if (!o && !i)
      throw new Error("Either config or configUrl must be provided");
    if (!o && i && (o = await (await fetch(i)).json()), !o)
      throw new Error("Failed to load config");
    return o;
  }, {});
  return { config: n, isReady: r, isLoading: s };
}
function oa(e) {
  const t = U(!1), n = U("");
  function r(s, o) {
    let i;
    return o.component ? i = `Error captured from component:tag: ${o.component.tag} ; id: ${o.component.id} ` : i = "Error captured from app init", console.group(i), console.error("Component:", o.component), console.error("Error:", s), console.groupEnd(), e && (t.value = !0, n.value = `${i} ${s.message}`), !1;
  }
  return Pr(r), { hasError: t, errorMessage: n };
}
function ia(e) {
  if (!(e === "web" || e === "webview") && e !== "zero")
    throw new Error(`Unsupported mode: ${e}`);
}
function aa(e, t) {
  const n = L(() => {
    const r = e.value;
    if (!r)
      return null;
    const i = new DOMParser().parseFromString(r, "image/svg+xml").querySelector("svg");
    if (!i)
      throw new Error("Invalid svg string");
    const a = {};
    for (const f of i.attributes)
      a[f.name] = f.value;
    const { size: c, color: h, attrs: u } = t;
    h.value !== null && h.value !== void 0 && (i.removeAttribute("fill"), i.querySelectorAll("*").forEach((d) => {
      d.hasAttribute("fill") && d.setAttribute("fill", "currentColor");
    }), a.color = h.value), c.value !== null && c.value !== void 0 && (a.width = c.value.toString(), a.height = c.value.toString());
    const l = i.innerHTML;
    return {
      ...a,
      ...u,
      innerHTML: l
    };
  });
  return () => {
    if (!n.value)
      return null;
    const r = n.value;
    return G("svg", r);
  };
}
const ln = "assets/icons";
async function ca(e) {
  if (!e) return;
  const { names: t, sets: n } = e, r = [];
  if (t) {
    const o = {};
    for (const i of t) {
      const [a, c] = i.split(":");
      o[a] || (o[a] = []), o[a].push(c);
    }
    for (const i of Object.keys(o)) {
      const a = `/${ln}/${i}.svg`, c = await fetch(a);
      if (!c.ok) throw new Error(`Failed to load ${a}`);
      const h = await c.text(), l = new DOMParser().parseFromString(h, "image/svg+xml");
      for (const f of o[i]) {
        const d = l.getElementById(f);
        if (!d) {
          console.warn(`Failed to find icon ${f} in ${a}`);
          continue;
        }
        d.setAttribute("id", `${i}:${f}`), r.push(d.outerHTML);
      }
    }
  }
  if (n)
    for (const o of n) {
      const i = `/${ln}/${o}.svg`, a = await fetch(i);
      if (!a.ok) throw new Error(`Failed to load ${i}`);
      const c = await a.text(), u = new DOMParser().parseFromString(c, "image/svg+xml"), l = Array.from(u.querySelectorAll("symbol"));
      if (l.length === 0) {
        console.warn(`No <symbol> found in ${i}`);
        continue;
      }
      for (const f of l) {
        const d = f.getAttribute("id");
        d && (f.setAttribute("id", `${o}:${d}`), r.push(f.outerHTML));
      }
    }
  const s = `<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
${r.join(
    `
`
  )}
</svg>`;
  document.body.insertAdjacentHTML("afterbegin", s);
}
const la = {
  class: "app-box insta-theme",
  "data-scaling": "100%"
}, ua = {
  key: 0,
  style: { position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)" }
}, fa = {
  key: 0,
  style: { color: "red", "font-size": "1.2em", margin: "1rem", border: "1px dashed red", padding: "1rem" }
}, da = /* @__PURE__ */ Z({
  __name: "App",
  props: {
    config: {},
    meta: {},
    configUrl: {}
  },
  setup(e) {
    const t = e, { debug: n = !1 } = t.meta, { config: r, isLoading: s } = sa(
      t.config,
      t.configUrl
    );
    q(r, (a) => {
      a.url && (Ir({
        mode: t.meta.mode,
        version: t.meta.version,
        queryPath: a.url.path,
        pathParams: a.url.params,
        webServerInfo: a.webInfo,
        debug: n
      }), Yr(t.meta.mode), ca(a.icons)), ia(t.meta.mode);
    });
    const { hasError: o, errorMessage: i } = oa(n);
    return (a, c) => (fe(), Ee("div", la, [
      K(s) ? (fe(), Ee("div", ua, c[0] || (c[0] = [
        yn("p", { style: { margin: "auto" } }, "Loading ...", -1)
      ]))) : (fe(), Ee("div", {
        key: 1,
        class: ut(["insta-main", K(r).class])
      }, [
        Vr(K(ir), {
          config: K(r).scope
        }, null, 8, ["config"]),
        K(o) ? (fe(), Ee("div", fa, mn(K(i)), 1)) : ft("", !0)
      ], 2))
    ]));
  }
}), un = /* @__PURE__ */ new Map([
  [
    "size",
    {
      classes: "ist-r-size",
      handler: (e) => ha(e)
    }
  ],
  [
    "weight",
    {
      classes: "ist-r-weight",
      styleVar: "--weight",
      handler: (e) => e
    }
  ],
  [
    "text_align",
    {
      classes: "ist-r-ta",
      styleVar: "--ta",
      handler: (e) => e
    }
  ],
  [
    "trim",
    {
      classes: (e) => pa("ist-r", e)
    }
  ],
  [
    "truncate",
    {
      classes: "ist-r-truncate"
    }
  ],
  [
    "text_wrap",
    {
      classes: "ist-r-tw",
      handler: (e) => ma(e)
    }
  ]
]);
function ar(e) {
  const t = {}, n = [], r = {};
  for (const [o, i] of Object.entries(e)) {
    if (i === void 0 || !un.has(o))
      continue;
    const a = typeof i == "object" ? i : { initial: i };
    for (const [c, h] of Object.entries(a)) {
      const { classes: u, styleVar: l, handler: f, propHandler: d } = un.get(o), p = c === "initial";
      if (u) {
        const m = typeof u == "function" ? u(h) : u, y = p ? m : `${c}:${m}`;
        n.push(y);
      }
      if (f) {
        const m = f(h);
        if (l) {
          const y = p ? l : `${l}-${c}`;
          t[y] = m;
        } else {
          if (!Array.isArray(m))
            throw new Error(`Invalid style value: ${m}`);
          m.forEach((y) => {
            for (const [_, w] of Object.entries(y))
              t[_] = w;
          });
        }
      }
      if (d) {
        const m = d(h);
        for (const [y, _] of Object.entries(m))
          r[y] = _;
      }
    }
  }
  return {
    classes: n.join(" "),
    style: t,
    props: r
  };
}
function ha(e) {
  const t = Number(e);
  if (isNaN(t))
    throw new Error(`Invalid font size value: ${e}`);
  return [
    { "--fs": `var(--font-size-${t})` },
    { "--lh": `var(--line-height-${t})` },
    { "--ls": `var(--letter-spacing-${t})` }
  ];
}
function pa(e, t) {
  return `${e}-lt-${t}`;
}
function ma(e) {
  if (e === "wrap")
    return [
      {
        "--ws": "normal"
      }
    ];
  if (e === "nowrap")
    return [
      {
        "--ws": "nowrap"
      }
    ];
  if (e === "pretty")
    return [{ "--ws": "normal" }, { "--tw": "pretty" }];
  if (e === "balance")
    return [{ "--ws": "normal" }, { "--tw": "balance" }];
  throw new Error(`Invalid text wrap value: ${e}`);
}
const ga = "insta-Heading", ya = Z(va, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function va(e) {
  return () => {
    const { classes: t, style: n, props: r } = ar(e), s = de(
      { class: t, style: n, ...r },
      { class: ga }
    );
    return G(e.as || "h1", s, e.innerText);
  };
}
const wa = /* @__PURE__ */ Z({
  __name: "_Teleport",
  props: {
    to: {},
    defer: { type: Boolean, default: !0 },
    disabled: { type: Boolean, default: !1 }
  },
  setup(e) {
    return (t, n) => (fe(), vn(Cr, {
      to: t.to,
      defer: t.defer,
      disabled: t.disabled
    }, [
      Ar(t.$slots, "default")
    ], 8, ["to", "defer", "disabled"]));
  }
}), _a = ["width", "height", "color"], Ea = ["xlink:href"], ba = /* @__PURE__ */ Z({
  __name: "Icon",
  props: {
    size: {},
    icon: {},
    color: {},
    assetPath: {},
    svgName: {},
    rawSvg: {}
  },
  setup(e) {
    const t = e, n = me(() => t.icon ? t.icon.split(":")[1] : ""), r = me(() => t.size || "1em"), s = me(() => t.color || "currentColor"), o = me(() => t.rawSvg || null), i = L(() => `#${t.icon}`), a = xr(), c = aa(o, {
      size: me(() => t.size),
      color: me(() => t.color),
      attrs: a
    });
    return (h, u) => (fe(), Ee($r, null, [
      n.value ? (fe(), Ee("svg", de({
        key: 0,
        width: r.value,
        height: r.value,
        color: s.value
      }, K(a)), [
        yn("use", { "xlink:href": i.value }, null, 8, Ea)
      ], 16, _a)) : ft("", !0),
      o.value ? (fe(), vn(K(c), { key: 1 })) : ft("", !0)
    ], 64));
  }
}), $e = /* @__PURE__ */ new Map([
  [
    "p",
    {
      classes: "ist-r-p",
      styleVar: "--p",
      handler: (e) => M("space", e)
    }
  ],
  [
    "px",
    {
      classes: "ist-r-px",
      styleVar: "--px",
      handler: (e) => M("space", e)
    }
  ],
  [
    "py",
    {
      classes: "ist-r-py",
      styleVar: "--py",
      handler: (e) => M("space", e)
    }
  ],
  [
    "pt",
    {
      classes: "ist-r-pt",
      styleVar: "--pt",
      handler: (e) => M("space", e)
    }
  ],
  [
    "pb",
    {
      classes: "ist-r-pb",
      styleVar: "--pb",
      handler: (e) => M("space", e)
    }
  ],
  [
    "pl",
    {
      classes: "ist-r-pl",
      styleVar: "--pl",
      handler: (e) => M("space", e)
    }
  ],
  [
    "pr",
    {
      classes: "ist-r-pr",
      styleVar: "--pr",
      handler: (e) => M("space", e)
    }
  ],
  [
    "width",
    {
      classes: "ist-r-w",
      styleVar: "--width",
      handler: (e) => e
    }
  ],
  [
    "height",
    {
      classes: "ist-r-h",
      styleVar: "--height",
      handler: (e) => e
    }
  ],
  [
    "min_width",
    {
      classes: "ist-r-min-w",
      styleVar: "--min_width",
      handler: (e) => e
    }
  ],
  [
    "min_height",
    {
      classes: "ist-r-min-h",
      styleVar: "--min_height",
      handler: (e) => e
    }
  ],
  [
    "max_width",
    {
      classes: "ist-r-max-w",
      styleVar: "--max_width",
      handler: (e) => e
    }
  ],
  [
    "max_height",
    {
      classes: "ist-r-max-h",
      styleVar: "--max_height",
      handler: (e) => e
    }
  ],
  [
    "position",
    {
      classes: "ist-r-position",
      styleVar: "--position",
      handler: (e) => e
    }
  ],
  [
    "inset",
    {
      classes: "ist-r-inset",
      styleVar: "--inset",
      handler: (e) => M("space", e)
    }
  ],
  [
    "top",
    {
      classes: "ist-r-top",
      styleVar: "--top",
      handler: (e) => M("space", e)
    }
  ],
  [
    "right",
    {
      classes: "ist-r-right",
      styleVar: "--right",
      handler: (e) => M("space", e)
    }
  ],
  [
    "bottom",
    {
      classes: "ist-r-bottom",
      styleVar: "--bottom",
      handler: (e) => M("space", e)
    }
  ],
  [
    "left",
    {
      classes: "ist-r-left",
      styleVar: "--left",
      handler: (e) => M("space", e)
    }
  ],
  [
    "overflow",
    {
      classes: "ist-r-overflow",
      styleVar: "--overflow",
      handler: (e) => e
    }
  ],
  [
    "overflow_x",
    {
      classes: "ist-r-ox",
      styleVar: "--overflow_x",
      handler: (e) => e
    }
  ],
  [
    "overflow_y",
    {
      classes: "ist-r-oy",
      styleVar: "--overflow_y",
      handler: (e) => e
    }
  ],
  [
    "flex_basis",
    {
      classes: "ist-r-fb",
      styleVar: "--flex_basis",
      handler: (e) => e
    }
  ],
  [
    "flex_shrink",
    {
      classes: "ist-r-fs",
      styleVar: "--flex_shrink",
      handler: (e) => e
    }
  ],
  [
    "flex_grow",
    {
      classes: "ist-r-fg",
      styleVar: "--flex_grow",
      handler: (e) => e
    }
  ],
  [
    "grid_area",
    {
      classes: "ist-r-ga",
      styleVar: "--grid_area",
      handler: (e) => e
    }
  ],
  [
    "grid_column",
    {
      classes: "ist-r-gc",
      styleVar: "--grid_column",
      handler: (e) => e
    }
  ],
  [
    "grid_column_start",
    {
      classes: "ist-r-gcs",
      styleVar: "--grid_column_start",
      handler: (e) => e
    }
  ],
  [
    "grid_column_end",
    {
      classes: "ist-r-gce",
      styleVar: "--grid_column_end",
      handler: (e) => e
    }
  ],
  [
    "grid_row",
    {
      classes: "ist-r-gr",
      styleVar: "--grid_row",
      handler: (e) => e
    }
  ],
  [
    "grid_row_start",
    {
      classes: "ist-r-grs",
      styleVar: "--grid_row_start",
      handler: (e) => e
    }
  ],
  [
    "grid_row_end",
    {
      classes: "ist-r-gre",
      styleVar: "--grid_row_end",
      handler: (e) => e
    }
  ],
  [
    "m",
    {
      classes: "ist-r-m",
      styleVar: "--m",
      handler: (e) => M("space", e)
    }
  ],
  [
    "mx",
    {
      classes: "ist-r-mx",
      styleVar: "--mx",
      handler: (e) => M("space", e)
    }
  ],
  [
    "my",
    {
      classes: "ist-r-my",
      styleVar: "--my",
      handler: (e) => M("space", e)
    }
  ],
  [
    "mt",
    {
      classes: "ist-r-mt",
      styleVar: "--mt",
      handler: (e) => M("space", e)
    }
  ],
  [
    "mr",
    {
      classes: "ist-r-mr",
      styleVar: "--mr",
      handler: (e) => M("space", e)
    }
  ],
  [
    "mb",
    {
      classes: "ist-r-mb",
      styleVar: "--mb",
      handler: (e) => M("space", e)
    }
  ],
  [
    "ml",
    {
      classes: "ist-r-ml",
      styleVar: "--ml",
      handler: (e) => M("space", e)
    }
  ],
  [
    "display",
    {
      classes: "ist-r-display",
      styleVar: "--display",
      handler: (e) => e
    }
  ],
  [
    "direction",
    {
      classes: "ist-r-fd",
      styleVar: "--direction",
      handler: (e) => e
    }
  ],
  [
    "align",
    {
      classes: "ist-r-ai",
      styleVar: "--align",
      handler: (e) => e
    }
  ],
  [
    "justify",
    {
      classes: "ist-r-jc",
      styleVar: "--justify",
      handler: (e) => e
    }
  ],
  [
    "wrap",
    {
      classes: "ist-r-wrap",
      styleVar: "--wrap",
      handler: (e) => e
    }
  ],
  [
    "gap",
    {
      classes: "ist-r-gap",
      styleVar: "--gap",
      handler: (e) => M("space", e)
    }
  ],
  [
    "gap_x",
    {
      classes: "ist-r-cg",
      styleVar: "--gap_x",
      handler: (e) => M("space", e)
    }
  ],
  [
    "gap_y",
    {
      classes: "ist-r-rg",
      styleVar: "--gap_y",
      handler: (e) => M("space", e)
    }
  ],
  [
    "areas",
    {
      classes: "ist-r-gta",
      styleVar: "--areas",
      handler: (e) => e
    }
  ],
  [
    "columns",
    {
      classes: "ist-r-gtc",
      styleVar: "--columns",
      handler: (e) => fn(e)
    }
  ],
  [
    "rows",
    {
      classes: "ist-r-gtr",
      styleVar: "--rows",
      handler: (e) => fn(e)
    }
  ],
  [
    "flow",
    {
      classes: "ist-r-gaf",
      styleVar: "--flow",
      handler: (e) => e
    }
  ],
  [
    "ctn_size",
    {
      classes: "ist-r-ctn_size",
      styleVar: "--ctn_size",
      handler: (e) => M("container", e)
    }
  ]
]);
function Ye(e) {
  e.length > 1 && console.warn("Only accept one child element when as_child is true");
}
function Xe(e) {
  return Object.fromEntries(
    Object.entries(e).filter(([t, n]) => n !== void 0)
  );
}
function Ze(e, t) {
  const n = {}, r = [], s = new Set(t || []), o = {
    style: {},
    class: []
  };
  for (const [a, c] of Object.entries(e)) {
    if (!$e.has(a))
      continue;
    const h = typeof c == "object" ? c : { initial: c };
    for (const [u, l] of Object.entries(h)) {
      const { classes: f, styleVar: d, handler: p } = $e.get(a), m = u === "initial", y = m ? f : `${u}:${f}`, _ = m ? d : `${d}-${u}`, w = p(l);
      if (s.has(a)) {
        o.class.push(y), o.style[_] = w;
        continue;
      }
      r.push(y), n[_] = w;
    }
  }
  return {
    classes: r.join(" "),
    style: n,
    excludeReslut: o
  };
}
function M(e, t) {
  const n = Number(t);
  if (isNaN(n))
    return t;
  {
    const r = n < 0 ? -1 : 1;
    return `calc(var(--${e}-${n}) * ${r})`;
  }
}
function fn(e) {
  const t = Number(e);
  return isNaN(t) ? e : `repeat(${t}, 1fr)`;
}
const et = [
  "p",
  "px",
  "py",
  "pt",
  "pb",
  "pl",
  "pr",
  "width",
  "height",
  "min_width",
  "min_height",
  "max_width",
  "max_height",
  "position",
  "inset",
  "top",
  "right",
  "bottom",
  "left",
  "overflow",
  "overflow_x",
  "overflow_y",
  "flex_basis",
  "flex_shrink",
  "flex_grow",
  "grid_area",
  "grid_column",
  "grid_column_start",
  "grid_column_end",
  "grid_row",
  "grid_row_start",
  "grid_row_end",
  "m",
  "mx",
  "my",
  "mt",
  "mr",
  "mb",
  "ml"
], Sa = [
  "as",
  "as_child",
  "display",
  "align",
  "justify",
  "wrap",
  "gap",
  "gap_x",
  "gap_y"
].concat(et), ka = ["direction"].concat(Sa), Ra = [
  "as_child",
  "size",
  "display",
  "align",
  "ctn_size"
].concat(et), Oa = ["as", "as_child", "display"].concat(et), Na = [
  "as",
  "as_child",
  "display",
  "areas",
  "columns",
  "rows",
  "flow",
  "align",
  "justify",
  "gap",
  "gap_x",
  "gap_y"
].concat(et), Pa = "insta-Box", Va = Z(Ca, {
  props: Oa
});
function Ca(e) {
  const t = Me();
  return () => {
    var a;
    const n = Xe(e), { classes: r, style: s } = Ze(n), o = de(
      { class: r, style: s },
      { class: Pa }
    ), i = (a = t.default) == null ? void 0 : a.call(t);
    return e.as_child && i && i.length > 0 ? (Ye(i), se(i[0], o)) : G(e.as || "div", o, i);
  };
}
const Aa = "insta-Flex", xa = {
  gap: "2"
}, $a = Z(Ta, {
  props: ka
});
function Ta(e) {
  const t = Me();
  return () => {
    var a;
    const n = { ...xa, ...Xe(e) }, { classes: r, style: s } = Ze(n), o = de(
      { class: r, style: s },
      { class: Aa }
    ), i = (a = t.default) == null ? void 0 : a.call(t);
    return e.as_child && i && i.length > 0 ? (Ye(i), se(i[0], o)) : G(e.as || "div", o, i);
  };
}
const Ia = "insta-Grid", Da = {
  gap: "2"
}, Ma = Z(ja, {
  props: Na
});
function ja(e) {
  const t = Me();
  return () => {
    var c;
    const n = { ...Da, ...Xe(e) }, r = Ze(n), [s, o] = La(r.classes, r.style), i = de(
      { class: s, style: o },
      { class: Ia }
    ), a = (c = t.default) == null ? void 0 : c.call(t);
    return e.as_child && a && a.length > 0 ? (Ye(a), se(a[0], i)) : G(e.as || "div", i, a);
  };
}
function La(e, t) {
  const n = $e.get("areas").styleVar, r = $e.get("columns").styleVar, s = n in t, o = r in t;
  if (!s || o)
    return [e, t];
  const i = Ba(t[n]);
  if (i) {
    const { classes: a, styleVar: c } = $e.get("columns");
    e = `${e} ${a}`, t[c] = i;
  }
  return [e, t];
}
function Ba(e) {
  if (typeof e != "string") return null;
  const t = [...e.matchAll(/"([^"]+)"/g)].map((i) => i[1]);
  if (t.length === 0) return null;
  const s = t[0].trim().split(/\s+/).length;
  return t.every(
    (i) => i.trim().split(/\s+/).length === s
  ) ? `repeat(${s}, 1fr)` : null;
}
const Fa = "insta-Container", Wa = Z(Ua, {
  props: Ra
});
function Ua(e) {
  const t = Me();
  return () => {
    var h;
    const n = Xe(e), { classes: r, style: s, excludeReslut: o } = Ze(n, [
      "ctn_size"
    ]), i = de(
      { class: r, style: s },
      { class: Fa }
    ), a = (h = t.default) == null ? void 0 : h.call(t);
    if (e.as_child && a && a.length > 0)
      return Ye(a), se(a[0], i);
    const c = G(
      "div",
      de({ class: "insta-ContainerInner" }, o),
      a
    );
    return G("div", i, c);
  };
}
const Ha = "insta-Text", za = Z(Ka, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function Ka(e) {
  return () => {
    const { classes: t, style: n, props: r } = ar(e), s = de(
      { class: t, style: n, ...r },
      { class: Ha }
    );
    return G(e.as || "span", s, e.innerText);
  };
}
const dn = "insta-Link", Ga = Z(qa, {
  props: ["href", "text", "target", "type"]
});
function qa(e) {
  const t = Me().default;
  return () => {
    const n = t ? [dn, "has-child"] : [dn], r = {
      href: e.href,
      target: e.target,
      type: e.type,
      class: n
    };
    return G("a", r, t ? t() : e.text);
  };
}
function Ja(e, t) {
  const { mode: n = "hash" } = t.router, r = n === "hash" ? Xo() : n === "memory" ? Yo() : qn();
  e.use(
    Wi({
      history: r,
      routes: Qa(t)
    })
  );
}
function Qa(e) {
  if (!e.router)
    throw new Error("Router config is not provided.");
  const { routes: t = [], kAlive: n = !1 } = e.router;
  return t.map(
    (s) => cr(s, n)
  );
}
function cr(e, t) {
  const {
    server: n = !1,
    vueItem: r,
    scope: s,
    children: o
  } = e, i = () => {
    if (n)
      throw new Error("Server-side rendering is not supported yet.");
    return Promise.resolve(Ya(e, t));
  }, a = o == null ? void 0 : o.map(
    (h) => cr(h, t)
  ), c = {
    ...r,
    children: a,
    component: i
  };
  return s || delete c.component, a || delete c.children, c;
}
function Ya(e, t) {
  const { scope: n } = e;
  if (!n)
    throw new Error("Scope is not provided.");
  const r = se(Te(n), { key: n.id });
  return t ? G(Tr, null, () => r) : r;
}
function tc(e, t) {
  e.component("insta-ui", da), e.component("teleport", wa), e.component("icon", ba), e.component("heading", ya), e.component("box", Va), e.component("flex", $a), e.component("grid", Ma), e.component("container", Wa), e.component("ui-text", za), e.component("ui-link", Ga), t.router && Ja(e, t);
}
export {
  He as convertDynamicProperties,
  dt as getAppInfo,
  tc as install,
  ec as useBindingGetter,
  eo as useLanguage
};
