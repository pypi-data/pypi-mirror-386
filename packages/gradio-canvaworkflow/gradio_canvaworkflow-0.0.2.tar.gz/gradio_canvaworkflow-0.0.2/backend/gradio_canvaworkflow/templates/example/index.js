const {
  SvelteComponent: R,
  append_hydration: g,
  attr: f,
  children: p,
  claim_element: D,
  claim_space: B,
  claim_svg_element: F,
  claim_text: q,
  destroy_each: G,
  detach: v,
  element: I,
  empty: H,
  ensure_array_like: j,
  get_svelte_dataset: T,
  init: U,
  insert_hydration: V,
  noop: z,
  safe_not_equal: W,
  set_data: A,
  set_style: E,
  space: J,
  svg_element: K,
  text: N,
  toggle_class: w
} = window.__gradio__svelte__internal;
function L(o, e, l) {
  const t = o.slice();
  t[3] = e[l];
  const s = (
    /*value*/
    t[0].nodes[
      /*connection*/
      t[3].from
    ]
  );
  t[4] = s;
  const n = (
    /*value*/
    t[0].nodes[
      /*connection*/
      t[3].to
    ]
  );
  return t[5] = n, t;
}
function M(o, e, l) {
  const t = o.slice();
  return t[8] = e[l], t;
}
function X(o) {
  let e, l = "Empty workflow";
  return {
    c() {
      e = I("div"), e.textContent = l, this.h();
    },
    l(t) {
      e = D(t, "DIV", { class: !0, "data-svelte-h": !0 }), T(e) !== "svelte-1paau9h" && (e.textContent = l), this.h();
    },
    h() {
      f(e, "class", "empty-example svelte-1tmel5k");
    },
    m(t, s) {
      V(t, e, s);
    },
    p: z,
    d(t) {
      t && v(e);
    }
  };
}
function Y(o) {
  let e, l, t, s, n, c = (
    /*value*/
    o[0].nodes.length + ""
  ), h, u, C = (
    /*value*/
    (o[0].connections || []).length + ""
  ), S, x, b = j(
    /*value*/
    o[0].nodes
  ), _ = [];
  for (let a = 0; a < b.length; a += 1)
    _[a] = O(M(o, b, a));
  let y = j(
    /*value*/
    o[0].connections || []
  ), r = [];
  for (let a = 0; a < y.length; a += 1)
    r[a] = Q(L(o, y, a));
  return {
    c() {
      e = I("div"), l = I("div");
      for (let a = 0; a < _.length; a += 1)
        _[a].c();
      t = J();
      for (let a = 0; a < r.length; a += 1)
        r[a].c();
      s = J(), n = I("div"), h = N(c), u = N(" nodes, "), S = N(C), x = N(" connections"), this.h();
    },
    l(a) {
      e = D(a, "DIV", { class: !0 });
      var d = p(e);
      l = D(d, "DIV", { class: !0 });
      var i = p(l);
      for (let k = 0; k < _.length; k += 1)
        _[k].l(i);
      t = B(i);
      for (let k = 0; k < r.length; k += 1)
        r[k].l(i);
      i.forEach(v), s = B(d), n = D(d, "DIV", { class: !0 });
      var m = p(n);
      h = q(m, c), u = q(m, " nodes, "), S = q(m, C), x = q(m, " connections"), m.forEach(v), d.forEach(v), this.h();
    },
    h() {
      f(l, "class", "mini-canvas svelte-1tmel5k"), f(n, "class", "example-info svelte-1tmel5k"), f(e, "class", "example-preview svelte-1tmel5k");
    },
    m(a, d) {
      V(a, e, d), g(e, l);
      for (let i = 0; i < _.length; i += 1)
        _[i] && _[i].m(l, null);
      g(l, t);
      for (let i = 0; i < r.length; i += 1)
        r[i] && r[i].m(l, null);
      g(e, s), g(e, n), g(n, h), g(n, u), g(n, S), g(n, x);
    },
    p(a, d) {
      if (d & /*value*/
      1) {
        b = j(
          /*value*/
          a[0].nodes
        );
        let i;
        for (i = 0; i < b.length; i += 1) {
          const m = M(a, b, i);
          _[i] ? _[i].p(m, d) : (_[i] = O(m), _[i].c(), _[i].m(l, t));
        }
        for (; i < _.length; i += 1)
          _[i].d(1);
        _.length = b.length;
      }
      if (d & /*value*/
      1) {
        y = j(
          /*value*/
          a[0].connections || []
        );
        let i;
        for (i = 0; i < y.length; i += 1) {
          const m = L(a, y, i);
          r[i] ? r[i].p(m, d) : (r[i] = Q(m), r[i].c(), r[i].m(l, null));
        }
        for (; i < r.length; i += 1)
          r[i].d(1);
        r.length = y.length;
      }
      d & /*value*/
      1 && c !== (c = /*value*/
      a[0].nodes.length + "") && A(h, c), d & /*value*/
      1 && C !== (C = /*value*/
      (a[0].connections || []).length + "") && A(S, C);
    },
    d(a) {
      a && v(e), G(_, a), G(r, a);
    }
  };
}
function O(o) {
  let e, l = (
    /*node*/
    o[8].label + ""
  ), t;
  return {
    c() {
      e = I("div"), t = N(l), this.h();
    },
    l(s) {
      e = D(s, "DIV", { class: !0, style: !0 });
      var n = p(e);
      t = q(n, l), n.forEach(v), this.h();
    },
    h() {
      f(e, "class", "mini-node svelte-1tmel5k"), E(
        e,
        "left",
        /*node*/
        (o[8].x || 0) / 4 + "px"
      ), E(
        e,
        "top",
        /*node*/
        (o[8].y || 0) / 4 + "px"
      ), E(
        e,
        "background-color",
        /*node*/
        o[8].color || "#007acc"
      );
    },
    m(s, n) {
      V(s, e, n), g(e, t);
    },
    p(s, n) {
      n & /*value*/
      1 && l !== (l = /*node*/
      s[8].label + "") && A(t, l), n & /*value*/
      1 && E(
        e,
        "left",
        /*node*/
        (s[8].x || 0) / 4 + "px"
      ), n & /*value*/
      1 && E(
        e,
        "top",
        /*node*/
        (s[8].y || 0) / 4 + "px"
      ), n & /*value*/
      1 && E(
        e,
        "background-color",
        /*node*/
        s[8].color || "#007acc"
      );
    },
    d(s) {
      s && v(e);
    }
  };
}
function P(o) {
  let e, l, t, s, n, c;
  return {
    c() {
      e = K("svg"), l = K("line"), this.h();
    },
    l(h) {
      e = F(h, "svg", { class: !0 });
      var u = p(e);
      l = F(u, "line", {
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0,
        stroke: !0,
        "stroke-width": !0
      }), p(l).forEach(v), u.forEach(v), this.h();
    },
    h() {
      f(l, "x1", t = /*fromNode*/
      (o[4].x || 0) / 4 + 20), f(l, "y1", s = /*fromNode*/
      (o[4].y || 0) / 4 + 10), f(l, "x2", n = /*toNode*/
      (o[5].x || 0) / 4), f(l, "y2", c = /*toNode*/
      (o[5].y || 0) / 4 + 10), f(l, "stroke", "#007acc"), f(l, "stroke-width", "1"), f(e, "class", "mini-connection svelte-1tmel5k");
    },
    m(h, u) {
      V(h, e, u), g(e, l);
    },
    p(h, u) {
      u & /*value*/
      1 && t !== (t = /*fromNode*/
      (h[4].x || 0) / 4 + 20) && f(l, "x1", t), u & /*value*/
      1 && s !== (s = /*fromNode*/
      (h[4].y || 0) / 4 + 10) && f(l, "y1", s), u & /*value*/
      1 && n !== (n = /*toNode*/
      (h[5].x || 0) / 4) && f(l, "x2", n), u & /*value*/
      1 && c !== (c = /*toNode*/
      (h[5].y || 0) / 4 + 10) && f(l, "y2", c);
    },
    d(h) {
      h && v(e);
    }
  };
}
function Q(o) {
  let e, l = (
    /*fromNode*/
    o[4] && /*toNode*/
    o[5] && P(o)
  );
  return {
    c() {
      l && l.c(), e = H();
    },
    l(t) {
      l && l.l(t), e = H();
    },
    m(t, s) {
      l && l.m(t, s), V(t, e, s);
    },
    p(t, s) {
      /*fromNode*/
      t[4] && /*toNode*/
      t[5] ? l ? l.p(t, s) : (l = P(t), l.c(), l.m(e.parentNode, e)) : l && (l.d(1), l = null);
    },
    d(t) {
      t && v(e), l && l.d(t);
    }
  };
}
function Z(o) {
  let e;
  function l(n, c) {
    return (
      /*value*/
      n[0] && /*value*/
      n[0].nodes ? Y : X
    );
  }
  let t = l(o), s = t(o);
  return {
    c() {
      e = I("div"), s.c(), this.h();
    },
    l(n) {
      e = D(n, "DIV", { class: !0 });
      var c = p(e);
      s.l(c), c.forEach(v), this.h();
    },
    h() {
      f(e, "class", "example-container svelte-1tmel5k"), w(
        e,
        "selected",
        /*selected*/
        o[2]
      ), w(
        e,
        "table",
        /*type*/
        o[1] === "table"
      ), w(
        e,
        "gallery",
        /*type*/
        o[1] === "gallery"
      );
    },
    m(n, c) {
      V(n, e, c), s.m(e, null);
    },
    p(n, [c]) {
      t === (t = l(n)) && s ? s.p(n, c) : (s.d(1), s = t(n), s && (s.c(), s.m(e, null))), c & /*selected*/
      4 && w(
        e,
        "selected",
        /*selected*/
        n[2]
      ), c & /*type*/
      2 && w(
        e,
        "table",
        /*type*/
        n[1] === "table"
      ), c & /*type*/
      2 && w(
        e,
        "gallery",
        /*type*/
        n[1] === "gallery"
      );
    },
    i: z,
    o: z,
    d(n) {
      n && v(e), s.d();
    }
  };
}
function $(o, e, l) {
  let { value: t } = e, { type: s } = e, { selected: n = !1 } = e;
  return o.$$set = (c) => {
    "value" in c && l(0, t = c.value), "type" in c && l(1, s = c.type), "selected" in c && l(2, n = c.selected);
  }, [t, s, n];
}
class ee extends R {
  constructor(e) {
    super(), U(this, e, $, Z, W, { value: 0, type: 1, selected: 2 });
  }
}
export {
  ee as default
};
