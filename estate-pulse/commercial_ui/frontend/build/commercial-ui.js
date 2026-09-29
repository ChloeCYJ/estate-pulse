var Pi = { exports: {} }, gu = {};
/**
 * @license React
 * react-jsx-runtime.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var ao;
function By() {
  if (ao) return gu;
  ao = 1;
  var f = Symbol.for("react.transitional.element"), x = Symbol.for("react.fragment");
  function z(h, Y, F) {
    var V = null;
    if (F !== void 0 && (V = "" + F), Y.key !== void 0 && (V = "" + Y.key), "key" in Y) {
      F = {};
      for (var fl in Y)
        fl !== "key" && (F[fl] = Y[fl]);
    } else F = Y;
    return Y = F.ref, {
      $$typeof: f,
      type: h,
      key: V,
      ref: Y !== void 0 ? Y : null,
      props: F
    };
  }
  return gu.Fragment = x, gu.jsx = z, gu.jsxs = z, gu;
}
var eo;
function Cy() {
  return eo || (eo = 1, Pi.exports = By()), Pi.exports;
}
var r = Cy(), lf = { exports: {} }, bu = {}, tf = { exports: {} }, af = {};
/**
 * @license React
 * scheduler.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var uo;
function Gy() {
  return uo || (uo = 1, (function(f) {
    function x(S, j) {
      var C = S.length;
      S.push(j);
      l: for (; 0 < C; ) {
        var cl = C - 1 >>> 1, d = S[cl];
        if (0 < Y(d, j))
          S[cl] = j, S[C] = d, C = cl;
        else break l;
      }
    }
    function z(S) {
      return S.length === 0 ? null : S[0];
    }
    function h(S) {
      if (S.length === 0) return null;
      var j = S[0], C = S.pop();
      if (C !== j) {
        S[0] = C;
        l: for (var cl = 0, d = S.length, A = d >>> 1; cl < A; ) {
          var D = 2 * (cl + 1) - 1, O = S[D], q = D + 1, I = S[q];
          if (0 > Y(O, C))
            q < d && 0 > Y(I, O) ? (S[cl] = I, S[q] = C, cl = q) : (S[cl] = O, S[D] = C, cl = D);
          else if (q < d && 0 > Y(I, C))
            S[cl] = I, S[q] = C, cl = q;
          else break l;
        }
      }
      return j;
    }
    function Y(S, j) {
      var C = S.sortIndex - j.sortIndex;
      return C !== 0 ? C : S.id - j.id;
    }
    if (f.unstable_now = void 0, typeof performance == "object" && typeof performance.now == "function") {
      var F = performance;
      f.unstable_now = function() {
        return F.now();
      };
    } else {
      var V = Date, fl = V.now();
      f.unstable_now = function() {
        return V.now() - fl;
      };
    }
    var R = [], T = [], N = 1, w = null, $ = 3, rl = !1, Sl = !1, Kl = !1, vl = !1, ft = typeof setTimeout == "function" ? setTimeout : null, Fl = typeof clearTimeout == "function" ? clearTimeout : null, El = typeof setImmediate < "u" ? setImmediate : null;
    function Ql(S) {
      for (var j = z(T); j !== null; ) {
        if (j.callback === null) h(T);
        else if (j.startTime <= S)
          h(T), j.sortIndex = j.expirationTime, x(R, j);
        else break;
        j = z(T);
      }
    }
    function K(S) {
      if (Kl = !1, Ql(S), !Sl)
        if (z(R) !== null)
          Sl = !0, Zl || (Zl = !0, Yl());
        else {
          var j = z(T);
          j !== null && Bl(K, j.startTime - S);
        }
    }
    var Zl = !1, Vl = -1, Hl = 5, st = -1;
    function Rl() {
      return vl ? !0 : !(f.unstable_now() - st < Hl);
    }
    function hl() {
      if (vl = !1, Zl) {
        var S = f.unstable_now();
        st = S;
        var j = !0;
        try {
          l: {
            Sl = !1, Kl && (Kl = !1, Fl(Vl), Vl = -1), rl = !0;
            var C = $;
            try {
              t: {
                for (Ql(S), w = z(R); w !== null && !(w.expirationTime > S && Rl()); ) {
                  var cl = w.callback;
                  if (typeof cl == "function") {
                    w.callback = null, $ = w.priorityLevel;
                    var d = cl(
                      w.expirationTime <= S
                    );
                    if (S = f.unstable_now(), typeof d == "function") {
                      w.callback = d, Ql(S), j = !0;
                      break t;
                    }
                    w === z(R) && h(R), Ql(S);
                  } else h(R);
                  w = z(R);
                }
                if (w !== null) j = !0;
                else {
                  var A = z(T);
                  A !== null && Bl(
                    K,
                    A.startTime - S
                  ), j = !1;
                }
              }
              break l;
            } finally {
              w = null, $ = C, rl = !1;
            }
            j = void 0;
          }
        } finally {
          j ? Yl() : Zl = !1;
        }
      }
    }
    var Yl;
    if (typeof El == "function")
      Yl = function() {
        El(hl);
      };
    else if (typeof MessageChannel < "u") {
      var va = new MessageChannel(), ma = va.port2;
      va.port1.onmessage = hl, Yl = function() {
        ma.postMessage(null);
      };
    } else
      Yl = function() {
        ft(hl, 0);
      };
    function Bl(S, j) {
      Vl = ft(function() {
        S(f.unstable_now());
      }, j);
    }
    f.unstable_IdlePriority = 5, f.unstable_ImmediatePriority = 1, f.unstable_LowPriority = 4, f.unstable_NormalPriority = 3, f.unstable_Profiling = null, f.unstable_UserBlockingPriority = 2, f.unstable_cancelCallback = function(S) {
      S.callback = null;
    }, f.unstable_forceFrameRate = function(S) {
      0 > S || 125 < S ? console.error(
        "forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"
      ) : Hl = 0 < S ? Math.floor(1e3 / S) : 5;
    }, f.unstable_getCurrentPriorityLevel = function() {
      return $;
    }, f.unstable_next = function(S) {
      switch ($) {
        case 1:
        case 2:
        case 3:
          var j = 3;
          break;
        default:
          j = $;
      }
      var C = $;
      $ = j;
      try {
        return S();
      } finally {
        $ = C;
      }
    }, f.unstable_requestPaint = function() {
      vl = !0;
    }, f.unstable_runWithPriority = function(S, j) {
      switch (S) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          S = 3;
      }
      var C = $;
      $ = S;
      try {
        return j();
      } finally {
        $ = C;
      }
    }, f.unstable_scheduleCallback = function(S, j, C) {
      var cl = f.unstable_now();
      switch (typeof C == "object" && C !== null ? (C = C.delay, C = typeof C == "number" && 0 < C ? cl + C : cl) : C = cl, S) {
        case 1:
          var d = -1;
          break;
        case 2:
          d = 250;
          break;
        case 5:
          d = 1073741823;
          break;
        case 4:
          d = 1e4;
          break;
        default:
          d = 5e3;
      }
      return d = C + d, S = {
        id: N++,
        callback: j,
        priorityLevel: S,
        startTime: C,
        expirationTime: d,
        sortIndex: -1
      }, C > cl ? (S.sortIndex = C, x(T, S), z(R) === null && S === z(T) && (Kl ? (Fl(Vl), Vl = -1) : Kl = !0, Bl(K, C - cl))) : (S.sortIndex = d, x(R, S), Sl || rl || (Sl = !0, Zl || (Zl = !0, Yl()))), S;
    }, f.unstable_shouldYield = Rl, f.unstable_wrapCallback = function(S) {
      var j = $;
      return function() {
        var C = $;
        $ = j;
        try {
          return S.apply(this, arguments);
        } finally {
          $ = C;
        }
      };
    };
  })(af)), af;
}
var no;
function Xy() {
  return no || (no = 1, tf.exports = Gy()), tf.exports;
}
var ef = { exports: {} }, Q = {};
/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var co;
function Qy() {
  if (co) return Q;
  co = 1;
  var f = Symbol.for("react.transitional.element"), x = Symbol.for("react.portal"), z = Symbol.for("react.fragment"), h = Symbol.for("react.strict_mode"), Y = Symbol.for("react.profiler"), F = Symbol.for("react.consumer"), V = Symbol.for("react.context"), fl = Symbol.for("react.forward_ref"), R = Symbol.for("react.suspense"), T = Symbol.for("react.memo"), N = Symbol.for("react.lazy"), w = Symbol.iterator;
  function $(d) {
    return d === null || typeof d != "object" ? null : (d = w && d[w] || d["@@iterator"], typeof d == "function" ? d : null);
  }
  var rl = {
    isMounted: function() {
      return !1;
    },
    enqueueForceUpdate: function() {
    },
    enqueueReplaceState: function() {
    },
    enqueueSetState: function() {
    }
  }, Sl = Object.assign, Kl = {};
  function vl(d, A, D) {
    this.props = d, this.context = A, this.refs = Kl, this.updater = D || rl;
  }
  vl.prototype.isReactComponent = {}, vl.prototype.setState = function(d, A) {
    if (typeof d != "object" && typeof d != "function" && d != null)
      throw Error(
        "takes an object of state variables to update or a function which returns an object of state variables."
      );
    this.updater.enqueueSetState(this, d, A, "setState");
  }, vl.prototype.forceUpdate = function(d) {
    this.updater.enqueueForceUpdate(this, d, "forceUpdate");
  };
  function ft() {
  }
  ft.prototype = vl.prototype;
  function Fl(d, A, D) {
    this.props = d, this.context = A, this.refs = Kl, this.updater = D || rl;
  }
  var El = Fl.prototype = new ft();
  El.constructor = Fl, Sl(El, vl.prototype), El.isPureReactComponent = !0;
  var Ql = Array.isArray, K = { H: null, A: null, T: null, S: null, V: null }, Zl = Object.prototype.hasOwnProperty;
  function Vl(d, A, D, O, q, I) {
    return D = I.ref, {
      $$typeof: f,
      type: d,
      key: A,
      ref: D !== void 0 ? D : null,
      props: I
    };
  }
  function Hl(d, A) {
    return Vl(
      d.type,
      A,
      void 0,
      void 0,
      void 0,
      d.props
    );
  }
  function st(d) {
    return typeof d == "object" && d !== null && d.$$typeof === f;
  }
  function Rl(d) {
    var A = { "=": "=0", ":": "=2" };
    return "$" + d.replace(/[=:]/g, function(D) {
      return A[D];
    });
  }
  var hl = /\/+/g;
  function Yl(d, A) {
    return typeof d == "object" && d !== null && d.key != null ? Rl("" + d.key) : A.toString(36);
  }
  function va() {
  }
  function ma(d) {
    switch (d.status) {
      case "fulfilled":
        return d.value;
      case "rejected":
        throw d.reason;
      default:
        switch (typeof d.status == "string" ? d.then(va, va) : (d.status = "pending", d.then(
          function(A) {
            d.status === "pending" && (d.status = "fulfilled", d.value = A);
          },
          function(A) {
            d.status === "pending" && (d.status = "rejected", d.reason = A);
          }
        )), d.status) {
          case "fulfilled":
            return d.value;
          case "rejected":
            throw d.reason;
        }
    }
    throw d;
  }
  function Bl(d, A, D, O, q) {
    var I = typeof d;
    (I === "undefined" || I === "boolean") && (d = null);
    var X = !1;
    if (d === null) X = !0;
    else
      switch (I) {
        case "bigint":
        case "string":
        case "number":
          X = !0;
          break;
        case "object":
          switch (d.$$typeof) {
            case f:
            case x:
              X = !0;
              break;
            case N:
              return X = d._init, Bl(
                X(d._payload),
                A,
                D,
                O,
                q
              );
          }
      }
    if (X)
      return q = q(d), X = O === "" ? "." + Yl(d, 0) : O, Ql(q) ? (D = "", X != null && (D = X.replace(hl, "$&/") + "/"), Bl(q, A, D, "", function(Lt) {
        return Lt;
      })) : q != null && (st(q) && (q = Hl(
        q,
        D + (q.key == null || d && d.key === q.key ? "" : ("" + q.key).replace(
          hl,
          "$&/"
        ) + "/") + X
      )), A.push(q)), 1;
    X = 0;
    var Il = O === "" ? "." : O + ":";
    if (Ql(d))
      for (var dl = 0; dl < d.length; dl++)
        O = d[dl], I = Il + Yl(O, dl), X += Bl(
          O,
          A,
          D,
          I,
          q
        );
    else if (dl = $(d), typeof dl == "function")
      for (d = dl.call(d), dl = 0; !(O = d.next()).done; )
        O = O.value, I = Il + Yl(O, dl++), X += Bl(
          O,
          A,
          D,
          I,
          q
        );
    else if (I === "object") {
      if (typeof d.then == "function")
        return Bl(
          ma(d),
          A,
          D,
          O,
          q
        );
      throw A = String(d), Error(
        "Objects are not valid as a React child (found: " + (A === "[object Object]" ? "object with keys {" + Object.keys(d).join(", ") + "}" : A) + "). If you meant to render a collection of children, use an array instead."
      );
    }
    return X;
  }
  function S(d, A, D) {
    if (d == null) return d;
    var O = [], q = 0;
    return Bl(d, O, "", "", function(I) {
      return A.call(D, I, q++);
    }), O;
  }
  function j(d) {
    if (d._status === -1) {
      var A = d._result;
      A = A(), A.then(
        function(D) {
          (d._status === 0 || d._status === -1) && (d._status = 1, d._result = D);
        },
        function(D) {
          (d._status === 0 || d._status === -1) && (d._status = 2, d._result = D);
        }
      ), d._status === -1 && (d._status = 0, d._result = A);
    }
    if (d._status === 1) return d._result.default;
    throw d._result;
  }
  var C = typeof reportError == "function" ? reportError : function(d) {
    if (typeof window == "object" && typeof window.ErrorEvent == "function") {
      var A = new window.ErrorEvent("error", {
        bubbles: !0,
        cancelable: !0,
        message: typeof d == "object" && d !== null && typeof d.message == "string" ? String(d.message) : String(d),
        error: d
      });
      if (!window.dispatchEvent(A)) return;
    } else if (typeof process == "object" && typeof process.emit == "function") {
      process.emit("uncaughtException", d);
      return;
    }
    console.error(d);
  };
  function cl() {
  }
  return Q.Children = {
    map: S,
    forEach: function(d, A, D) {
      S(
        d,
        function() {
          A.apply(this, arguments);
        },
        D
      );
    },
    count: function(d) {
      var A = 0;
      return S(d, function() {
        A++;
      }), A;
    },
    toArray: function(d) {
      return S(d, function(A) {
        return A;
      }) || [];
    },
    only: function(d) {
      if (!st(d))
        throw Error(
          "React.Children.only expected to receive a single React element child."
        );
      return d;
    }
  }, Q.Component = vl, Q.Fragment = z, Q.Profiler = Y, Q.PureComponent = Fl, Q.StrictMode = h, Q.Suspense = R, Q.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = K, Q.__COMPILER_RUNTIME = {
    __proto__: null,
    c: function(d) {
      return K.H.useMemoCache(d);
    }
  }, Q.cache = function(d) {
    return function() {
      return d.apply(null, arguments);
    };
  }, Q.cloneElement = function(d, A, D) {
    if (d == null)
      throw Error(
        "The argument must be a React element, but you passed " + d + "."
      );
    var O = Sl({}, d.props), q = d.key, I = void 0;
    if (A != null)
      for (X in A.ref !== void 0 && (I = void 0), A.key !== void 0 && (q = "" + A.key), A)
        !Zl.call(A, X) || X === "key" || X === "__self" || X === "__source" || X === "ref" && A.ref === void 0 || (O[X] = A[X]);
    var X = arguments.length - 2;
    if (X === 1) O.children = D;
    else if (1 < X) {
      for (var Il = Array(X), dl = 0; dl < X; dl++)
        Il[dl] = arguments[dl + 2];
      O.children = Il;
    }
    return Vl(d.type, q, void 0, void 0, I, O);
  }, Q.createContext = function(d) {
    return d = {
      $$typeof: V,
      _currentValue: d,
      _currentValue2: d,
      _threadCount: 0,
      Provider: null,
      Consumer: null
    }, d.Provider = d, d.Consumer = {
      $$typeof: F,
      _context: d
    }, d;
  }, Q.createElement = function(d, A, D) {
    var O, q = {}, I = null;
    if (A != null)
      for (O in A.key !== void 0 && (I = "" + A.key), A)
        Zl.call(A, O) && O !== "key" && O !== "__self" && O !== "__source" && (q[O] = A[O]);
    var X = arguments.length - 2;
    if (X === 1) q.children = D;
    else if (1 < X) {
      for (var Il = Array(X), dl = 0; dl < X; dl++)
        Il[dl] = arguments[dl + 2];
      q.children = Il;
    }
    if (d && d.defaultProps)
      for (O in X = d.defaultProps, X)
        q[O] === void 0 && (q[O] = X[O]);
    return Vl(d, I, void 0, void 0, null, q);
  }, Q.createRef = function() {
    return { current: null };
  }, Q.forwardRef = function(d) {
    return { $$typeof: fl, render: d };
  }, Q.isValidElement = st, Q.lazy = function(d) {
    return {
      $$typeof: N,
      _payload: { _status: -1, _result: d },
      _init: j
    };
  }, Q.memo = function(d, A) {
    return {
      $$typeof: T,
      type: d,
      compare: A === void 0 ? null : A
    };
  }, Q.startTransition = function(d) {
    var A = K.T, D = {};
    K.T = D;
    try {
      var O = d(), q = K.S;
      q !== null && q(D, O), typeof O == "object" && O !== null && typeof O.then == "function" && O.then(cl, C);
    } catch (I) {
      C(I);
    } finally {
      K.T = A;
    }
  }, Q.unstable_useCacheRefresh = function() {
    return K.H.useCacheRefresh();
  }, Q.use = function(d) {
    return K.H.use(d);
  }, Q.useActionState = function(d, A, D) {
    return K.H.useActionState(d, A, D);
  }, Q.useCallback = function(d, A) {
    return K.H.useCallback(d, A);
  }, Q.useContext = function(d) {
    return K.H.useContext(d);
  }, Q.useDebugValue = function() {
  }, Q.useDeferredValue = function(d, A) {
    return K.H.useDeferredValue(d, A);
  }, Q.useEffect = function(d, A, D) {
    var O = K.H;
    if (typeof D == "function")
      throw Error(
        "useEffect CRUD overload is not enabled in this build of React."
      );
    return O.useEffect(d, A);
  }, Q.useId = function() {
    return K.H.useId();
  }, Q.useImperativeHandle = function(d, A, D) {
    return K.H.useImperativeHandle(d, A, D);
  }, Q.useInsertionEffect = function(d, A) {
    return K.H.useInsertionEffect(d, A);
  }, Q.useLayoutEffect = function(d, A) {
    return K.H.useLayoutEffect(d, A);
  }, Q.useMemo = function(d, A) {
    return K.H.useMemo(d, A);
  }, Q.useOptimistic = function(d, A) {
    return K.H.useOptimistic(d, A);
  }, Q.useReducer = function(d, A, D) {
    return K.H.useReducer(d, A, D);
  }, Q.useRef = function(d) {
    return K.H.useRef(d);
  }, Q.useState = function(d) {
    return K.H.useState(d);
  }, Q.useSyncExternalStore = function(d, A, D) {
    return K.H.useSyncExternalStore(
      d,
      A,
      D
    );
  }, Q.useTransition = function() {
    return K.H.useTransition();
  }, Q.version = "19.1.1", Q;
}
var io;
function cf() {
  return io || (io = 1, ef.exports = Qy()), ef.exports;
}
var uf = { exports: {} }, Xl = {};
/**
 * @license React
 * react-dom.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var fo;
function Zy() {
  if (fo) return Xl;
  fo = 1;
  var f = cf();
  function x(R) {
    var T = "https://react.dev/errors/" + R;
    if (1 < arguments.length) {
      T += "?args[]=" + encodeURIComponent(arguments[1]);
      for (var N = 2; N < arguments.length; N++)
        T += "&args[]=" + encodeURIComponent(arguments[N]);
    }
    return "Minified React error #" + R + "; visit " + T + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  function z() {
  }
  var h = {
    d: {
      f: z,
      r: function() {
        throw Error(x(522));
      },
      D: z,
      C: z,
      L: z,
      m: z,
      X: z,
      S: z,
      M: z
    },
    p: 0,
    findDOMNode: null
  }, Y = Symbol.for("react.portal");
  function F(R, T, N) {
    var w = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return {
      $$typeof: Y,
      key: w == null ? null : "" + w,
      children: R,
      containerInfo: T,
      implementation: N
    };
  }
  var V = f.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;
  function fl(R, T) {
    if (R === "font") return "";
    if (typeof T == "string")
      return T === "use-credentials" ? T : "";
  }
  return Xl.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = h, Xl.createPortal = function(R, T) {
    var N = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!T || T.nodeType !== 1 && T.nodeType !== 9 && T.nodeType !== 11)
      throw Error(x(299));
    return F(R, T, null, N);
  }, Xl.flushSync = function(R) {
    var T = V.T, N = h.p;
    try {
      if (V.T = null, h.p = 2, R) return R();
    } finally {
      V.T = T, h.p = N, h.d.f();
    }
  }, Xl.preconnect = function(R, T) {
    typeof R == "string" && (T ? (T = T.crossOrigin, T = typeof T == "string" ? T === "use-credentials" ? T : "" : void 0) : T = null, h.d.C(R, T));
  }, Xl.prefetchDNS = function(R) {
    typeof R == "string" && h.d.D(R);
  }, Xl.preinit = function(R, T) {
    if (typeof R == "string" && T && typeof T.as == "string") {
      var N = T.as, w = fl(N, T.crossOrigin), $ = typeof T.integrity == "string" ? T.integrity : void 0, rl = typeof T.fetchPriority == "string" ? T.fetchPriority : void 0;
      N === "style" ? h.d.S(
        R,
        typeof T.precedence == "string" ? T.precedence : void 0,
        {
          crossOrigin: w,
          integrity: $,
          fetchPriority: rl
        }
      ) : N === "script" && h.d.X(R, {
        crossOrigin: w,
        integrity: $,
        fetchPriority: rl,
        nonce: typeof T.nonce == "string" ? T.nonce : void 0
      });
    }
  }, Xl.preinitModule = function(R, T) {
    if (typeof R == "string")
      if (typeof T == "object" && T !== null) {
        if (T.as == null || T.as === "script") {
          var N = fl(
            T.as,
            T.crossOrigin
          );
          h.d.M(R, {
            crossOrigin: N,
            integrity: typeof T.integrity == "string" ? T.integrity : void 0,
            nonce: typeof T.nonce == "string" ? T.nonce : void 0
          });
        }
      } else T == null && h.d.M(R);
  }, Xl.preload = function(R, T) {
    if (typeof R == "string" && typeof T == "object" && T !== null && typeof T.as == "string") {
      var N = T.as, w = fl(N, T.crossOrigin);
      h.d.L(R, N, {
        crossOrigin: w,
        integrity: typeof T.integrity == "string" ? T.integrity : void 0,
        nonce: typeof T.nonce == "string" ? T.nonce : void 0,
        type: typeof T.type == "string" ? T.type : void 0,
        fetchPriority: typeof T.fetchPriority == "string" ? T.fetchPriority : void 0,
        referrerPolicy: typeof T.referrerPolicy == "string" ? T.referrerPolicy : void 0,
        imageSrcSet: typeof T.imageSrcSet == "string" ? T.imageSrcSet : void 0,
        imageSizes: typeof T.imageSizes == "string" ? T.imageSizes : void 0,
        media: typeof T.media == "string" ? T.media : void 0
      });
    }
  }, Xl.preloadModule = function(R, T) {
    if (typeof R == "string")
      if (T) {
        var N = fl(T.as, T.crossOrigin);
        h.d.m(R, {
          as: typeof T.as == "string" && T.as !== "script" ? T.as : void 0,
          crossOrigin: N,
          integrity: typeof T.integrity == "string" ? T.integrity : void 0
        });
      } else h.d.m(R);
  }, Xl.requestFormReset = function(R) {
    h.d.r(R);
  }, Xl.unstable_batchedUpdates = function(R, T) {
    return R(T);
  }, Xl.useFormState = function(R, T, N) {
    return V.H.useFormState(R, T, N);
  }, Xl.useFormStatus = function() {
    return V.H.useHostTransitionStatus();
  }, Xl.version = "19.1.1", Xl;
}
var so;
function Vy() {
  if (so) return uf.exports;
  so = 1;
  function f() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(f);
      } catch (x) {
        console.error(x);
      }
  }
  return f(), uf.exports = Zy(), uf.exports;
}
/**
 * @license React
 * react-dom-client.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var ro;
function Ly() {
  if (ro) return bu;
  ro = 1;
  var f = Xy(), x = cf(), z = Vy();
  function h(l) {
    var t = "https://react.dev/errors/" + l;
    if (1 < arguments.length) {
      t += "?args[]=" + encodeURIComponent(arguments[1]);
      for (var a = 2; a < arguments.length; a++)
        t += "&args[]=" + encodeURIComponent(arguments[a]);
    }
    return "Minified React error #" + l + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  function Y(l) {
    return !(!l || l.nodeType !== 1 && l.nodeType !== 9 && l.nodeType !== 11);
  }
  function F(l) {
    var t = l, a = l;
    if (l.alternate) for (; t.return; ) t = t.return;
    else {
      l = t;
      do
        t = l, (t.flags & 4098) !== 0 && (a = t.return), l = t.return;
      while (l);
    }
    return t.tag === 3 ? a : null;
  }
  function V(l) {
    if (l.tag === 13) {
      var t = l.memoizedState;
      if (t === null && (l = l.alternate, l !== null && (t = l.memoizedState)), t !== null) return t.dehydrated;
    }
    return null;
  }
  function fl(l) {
    if (F(l) !== l)
      throw Error(h(188));
  }
  function R(l) {
    var t = l.alternate;
    if (!t) {
      if (t = F(l), t === null) throw Error(h(188));
      return t !== l ? null : l;
    }
    for (var a = l, e = t; ; ) {
      var u = a.return;
      if (u === null) break;
      var n = u.alternate;
      if (n === null) {
        if (e = u.return, e !== null) {
          a = e;
          continue;
        }
        break;
      }
      if (u.child === n.child) {
        for (n = u.child; n; ) {
          if (n === a) return fl(u), l;
          if (n === e) return fl(u), t;
          n = n.sibling;
        }
        throw Error(h(188));
      }
      if (a.return !== e.return) a = u, e = n;
      else {
        for (var c = !1, i = u.child; i; ) {
          if (i === a) {
            c = !0, a = u, e = n;
            break;
          }
          if (i === e) {
            c = !0, e = u, a = n;
            break;
          }
          i = i.sibling;
        }
        if (!c) {
          for (i = n.child; i; ) {
            if (i === a) {
              c = !0, a = n, e = u;
              break;
            }
            if (i === e) {
              c = !0, e = n, a = u;
              break;
            }
            i = i.sibling;
          }
          if (!c) throw Error(h(189));
        }
      }
      if (a.alternate !== e) throw Error(h(190));
    }
    if (a.tag !== 3) throw Error(h(188));
    return a.stateNode.current === a ? l : t;
  }
  function T(l) {
    var t = l.tag;
    if (t === 5 || t === 26 || t === 27 || t === 6) return l;
    for (l = l.child; l !== null; ) {
      if (t = T(l), t !== null) return t;
      l = l.sibling;
    }
    return null;
  }
  var N = Object.assign, w = Symbol.for("react.element"), $ = Symbol.for("react.transitional.element"), rl = Symbol.for("react.portal"), Sl = Symbol.for("react.fragment"), Kl = Symbol.for("react.strict_mode"), vl = Symbol.for("react.profiler"), ft = Symbol.for("react.provider"), Fl = Symbol.for("react.consumer"), El = Symbol.for("react.context"), Ql = Symbol.for("react.forward_ref"), K = Symbol.for("react.suspense"), Zl = Symbol.for("react.suspense_list"), Vl = Symbol.for("react.memo"), Hl = Symbol.for("react.lazy"), st = Symbol.for("react.activity"), Rl = Symbol.for("react.memo_cache_sentinel"), hl = Symbol.iterator;
  function Yl(l) {
    return l === null || typeof l != "object" ? null : (l = hl && l[hl] || l["@@iterator"], typeof l == "function" ? l : null);
  }
  var va = Symbol.for("react.client.reference");
  function ma(l) {
    if (l == null) return null;
    if (typeof l == "function")
      return l.$$typeof === va ? null : l.displayName || l.name || null;
    if (typeof l == "string") return l;
    switch (l) {
      case Sl:
        return "Fragment";
      case vl:
        return "Profiler";
      case Kl:
        return "StrictMode";
      case K:
        return "Suspense";
      case Zl:
        return "SuspenseList";
      case st:
        return "Activity";
    }
    if (typeof l == "object")
      switch (l.$$typeof) {
        case rl:
          return "Portal";
        case El:
          return (l.displayName || "Context") + ".Provider";
        case Fl:
          return (l._context.displayName || "Context") + ".Consumer";
        case Ql:
          var t = l.render;
          return l = l.displayName, l || (l = t.displayName || t.name || "", l = l !== "" ? "ForwardRef(" + l + ")" : "ForwardRef"), l;
        case Vl:
          return t = l.displayName || null, t !== null ? t : ma(l.type) || "Memo";
        case Hl:
          t = l._payload, l = l._init;
          try {
            return ma(l(t));
          } catch {
          }
      }
    return null;
  }
  var Bl = Array.isArray, S = x.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, j = z.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, C = {
    pending: !1,
    data: null,
    method: null,
    action: null
  }, cl = [], d = -1;
  function A(l) {
    return { current: l };
  }
  function D(l) {
    0 > d || (l.current = cl[d], cl[d] = null, d--);
  }
  function O(l, t) {
    d++, cl[d] = l.current, l.current = t;
  }
  var q = A(null), I = A(null), X = A(null), Il = A(null);
  function dl(l, t) {
    switch (O(X, t), O(I, l), O(q, null), t.nodeType) {
      case 9:
      case 11:
        l = (l = t.documentElement) && (l = l.namespaceURI) ? Dd(l) : 0;
        break;
      default:
        if (l = t.tagName, t = t.namespaceURI)
          t = Dd(t), l = Rd(t, l);
        else
          switch (l) {
            case "svg":
              l = 1;
              break;
            case "math":
              l = 2;
              break;
            default:
              l = 0;
          }
    }
    D(q), O(q, l);
  }
  function Lt() {
    D(q), D(I), D(X);
  }
  function Cn(l) {
    l.memoizedState !== null && O(Il, l);
    var t = q.current, a = Rd(t, l.type);
    t !== a && (O(I, l), O(q, a));
  }
  function Su(l) {
    I.current === l && (D(q), D(I)), Il.current === l && (D(Il), ou._currentValue = C);
  }
  var Gn = Object.prototype.hasOwnProperty, Xn = f.unstable_scheduleCallback, Qn = f.unstable_cancelCallback, vo = f.unstable_shouldYield, mo = f.unstable_requestPaint, Tt = f.unstable_now, go = f.unstable_getCurrentPriorityLevel, rf = f.unstable_ImmediatePriority, df = f.unstable_UserBlockingPriority, pu = f.unstable_NormalPriority, bo = f.unstable_LowPriority, of = f.unstable_IdlePriority, _o = f.log, So = f.unstable_setDisableYieldValue, Se = null, Pl = null;
  function Kt(l) {
    if (typeof _o == "function" && So(l), Pl && typeof Pl.setStrictMode == "function")
      try {
        Pl.setStrictMode(Se, l);
      } catch {
      }
  }
  var lt = Math.clz32 ? Math.clz32 : Eo, po = Math.log, To = Math.LN2;
  function Eo(l) {
    return l >>>= 0, l === 0 ? 32 : 31 - (po(l) / To | 0) | 0;
  }
  var Tu = 256, Eu = 4194304;
  function ga(l) {
    var t = l & 42;
    if (t !== 0) return t;
    switch (l & -l) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
        return 64;
      case 128:
        return 128;
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return l & 4194048;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
        return l & 62914560;
      case 67108864:
        return 67108864;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 0;
      default:
        return l;
    }
  }
  function Au(l, t, a) {
    var e = l.pendingLanes;
    if (e === 0) return 0;
    var u = 0, n = l.suspendedLanes, c = l.pingedLanes;
    l = l.warmLanes;
    var i = e & 134217727;
    return i !== 0 ? (e = i & ~n, e !== 0 ? u = ga(e) : (c &= i, c !== 0 ? u = ga(c) : a || (a = i & ~l, a !== 0 && (u = ga(a))))) : (i = e & ~n, i !== 0 ? u = ga(i) : c !== 0 ? u = ga(c) : a || (a = e & ~l, a !== 0 && (u = ga(a)))), u === 0 ? 0 : t !== 0 && t !== u && (t & n) === 0 && (n = u & -u, a = t & -t, n >= a || n === 32 && (a & 4194048) !== 0) ? t : u;
  }
  function pe(l, t) {
    return (l.pendingLanes & ~(l.suspendedLanes & ~l.pingedLanes) & t) === 0;
  }
  function Ao(l, t) {
    switch (l) {
      case 1:
      case 2:
      case 4:
      case 8:
      case 64:
        return t + 250;
      case 16:
      case 32:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return t + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
        return -1;
      case 67108864:
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function hf() {
    var l = Tu;
    return Tu <<= 1, (Tu & 4194048) === 0 && (Tu = 256), l;
  }
  function yf() {
    var l = Eu;
    return Eu <<= 1, (Eu & 62914560) === 0 && (Eu = 4194304), l;
  }
  function Zn(l) {
    for (var t = [], a = 0; 31 > a; a++) t.push(l);
    return t;
  }
  function Te(l, t) {
    l.pendingLanes |= t, t !== 268435456 && (l.suspendedLanes = 0, l.pingedLanes = 0, l.warmLanes = 0);
  }
  function zo(l, t, a, e, u, n) {
    var c = l.pendingLanes;
    l.pendingLanes = a, l.suspendedLanes = 0, l.pingedLanes = 0, l.warmLanes = 0, l.expiredLanes &= a, l.entangledLanes &= a, l.errorRecoveryDisabledLanes &= a, l.shellSuspendCounter = 0;
    var i = l.entanglements, s = l.expirationTimes, m = l.hiddenUpdates;
    for (a = c & ~a; 0 < a; ) {
      var _ = 31 - lt(a), E = 1 << _;
      i[_] = 0, s[_] = -1;
      var g = m[_];
      if (g !== null)
        for (m[_] = null, _ = 0; _ < g.length; _++) {
          var b = g[_];
          b !== null && (b.lane &= -536870913);
        }
      a &= ~E;
    }
    e !== 0 && vf(l, e, 0), n !== 0 && u === 0 && l.tag !== 0 && (l.suspendedLanes |= n & ~(c & ~t));
  }
  function vf(l, t, a) {
    l.pendingLanes |= t, l.suspendedLanes &= ~t;
    var e = 31 - lt(t);
    l.entangledLanes |= t, l.entanglements[e] = l.entanglements[e] | 1073741824 | a & 4194090;
  }
  function mf(l, t) {
    var a = l.entangledLanes |= t;
    for (l = l.entanglements; a; ) {
      var e = 31 - lt(a), u = 1 << e;
      u & t | l[e] & t && (l[e] |= t), a &= ~u;
    }
  }
  function Vn(l) {
    switch (l) {
      case 2:
        l = 1;
        break;
      case 8:
        l = 4;
        break;
      case 32:
        l = 16;
        break;
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
        l = 128;
        break;
      case 268435456:
        l = 134217728;
        break;
      default:
        l = 0;
    }
    return l;
  }
  function Ln(l) {
    return l &= -l, 2 < l ? 8 < l ? (l & 134217727) !== 0 ? 32 : 268435456 : 8 : 2;
  }
  function gf() {
    var l = j.p;
    return l !== 0 ? l : (l = window.event, l === void 0 ? 32 : wd(l.type));
  }
  function xo(l, t) {
    var a = j.p;
    try {
      return j.p = l, t();
    } finally {
      j.p = a;
    }
  }
  var Jt = Math.random().toString(36).slice(2), Cl = "__reactFiber$" + Jt, Jl = "__reactProps$" + Jt, Ha = "__reactContainer$" + Jt, Kn = "__reactEvents$" + Jt, No = "__reactListeners$" + Jt, Oo = "__reactHandles$" + Jt, bf = "__reactResources$" + Jt, Ee = "__reactMarker$" + Jt;
  function Jn(l) {
    delete l[Cl], delete l[Jl], delete l[Kn], delete l[No], delete l[Oo];
  }
  function Ya(l) {
    var t = l[Cl];
    if (t) return t;
    for (var a = l.parentNode; a; ) {
      if (t = a[Ha] || a[Cl]) {
        if (a = t.alternate, t.child !== null || a !== null && a.child !== null)
          for (l = Hd(l); l !== null; ) {
            if (a = l[Cl]) return a;
            l = Hd(l);
          }
        return t;
      }
      l = a, a = l.parentNode;
    }
    return null;
  }
  function Ba(l) {
    if (l = l[Cl] || l[Ha]) {
      var t = l.tag;
      if (t === 5 || t === 6 || t === 13 || t === 26 || t === 27 || t === 3)
        return l;
    }
    return null;
  }
  function Ae(l) {
    var t = l.tag;
    if (t === 5 || t === 26 || t === 27 || t === 6) return l.stateNode;
    throw Error(h(33));
  }
  function Ca(l) {
    var t = l[bf];
    return t || (t = l[bf] = { hoistableStyles: /* @__PURE__ */ new Map(), hoistableScripts: /* @__PURE__ */ new Map() }), t;
  }
  function xl(l) {
    l[Ee] = !0;
  }
  var _f = /* @__PURE__ */ new Set(), Sf = {};
  function ba(l, t) {
    Ga(l, t), Ga(l + "Capture", t);
  }
  function Ga(l, t) {
    for (Sf[l] = t, l = 0; l < t.length; l++)
      _f.add(t[l]);
  }
  var jo = RegExp(
    "^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"
  ), pf = {}, Tf = {};
  function Do(l) {
    return Gn.call(Tf, l) ? !0 : Gn.call(pf, l) ? !1 : jo.test(l) ? Tf[l] = !0 : (pf[l] = !0, !1);
  }
  function zu(l, t, a) {
    if (Do(t))
      if (a === null) l.removeAttribute(t);
      else {
        switch (typeof a) {
          case "undefined":
          case "function":
          case "symbol":
            l.removeAttribute(t);
            return;
          case "boolean":
            var e = t.toLowerCase().slice(0, 5);
            if (e !== "data-" && e !== "aria-") {
              l.removeAttribute(t);
              return;
            }
        }
        l.setAttribute(t, "" + a);
      }
  }
  function xu(l, t, a) {
    if (a === null) l.removeAttribute(t);
    else {
      switch (typeof a) {
        case "undefined":
        case "function":
        case "symbol":
        case "boolean":
          l.removeAttribute(t);
          return;
      }
      l.setAttribute(t, "" + a);
    }
  }
  function Ot(l, t, a, e) {
    if (e === null) l.removeAttribute(a);
    else {
      switch (typeof e) {
        case "undefined":
        case "function":
        case "symbol":
        case "boolean":
          l.removeAttribute(a);
          return;
      }
      l.setAttributeNS(t, a, "" + e);
    }
  }
  var kn, Ef;
  function Xa(l) {
    if (kn === void 0)
      try {
        throw Error();
      } catch (a) {
        var t = a.stack.trim().match(/\n( *(at )?)/);
        kn = t && t[1] || "", Ef = -1 < a.stack.indexOf(`
    at`) ? " (<anonymous>)" : -1 < a.stack.indexOf("@") ? "@unknown:0:0" : "";
      }
    return `
` + kn + l + Ef;
  }
  var $n = !1;
  function Wn(l, t) {
    if (!l || $n) return "";
    $n = !0;
    var a = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      var e = {
        DetermineComponentFrameRoot: function() {
          try {
            if (t) {
              var E = function() {
                throw Error();
              };
              if (Object.defineProperty(E.prototype, "props", {
                set: function() {
                  throw Error();
                }
              }), typeof Reflect == "object" && Reflect.construct) {
                try {
                  Reflect.construct(E, []);
                } catch (b) {
                  var g = b;
                }
                Reflect.construct(l, [], E);
              } else {
                try {
                  E.call();
                } catch (b) {
                  g = b;
                }
                l.call(E.prototype);
              }
            } else {
              try {
                throw Error();
              } catch (b) {
                g = b;
              }
              (E = l()) && typeof E.catch == "function" && E.catch(function() {
              });
            }
          } catch (b) {
            if (b && g && typeof b.stack == "string")
              return [b.stack, g.stack];
          }
          return [null, null];
        }
      };
      e.DetermineComponentFrameRoot.displayName = "DetermineComponentFrameRoot";
      var u = Object.getOwnPropertyDescriptor(
        e.DetermineComponentFrameRoot,
        "name"
      );
      u && u.configurable && Object.defineProperty(
        e.DetermineComponentFrameRoot,
        "name",
        { value: "DetermineComponentFrameRoot" }
      );
      var n = e.DetermineComponentFrameRoot(), c = n[0], i = n[1];
      if (c && i) {
        var s = c.split(`
`), m = i.split(`
`);
        for (u = e = 0; e < s.length && !s[e].includes("DetermineComponentFrameRoot"); )
          e++;
        for (; u < m.length && !m[u].includes(
          "DetermineComponentFrameRoot"
        ); )
          u++;
        if (e === s.length || u === m.length)
          for (e = s.length - 1, u = m.length - 1; 1 <= e && 0 <= u && s[e] !== m[u]; )
            u--;
        for (; 1 <= e && 0 <= u; e--, u--)
          if (s[e] !== m[u]) {
            if (e !== 1 || u !== 1)
              do
                if (e--, u--, 0 > u || s[e] !== m[u]) {
                  var _ = `
` + s[e].replace(" at new ", " at ");
                  return l.displayName && _.includes("<anonymous>") && (_ = _.replace("<anonymous>", l.displayName)), _;
                }
              while (1 <= e && 0 <= u);
            break;
          }
      }
    } finally {
      $n = !1, Error.prepareStackTrace = a;
    }
    return (a = l ? l.displayName || l.name : "") ? Xa(a) : "";
  }
  function Ro(l) {
    switch (l.tag) {
      case 26:
      case 27:
      case 5:
        return Xa(l.type);
      case 16:
        return Xa("Lazy");
      case 13:
        return Xa("Suspense");
      case 19:
        return Xa("SuspenseList");
      case 0:
      case 15:
        return Wn(l.type, !1);
      case 11:
        return Wn(l.type.render, !1);
      case 1:
        return Wn(l.type, !0);
      case 31:
        return Xa("Activity");
      default:
        return "";
    }
  }
  function Af(l) {
    try {
      var t = "";
      do
        t += Ro(l), l = l.return;
      while (l);
      return t;
    } catch (a) {
      return `
Error generating stack: ` + a.message + `
` + a.stack;
    }
  }
  function rt(l) {
    switch (typeof l) {
      case "bigint":
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return l;
      case "object":
        return l;
      default:
        return "";
    }
  }
  function zf(l) {
    var t = l.type;
    return (l = l.nodeName) && l.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
  }
  function Uo(l) {
    var t = zf(l) ? "checked" : "value", a = Object.getOwnPropertyDescriptor(
      l.constructor.prototype,
      t
    ), e = "" + l[t];
    if (!l.hasOwnProperty(t) && typeof a < "u" && typeof a.get == "function" && typeof a.set == "function") {
      var u = a.get, n = a.set;
      return Object.defineProperty(l, t, {
        configurable: !0,
        get: function() {
          return u.call(this);
        },
        set: function(c) {
          e = "" + c, n.call(this, c);
        }
      }), Object.defineProperty(l, t, {
        enumerable: a.enumerable
      }), {
        getValue: function() {
          return e;
        },
        setValue: function(c) {
          e = "" + c;
        },
        stopTracking: function() {
          l._valueTracker = null, delete l[t];
        }
      };
    }
  }
  function Nu(l) {
    l._valueTracker || (l._valueTracker = Uo(l));
  }
  function xf(l) {
    if (!l) return !1;
    var t = l._valueTracker;
    if (!t) return !0;
    var a = t.getValue(), e = "";
    return l && (e = zf(l) ? l.checked ? "true" : "false" : l.value), l = e, l !== a ? (t.setValue(l), !0) : !1;
  }
  function Ou(l) {
    if (l = l || (typeof document < "u" ? document : void 0), typeof l > "u") return null;
    try {
      return l.activeElement || l.body;
    } catch {
      return l.body;
    }
  }
  var Mo = /[\n"\\]/g;
  function dt(l) {
    return l.replace(
      Mo,
      function(t) {
        return "\\" + t.charCodeAt(0).toString(16) + " ";
      }
    );
  }
  function wn(l, t, a, e, u, n, c, i) {
    l.name = "", c != null && typeof c != "function" && typeof c != "symbol" && typeof c != "boolean" ? l.type = c : l.removeAttribute("type"), t != null ? c === "number" ? (t === 0 && l.value === "" || l.value != t) && (l.value = "" + rt(t)) : l.value !== "" + rt(t) && (l.value = "" + rt(t)) : c !== "submit" && c !== "reset" || l.removeAttribute("value"), t != null ? Fn(l, c, rt(t)) : a != null ? Fn(l, c, rt(a)) : e != null && l.removeAttribute("value"), u == null && n != null && (l.defaultChecked = !!n), u != null && (l.checked = u && typeof u != "function" && typeof u != "symbol"), i != null && typeof i != "function" && typeof i != "symbol" && typeof i != "boolean" ? l.name = "" + rt(i) : l.removeAttribute("name");
  }
  function Nf(l, t, a, e, u, n, c, i) {
    if (n != null && typeof n != "function" && typeof n != "symbol" && typeof n != "boolean" && (l.type = n), t != null || a != null) {
      if (!(n !== "submit" && n !== "reset" || t != null))
        return;
      a = a != null ? "" + rt(a) : "", t = t != null ? "" + rt(t) : a, i || t === l.value || (l.value = t), l.defaultValue = t;
    }
    e = e ?? u, e = typeof e != "function" && typeof e != "symbol" && !!e, l.checked = i ? l.checked : !!e, l.defaultChecked = !!e, c != null && typeof c != "function" && typeof c != "symbol" && typeof c != "boolean" && (l.name = c);
  }
  function Fn(l, t, a) {
    t === "number" && Ou(l.ownerDocument) === l || l.defaultValue === "" + a || (l.defaultValue = "" + a);
  }
  function Qa(l, t, a, e) {
    if (l = l.options, t) {
      t = {};
      for (var u = 0; u < a.length; u++)
        t["$" + a[u]] = !0;
      for (a = 0; a < l.length; a++)
        u = t.hasOwnProperty("$" + l[a].value), l[a].selected !== u && (l[a].selected = u), u && e && (l[a].defaultSelected = !0);
    } else {
      for (a = "" + rt(a), t = null, u = 0; u < l.length; u++) {
        if (l[u].value === a) {
          l[u].selected = !0, e && (l[u].defaultSelected = !0);
          return;
        }
        t !== null || l[u].disabled || (t = l[u]);
      }
      t !== null && (t.selected = !0);
    }
  }
  function Of(l, t, a) {
    if (t != null && (t = "" + rt(t), t !== l.value && (l.value = t), a == null)) {
      l.defaultValue !== t && (l.defaultValue = t);
      return;
    }
    l.defaultValue = a != null ? "" + rt(a) : "";
  }
  function jf(l, t, a, e) {
    if (t == null) {
      if (e != null) {
        if (a != null) throw Error(h(92));
        if (Bl(e)) {
          if (1 < e.length) throw Error(h(93));
          e = e[0];
        }
        a = e;
      }
      a == null && (a = ""), t = a;
    }
    a = rt(t), l.defaultValue = a, e = l.textContent, e === a && e !== "" && e !== null && (l.value = e);
  }
  function Za(l, t) {
    if (t) {
      var a = l.firstChild;
      if (a && a === l.lastChild && a.nodeType === 3) {
        a.nodeValue = t;
        return;
      }
    }
    l.textContent = t;
  }
  var qo = new Set(
    "animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(
      " "
    )
  );
  function Df(l, t, a) {
    var e = t.indexOf("--") === 0;
    a == null || typeof a == "boolean" || a === "" ? e ? l.setProperty(t, "") : t === "float" ? l.cssFloat = "" : l[t] = "" : e ? l.setProperty(t, a) : typeof a != "number" || a === 0 || qo.has(t) ? t === "float" ? l.cssFloat = a : l[t] = ("" + a).trim() : l[t] = a + "px";
  }
  function Rf(l, t, a) {
    if (t != null && typeof t != "object")
      throw Error(h(62));
    if (l = l.style, a != null) {
      for (var e in a)
        !a.hasOwnProperty(e) || t != null && t.hasOwnProperty(e) || (e.indexOf("--") === 0 ? l.setProperty(e, "") : e === "float" ? l.cssFloat = "" : l[e] = "");
      for (var u in t)
        e = t[u], t.hasOwnProperty(u) && a[u] !== e && Df(l, u, e);
    } else
      for (var n in t)
        t.hasOwnProperty(n) && Df(l, n, t[n]);
  }
  function In(l) {
    if (l.indexOf("-") === -1) return !1;
    switch (l) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var Ho = /* @__PURE__ */ new Map([
    ["acceptCharset", "accept-charset"],
    ["htmlFor", "for"],
    ["httpEquiv", "http-equiv"],
    ["crossOrigin", "crossorigin"],
    ["accentHeight", "accent-height"],
    ["alignmentBaseline", "alignment-baseline"],
    ["arabicForm", "arabic-form"],
    ["baselineShift", "baseline-shift"],
    ["capHeight", "cap-height"],
    ["clipPath", "clip-path"],
    ["clipRule", "clip-rule"],
    ["colorInterpolation", "color-interpolation"],
    ["colorInterpolationFilters", "color-interpolation-filters"],
    ["colorProfile", "color-profile"],
    ["colorRendering", "color-rendering"],
    ["dominantBaseline", "dominant-baseline"],
    ["enableBackground", "enable-background"],
    ["fillOpacity", "fill-opacity"],
    ["fillRule", "fill-rule"],
    ["floodColor", "flood-color"],
    ["floodOpacity", "flood-opacity"],
    ["fontFamily", "font-family"],
    ["fontSize", "font-size"],
    ["fontSizeAdjust", "font-size-adjust"],
    ["fontStretch", "font-stretch"],
    ["fontStyle", "font-style"],
    ["fontVariant", "font-variant"],
    ["fontWeight", "font-weight"],
    ["glyphName", "glyph-name"],
    ["glyphOrientationHorizontal", "glyph-orientation-horizontal"],
    ["glyphOrientationVertical", "glyph-orientation-vertical"],
    ["horizAdvX", "horiz-adv-x"],
    ["horizOriginX", "horiz-origin-x"],
    ["imageRendering", "image-rendering"],
    ["letterSpacing", "letter-spacing"],
    ["lightingColor", "lighting-color"],
    ["markerEnd", "marker-end"],
    ["markerMid", "marker-mid"],
    ["markerStart", "marker-start"],
    ["overlinePosition", "overline-position"],
    ["overlineThickness", "overline-thickness"],
    ["paintOrder", "paint-order"],
    ["panose-1", "panose-1"],
    ["pointerEvents", "pointer-events"],
    ["renderingIntent", "rendering-intent"],
    ["shapeRendering", "shape-rendering"],
    ["stopColor", "stop-color"],
    ["stopOpacity", "stop-opacity"],
    ["strikethroughPosition", "strikethrough-position"],
    ["strikethroughThickness", "strikethrough-thickness"],
    ["strokeDasharray", "stroke-dasharray"],
    ["strokeDashoffset", "stroke-dashoffset"],
    ["strokeLinecap", "stroke-linecap"],
    ["strokeLinejoin", "stroke-linejoin"],
    ["strokeMiterlimit", "stroke-miterlimit"],
    ["strokeOpacity", "stroke-opacity"],
    ["strokeWidth", "stroke-width"],
    ["textAnchor", "text-anchor"],
    ["textDecoration", "text-decoration"],
    ["textRendering", "text-rendering"],
    ["transformOrigin", "transform-origin"],
    ["underlinePosition", "underline-position"],
    ["underlineThickness", "underline-thickness"],
    ["unicodeBidi", "unicode-bidi"],
    ["unicodeRange", "unicode-range"],
    ["unitsPerEm", "units-per-em"],
    ["vAlphabetic", "v-alphabetic"],
    ["vHanging", "v-hanging"],
    ["vIdeographic", "v-ideographic"],
    ["vMathematical", "v-mathematical"],
    ["vectorEffect", "vector-effect"],
    ["vertAdvY", "vert-adv-y"],
    ["vertOriginX", "vert-origin-x"],
    ["vertOriginY", "vert-origin-y"],
    ["wordSpacing", "word-spacing"],
    ["writingMode", "writing-mode"],
    ["xmlnsXlink", "xmlns:xlink"],
    ["xHeight", "x-height"]
  ]), Yo = /^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;
  function ju(l) {
    return Yo.test("" + l) ? "javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')" : l;
  }
  var Pn = null;
  function lc(l) {
    return l = l.target || l.srcElement || window, l.correspondingUseElement && (l = l.correspondingUseElement), l.nodeType === 3 ? l.parentNode : l;
  }
  var Va = null, La = null;
  function Uf(l) {
    var t = Ba(l);
    if (t && (l = t.stateNode)) {
      var a = l[Jl] || null;
      l: switch (l = t.stateNode, t.type) {
        case "input":
          if (wn(
            l,
            a.value,
            a.defaultValue,
            a.defaultValue,
            a.checked,
            a.defaultChecked,
            a.type,
            a.name
          ), t = a.name, a.type === "radio" && t != null) {
            for (a = l; a.parentNode; ) a = a.parentNode;
            for (a = a.querySelectorAll(
              'input[name="' + dt(
                "" + t
              ) + '"][type="radio"]'
            ), t = 0; t < a.length; t++) {
              var e = a[t];
              if (e !== l && e.form === l.form) {
                var u = e[Jl] || null;
                if (!u) throw Error(h(90));
                wn(
                  e,
                  u.value,
                  u.defaultValue,
                  u.defaultValue,
                  u.checked,
                  u.defaultChecked,
                  u.type,
                  u.name
                );
              }
            }
            for (t = 0; t < a.length; t++)
              e = a[t], e.form === l.form && xf(e);
          }
          break l;
        case "textarea":
          Of(l, a.value, a.defaultValue);
          break l;
        case "select":
          t = a.value, t != null && Qa(l, !!a.multiple, t, !1);
      }
    }
  }
  var tc = !1;
  function Mf(l, t, a) {
    if (tc) return l(t, a);
    tc = !0;
    try {
      var e = l(t);
      return e;
    } finally {
      if (tc = !1, (Va !== null || La !== null) && (vn(), Va && (t = Va, l = La, La = Va = null, Uf(t), l)))
        for (t = 0; t < l.length; t++) Uf(l[t]);
    }
  }
  function ze(l, t) {
    var a = l.stateNode;
    if (a === null) return null;
    var e = a[Jl] || null;
    if (e === null) return null;
    a = e[t];
    l: switch (t) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (e = !e.disabled) || (l = l.type, e = !(l === "button" || l === "input" || l === "select" || l === "textarea")), l = !e;
        break l;
      default:
        l = !1;
    }
    if (l) return null;
    if (a && typeof a != "function")
      throw Error(
        h(231, t, typeof a)
      );
    return a;
  }
  var jt = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), ac = !1;
  if (jt)
    try {
      var xe = {};
      Object.defineProperty(xe, "passive", {
        get: function() {
          ac = !0;
        }
      }), window.addEventListener("test", xe, xe), window.removeEventListener("test", xe, xe);
    } catch {
      ac = !1;
    }
  var kt = null, ec = null, Du = null;
  function qf() {
    if (Du) return Du;
    var l, t = ec, a = t.length, e, u = "value" in kt ? kt.value : kt.textContent, n = u.length;
    for (l = 0; l < a && t[l] === u[l]; l++) ;
    var c = a - l;
    for (e = 1; e <= c && t[a - e] === u[n - e]; e++) ;
    return Du = u.slice(l, 1 < e ? 1 - e : void 0);
  }
  function Ru(l) {
    var t = l.keyCode;
    return "charCode" in l ? (l = l.charCode, l === 0 && t === 13 && (l = 13)) : l = t, l === 10 && (l = 13), 32 <= l || l === 13 ? l : 0;
  }
  function Uu() {
    return !0;
  }
  function Hf() {
    return !1;
  }
  function kl(l) {
    function t(a, e, u, n, c) {
      this._reactName = a, this._targetInst = u, this.type = e, this.nativeEvent = n, this.target = c, this.currentTarget = null;
      for (var i in l)
        l.hasOwnProperty(i) && (a = l[i], this[i] = a ? a(n) : n[i]);
      return this.isDefaultPrevented = (n.defaultPrevented != null ? n.defaultPrevented : n.returnValue === !1) ? Uu : Hf, this.isPropagationStopped = Hf, this;
    }
    return N(t.prototype, {
      preventDefault: function() {
        this.defaultPrevented = !0;
        var a = this.nativeEvent;
        a && (a.preventDefault ? a.preventDefault() : typeof a.returnValue != "unknown" && (a.returnValue = !1), this.isDefaultPrevented = Uu);
      },
      stopPropagation: function() {
        var a = this.nativeEvent;
        a && (a.stopPropagation ? a.stopPropagation() : typeof a.cancelBubble != "unknown" && (a.cancelBubble = !0), this.isPropagationStopped = Uu);
      },
      persist: function() {
      },
      isPersistent: Uu
    }), t;
  }
  var _a = {
    eventPhase: 0,
    bubbles: 0,
    cancelable: 0,
    timeStamp: function(l) {
      return l.timeStamp || Date.now();
    },
    defaultPrevented: 0,
    isTrusted: 0
  }, Mu = kl(_a), Ne = N({}, _a, { view: 0, detail: 0 }), Bo = kl(Ne), uc, nc, Oe, qu = N({}, Ne, {
    screenX: 0,
    screenY: 0,
    clientX: 0,
    clientY: 0,
    pageX: 0,
    pageY: 0,
    ctrlKey: 0,
    shiftKey: 0,
    altKey: 0,
    metaKey: 0,
    getModifierState: ic,
    button: 0,
    buttons: 0,
    relatedTarget: function(l) {
      return l.relatedTarget === void 0 ? l.fromElement === l.srcElement ? l.toElement : l.fromElement : l.relatedTarget;
    },
    movementX: function(l) {
      return "movementX" in l ? l.movementX : (l !== Oe && (Oe && l.type === "mousemove" ? (uc = l.screenX - Oe.screenX, nc = l.screenY - Oe.screenY) : nc = uc = 0, Oe = l), uc);
    },
    movementY: function(l) {
      return "movementY" in l ? l.movementY : nc;
    }
  }), Yf = kl(qu), Co = N({}, qu, { dataTransfer: 0 }), Go = kl(Co), Xo = N({}, Ne, { relatedTarget: 0 }), cc = kl(Xo), Qo = N({}, _a, {
    animationName: 0,
    elapsedTime: 0,
    pseudoElement: 0
  }), Zo = kl(Qo), Vo = N({}, _a, {
    clipboardData: function(l) {
      return "clipboardData" in l ? l.clipboardData : window.clipboardData;
    }
  }), Lo = kl(Vo), Ko = N({}, _a, { data: 0 }), Bf = kl(Ko), Jo = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, ko = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, $o = {
    Alt: "altKey",
    Control: "ctrlKey",
    Meta: "metaKey",
    Shift: "shiftKey"
  };
  function Wo(l) {
    var t = this.nativeEvent;
    return t.getModifierState ? t.getModifierState(l) : (l = $o[l]) ? !!t[l] : !1;
  }
  function ic() {
    return Wo;
  }
  var wo = N({}, Ne, {
    key: function(l) {
      if (l.key) {
        var t = Jo[l.key] || l.key;
        if (t !== "Unidentified") return t;
      }
      return l.type === "keypress" ? (l = Ru(l), l === 13 ? "Enter" : String.fromCharCode(l)) : l.type === "keydown" || l.type === "keyup" ? ko[l.keyCode] || "Unidentified" : "";
    },
    code: 0,
    location: 0,
    ctrlKey: 0,
    shiftKey: 0,
    altKey: 0,
    metaKey: 0,
    repeat: 0,
    locale: 0,
    getModifierState: ic,
    charCode: function(l) {
      return l.type === "keypress" ? Ru(l) : 0;
    },
    keyCode: function(l) {
      return l.type === "keydown" || l.type === "keyup" ? l.keyCode : 0;
    },
    which: function(l) {
      return l.type === "keypress" ? Ru(l) : l.type === "keydown" || l.type === "keyup" ? l.keyCode : 0;
    }
  }), Fo = kl(wo), Io = N({}, qu, {
    pointerId: 0,
    width: 0,
    height: 0,
    pressure: 0,
    tangentialPressure: 0,
    tiltX: 0,
    tiltY: 0,
    twist: 0,
    pointerType: 0,
    isPrimary: 0
  }), Cf = kl(Io), Po = N({}, Ne, {
    touches: 0,
    targetTouches: 0,
    changedTouches: 0,
    altKey: 0,
    metaKey: 0,
    ctrlKey: 0,
    shiftKey: 0,
    getModifierState: ic
  }), lh = kl(Po), th = N({}, _a, {
    propertyName: 0,
    elapsedTime: 0,
    pseudoElement: 0
  }), ah = kl(th), eh = N({}, qu, {
    deltaX: function(l) {
      return "deltaX" in l ? l.deltaX : "wheelDeltaX" in l ? -l.wheelDeltaX : 0;
    },
    deltaY: function(l) {
      return "deltaY" in l ? l.deltaY : "wheelDeltaY" in l ? -l.wheelDeltaY : "wheelDelta" in l ? -l.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), uh = kl(eh), nh = N({}, _a, {
    newState: 0,
    oldState: 0
  }), ch = kl(nh), ih = [9, 13, 27, 32], fc = jt && "CompositionEvent" in window, je = null;
  jt && "documentMode" in document && (je = document.documentMode);
  var fh = jt && "TextEvent" in window && !je, Gf = jt && (!fc || je && 8 < je && 11 >= je), Xf = " ", Qf = !1;
  function Zf(l, t) {
    switch (l) {
      case "keyup":
        return ih.indexOf(t.keyCode) !== -1;
      case "keydown":
        return t.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function Vf(l) {
    return l = l.detail, typeof l == "object" && "data" in l ? l.data : null;
  }
  var Ka = !1;
  function sh(l, t) {
    switch (l) {
      case "compositionend":
        return Vf(t);
      case "keypress":
        return t.which !== 32 ? null : (Qf = !0, Xf);
      case "textInput":
        return l = t.data, l === Xf && Qf ? null : l;
      default:
        return null;
    }
  }
  function rh(l, t) {
    if (Ka)
      return l === "compositionend" || !fc && Zf(l, t) ? (l = qf(), Du = ec = kt = null, Ka = !1, l) : null;
    switch (l) {
      case "paste":
        return null;
      case "keypress":
        if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
          if (t.char && 1 < t.char.length)
            return t.char;
          if (t.which) return String.fromCharCode(t.which);
        }
        return null;
      case "compositionend":
        return Gf && t.locale !== "ko" ? null : t.data;
      default:
        return null;
    }
  }
  var dh = {
    color: !0,
    date: !0,
    datetime: !0,
    "datetime-local": !0,
    email: !0,
    month: !0,
    number: !0,
    password: !0,
    range: !0,
    search: !0,
    tel: !0,
    text: !0,
    time: !0,
    url: !0,
    week: !0
  };
  function Lf(l) {
    var t = l && l.nodeName && l.nodeName.toLowerCase();
    return t === "input" ? !!dh[l.type] : t === "textarea";
  }
  function Kf(l, t, a, e) {
    Va ? La ? La.push(e) : La = [e] : Va = e, t = pn(t, "onChange"), 0 < t.length && (a = new Mu(
      "onChange",
      "change",
      null,
      a,
      e
    ), l.push({ event: a, listeners: t }));
  }
  var De = null, Re = null;
  function oh(l) {
    zd(l, 0);
  }
  function Hu(l) {
    var t = Ae(l);
    if (xf(t)) return l;
  }
  function Jf(l, t) {
    if (l === "change") return t;
  }
  var kf = !1;
  if (jt) {
    var sc;
    if (jt) {
      var rc = "oninput" in document;
      if (!rc) {
        var $f = document.createElement("div");
        $f.setAttribute("oninput", "return;"), rc = typeof $f.oninput == "function";
      }
      sc = rc;
    } else sc = !1;
    kf = sc && (!document.documentMode || 9 < document.documentMode);
  }
  function Wf() {
    De && (De.detachEvent("onpropertychange", wf), Re = De = null);
  }
  function wf(l) {
    if (l.propertyName === "value" && Hu(Re)) {
      var t = [];
      Kf(
        t,
        Re,
        l,
        lc(l)
      ), Mf(oh, t);
    }
  }
  function hh(l, t, a) {
    l === "focusin" ? (Wf(), De = t, Re = a, De.attachEvent("onpropertychange", wf)) : l === "focusout" && Wf();
  }
  function yh(l) {
    if (l === "selectionchange" || l === "keyup" || l === "keydown")
      return Hu(Re);
  }
  function vh(l, t) {
    if (l === "click") return Hu(t);
  }
  function mh(l, t) {
    if (l === "input" || l === "change")
      return Hu(t);
  }
  function gh(l, t) {
    return l === t && (l !== 0 || 1 / l === 1 / t) || l !== l && t !== t;
  }
  var tt = typeof Object.is == "function" ? Object.is : gh;
  function Ue(l, t) {
    if (tt(l, t)) return !0;
    if (typeof l != "object" || l === null || typeof t != "object" || t === null)
      return !1;
    var a = Object.keys(l), e = Object.keys(t);
    if (a.length !== e.length) return !1;
    for (e = 0; e < a.length; e++) {
      var u = a[e];
      if (!Gn.call(t, u) || !tt(l[u], t[u]))
        return !1;
    }
    return !0;
  }
  function Ff(l) {
    for (; l && l.firstChild; ) l = l.firstChild;
    return l;
  }
  function If(l, t) {
    var a = Ff(l);
    l = 0;
    for (var e; a; ) {
      if (a.nodeType === 3) {
        if (e = l + a.textContent.length, l <= t && e >= t)
          return { node: a, offset: t - l };
        l = e;
      }
      l: {
        for (; a; ) {
          if (a.nextSibling) {
            a = a.nextSibling;
            break l;
          }
          a = a.parentNode;
        }
        a = void 0;
      }
      a = Ff(a);
    }
  }
  function Pf(l, t) {
    return l && t ? l === t ? !0 : l && l.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Pf(l, t.parentNode) : "contains" in l ? l.contains(t) : l.compareDocumentPosition ? !!(l.compareDocumentPosition(t) & 16) : !1 : !1;
  }
  function ls(l) {
    l = l != null && l.ownerDocument != null && l.ownerDocument.defaultView != null ? l.ownerDocument.defaultView : window;
    for (var t = Ou(l.document); t instanceof l.HTMLIFrameElement; ) {
      try {
        var a = typeof t.contentWindow.location.href == "string";
      } catch {
        a = !1;
      }
      if (a) l = t.contentWindow;
      else break;
      t = Ou(l.document);
    }
    return t;
  }
  function dc(l) {
    var t = l && l.nodeName && l.nodeName.toLowerCase();
    return t && (t === "input" && (l.type === "text" || l.type === "search" || l.type === "tel" || l.type === "url" || l.type === "password") || t === "textarea" || l.contentEditable === "true");
  }
  var bh = jt && "documentMode" in document && 11 >= document.documentMode, Ja = null, oc = null, Me = null, hc = !1;
  function ts(l, t, a) {
    var e = a.window === a ? a.document : a.nodeType === 9 ? a : a.ownerDocument;
    hc || Ja == null || Ja !== Ou(e) || (e = Ja, "selectionStart" in e && dc(e) ? e = { start: e.selectionStart, end: e.selectionEnd } : (e = (e.ownerDocument && e.ownerDocument.defaultView || window).getSelection(), e = {
      anchorNode: e.anchorNode,
      anchorOffset: e.anchorOffset,
      focusNode: e.focusNode,
      focusOffset: e.focusOffset
    }), Me && Ue(Me, e) || (Me = e, e = pn(oc, "onSelect"), 0 < e.length && (t = new Mu(
      "onSelect",
      "select",
      null,
      t,
      a
    ), l.push({ event: t, listeners: e }), t.target = Ja)));
  }
  function Sa(l, t) {
    var a = {};
    return a[l.toLowerCase()] = t.toLowerCase(), a["Webkit" + l] = "webkit" + t, a["Moz" + l] = "moz" + t, a;
  }
  var ka = {
    animationend: Sa("Animation", "AnimationEnd"),
    animationiteration: Sa("Animation", "AnimationIteration"),
    animationstart: Sa("Animation", "AnimationStart"),
    transitionrun: Sa("Transition", "TransitionRun"),
    transitionstart: Sa("Transition", "TransitionStart"),
    transitioncancel: Sa("Transition", "TransitionCancel"),
    transitionend: Sa("Transition", "TransitionEnd")
  }, yc = {}, as = {};
  jt && (as = document.createElement("div").style, "AnimationEvent" in window || (delete ka.animationend.animation, delete ka.animationiteration.animation, delete ka.animationstart.animation), "TransitionEvent" in window || delete ka.transitionend.transition);
  function pa(l) {
    if (yc[l]) return yc[l];
    if (!ka[l]) return l;
    var t = ka[l], a;
    for (a in t)
      if (t.hasOwnProperty(a) && a in as)
        return yc[l] = t[a];
    return l;
  }
  var es = pa("animationend"), us = pa("animationiteration"), ns = pa("animationstart"), _h = pa("transitionrun"), Sh = pa("transitionstart"), ph = pa("transitioncancel"), cs = pa("transitionend"), is = /* @__PURE__ */ new Map(), vc = "abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(
    " "
  );
  vc.push("scrollEnd");
  function _t(l, t) {
    is.set(l, t), ba(t, [l]);
  }
  var fs = /* @__PURE__ */ new WeakMap();
  function ot(l, t) {
    if (typeof l == "object" && l !== null) {
      var a = fs.get(l);
      return a !== void 0 ? a : (t = {
        value: l,
        source: t,
        stack: Af(t)
      }, fs.set(l, t), t);
    }
    return {
      value: l,
      source: t,
      stack: Af(t)
    };
  }
  var ht = [], $a = 0, mc = 0;
  function Yu() {
    for (var l = $a, t = mc = $a = 0; t < l; ) {
      var a = ht[t];
      ht[t++] = null;
      var e = ht[t];
      ht[t++] = null;
      var u = ht[t];
      ht[t++] = null;
      var n = ht[t];
      if (ht[t++] = null, e !== null && u !== null) {
        var c = e.pending;
        c === null ? u.next = u : (u.next = c.next, c.next = u), e.pending = u;
      }
      n !== 0 && ss(a, u, n);
    }
  }
  function Bu(l, t, a, e) {
    ht[$a++] = l, ht[$a++] = t, ht[$a++] = a, ht[$a++] = e, mc |= e, l.lanes |= e, l = l.alternate, l !== null && (l.lanes |= e);
  }
  function gc(l, t, a, e) {
    return Bu(l, t, a, e), Cu(l);
  }
  function Wa(l, t) {
    return Bu(l, null, null, t), Cu(l);
  }
  function ss(l, t, a) {
    l.lanes |= a;
    var e = l.alternate;
    e !== null && (e.lanes |= a);
    for (var u = !1, n = l.return; n !== null; )
      n.childLanes |= a, e = n.alternate, e !== null && (e.childLanes |= a), n.tag === 22 && (l = n.stateNode, l === null || l._visibility & 1 || (u = !0)), l = n, n = n.return;
    return l.tag === 3 ? (n = l.stateNode, u && t !== null && (u = 31 - lt(a), l = n.hiddenUpdates, e = l[u], e === null ? l[u] = [t] : e.push(t), t.lane = a | 536870912), n) : null;
  }
  function Cu(l) {
    if (50 < uu)
      throw uu = 0, Ei = null, Error(h(185));
    for (var t = l.return; t !== null; )
      l = t, t = l.return;
    return l.tag === 3 ? l.stateNode : null;
  }
  var wa = {};
  function Th(l, t, a, e) {
    this.tag = l, this.key = a, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.refCleanup = this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = e, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function at(l, t, a, e) {
    return new Th(l, t, a, e);
  }
  function bc(l) {
    return l = l.prototype, !(!l || !l.isReactComponent);
  }
  function Dt(l, t) {
    var a = l.alternate;
    return a === null ? (a = at(
      l.tag,
      t,
      l.key,
      l.mode
    ), a.elementType = l.elementType, a.type = l.type, a.stateNode = l.stateNode, a.alternate = l, l.alternate = a) : (a.pendingProps = t, a.type = l.type, a.flags = 0, a.subtreeFlags = 0, a.deletions = null), a.flags = l.flags & 65011712, a.childLanes = l.childLanes, a.lanes = l.lanes, a.child = l.child, a.memoizedProps = l.memoizedProps, a.memoizedState = l.memoizedState, a.updateQueue = l.updateQueue, t = l.dependencies, a.dependencies = t === null ? null : { lanes: t.lanes, firstContext: t.firstContext }, a.sibling = l.sibling, a.index = l.index, a.ref = l.ref, a.refCleanup = l.refCleanup, a;
  }
  function rs(l, t) {
    l.flags &= 65011714;
    var a = l.alternate;
    return a === null ? (l.childLanes = 0, l.lanes = t, l.child = null, l.subtreeFlags = 0, l.memoizedProps = null, l.memoizedState = null, l.updateQueue = null, l.dependencies = null, l.stateNode = null) : (l.childLanes = a.childLanes, l.lanes = a.lanes, l.child = a.child, l.subtreeFlags = 0, l.deletions = null, l.memoizedProps = a.memoizedProps, l.memoizedState = a.memoizedState, l.updateQueue = a.updateQueue, l.type = a.type, t = a.dependencies, l.dependencies = t === null ? null : {
      lanes: t.lanes,
      firstContext: t.firstContext
    }), l;
  }
  function Gu(l, t, a, e, u, n) {
    var c = 0;
    if (e = l, typeof l == "function") bc(l) && (c = 1);
    else if (typeof l == "string")
      c = Ay(
        l,
        a,
        q.current
      ) ? 26 : l === "html" || l === "head" || l === "body" ? 27 : 5;
    else
      l: switch (l) {
        case st:
          return l = at(31, a, t, u), l.elementType = st, l.lanes = n, l;
        case Sl:
          return Ta(a.children, u, n, t);
        case Kl:
          c = 8, u |= 24;
          break;
        case vl:
          return l = at(12, a, t, u | 2), l.elementType = vl, l.lanes = n, l;
        case K:
          return l = at(13, a, t, u), l.elementType = K, l.lanes = n, l;
        case Zl:
          return l = at(19, a, t, u), l.elementType = Zl, l.lanes = n, l;
        default:
          if (typeof l == "object" && l !== null)
            switch (l.$$typeof) {
              case ft:
              case El:
                c = 10;
                break l;
              case Fl:
                c = 9;
                break l;
              case Ql:
                c = 11;
                break l;
              case Vl:
                c = 14;
                break l;
              case Hl:
                c = 16, e = null;
                break l;
            }
          c = 29, a = Error(
            h(130, l === null ? "null" : typeof l, "")
          ), e = null;
      }
    return t = at(c, a, t, u), t.elementType = l, t.type = e, t.lanes = n, t;
  }
  function Ta(l, t, a, e) {
    return l = at(7, l, e, t), l.lanes = a, l;
  }
  function _c(l, t, a) {
    return l = at(6, l, null, t), l.lanes = a, l;
  }
  function Sc(l, t, a) {
    return t = at(
      4,
      l.children !== null ? l.children : [],
      l.key,
      t
    ), t.lanes = a, t.stateNode = {
      containerInfo: l.containerInfo,
      pendingChildren: null,
      implementation: l.implementation
    }, t;
  }
  var Fa = [], Ia = 0, Xu = null, Qu = 0, yt = [], vt = 0, Ea = null, Rt = 1, Ut = "";
  function Aa(l, t) {
    Fa[Ia++] = Qu, Fa[Ia++] = Xu, Xu = l, Qu = t;
  }
  function ds(l, t, a) {
    yt[vt++] = Rt, yt[vt++] = Ut, yt[vt++] = Ea, Ea = l;
    var e = Rt;
    l = Ut;
    var u = 32 - lt(e) - 1;
    e &= ~(1 << u), a += 1;
    var n = 32 - lt(t) + u;
    if (30 < n) {
      var c = u - u % 5;
      n = (e & (1 << c) - 1).toString(32), e >>= c, u -= c, Rt = 1 << 32 - lt(t) + u | a << u | e, Ut = n + l;
    } else
      Rt = 1 << n | a << u | e, Ut = l;
  }
  function pc(l) {
    l.return !== null && (Aa(l, 1), ds(l, 1, 0));
  }
  function Tc(l) {
    for (; l === Xu; )
      Xu = Fa[--Ia], Fa[Ia] = null, Qu = Fa[--Ia], Fa[Ia] = null;
    for (; l === Ea; )
      Ea = yt[--vt], yt[vt] = null, Ut = yt[--vt], yt[vt] = null, Rt = yt[--vt], yt[vt] = null;
  }
  var Ll = null, ml = null, ll = !1, za = null, Et = !1, Ec = Error(h(519));
  function xa(l) {
    var t = Error(h(418, ""));
    throw Ye(ot(t, l)), Ec;
  }
  function os(l) {
    var t = l.stateNode, a = l.type, e = l.memoizedProps;
    switch (t[Cl] = l, t[Jl] = e, a) {
      case "dialog":
        k("cancel", t), k("close", t);
        break;
      case "iframe":
      case "object":
      case "embed":
        k("load", t);
        break;
      case "video":
      case "audio":
        for (a = 0; a < cu.length; a++)
          k(cu[a], t);
        break;
      case "source":
        k("error", t);
        break;
      case "img":
      case "image":
      case "link":
        k("error", t), k("load", t);
        break;
      case "details":
        k("toggle", t);
        break;
      case "input":
        k("invalid", t), Nf(
          t,
          e.value,
          e.defaultValue,
          e.checked,
          e.defaultChecked,
          e.type,
          e.name,
          !0
        ), Nu(t);
        break;
      case "select":
        k("invalid", t);
        break;
      case "textarea":
        k("invalid", t), jf(t, e.value, e.defaultValue, e.children), Nu(t);
    }
    a = e.children, typeof a != "string" && typeof a != "number" && typeof a != "bigint" || t.textContent === "" + a || e.suppressHydrationWarning === !0 || jd(t.textContent, a) ? (e.popover != null && (k("beforetoggle", t), k("toggle", t)), e.onScroll != null && k("scroll", t), e.onScrollEnd != null && k("scrollend", t), e.onClick != null && (t.onclick = Tn), t = !0) : t = !1, t || xa(l);
  }
  function hs(l) {
    for (Ll = l.return; Ll; )
      switch (Ll.tag) {
        case 5:
        case 13:
          Et = !1;
          return;
        case 27:
        case 3:
          Et = !0;
          return;
        default:
          Ll = Ll.return;
      }
  }
  function qe(l) {
    if (l !== Ll) return !1;
    if (!ll) return hs(l), ll = !0, !1;
    var t = l.tag, a;
    if ((a = t !== 3 && t !== 27) && ((a = t === 5) && (a = l.type, a = !(a !== "form" && a !== "button") || Gi(l.type, l.memoizedProps)), a = !a), a && ml && xa(l), hs(l), t === 13) {
      if (l = l.memoizedState, l = l !== null ? l.dehydrated : null, !l) throw Error(h(317));
      l: {
        for (l = l.nextSibling, t = 0; l; ) {
          if (l.nodeType === 8)
            if (a = l.data, a === "/$") {
              if (t === 0) {
                ml = pt(l.nextSibling);
                break l;
              }
              t--;
            } else
              a !== "$" && a !== "$!" && a !== "$?" || t++;
          l = l.nextSibling;
        }
        ml = null;
      }
    } else
      t === 27 ? (t = ml, sa(l.type) ? (l = Vi, Vi = null, ml = l) : ml = t) : ml = Ll ? pt(l.stateNode.nextSibling) : null;
    return !0;
  }
  function He() {
    ml = Ll = null, ll = !1;
  }
  function ys() {
    var l = za;
    return l !== null && (wl === null ? wl = l : wl.push.apply(
      wl,
      l
    ), za = null), l;
  }
  function Ye(l) {
    za === null ? za = [l] : za.push(l);
  }
  var Ac = A(null), Na = null, Mt = null;
  function $t(l, t, a) {
    O(Ac, t._currentValue), t._currentValue = a;
  }
  function qt(l) {
    l._currentValue = Ac.current, D(Ac);
  }
  function zc(l, t, a) {
    for (; l !== null; ) {
      var e = l.alternate;
      if ((l.childLanes & t) !== t ? (l.childLanes |= t, e !== null && (e.childLanes |= t)) : e !== null && (e.childLanes & t) !== t && (e.childLanes |= t), l === a) break;
      l = l.return;
    }
  }
  function xc(l, t, a, e) {
    var u = l.child;
    for (u !== null && (u.return = l); u !== null; ) {
      var n = u.dependencies;
      if (n !== null) {
        var c = u.child;
        n = n.firstContext;
        l: for (; n !== null; ) {
          var i = n;
          n = u;
          for (var s = 0; s < t.length; s++)
            if (i.context === t[s]) {
              n.lanes |= a, i = n.alternate, i !== null && (i.lanes |= a), zc(
                n.return,
                a,
                l
              ), e || (c = null);
              break l;
            }
          n = i.next;
        }
      } else if (u.tag === 18) {
        if (c = u.return, c === null) throw Error(h(341));
        c.lanes |= a, n = c.alternate, n !== null && (n.lanes |= a), zc(c, a, l), c = null;
      } else c = u.child;
      if (c !== null) c.return = u;
      else
        for (c = u; c !== null; ) {
          if (c === l) {
            c = null;
            break;
          }
          if (u = c.sibling, u !== null) {
            u.return = c.return, c = u;
            break;
          }
          c = c.return;
        }
      u = c;
    }
  }
  function Be(l, t, a, e) {
    l = null;
    for (var u = t, n = !1; u !== null; ) {
      if (!n) {
        if ((u.flags & 524288) !== 0) n = !0;
        else if ((u.flags & 262144) !== 0) break;
      }
      if (u.tag === 10) {
        var c = u.alternate;
        if (c === null) throw Error(h(387));
        if (c = c.memoizedProps, c !== null) {
          var i = u.type;
          tt(u.pendingProps.value, c.value) || (l !== null ? l.push(i) : l = [i]);
        }
      } else if (u === Il.current) {
        if (c = u.alternate, c === null) throw Error(h(387));
        c.memoizedState.memoizedState !== u.memoizedState.memoizedState && (l !== null ? l.push(ou) : l = [ou]);
      }
      u = u.return;
    }
    l !== null && xc(
      t,
      l,
      a,
      e
    ), t.flags |= 262144;
  }
  function Zu(l) {
    for (l = l.firstContext; l !== null; ) {
      if (!tt(
        l.context._currentValue,
        l.memoizedValue
      ))
        return !0;
      l = l.next;
    }
    return !1;
  }
  function Oa(l) {
    Na = l, Mt = null, l = l.dependencies, l !== null && (l.firstContext = null);
  }
  function Gl(l) {
    return vs(Na, l);
  }
  function Vu(l, t) {
    return Na === null && Oa(l), vs(l, t);
  }
  function vs(l, t) {
    var a = t._currentValue;
    if (t = { context: t, memoizedValue: a, next: null }, Mt === null) {
      if (l === null) throw Error(h(308));
      Mt = t, l.dependencies = { lanes: 0, firstContext: t }, l.flags |= 524288;
    } else Mt = Mt.next = t;
    return a;
  }
  var Eh = typeof AbortController < "u" ? AbortController : function() {
    var l = [], t = this.signal = {
      aborted: !1,
      addEventListener: function(a, e) {
        l.push(e);
      }
    };
    this.abort = function() {
      t.aborted = !0, l.forEach(function(a) {
        return a();
      });
    };
  }, Ah = f.unstable_scheduleCallback, zh = f.unstable_NormalPriority, Al = {
    $$typeof: El,
    Consumer: null,
    Provider: null,
    _currentValue: null,
    _currentValue2: null,
    _threadCount: 0
  };
  function Nc() {
    return {
      controller: new Eh(),
      data: /* @__PURE__ */ new Map(),
      refCount: 0
    };
  }
  function Ce(l) {
    l.refCount--, l.refCount === 0 && Ah(zh, function() {
      l.controller.abort();
    });
  }
  var Ge = null, Oc = 0, Pa = 0, le = null;
  function xh(l, t) {
    if (Ge === null) {
      var a = Ge = [];
      Oc = 0, Pa = Di(), le = {
        status: "pending",
        value: void 0,
        then: function(e) {
          a.push(e);
        }
      };
    }
    return Oc++, t.then(ms, ms), t;
  }
  function ms() {
    if (--Oc === 0 && Ge !== null) {
      le !== null && (le.status = "fulfilled");
      var l = Ge;
      Ge = null, Pa = 0, le = null;
      for (var t = 0; t < l.length; t++) (0, l[t])();
    }
  }
  function Nh(l, t) {
    var a = [], e = {
      status: "pending",
      value: null,
      reason: null,
      then: function(u) {
        a.push(u);
      }
    };
    return l.then(
      function() {
        e.status = "fulfilled", e.value = t;
        for (var u = 0; u < a.length; u++) (0, a[u])(t);
      },
      function(u) {
        for (e.status = "rejected", e.reason = u, u = 0; u < a.length; u++)
          (0, a[u])(void 0);
      }
    ), e;
  }
  var gs = S.S;
  S.S = function(l, t) {
    typeof t == "object" && t !== null && typeof t.then == "function" && xh(l, t), gs !== null && gs(l, t);
  };
  var ja = A(null);
  function jc() {
    var l = ja.current;
    return l !== null ? l : sl.pooledCache;
  }
  function Lu(l, t) {
    t === null ? O(ja, ja.current) : O(ja, t.pool);
  }
  function bs() {
    var l = jc();
    return l === null ? null : { parent: Al._currentValue, pool: l };
  }
  var Xe = Error(h(460)), _s = Error(h(474)), Ku = Error(h(542)), Dc = { then: function() {
  } };
  function Ss(l) {
    return l = l.status, l === "fulfilled" || l === "rejected";
  }
  function Ju() {
  }
  function ps(l, t, a) {
    switch (a = l[a], a === void 0 ? l.push(t) : a !== t && (t.then(Ju, Ju), t = a), t.status) {
      case "fulfilled":
        return t.value;
      case "rejected":
        throw l = t.reason, Es(l), l;
      default:
        if (typeof t.status == "string") t.then(Ju, Ju);
        else {
          if (l = sl, l !== null && 100 < l.shellSuspendCounter)
            throw Error(h(482));
          l = t, l.status = "pending", l.then(
            function(e) {
              if (t.status === "pending") {
                var u = t;
                u.status = "fulfilled", u.value = e;
              }
            },
            function(e) {
              if (t.status === "pending") {
                var u = t;
                u.status = "rejected", u.reason = e;
              }
            }
          );
        }
        switch (t.status) {
          case "fulfilled":
            return t.value;
          case "rejected":
            throw l = t.reason, Es(l), l;
        }
        throw Qe = t, Xe;
    }
  }
  var Qe = null;
  function Ts() {
    if (Qe === null) throw Error(h(459));
    var l = Qe;
    return Qe = null, l;
  }
  function Es(l) {
    if (l === Xe || l === Ku)
      throw Error(h(483));
  }
  var Wt = !1;
  function Rc(l) {
    l.updateQueue = {
      baseState: l.memoizedState,
      firstBaseUpdate: null,
      lastBaseUpdate: null,
      shared: { pending: null, lanes: 0, hiddenCallbacks: null },
      callbacks: null
    };
  }
  function Uc(l, t) {
    l = l.updateQueue, t.updateQueue === l && (t.updateQueue = {
      baseState: l.baseState,
      firstBaseUpdate: l.firstBaseUpdate,
      lastBaseUpdate: l.lastBaseUpdate,
      shared: l.shared,
      callbacks: null
    });
  }
  function wt(l) {
    return { lane: l, tag: 0, payload: null, callback: null, next: null };
  }
  function Ft(l, t, a) {
    var e = l.updateQueue;
    if (e === null) return null;
    if (e = e.shared, (tl & 2) !== 0) {
      var u = e.pending;
      return u === null ? t.next = t : (t.next = u.next, u.next = t), e.pending = t, t = Cu(l), ss(l, null, a), t;
    }
    return Bu(l, e, t, a), Cu(l);
  }
  function Ze(l, t, a) {
    if (t = t.updateQueue, t !== null && (t = t.shared, (a & 4194048) !== 0)) {
      var e = t.lanes;
      e &= l.pendingLanes, a |= e, t.lanes = a, mf(l, a);
    }
  }
  function Mc(l, t) {
    var a = l.updateQueue, e = l.alternate;
    if (e !== null && (e = e.updateQueue, a === e)) {
      var u = null, n = null;
      if (a = a.firstBaseUpdate, a !== null) {
        do {
          var c = {
            lane: a.lane,
            tag: a.tag,
            payload: a.payload,
            callback: null,
            next: null
          };
          n === null ? u = n = c : n = n.next = c, a = a.next;
        } while (a !== null);
        n === null ? u = n = t : n = n.next = t;
      } else u = n = t;
      a = {
        baseState: e.baseState,
        firstBaseUpdate: u,
        lastBaseUpdate: n,
        shared: e.shared,
        callbacks: e.callbacks
      }, l.updateQueue = a;
      return;
    }
    l = a.lastBaseUpdate, l === null ? a.firstBaseUpdate = t : l.next = t, a.lastBaseUpdate = t;
  }
  var qc = !1;
  function Ve() {
    if (qc) {
      var l = le;
      if (l !== null) throw l;
    }
  }
  function Le(l, t, a, e) {
    qc = !1;
    var u = l.updateQueue;
    Wt = !1;
    var n = u.firstBaseUpdate, c = u.lastBaseUpdate, i = u.shared.pending;
    if (i !== null) {
      u.shared.pending = null;
      var s = i, m = s.next;
      s.next = null, c === null ? n = m : c.next = m, c = s;
      var _ = l.alternate;
      _ !== null && (_ = _.updateQueue, i = _.lastBaseUpdate, i !== c && (i === null ? _.firstBaseUpdate = m : i.next = m, _.lastBaseUpdate = s));
    }
    if (n !== null) {
      var E = u.baseState;
      c = 0, _ = m = s = null, i = n;
      do {
        var g = i.lane & -536870913, b = g !== i.lane;
        if (b ? (W & g) === g : (e & g) === g) {
          g !== 0 && g === Pa && (qc = !0), _ !== null && (_ = _.next = {
            lane: 0,
            tag: i.tag,
            payload: i.payload,
            callback: null,
            next: null
          });
          l: {
            var G = l, H = i;
            g = t;
            var nl = a;
            switch (H.tag) {
              case 1:
                if (G = H.payload, typeof G == "function") {
                  E = G.call(nl, E, g);
                  break l;
                }
                E = G;
                break l;
              case 3:
                G.flags = G.flags & -65537 | 128;
              case 0:
                if (G = H.payload, g = typeof G == "function" ? G.call(nl, E, g) : G, g == null) break l;
                E = N({}, E, g);
                break l;
              case 2:
                Wt = !0;
            }
          }
          g = i.callback, g !== null && (l.flags |= 64, b && (l.flags |= 8192), b = u.callbacks, b === null ? u.callbacks = [g] : b.push(g));
        } else
          b = {
            lane: g,
            tag: i.tag,
            payload: i.payload,
            callback: i.callback,
            next: null
          }, _ === null ? (m = _ = b, s = E) : _ = _.next = b, c |= g;
        if (i = i.next, i === null) {
          if (i = u.shared.pending, i === null)
            break;
          b = i, i = b.next, b.next = null, u.lastBaseUpdate = b, u.shared.pending = null;
        }
      } while (!0);
      _ === null && (s = E), u.baseState = s, u.firstBaseUpdate = m, u.lastBaseUpdate = _, n === null && (u.shared.lanes = 0), na |= c, l.lanes = c, l.memoizedState = E;
    }
  }
  function As(l, t) {
    if (typeof l != "function")
      throw Error(h(191, l));
    l.call(t);
  }
  function zs(l, t) {
    var a = l.callbacks;
    if (a !== null)
      for (l.callbacks = null, l = 0; l < a.length; l++)
        As(a[l], t);
  }
  var te = A(null), ku = A(0);
  function xs(l, t) {
    l = Qt, O(ku, l), O(te, t), Qt = l | t.baseLanes;
  }
  function Hc() {
    O(ku, Qt), O(te, te.current);
  }
  function Yc() {
    Qt = ku.current, D(te), D(ku);
  }
  var It = 0, Z = null, el = null, pl = null, $u = !1, ae = !1, Da = !1, Wu = 0, Ke = 0, ee = null, Oh = 0;
  function bl() {
    throw Error(h(321));
  }
  function Bc(l, t) {
    if (t === null) return !1;
    for (var a = 0; a < t.length && a < l.length; a++)
      if (!tt(l[a], t[a])) return !1;
    return !0;
  }
  function Cc(l, t, a, e, u, n) {
    return It = n, Z = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, S.H = l === null || l.memoizedState === null ? sr : rr, Da = !1, n = a(e, u), Da = !1, ae && (n = Os(
      t,
      a,
      e,
      u
    )), Ns(l), n;
  }
  function Ns(l) {
    S.H = tn;
    var t = el !== null && el.next !== null;
    if (It = 0, pl = el = Z = null, $u = !1, Ke = 0, ee = null, t) throw Error(h(300));
    l === null || Nl || (l = l.dependencies, l !== null && Zu(l) && (Nl = !0));
  }
  function Os(l, t, a, e) {
    Z = l;
    var u = 0;
    do {
      if (ae && (ee = null), Ke = 0, ae = !1, 25 <= u) throw Error(h(301));
      if (u += 1, pl = el = null, l.updateQueue != null) {
        var n = l.updateQueue;
        n.lastEffect = null, n.events = null, n.stores = null, n.memoCache != null && (n.memoCache.index = 0);
      }
      S.H = Hh, n = t(a, e);
    } while (ae);
    return n;
  }
  function jh() {
    var l = S.H, t = l.useState()[0];
    return t = typeof t.then == "function" ? Je(t) : t, l = l.useState()[0], (el !== null ? el.memoizedState : null) !== l && (Z.flags |= 1024), t;
  }
  function Gc() {
    var l = Wu !== 0;
    return Wu = 0, l;
  }
  function Xc(l, t, a) {
    t.updateQueue = l.updateQueue, t.flags &= -2053, l.lanes &= ~a;
  }
  function Qc(l) {
    if ($u) {
      for (l = l.memoizedState; l !== null; ) {
        var t = l.queue;
        t !== null && (t.pending = null), l = l.next;
      }
      $u = !1;
    }
    It = 0, pl = el = Z = null, ae = !1, Ke = Wu = 0, ee = null;
  }
  function $l() {
    var l = {
      memoizedState: null,
      baseState: null,
      baseQueue: null,
      queue: null,
      next: null
    };
    return pl === null ? Z.memoizedState = pl = l : pl = pl.next = l, pl;
  }
  function Tl() {
    if (el === null) {
      var l = Z.alternate;
      l = l !== null ? l.memoizedState : null;
    } else l = el.next;
    var t = pl === null ? Z.memoizedState : pl.next;
    if (t !== null)
      pl = t, el = l;
    else {
      if (l === null)
        throw Z.alternate === null ? Error(h(467)) : Error(h(310));
      el = l, l = {
        memoizedState: el.memoizedState,
        baseState: el.baseState,
        baseQueue: el.baseQueue,
        queue: el.queue,
        next: null
      }, pl === null ? Z.memoizedState = pl = l : pl = pl.next = l;
    }
    return pl;
  }
  function Zc() {
    return { lastEffect: null, events: null, stores: null, memoCache: null };
  }
  function Je(l) {
    var t = Ke;
    return Ke += 1, ee === null && (ee = []), l = ps(ee, l, t), t = Z, (pl === null ? t.memoizedState : pl.next) === null && (t = t.alternate, S.H = t === null || t.memoizedState === null ? sr : rr), l;
  }
  function wu(l) {
    if (l !== null && typeof l == "object") {
      if (typeof l.then == "function") return Je(l);
      if (l.$$typeof === El) return Gl(l);
    }
    throw Error(h(438, String(l)));
  }
  function Vc(l) {
    var t = null, a = Z.updateQueue;
    if (a !== null && (t = a.memoCache), t == null) {
      var e = Z.alternate;
      e !== null && (e = e.updateQueue, e !== null && (e = e.memoCache, e != null && (t = {
        data: e.data.map(function(u) {
          return u.slice();
        }),
        index: 0
      })));
    }
    if (t == null && (t = { data: [], index: 0 }), a === null && (a = Zc(), Z.updateQueue = a), a.memoCache = t, a = t.data[t.index], a === void 0)
      for (a = t.data[t.index] = Array(l), e = 0; e < l; e++)
        a[e] = Rl;
    return t.index++, a;
  }
  function Ht(l, t) {
    return typeof t == "function" ? t(l) : t;
  }
  function Fu(l) {
    var t = Tl();
    return Lc(t, el, l);
  }
  function Lc(l, t, a) {
    var e = l.queue;
    if (e === null) throw Error(h(311));
    e.lastRenderedReducer = a;
    var u = l.baseQueue, n = e.pending;
    if (n !== null) {
      if (u !== null) {
        var c = u.next;
        u.next = n.next, n.next = c;
      }
      t.baseQueue = u = n, e.pending = null;
    }
    if (n = l.baseState, u === null) l.memoizedState = n;
    else {
      t = u.next;
      var i = c = null, s = null, m = t, _ = !1;
      do {
        var E = m.lane & -536870913;
        if (E !== m.lane ? (W & E) === E : (It & E) === E) {
          var g = m.revertLane;
          if (g === 0)
            s !== null && (s = s.next = {
              lane: 0,
              revertLane: 0,
              action: m.action,
              hasEagerState: m.hasEagerState,
              eagerState: m.eagerState,
              next: null
            }), E === Pa && (_ = !0);
          else if ((It & g) === g) {
            m = m.next, g === Pa && (_ = !0);
            continue;
          } else
            E = {
              lane: 0,
              revertLane: m.revertLane,
              action: m.action,
              hasEagerState: m.hasEagerState,
              eagerState: m.eagerState,
              next: null
            }, s === null ? (i = s = E, c = n) : s = s.next = E, Z.lanes |= g, na |= g;
          E = m.action, Da && a(n, E), n = m.hasEagerState ? m.eagerState : a(n, E);
        } else
          g = {
            lane: E,
            revertLane: m.revertLane,
            action: m.action,
            hasEagerState: m.hasEagerState,
            eagerState: m.eagerState,
            next: null
          }, s === null ? (i = s = g, c = n) : s = s.next = g, Z.lanes |= E, na |= E;
        m = m.next;
      } while (m !== null && m !== t);
      if (s === null ? c = n : s.next = i, !tt(n, l.memoizedState) && (Nl = !0, _ && (a = le, a !== null)))
        throw a;
      l.memoizedState = n, l.baseState = c, l.baseQueue = s, e.lastRenderedState = n;
    }
    return u === null && (e.lanes = 0), [l.memoizedState, e.dispatch];
  }
  function Kc(l) {
    var t = Tl(), a = t.queue;
    if (a === null) throw Error(h(311));
    a.lastRenderedReducer = l;
    var e = a.dispatch, u = a.pending, n = t.memoizedState;
    if (u !== null) {
      a.pending = null;
      var c = u = u.next;
      do
        n = l(n, c.action), c = c.next;
      while (c !== u);
      tt(n, t.memoizedState) || (Nl = !0), t.memoizedState = n, t.baseQueue === null && (t.baseState = n), a.lastRenderedState = n;
    }
    return [n, e];
  }
  function js(l, t, a) {
    var e = Z, u = Tl(), n = ll;
    if (n) {
      if (a === void 0) throw Error(h(407));
      a = a();
    } else a = t();
    var c = !tt(
      (el || u).memoizedState,
      a
    );
    c && (u.memoizedState = a, Nl = !0), u = u.queue;
    var i = Us.bind(null, e, u, l);
    if (ke(2048, 8, i, [l]), u.getSnapshot !== t || c || pl !== null && pl.memoizedState.tag & 1) {
      if (e.flags |= 2048, ue(
        9,
        Iu(),
        Rs.bind(
          null,
          e,
          u,
          a,
          t
        ),
        null
      ), sl === null) throw Error(h(349));
      n || (It & 124) !== 0 || Ds(e, t, a);
    }
    return a;
  }
  function Ds(l, t, a) {
    l.flags |= 16384, l = { getSnapshot: t, value: a }, t = Z.updateQueue, t === null ? (t = Zc(), Z.updateQueue = t, t.stores = [l]) : (a = t.stores, a === null ? t.stores = [l] : a.push(l));
  }
  function Rs(l, t, a, e) {
    t.value = a, t.getSnapshot = e, Ms(t) && qs(l);
  }
  function Us(l, t, a) {
    return a(function() {
      Ms(t) && qs(l);
    });
  }
  function Ms(l) {
    var t = l.getSnapshot;
    l = l.value;
    try {
      var a = t();
      return !tt(l, a);
    } catch {
      return !0;
    }
  }
  function qs(l) {
    var t = Wa(l, 2);
    t !== null && it(t, l, 2);
  }
  function Jc(l) {
    var t = $l();
    if (typeof l == "function") {
      var a = l;
      if (l = a(), Da) {
        Kt(!0);
        try {
          a();
        } finally {
          Kt(!1);
        }
      }
    }
    return t.memoizedState = t.baseState = l, t.queue = {
      pending: null,
      lanes: 0,
      dispatch: null,
      lastRenderedReducer: Ht,
      lastRenderedState: l
    }, t;
  }
  function Hs(l, t, a, e) {
    return l.baseState = a, Lc(
      l,
      el,
      typeof e == "function" ? e : Ht
    );
  }
  function Dh(l, t, a, e, u) {
    if (ln(l)) throw Error(h(485));
    if (l = t.action, l !== null) {
      var n = {
        payload: u,
        action: l,
        next: null,
        isTransition: !0,
        status: "pending",
        value: null,
        reason: null,
        listeners: [],
        then: function(c) {
          n.listeners.push(c);
        }
      };
      S.T !== null ? a(!0) : n.isTransition = !1, e(n), a = t.pending, a === null ? (n.next = t.pending = n, Ys(t, n)) : (n.next = a.next, t.pending = a.next = n);
    }
  }
  function Ys(l, t) {
    var a = t.action, e = t.payload, u = l.state;
    if (t.isTransition) {
      var n = S.T, c = {};
      S.T = c;
      try {
        var i = a(u, e), s = S.S;
        s !== null && s(c, i), Bs(l, t, i);
      } catch (m) {
        kc(l, t, m);
      } finally {
        S.T = n;
      }
    } else
      try {
        n = a(u, e), Bs(l, t, n);
      } catch (m) {
        kc(l, t, m);
      }
  }
  function Bs(l, t, a) {
    a !== null && typeof a == "object" && typeof a.then == "function" ? a.then(
      function(e) {
        Cs(l, t, e);
      },
      function(e) {
        return kc(l, t, e);
      }
    ) : Cs(l, t, a);
  }
  function Cs(l, t, a) {
    t.status = "fulfilled", t.value = a, Gs(t), l.state = a, t = l.pending, t !== null && (a = t.next, a === t ? l.pending = null : (a = a.next, t.next = a, Ys(l, a)));
  }
  function kc(l, t, a) {
    var e = l.pending;
    if (l.pending = null, e !== null) {
      e = e.next;
      do
        t.status = "rejected", t.reason = a, Gs(t), t = t.next;
      while (t !== e);
    }
    l.action = null;
  }
  function Gs(l) {
    l = l.listeners;
    for (var t = 0; t < l.length; t++) (0, l[t])();
  }
  function Xs(l, t) {
    return t;
  }
  function Qs(l, t) {
    if (ll) {
      var a = sl.formState;
      if (a !== null) {
        l: {
          var e = Z;
          if (ll) {
            if (ml) {
              t: {
                for (var u = ml, n = Et; u.nodeType !== 8; ) {
                  if (!n) {
                    u = null;
                    break t;
                  }
                  if (u = pt(
                    u.nextSibling
                  ), u === null) {
                    u = null;
                    break t;
                  }
                }
                n = u.data, u = n === "F!" || n === "F" ? u : null;
              }
              if (u) {
                ml = pt(
                  u.nextSibling
                ), e = u.data === "F!";
                break l;
              }
            }
            xa(e);
          }
          e = !1;
        }
        e && (t = a[0]);
      }
    }
    return a = $l(), a.memoizedState = a.baseState = t, e = {
      pending: null,
      lanes: 0,
      dispatch: null,
      lastRenderedReducer: Xs,
      lastRenderedState: t
    }, a.queue = e, a = cr.bind(
      null,
      Z,
      e
    ), e.dispatch = a, e = Jc(!1), n = Ic.bind(
      null,
      Z,
      !1,
      e.queue
    ), e = $l(), u = {
      state: t,
      dispatch: null,
      action: l,
      pending: null
    }, e.queue = u, a = Dh.bind(
      null,
      Z,
      u,
      n,
      a
    ), u.dispatch = a, e.memoizedState = l, [t, a, !1];
  }
  function Zs(l) {
    var t = Tl();
    return Vs(t, el, l);
  }
  function Vs(l, t, a) {
    if (t = Lc(
      l,
      t,
      Xs
    )[0], l = Fu(Ht)[0], typeof t == "object" && t !== null && typeof t.then == "function")
      try {
        var e = Je(t);
      } catch (c) {
        throw c === Xe ? Ku : c;
      }
    else e = t;
    t = Tl();
    var u = t.queue, n = u.dispatch;
    return a !== t.memoizedState && (Z.flags |= 2048, ue(
      9,
      Iu(),
      Rh.bind(null, u, a),
      null
    )), [e, n, l];
  }
  function Rh(l, t) {
    l.action = t;
  }
  function Ls(l) {
    var t = Tl(), a = el;
    if (a !== null)
      return Vs(t, a, l);
    Tl(), t = t.memoizedState, a = Tl();
    var e = a.queue.dispatch;
    return a.memoizedState = l, [t, e, !1];
  }
  function ue(l, t, a, e) {
    return l = { tag: l, create: a, deps: e, inst: t, next: null }, t = Z.updateQueue, t === null && (t = Zc(), Z.updateQueue = t), a = t.lastEffect, a === null ? t.lastEffect = l.next = l : (e = a.next, a.next = l, l.next = e, t.lastEffect = l), l;
  }
  function Iu() {
    return { destroy: void 0, resource: void 0 };
  }
  function Ks() {
    return Tl().memoizedState;
  }
  function Pu(l, t, a, e) {
    var u = $l();
    e = e === void 0 ? null : e, Z.flags |= l, u.memoizedState = ue(
      1 | t,
      Iu(),
      a,
      e
    );
  }
  function ke(l, t, a, e) {
    var u = Tl();
    e = e === void 0 ? null : e;
    var n = u.memoizedState.inst;
    el !== null && e !== null && Bc(e, el.memoizedState.deps) ? u.memoizedState = ue(t, n, a, e) : (Z.flags |= l, u.memoizedState = ue(
      1 | t,
      n,
      a,
      e
    ));
  }
  function Js(l, t) {
    Pu(8390656, 8, l, t);
  }
  function ks(l, t) {
    ke(2048, 8, l, t);
  }
  function $s(l, t) {
    return ke(4, 2, l, t);
  }
  function Ws(l, t) {
    return ke(4, 4, l, t);
  }
  function ws(l, t) {
    if (typeof t == "function") {
      l = l();
      var a = t(l);
      return function() {
        typeof a == "function" ? a() : t(null);
      };
    }
    if (t != null)
      return l = l(), t.current = l, function() {
        t.current = null;
      };
  }
  function Fs(l, t, a) {
    a = a != null ? a.concat([l]) : null, ke(4, 4, ws.bind(null, t, l), a);
  }
  function $c() {
  }
  function Is(l, t) {
    var a = Tl();
    t = t === void 0 ? null : t;
    var e = a.memoizedState;
    return t !== null && Bc(t, e[1]) ? e[0] : (a.memoizedState = [l, t], l);
  }
  function Ps(l, t) {
    var a = Tl();
    t = t === void 0 ? null : t;
    var e = a.memoizedState;
    if (t !== null && Bc(t, e[1]))
      return e[0];
    if (e = l(), Da) {
      Kt(!0);
      try {
        l();
      } finally {
        Kt(!1);
      }
    }
    return a.memoizedState = [e, t], e;
  }
  function Wc(l, t, a) {
    return a === void 0 || (It & 1073741824) !== 0 ? l.memoizedState = t : (l.memoizedState = a, l = ad(), Z.lanes |= l, na |= l, a);
  }
  function lr(l, t, a, e) {
    return tt(a, t) ? a : te.current !== null ? (l = Wc(l, a, e), tt(l, t) || (Nl = !0), l) : (It & 42) === 0 ? (Nl = !0, l.memoizedState = a) : (l = ad(), Z.lanes |= l, na |= l, t);
  }
  function tr(l, t, a, e, u) {
    var n = j.p;
    j.p = n !== 0 && 8 > n ? n : 8;
    var c = S.T, i = {};
    S.T = i, Ic(l, !1, t, a);
    try {
      var s = u(), m = S.S;
      if (m !== null && m(i, s), s !== null && typeof s == "object" && typeof s.then == "function") {
        var _ = Nh(
          s,
          e
        );
        $e(
          l,
          t,
          _,
          ct(l)
        );
      } else
        $e(
          l,
          t,
          e,
          ct(l)
        );
    } catch (E) {
      $e(
        l,
        t,
        { then: function() {
        }, status: "rejected", reason: E },
        ct()
      );
    } finally {
      j.p = n, S.T = c;
    }
  }
  function Uh() {
  }
  function wc(l, t, a, e) {
    if (l.tag !== 5) throw Error(h(476));
    var u = ar(l).queue;
    tr(
      l,
      u,
      t,
      C,
      a === null ? Uh : function() {
        return er(l), a(e);
      }
    );
  }
  function ar(l) {
    var t = l.memoizedState;
    if (t !== null) return t;
    t = {
      memoizedState: C,
      baseState: C,
      baseQueue: null,
      queue: {
        pending: null,
        lanes: 0,
        dispatch: null,
        lastRenderedReducer: Ht,
        lastRenderedState: C
      },
      next: null
    };
    var a = {};
    return t.next = {
      memoizedState: a,
      baseState: a,
      baseQueue: null,
      queue: {
        pending: null,
        lanes: 0,
        dispatch: null,
        lastRenderedReducer: Ht,
        lastRenderedState: a
      },
      next: null
    }, l.memoizedState = t, l = l.alternate, l !== null && (l.memoizedState = t), t;
  }
  function er(l) {
    var t = ar(l).next.queue;
    $e(l, t, {}, ct());
  }
  function Fc() {
    return Gl(ou);
  }
  function ur() {
    return Tl().memoizedState;
  }
  function nr() {
    return Tl().memoizedState;
  }
  function Mh(l) {
    for (var t = l.return; t !== null; ) {
      switch (t.tag) {
        case 24:
        case 3:
          var a = ct();
          l = wt(a);
          var e = Ft(t, l, a);
          e !== null && (it(e, t, a), Ze(e, t, a)), t = { cache: Nc() }, l.payload = t;
          return;
      }
      t = t.return;
    }
  }
  function qh(l, t, a) {
    var e = ct();
    a = {
      lane: e,
      revertLane: 0,
      action: a,
      hasEagerState: !1,
      eagerState: null,
      next: null
    }, ln(l) ? ir(t, a) : (a = gc(l, t, a, e), a !== null && (it(a, l, e), fr(a, t, e)));
  }
  function cr(l, t, a) {
    var e = ct();
    $e(l, t, a, e);
  }
  function $e(l, t, a, e) {
    var u = {
      lane: e,
      revertLane: 0,
      action: a,
      hasEagerState: !1,
      eagerState: null,
      next: null
    };
    if (ln(l)) ir(t, u);
    else {
      var n = l.alternate;
      if (l.lanes === 0 && (n === null || n.lanes === 0) && (n = t.lastRenderedReducer, n !== null))
        try {
          var c = t.lastRenderedState, i = n(c, a);
          if (u.hasEagerState = !0, u.eagerState = i, tt(i, c))
            return Bu(l, t, u, 0), sl === null && Yu(), !1;
        } catch {
        } finally {
        }
      if (a = gc(l, t, u, e), a !== null)
        return it(a, l, e), fr(a, t, e), !0;
    }
    return !1;
  }
  function Ic(l, t, a, e) {
    if (e = {
      lane: 2,
      revertLane: Di(),
      action: e,
      hasEagerState: !1,
      eagerState: null,
      next: null
    }, ln(l)) {
      if (t) throw Error(h(479));
    } else
      t = gc(
        l,
        a,
        e,
        2
      ), t !== null && it(t, l, 2);
  }
  function ln(l) {
    var t = l.alternate;
    return l === Z || t !== null && t === Z;
  }
  function ir(l, t) {
    ae = $u = !0;
    var a = l.pending;
    a === null ? t.next = t : (t.next = a.next, a.next = t), l.pending = t;
  }
  function fr(l, t, a) {
    if ((a & 4194048) !== 0) {
      var e = t.lanes;
      e &= l.pendingLanes, a |= e, t.lanes = a, mf(l, a);
    }
  }
  var tn = {
    readContext: Gl,
    use: wu,
    useCallback: bl,
    useContext: bl,
    useEffect: bl,
    useImperativeHandle: bl,
    useLayoutEffect: bl,
    useInsertionEffect: bl,
    useMemo: bl,
    useReducer: bl,
    useRef: bl,
    useState: bl,
    useDebugValue: bl,
    useDeferredValue: bl,
    useTransition: bl,
    useSyncExternalStore: bl,
    useId: bl,
    useHostTransitionStatus: bl,
    useFormState: bl,
    useActionState: bl,
    useOptimistic: bl,
    useMemoCache: bl,
    useCacheRefresh: bl
  }, sr = {
    readContext: Gl,
    use: wu,
    useCallback: function(l, t) {
      return $l().memoizedState = [
        l,
        t === void 0 ? null : t
      ], l;
    },
    useContext: Gl,
    useEffect: Js,
    useImperativeHandle: function(l, t, a) {
      a = a != null ? a.concat([l]) : null, Pu(
        4194308,
        4,
        ws.bind(null, t, l),
        a
      );
    },
    useLayoutEffect: function(l, t) {
      return Pu(4194308, 4, l, t);
    },
    useInsertionEffect: function(l, t) {
      Pu(4, 2, l, t);
    },
    useMemo: function(l, t) {
      var a = $l();
      t = t === void 0 ? null : t;
      var e = l();
      if (Da) {
        Kt(!0);
        try {
          l();
        } finally {
          Kt(!1);
        }
      }
      return a.memoizedState = [e, t], e;
    },
    useReducer: function(l, t, a) {
      var e = $l();
      if (a !== void 0) {
        var u = a(t);
        if (Da) {
          Kt(!0);
          try {
            a(t);
          } finally {
            Kt(!1);
          }
        }
      } else u = t;
      return e.memoizedState = e.baseState = u, l = {
        pending: null,
        lanes: 0,
        dispatch: null,
        lastRenderedReducer: l,
        lastRenderedState: u
      }, e.queue = l, l = l.dispatch = qh.bind(
        null,
        Z,
        l
      ), [e.memoizedState, l];
    },
    useRef: function(l) {
      var t = $l();
      return l = { current: l }, t.memoizedState = l;
    },
    useState: function(l) {
      l = Jc(l);
      var t = l.queue, a = cr.bind(null, Z, t);
      return t.dispatch = a, [l.memoizedState, a];
    },
    useDebugValue: $c,
    useDeferredValue: function(l, t) {
      var a = $l();
      return Wc(a, l, t);
    },
    useTransition: function() {
      var l = Jc(!1);
      return l = tr.bind(
        null,
        Z,
        l.queue,
        !0,
        !1
      ), $l().memoizedState = l, [!1, l];
    },
    useSyncExternalStore: function(l, t, a) {
      var e = Z, u = $l();
      if (ll) {
        if (a === void 0)
          throw Error(h(407));
        a = a();
      } else {
        if (a = t(), sl === null)
          throw Error(h(349));
        (W & 124) !== 0 || Ds(e, t, a);
      }
      u.memoizedState = a;
      var n = { value: a, getSnapshot: t };
      return u.queue = n, Js(Us.bind(null, e, n, l), [
        l
      ]), e.flags |= 2048, ue(
        9,
        Iu(),
        Rs.bind(
          null,
          e,
          n,
          a,
          t
        ),
        null
      ), a;
    },
    useId: function() {
      var l = $l(), t = sl.identifierPrefix;
      if (ll) {
        var a = Ut, e = Rt;
        a = (e & ~(1 << 32 - lt(e) - 1)).toString(32) + a, t = "«" + t + "R" + a, a = Wu++, 0 < a && (t += "H" + a.toString(32)), t += "»";
      } else
        a = Oh++, t = "«" + t + "r" + a.toString(32) + "»";
      return l.memoizedState = t;
    },
    useHostTransitionStatus: Fc,
    useFormState: Qs,
    useActionState: Qs,
    useOptimistic: function(l) {
      var t = $l();
      t.memoizedState = t.baseState = l;
      var a = {
        pending: null,
        lanes: 0,
        dispatch: null,
        lastRenderedReducer: null,
        lastRenderedState: null
      };
      return t.queue = a, t = Ic.bind(
        null,
        Z,
        !0,
        a
      ), a.dispatch = t, [l, t];
    },
    useMemoCache: Vc,
    useCacheRefresh: function() {
      return $l().memoizedState = Mh.bind(
        null,
        Z
      );
    }
  }, rr = {
    readContext: Gl,
    use: wu,
    useCallback: Is,
    useContext: Gl,
    useEffect: ks,
    useImperativeHandle: Fs,
    useInsertionEffect: $s,
    useLayoutEffect: Ws,
    useMemo: Ps,
    useReducer: Fu,
    useRef: Ks,
    useState: function() {
      return Fu(Ht);
    },
    useDebugValue: $c,
    useDeferredValue: function(l, t) {
      var a = Tl();
      return lr(
        a,
        el.memoizedState,
        l,
        t
      );
    },
    useTransition: function() {
      var l = Fu(Ht)[0], t = Tl().memoizedState;
      return [
        typeof l == "boolean" ? l : Je(l),
        t
      ];
    },
    useSyncExternalStore: js,
    useId: ur,
    useHostTransitionStatus: Fc,
    useFormState: Zs,
    useActionState: Zs,
    useOptimistic: function(l, t) {
      var a = Tl();
      return Hs(a, el, l, t);
    },
    useMemoCache: Vc,
    useCacheRefresh: nr
  }, Hh = {
    readContext: Gl,
    use: wu,
    useCallback: Is,
    useContext: Gl,
    useEffect: ks,
    useImperativeHandle: Fs,
    useInsertionEffect: $s,
    useLayoutEffect: Ws,
    useMemo: Ps,
    useReducer: Kc,
    useRef: Ks,
    useState: function() {
      return Kc(Ht);
    },
    useDebugValue: $c,
    useDeferredValue: function(l, t) {
      var a = Tl();
      return el === null ? Wc(a, l, t) : lr(
        a,
        el.memoizedState,
        l,
        t
      );
    },
    useTransition: function() {
      var l = Kc(Ht)[0], t = Tl().memoizedState;
      return [
        typeof l == "boolean" ? l : Je(l),
        t
      ];
    },
    useSyncExternalStore: js,
    useId: ur,
    useHostTransitionStatus: Fc,
    useFormState: Ls,
    useActionState: Ls,
    useOptimistic: function(l, t) {
      var a = Tl();
      return el !== null ? Hs(a, el, l, t) : (a.baseState = l, [l, a.queue.dispatch]);
    },
    useMemoCache: Vc,
    useCacheRefresh: nr
  }, ne = null, We = 0;
  function an(l) {
    var t = We;
    return We += 1, ne === null && (ne = []), ps(ne, l, t);
  }
  function we(l, t) {
    t = t.props.ref, l.ref = t !== void 0 ? t : null;
  }
  function en(l, t) {
    throw t.$$typeof === w ? Error(h(525)) : (l = Object.prototype.toString.call(t), Error(
      h(
        31,
        l === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : l
      )
    ));
  }
  function dr(l) {
    var t = l._init;
    return t(l._payload);
  }
  function or(l) {
    function t(y, o) {
      if (l) {
        var v = y.deletions;
        v === null ? (y.deletions = [o], y.flags |= 16) : v.push(o);
      }
    }
    function a(y, o) {
      if (!l) return null;
      for (; o !== null; )
        t(y, o), o = o.sibling;
      return null;
    }
    function e(y) {
      for (var o = /* @__PURE__ */ new Map(); y !== null; )
        y.key !== null ? o.set(y.key, y) : o.set(y.index, y), y = y.sibling;
      return o;
    }
    function u(y, o) {
      return y = Dt(y, o), y.index = 0, y.sibling = null, y;
    }
    function n(y, o, v) {
      return y.index = v, l ? (v = y.alternate, v !== null ? (v = v.index, v < o ? (y.flags |= 67108866, o) : v) : (y.flags |= 67108866, o)) : (y.flags |= 1048576, o);
    }
    function c(y) {
      return l && y.alternate === null && (y.flags |= 67108866), y;
    }
    function i(y, o, v, p) {
      return o === null || o.tag !== 6 ? (o = _c(v, y.mode, p), o.return = y, o) : (o = u(o, v), o.return = y, o);
    }
    function s(y, o, v, p) {
      var U = v.type;
      return U === Sl ? _(
        y,
        o,
        v.props.children,
        p,
        v.key
      ) : o !== null && (o.elementType === U || typeof U == "object" && U !== null && U.$$typeof === Hl && dr(U) === o.type) ? (o = u(o, v.props), we(o, v), o.return = y, o) : (o = Gu(
        v.type,
        v.key,
        v.props,
        null,
        y.mode,
        p
      ), we(o, v), o.return = y, o);
    }
    function m(y, o, v, p) {
      return o === null || o.tag !== 4 || o.stateNode.containerInfo !== v.containerInfo || o.stateNode.implementation !== v.implementation ? (o = Sc(v, y.mode, p), o.return = y, o) : (o = u(o, v.children || []), o.return = y, o);
    }
    function _(y, o, v, p, U) {
      return o === null || o.tag !== 7 ? (o = Ta(
        v,
        y.mode,
        p,
        U
      ), o.return = y, o) : (o = u(o, v), o.return = y, o);
    }
    function E(y, o, v) {
      if (typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint")
        return o = _c(
          "" + o,
          y.mode,
          v
        ), o.return = y, o;
      if (typeof o == "object" && o !== null) {
        switch (o.$$typeof) {
          case $:
            return v = Gu(
              o.type,
              o.key,
              o.props,
              null,
              y.mode,
              v
            ), we(v, o), v.return = y, v;
          case rl:
            return o = Sc(
              o,
              y.mode,
              v
            ), o.return = y, o;
          case Hl:
            var p = o._init;
            return o = p(o._payload), E(y, o, v);
        }
        if (Bl(o) || Yl(o))
          return o = Ta(
            o,
            y.mode,
            v,
            null
          ), o.return = y, o;
        if (typeof o.then == "function")
          return E(y, an(o), v);
        if (o.$$typeof === El)
          return E(
            y,
            Vu(y, o),
            v
          );
        en(y, o);
      }
      return null;
    }
    function g(y, o, v, p) {
      var U = o !== null ? o.key : null;
      if (typeof v == "string" && v !== "" || typeof v == "number" || typeof v == "bigint")
        return U !== null ? null : i(y, o, "" + v, p);
      if (typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case $:
            return v.key === U ? s(y, o, v, p) : null;
          case rl:
            return v.key === U ? m(y, o, v, p) : null;
          case Hl:
            return U = v._init, v = U(v._payload), g(y, o, v, p);
        }
        if (Bl(v) || Yl(v))
          return U !== null ? null : _(y, o, v, p, null);
        if (typeof v.then == "function")
          return g(
            y,
            o,
            an(v),
            p
          );
        if (v.$$typeof === El)
          return g(
            y,
            o,
            Vu(y, v),
            p
          );
        en(y, v);
      }
      return null;
    }
    function b(y, o, v, p, U) {
      if (typeof p == "string" && p !== "" || typeof p == "number" || typeof p == "bigint")
        return y = y.get(v) || null, i(o, y, "" + p, U);
      if (typeof p == "object" && p !== null) {
        switch (p.$$typeof) {
          case $:
            return y = y.get(
              p.key === null ? v : p.key
            ) || null, s(o, y, p, U);
          case rl:
            return y = y.get(
              p.key === null ? v : p.key
            ) || null, m(o, y, p, U);
          case Hl:
            var L = p._init;
            return p = L(p._payload), b(
              y,
              o,
              v,
              p,
              U
            );
        }
        if (Bl(p) || Yl(p))
          return y = y.get(v) || null, _(o, y, p, U, null);
        if (typeof p.then == "function")
          return b(
            y,
            o,
            v,
            an(p),
            U
          );
        if (p.$$typeof === El)
          return b(
            y,
            o,
            v,
            Vu(o, p),
            U
          );
        en(o, p);
      }
      return null;
    }
    function G(y, o, v, p) {
      for (var U = null, L = null, M = o, B = o = 0, jl = null; M !== null && B < v.length; B++) {
        M.index > B ? (jl = M, M = null) : jl = M.sibling;
        var P = g(
          y,
          M,
          v[B],
          p
        );
        if (P === null) {
          M === null && (M = jl);
          break;
        }
        l && M && P.alternate === null && t(y, M), o = n(P, o, B), L === null ? U = P : L.sibling = P, L = P, M = jl;
      }
      if (B === v.length)
        return a(y, M), ll && Aa(y, B), U;
      if (M === null) {
        for (; B < v.length; B++)
          M = E(y, v[B], p), M !== null && (o = n(
            M,
            o,
            B
          ), L === null ? U = M : L.sibling = M, L = M);
        return ll && Aa(y, B), U;
      }
      for (M = e(M); B < v.length; B++)
        jl = b(
          M,
          y,
          B,
          v[B],
          p
        ), jl !== null && (l && jl.alternate !== null && M.delete(
          jl.key === null ? B : jl.key
        ), o = n(
          jl,
          o,
          B
        ), L === null ? U = jl : L.sibling = jl, L = jl);
      return l && M.forEach(function(ya) {
        return t(y, ya);
      }), ll && Aa(y, B), U;
    }
    function H(y, o, v, p) {
      if (v == null) throw Error(h(151));
      for (var U = null, L = null, M = o, B = o = 0, jl = null, P = v.next(); M !== null && !P.done; B++, P = v.next()) {
        M.index > B ? (jl = M, M = null) : jl = M.sibling;
        var ya = g(y, M, P.value, p);
        if (ya === null) {
          M === null && (M = jl);
          break;
        }
        l && M && ya.alternate === null && t(y, M), o = n(ya, o, B), L === null ? U = ya : L.sibling = ya, L = ya, M = jl;
      }
      if (P.done)
        return a(y, M), ll && Aa(y, B), U;
      if (M === null) {
        for (; !P.done; B++, P = v.next())
          P = E(y, P.value, p), P !== null && (o = n(P, o, B), L === null ? U = P : L.sibling = P, L = P);
        return ll && Aa(y, B), U;
      }
      for (M = e(M); !P.done; B++, P = v.next())
        P = b(M, y, B, P.value, p), P !== null && (l && P.alternate !== null && M.delete(P.key === null ? B : P.key), o = n(P, o, B), L === null ? U = P : L.sibling = P, L = P);
      return l && M.forEach(function(Yy) {
        return t(y, Yy);
      }), ll && Aa(y, B), U;
    }
    function nl(y, o, v, p) {
      if (typeof v == "object" && v !== null && v.type === Sl && v.key === null && (v = v.props.children), typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case $:
            l: {
              for (var U = v.key; o !== null; ) {
                if (o.key === U) {
                  if (U = v.type, U === Sl) {
                    if (o.tag === 7) {
                      a(
                        y,
                        o.sibling
                      ), p = u(
                        o,
                        v.props.children
                      ), p.return = y, y = p;
                      break l;
                    }
                  } else if (o.elementType === U || typeof U == "object" && U !== null && U.$$typeof === Hl && dr(U) === o.type) {
                    a(
                      y,
                      o.sibling
                    ), p = u(o, v.props), we(p, v), p.return = y, y = p;
                    break l;
                  }
                  a(y, o);
                  break;
                } else t(y, o);
                o = o.sibling;
              }
              v.type === Sl ? (p = Ta(
                v.props.children,
                y.mode,
                p,
                v.key
              ), p.return = y, y = p) : (p = Gu(
                v.type,
                v.key,
                v.props,
                null,
                y.mode,
                p
              ), we(p, v), p.return = y, y = p);
            }
            return c(y);
          case rl:
            l: {
              for (U = v.key; o !== null; ) {
                if (o.key === U)
                  if (o.tag === 4 && o.stateNode.containerInfo === v.containerInfo && o.stateNode.implementation === v.implementation) {
                    a(
                      y,
                      o.sibling
                    ), p = u(o, v.children || []), p.return = y, y = p;
                    break l;
                  } else {
                    a(y, o);
                    break;
                  }
                else t(y, o);
                o = o.sibling;
              }
              p = Sc(v, y.mode, p), p.return = y, y = p;
            }
            return c(y);
          case Hl:
            return U = v._init, v = U(v._payload), nl(
              y,
              o,
              v,
              p
            );
        }
        if (Bl(v))
          return G(
            y,
            o,
            v,
            p
          );
        if (Yl(v)) {
          if (U = Yl(v), typeof U != "function") throw Error(h(150));
          return v = U.call(v), H(
            y,
            o,
            v,
            p
          );
        }
        if (typeof v.then == "function")
          return nl(
            y,
            o,
            an(v),
            p
          );
        if (v.$$typeof === El)
          return nl(
            y,
            o,
            Vu(y, v),
            p
          );
        en(y, v);
      }
      return typeof v == "string" && v !== "" || typeof v == "number" || typeof v == "bigint" ? (v = "" + v, o !== null && o.tag === 6 ? (a(y, o.sibling), p = u(o, v), p.return = y, y = p) : (a(y, o), p = _c(v, y.mode, p), p.return = y, y = p), c(y)) : a(y, o);
    }
    return function(y, o, v, p) {
      try {
        We = 0;
        var U = nl(
          y,
          o,
          v,
          p
        );
        return ne = null, U;
      } catch (M) {
        if (M === Xe || M === Ku) throw M;
        var L = at(29, M, null, y.mode);
        return L.lanes = p, L.return = y, L;
      } finally {
      }
    };
  }
  var ce = or(!0), hr = or(!1), mt = A(null), At = null;
  function Pt(l) {
    var t = l.alternate;
    O(zl, zl.current & 1), O(mt, l), At === null && (t === null || te.current !== null || t.memoizedState !== null) && (At = l);
  }
  function yr(l) {
    if (l.tag === 22) {
      if (O(zl, zl.current), O(mt, l), At === null) {
        var t = l.alternate;
        t !== null && t.memoizedState !== null && (At = l);
      }
    } else la();
  }
  function la() {
    O(zl, zl.current), O(mt, mt.current);
  }
  function Yt(l) {
    D(mt), At === l && (At = null), D(zl);
  }
  var zl = A(0);
  function un(l) {
    for (var t = l; t !== null; ) {
      if (t.tag === 13) {
        var a = t.memoizedState;
        if (a !== null && (a = a.dehydrated, a === null || a.data === "$?" || Zi(a)))
          return t;
      } else if (t.tag === 19 && t.memoizedProps.revealOrder !== void 0) {
        if ((t.flags & 128) !== 0) return t;
      } else if (t.child !== null) {
        t.child.return = t, t = t.child;
        continue;
      }
      if (t === l) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === l) return null;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
    return null;
  }
  function Pc(l, t, a, e) {
    t = l.memoizedState, a = a(e, t), a = a == null ? t : N({}, t, a), l.memoizedState = a, l.lanes === 0 && (l.updateQueue.baseState = a);
  }
  var li = {
    enqueueSetState: function(l, t, a) {
      l = l._reactInternals;
      var e = ct(), u = wt(e);
      u.payload = t, a != null && (u.callback = a), t = Ft(l, u, e), t !== null && (it(t, l, e), Ze(t, l, e));
    },
    enqueueReplaceState: function(l, t, a) {
      l = l._reactInternals;
      var e = ct(), u = wt(e);
      u.tag = 1, u.payload = t, a != null && (u.callback = a), t = Ft(l, u, e), t !== null && (it(t, l, e), Ze(t, l, e));
    },
    enqueueForceUpdate: function(l, t) {
      l = l._reactInternals;
      var a = ct(), e = wt(a);
      e.tag = 2, t != null && (e.callback = t), t = Ft(l, e, a), t !== null && (it(t, l, a), Ze(t, l, a));
    }
  };
  function vr(l, t, a, e, u, n, c) {
    return l = l.stateNode, typeof l.shouldComponentUpdate == "function" ? l.shouldComponentUpdate(e, n, c) : t.prototype && t.prototype.isPureReactComponent ? !Ue(a, e) || !Ue(u, n) : !0;
  }
  function mr(l, t, a, e) {
    l = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(a, e), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(a, e), t.state !== l && li.enqueueReplaceState(t, t.state, null);
  }
  function Ra(l, t) {
    var a = t;
    if ("ref" in t) {
      a = {};
      for (var e in t)
        e !== "ref" && (a[e] = t[e]);
    }
    if (l = l.defaultProps) {
      a === t && (a = N({}, a));
      for (var u in l)
        a[u] === void 0 && (a[u] = l[u]);
    }
    return a;
  }
  var nn = typeof reportError == "function" ? reportError : function(l) {
    if (typeof window == "object" && typeof window.ErrorEvent == "function") {
      var t = new window.ErrorEvent("error", {
        bubbles: !0,
        cancelable: !0,
        message: typeof l == "object" && l !== null && typeof l.message == "string" ? String(l.message) : String(l),
        error: l
      });
      if (!window.dispatchEvent(t)) return;
    } else if (typeof process == "object" && typeof process.emit == "function") {
      process.emit("uncaughtException", l);
      return;
    }
    console.error(l);
  };
  function gr(l) {
    nn(l);
  }
  function br(l) {
    console.error(l);
  }
  function _r(l) {
    nn(l);
  }
  function cn(l, t) {
    try {
      var a = l.onUncaughtError;
      a(t.value, { componentStack: t.stack });
    } catch (e) {
      setTimeout(function() {
        throw e;
      });
    }
  }
  function Sr(l, t, a) {
    try {
      var e = l.onCaughtError;
      e(a.value, {
        componentStack: a.stack,
        errorBoundary: t.tag === 1 ? t.stateNode : null
      });
    } catch (u) {
      setTimeout(function() {
        throw u;
      });
    }
  }
  function ti(l, t, a) {
    return a = wt(a), a.tag = 3, a.payload = { element: null }, a.callback = function() {
      cn(l, t);
    }, a;
  }
  function pr(l) {
    return l = wt(l), l.tag = 3, l;
  }
  function Tr(l, t, a, e) {
    var u = a.type.getDerivedStateFromError;
    if (typeof u == "function") {
      var n = e.value;
      l.payload = function() {
        return u(n);
      }, l.callback = function() {
        Sr(t, a, e);
      };
    }
    var c = a.stateNode;
    c !== null && typeof c.componentDidCatch == "function" && (l.callback = function() {
      Sr(t, a, e), typeof u != "function" && (ca === null ? ca = /* @__PURE__ */ new Set([this]) : ca.add(this));
      var i = e.stack;
      this.componentDidCatch(e.value, {
        componentStack: i !== null ? i : ""
      });
    });
  }
  function Yh(l, t, a, e, u) {
    if (a.flags |= 32768, e !== null && typeof e == "object" && typeof e.then == "function") {
      if (t = a.alternate, t !== null && Be(
        t,
        a,
        u,
        !0
      ), a = mt.current, a !== null) {
        switch (a.tag) {
          case 13:
            return At === null ? zi() : a.alternate === null && gl === 0 && (gl = 3), a.flags &= -257, a.flags |= 65536, a.lanes = u, e === Dc ? a.flags |= 16384 : (t = a.updateQueue, t === null ? a.updateQueue = /* @__PURE__ */ new Set([e]) : t.add(e), Ni(l, e, u)), !1;
          case 22:
            return a.flags |= 65536, e === Dc ? a.flags |= 16384 : (t = a.updateQueue, t === null ? (t = {
              transitions: null,
              markerInstances: null,
              retryQueue: /* @__PURE__ */ new Set([e])
            }, a.updateQueue = t) : (a = t.retryQueue, a === null ? t.retryQueue = /* @__PURE__ */ new Set([e]) : a.add(e)), Ni(l, e, u)), !1;
        }
        throw Error(h(435, a.tag));
      }
      return Ni(l, e, u), zi(), !1;
    }
    if (ll)
      return t = mt.current, t !== null ? ((t.flags & 65536) === 0 && (t.flags |= 256), t.flags |= 65536, t.lanes = u, e !== Ec && (l = Error(h(422), { cause: e }), Ye(ot(l, a)))) : (e !== Ec && (t = Error(h(423), {
        cause: e
      }), Ye(
        ot(t, a)
      )), l = l.current.alternate, l.flags |= 65536, u &= -u, l.lanes |= u, e = ot(e, a), u = ti(
        l.stateNode,
        e,
        u
      ), Mc(l, u), gl !== 4 && (gl = 2)), !1;
    var n = Error(h(520), { cause: e });
    if (n = ot(n, a), eu === null ? eu = [n] : eu.push(n), gl !== 4 && (gl = 2), t === null) return !0;
    e = ot(e, a), a = t;
    do {
      switch (a.tag) {
        case 3:
          return a.flags |= 65536, l = u & -u, a.lanes |= l, l = ti(a.stateNode, e, l), Mc(a, l), !1;
        case 1:
          if (t = a.type, n = a.stateNode, (a.flags & 128) === 0 && (typeof t.getDerivedStateFromError == "function" || n !== null && typeof n.componentDidCatch == "function" && (ca === null || !ca.has(n))))
            return a.flags |= 65536, u &= -u, a.lanes |= u, u = pr(u), Tr(
              u,
              l,
              a,
              e
            ), Mc(a, u), !1;
      }
      a = a.return;
    } while (a !== null);
    return !1;
  }
  var Er = Error(h(461)), Nl = !1;
  function Ul(l, t, a, e) {
    t.child = l === null ? hr(t, null, a, e) : ce(
      t,
      l.child,
      a,
      e
    );
  }
  function Ar(l, t, a, e, u) {
    a = a.render;
    var n = t.ref;
    if ("ref" in e) {
      var c = {};
      for (var i in e)
        i !== "ref" && (c[i] = e[i]);
    } else c = e;
    return Oa(t), e = Cc(
      l,
      t,
      a,
      c,
      n,
      u
    ), i = Gc(), l !== null && !Nl ? (Xc(l, t, u), Bt(l, t, u)) : (ll && i && pc(t), t.flags |= 1, Ul(l, t, e, u), t.child);
  }
  function zr(l, t, a, e, u) {
    if (l === null) {
      var n = a.type;
      return typeof n == "function" && !bc(n) && n.defaultProps === void 0 && a.compare === null ? (t.tag = 15, t.type = n, xr(
        l,
        t,
        n,
        e,
        u
      )) : (l = Gu(
        a.type,
        null,
        e,
        t,
        t.mode,
        u
      ), l.ref = t.ref, l.return = t, t.child = l);
    }
    if (n = l.child, !si(l, u)) {
      var c = n.memoizedProps;
      if (a = a.compare, a = a !== null ? a : Ue, a(c, e) && l.ref === t.ref)
        return Bt(l, t, u);
    }
    return t.flags |= 1, l = Dt(n, e), l.ref = t.ref, l.return = t, t.child = l;
  }
  function xr(l, t, a, e, u) {
    if (l !== null) {
      var n = l.memoizedProps;
      if (Ue(n, e) && l.ref === t.ref)
        if (Nl = !1, t.pendingProps = e = n, si(l, u))
          (l.flags & 131072) !== 0 && (Nl = !0);
        else
          return t.lanes = l.lanes, Bt(l, t, u);
    }
    return ai(
      l,
      t,
      a,
      e,
      u
    );
  }
  function Nr(l, t, a) {
    var e = t.pendingProps, u = e.children, n = l !== null ? l.memoizedState : null;
    if (e.mode === "hidden") {
      if ((t.flags & 128) !== 0) {
        if (e = n !== null ? n.baseLanes | a : a, l !== null) {
          for (u = t.child = l.child, n = 0; u !== null; )
            n = n | u.lanes | u.childLanes, u = u.sibling;
          t.childLanes = n & ~e;
        } else t.childLanes = 0, t.child = null;
        return Or(
          l,
          t,
          e,
          a
        );
      }
      if ((a & 536870912) !== 0)
        t.memoizedState = { baseLanes: 0, cachePool: null }, l !== null && Lu(
          t,
          n !== null ? n.cachePool : null
        ), n !== null ? xs(t, n) : Hc(), yr(t);
      else
        return t.lanes = t.childLanes = 536870912, Or(
          l,
          t,
          n !== null ? n.baseLanes | a : a,
          a
        );
    } else
      n !== null ? (Lu(t, n.cachePool), xs(t, n), la(), t.memoizedState = null) : (l !== null && Lu(t, null), Hc(), la());
    return Ul(l, t, u, a), t.child;
  }
  function Or(l, t, a, e) {
    var u = jc();
    return u = u === null ? null : { parent: Al._currentValue, pool: u }, t.memoizedState = {
      baseLanes: a,
      cachePool: u
    }, l !== null && Lu(t, null), Hc(), yr(t), l !== null && Be(l, t, e, !0), null;
  }
  function fn(l, t) {
    var a = t.ref;
    if (a === null)
      l !== null && l.ref !== null && (t.flags |= 4194816);
    else {
      if (typeof a != "function" && typeof a != "object")
        throw Error(h(284));
      (l === null || l.ref !== a) && (t.flags |= 4194816);
    }
  }
  function ai(l, t, a, e, u) {
    return Oa(t), a = Cc(
      l,
      t,
      a,
      e,
      void 0,
      u
    ), e = Gc(), l !== null && !Nl ? (Xc(l, t, u), Bt(l, t, u)) : (ll && e && pc(t), t.flags |= 1, Ul(l, t, a, u), t.child);
  }
  function jr(l, t, a, e, u, n) {
    return Oa(t), t.updateQueue = null, a = Os(
      t,
      e,
      a,
      u
    ), Ns(l), e = Gc(), l !== null && !Nl ? (Xc(l, t, n), Bt(l, t, n)) : (ll && e && pc(t), t.flags |= 1, Ul(l, t, a, n), t.child);
  }
  function Dr(l, t, a, e, u) {
    if (Oa(t), t.stateNode === null) {
      var n = wa, c = a.contextType;
      typeof c == "object" && c !== null && (n = Gl(c)), n = new a(e, n), t.memoizedState = n.state !== null && n.state !== void 0 ? n.state : null, n.updater = li, t.stateNode = n, n._reactInternals = t, n = t.stateNode, n.props = e, n.state = t.memoizedState, n.refs = {}, Rc(t), c = a.contextType, n.context = typeof c == "object" && c !== null ? Gl(c) : wa, n.state = t.memoizedState, c = a.getDerivedStateFromProps, typeof c == "function" && (Pc(
        t,
        a,
        c,
        e
      ), n.state = t.memoizedState), typeof a.getDerivedStateFromProps == "function" || typeof n.getSnapshotBeforeUpdate == "function" || typeof n.UNSAFE_componentWillMount != "function" && typeof n.componentWillMount != "function" || (c = n.state, typeof n.componentWillMount == "function" && n.componentWillMount(), typeof n.UNSAFE_componentWillMount == "function" && n.UNSAFE_componentWillMount(), c !== n.state && li.enqueueReplaceState(n, n.state, null), Le(t, e, n, u), Ve(), n.state = t.memoizedState), typeof n.componentDidMount == "function" && (t.flags |= 4194308), e = !0;
    } else if (l === null) {
      n = t.stateNode;
      var i = t.memoizedProps, s = Ra(a, i);
      n.props = s;
      var m = n.context, _ = a.contextType;
      c = wa, typeof _ == "object" && _ !== null && (c = Gl(_));
      var E = a.getDerivedStateFromProps;
      _ = typeof E == "function" || typeof n.getSnapshotBeforeUpdate == "function", i = t.pendingProps !== i, _ || typeof n.UNSAFE_componentWillReceiveProps != "function" && typeof n.componentWillReceiveProps != "function" || (i || m !== c) && mr(
        t,
        n,
        e,
        c
      ), Wt = !1;
      var g = t.memoizedState;
      n.state = g, Le(t, e, n, u), Ve(), m = t.memoizedState, i || g !== m || Wt ? (typeof E == "function" && (Pc(
        t,
        a,
        E,
        e
      ), m = t.memoizedState), (s = Wt || vr(
        t,
        a,
        s,
        e,
        g,
        m,
        c
      )) ? (_ || typeof n.UNSAFE_componentWillMount != "function" && typeof n.componentWillMount != "function" || (typeof n.componentWillMount == "function" && n.componentWillMount(), typeof n.UNSAFE_componentWillMount == "function" && n.UNSAFE_componentWillMount()), typeof n.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof n.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = e, t.memoizedState = m), n.props = e, n.state = m, n.context = c, e = s) : (typeof n.componentDidMount == "function" && (t.flags |= 4194308), e = !1);
    } else {
      n = t.stateNode, Uc(l, t), c = t.memoizedProps, _ = Ra(a, c), n.props = _, E = t.pendingProps, g = n.context, m = a.contextType, s = wa, typeof m == "object" && m !== null && (s = Gl(m)), i = a.getDerivedStateFromProps, (m = typeof i == "function" || typeof n.getSnapshotBeforeUpdate == "function") || typeof n.UNSAFE_componentWillReceiveProps != "function" && typeof n.componentWillReceiveProps != "function" || (c !== E || g !== s) && mr(
        t,
        n,
        e,
        s
      ), Wt = !1, g = t.memoizedState, n.state = g, Le(t, e, n, u), Ve();
      var b = t.memoizedState;
      c !== E || g !== b || Wt || l !== null && l.dependencies !== null && Zu(l.dependencies) ? (typeof i == "function" && (Pc(
        t,
        a,
        i,
        e
      ), b = t.memoizedState), (_ = Wt || vr(
        t,
        a,
        _,
        e,
        g,
        b,
        s
      ) || l !== null && l.dependencies !== null && Zu(l.dependencies)) ? (m || typeof n.UNSAFE_componentWillUpdate != "function" && typeof n.componentWillUpdate != "function" || (typeof n.componentWillUpdate == "function" && n.componentWillUpdate(e, b, s), typeof n.UNSAFE_componentWillUpdate == "function" && n.UNSAFE_componentWillUpdate(
        e,
        b,
        s
      )), typeof n.componentDidUpdate == "function" && (t.flags |= 4), typeof n.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof n.componentDidUpdate != "function" || c === l.memoizedProps && g === l.memoizedState || (t.flags |= 4), typeof n.getSnapshotBeforeUpdate != "function" || c === l.memoizedProps && g === l.memoizedState || (t.flags |= 1024), t.memoizedProps = e, t.memoizedState = b), n.props = e, n.state = b, n.context = s, e = _) : (typeof n.componentDidUpdate != "function" || c === l.memoizedProps && g === l.memoizedState || (t.flags |= 4), typeof n.getSnapshotBeforeUpdate != "function" || c === l.memoizedProps && g === l.memoizedState || (t.flags |= 1024), e = !1);
    }
    return n = e, fn(l, t), e = (t.flags & 128) !== 0, n || e ? (n = t.stateNode, a = e && typeof a.getDerivedStateFromError != "function" ? null : n.render(), t.flags |= 1, l !== null && e ? (t.child = ce(
      t,
      l.child,
      null,
      u
    ), t.child = ce(
      t,
      null,
      a,
      u
    )) : Ul(l, t, a, u), t.memoizedState = n.state, l = t.child) : l = Bt(
      l,
      t,
      u
    ), l;
  }
  function Rr(l, t, a, e) {
    return He(), t.flags |= 256, Ul(l, t, a, e), t.child;
  }
  var ei = {
    dehydrated: null,
    treeContext: null,
    retryLane: 0,
    hydrationErrors: null
  };
  function ui(l) {
    return { baseLanes: l, cachePool: bs() };
  }
  function ni(l, t, a) {
    return l = l !== null ? l.childLanes & ~a : 0, t && (l |= gt), l;
  }
  function Ur(l, t, a) {
    var e = t.pendingProps, u = !1, n = (t.flags & 128) !== 0, c;
    if ((c = n) || (c = l !== null && l.memoizedState === null ? !1 : (zl.current & 2) !== 0), c && (u = !0, t.flags &= -129), c = (t.flags & 32) !== 0, t.flags &= -33, l === null) {
      if (ll) {
        if (u ? Pt(t) : la(), ll) {
          var i = ml, s;
          if (s = i) {
            l: {
              for (s = i, i = Et; s.nodeType !== 8; ) {
                if (!i) {
                  i = null;
                  break l;
                }
                if (s = pt(
                  s.nextSibling
                ), s === null) {
                  i = null;
                  break l;
                }
              }
              i = s;
            }
            i !== null ? (t.memoizedState = {
              dehydrated: i,
              treeContext: Ea !== null ? { id: Rt, overflow: Ut } : null,
              retryLane: 536870912,
              hydrationErrors: null
            }, s = at(
              18,
              null,
              null,
              0
            ), s.stateNode = i, s.return = t, t.child = s, Ll = t, ml = null, s = !0) : s = !1;
          }
          s || xa(t);
        }
        if (i = t.memoizedState, i !== null && (i = i.dehydrated, i !== null))
          return Zi(i) ? t.lanes = 32 : t.lanes = 536870912, null;
        Yt(t);
      }
      return i = e.children, e = e.fallback, u ? (la(), u = t.mode, i = sn(
        { mode: "hidden", children: i },
        u
      ), e = Ta(
        e,
        u,
        a,
        null
      ), i.return = t, e.return = t, i.sibling = e, t.child = i, u = t.child, u.memoizedState = ui(a), u.childLanes = ni(
        l,
        c,
        a
      ), t.memoizedState = ei, e) : (Pt(t), ci(t, i));
    }
    if (s = l.memoizedState, s !== null && (i = s.dehydrated, i !== null)) {
      if (n)
        t.flags & 256 ? (Pt(t), t.flags &= -257, t = ii(
          l,
          t,
          a
        )) : t.memoizedState !== null ? (la(), t.child = l.child, t.flags |= 128, t = null) : (la(), u = e.fallback, i = t.mode, e = sn(
          { mode: "visible", children: e.children },
          i
        ), u = Ta(
          u,
          i,
          a,
          null
        ), u.flags |= 2, e.return = t, u.return = t, e.sibling = u, t.child = e, ce(
          t,
          l.child,
          null,
          a
        ), e = t.child, e.memoizedState = ui(a), e.childLanes = ni(
          l,
          c,
          a
        ), t.memoizedState = ei, t = u);
      else if (Pt(t), Zi(i)) {
        if (c = i.nextSibling && i.nextSibling.dataset, c) var m = c.dgst;
        c = m, e = Error(h(419)), e.stack = "", e.digest = c, Ye({ value: e, source: null, stack: null }), t = ii(
          l,
          t,
          a
        );
      } else if (Nl || Be(l, t, a, !1), c = (a & l.childLanes) !== 0, Nl || c) {
        if (c = sl, c !== null && (e = a & -a, e = (e & 42) !== 0 ? 1 : Vn(e), e = (e & (c.suspendedLanes | a)) !== 0 ? 0 : e, e !== 0 && e !== s.retryLane))
          throw s.retryLane = e, Wa(l, e), it(c, l, e), Er;
        i.data === "$?" || zi(), t = ii(
          l,
          t,
          a
        );
      } else
        i.data === "$?" ? (t.flags |= 192, t.child = l.child, t = null) : (l = s.treeContext, ml = pt(
          i.nextSibling
        ), Ll = t, ll = !0, za = null, Et = !1, l !== null && (yt[vt++] = Rt, yt[vt++] = Ut, yt[vt++] = Ea, Rt = l.id, Ut = l.overflow, Ea = t), t = ci(
          t,
          e.children
        ), t.flags |= 4096);
      return t;
    }
    return u ? (la(), u = e.fallback, i = t.mode, s = l.child, m = s.sibling, e = Dt(s, {
      mode: "hidden",
      children: e.children
    }), e.subtreeFlags = s.subtreeFlags & 65011712, m !== null ? u = Dt(m, u) : (u = Ta(
      u,
      i,
      a,
      null
    ), u.flags |= 2), u.return = t, e.return = t, e.sibling = u, t.child = e, e = u, u = t.child, i = l.child.memoizedState, i === null ? i = ui(a) : (s = i.cachePool, s !== null ? (m = Al._currentValue, s = s.parent !== m ? { parent: m, pool: m } : s) : s = bs(), i = {
      baseLanes: i.baseLanes | a,
      cachePool: s
    }), u.memoizedState = i, u.childLanes = ni(
      l,
      c,
      a
    ), t.memoizedState = ei, e) : (Pt(t), a = l.child, l = a.sibling, a = Dt(a, {
      mode: "visible",
      children: e.children
    }), a.return = t, a.sibling = null, l !== null && (c = t.deletions, c === null ? (t.deletions = [l], t.flags |= 16) : c.push(l)), t.child = a, t.memoizedState = null, a);
  }
  function ci(l, t) {
    return t = sn(
      { mode: "visible", children: t },
      l.mode
    ), t.return = l, l.child = t;
  }
  function sn(l, t) {
    return l = at(22, l, null, t), l.lanes = 0, l.stateNode = {
      _visibility: 1,
      _pendingMarkers: null,
      _retryCache: null,
      _transitions: null
    }, l;
  }
  function ii(l, t, a) {
    return ce(t, l.child, null, a), l = ci(
      t,
      t.pendingProps.children
    ), l.flags |= 2, t.memoizedState = null, l;
  }
  function Mr(l, t, a) {
    l.lanes |= t;
    var e = l.alternate;
    e !== null && (e.lanes |= t), zc(l.return, t, a);
  }
  function fi(l, t, a, e, u) {
    var n = l.memoizedState;
    n === null ? l.memoizedState = {
      isBackwards: t,
      rendering: null,
      renderingStartTime: 0,
      last: e,
      tail: a,
      tailMode: u
    } : (n.isBackwards = t, n.rendering = null, n.renderingStartTime = 0, n.last = e, n.tail = a, n.tailMode = u);
  }
  function qr(l, t, a) {
    var e = t.pendingProps, u = e.revealOrder, n = e.tail;
    if (Ul(l, t, e.children, a), e = zl.current, (e & 2) !== 0)
      e = e & 1 | 2, t.flags |= 128;
    else {
      if (l !== null && (l.flags & 128) !== 0)
        l: for (l = t.child; l !== null; ) {
          if (l.tag === 13)
            l.memoizedState !== null && Mr(l, a, t);
          else if (l.tag === 19)
            Mr(l, a, t);
          else if (l.child !== null) {
            l.child.return = l, l = l.child;
            continue;
          }
          if (l === t) break l;
          for (; l.sibling === null; ) {
            if (l.return === null || l.return === t)
              break l;
            l = l.return;
          }
          l.sibling.return = l.return, l = l.sibling;
        }
      e &= 1;
    }
    switch (O(zl, e), u) {
      case "forwards":
        for (a = t.child, u = null; a !== null; )
          l = a.alternate, l !== null && un(l) === null && (u = a), a = a.sibling;
        a = u, a === null ? (u = t.child, t.child = null) : (u = a.sibling, a.sibling = null), fi(
          t,
          !1,
          u,
          a,
          n
        );
        break;
      case "backwards":
        for (a = null, u = t.child, t.child = null; u !== null; ) {
          if (l = u.alternate, l !== null && un(l) === null) {
            t.child = u;
            break;
          }
          l = u.sibling, u.sibling = a, a = u, u = l;
        }
        fi(
          t,
          !0,
          a,
          null,
          n
        );
        break;
      case "together":
        fi(t, !1, null, null, void 0);
        break;
      default:
        t.memoizedState = null;
    }
    return t.child;
  }
  function Bt(l, t, a) {
    if (l !== null && (t.dependencies = l.dependencies), na |= t.lanes, (a & t.childLanes) === 0)
      if (l !== null) {
        if (Be(
          l,
          t,
          a,
          !1
        ), (a & t.childLanes) === 0)
          return null;
      } else return null;
    if (l !== null && t.child !== l.child)
      throw Error(h(153));
    if (t.child !== null) {
      for (l = t.child, a = Dt(l, l.pendingProps), t.child = a, a.return = t; l.sibling !== null; )
        l = l.sibling, a = a.sibling = Dt(l, l.pendingProps), a.return = t;
      a.sibling = null;
    }
    return t.child;
  }
  function si(l, t) {
    return (l.lanes & t) !== 0 ? !0 : (l = l.dependencies, !!(l !== null && Zu(l)));
  }
  function Bh(l, t, a) {
    switch (t.tag) {
      case 3:
        dl(t, t.stateNode.containerInfo), $t(t, Al, l.memoizedState.cache), He();
        break;
      case 27:
      case 5:
        Cn(t);
        break;
      case 4:
        dl(t, t.stateNode.containerInfo);
        break;
      case 10:
        $t(
          t,
          t.type,
          t.memoizedProps.value
        );
        break;
      case 13:
        var e = t.memoizedState;
        if (e !== null)
          return e.dehydrated !== null ? (Pt(t), t.flags |= 128, null) : (a & t.child.childLanes) !== 0 ? Ur(l, t, a) : (Pt(t), l = Bt(
            l,
            t,
            a
          ), l !== null ? l.sibling : null);
        Pt(t);
        break;
      case 19:
        var u = (l.flags & 128) !== 0;
        if (e = (a & t.childLanes) !== 0, e || (Be(
          l,
          t,
          a,
          !1
        ), e = (a & t.childLanes) !== 0), u) {
          if (e)
            return qr(
              l,
              t,
              a
            );
          t.flags |= 128;
        }
        if (u = t.memoizedState, u !== null && (u.rendering = null, u.tail = null, u.lastEffect = null), O(zl, zl.current), e) break;
        return null;
      case 22:
      case 23:
        return t.lanes = 0, Nr(l, t, a);
      case 24:
        $t(t, Al, l.memoizedState.cache);
    }
    return Bt(l, t, a);
  }
  function Hr(l, t, a) {
    if (l !== null)
      if (l.memoizedProps !== t.pendingProps)
        Nl = !0;
      else {
        if (!si(l, a) && (t.flags & 128) === 0)
          return Nl = !1, Bh(
            l,
            t,
            a
          );
        Nl = (l.flags & 131072) !== 0;
      }
    else
      Nl = !1, ll && (t.flags & 1048576) !== 0 && ds(t, Qu, t.index);
    switch (t.lanes = 0, t.tag) {
      case 16:
        l: {
          l = t.pendingProps;
          var e = t.elementType, u = e._init;
          if (e = u(e._payload), t.type = e, typeof e == "function")
            bc(e) ? (l = Ra(e, l), t.tag = 1, t = Dr(
              null,
              t,
              e,
              l,
              a
            )) : (t.tag = 0, t = ai(
              null,
              t,
              e,
              l,
              a
            ));
          else {
            if (e != null) {
              if (u = e.$$typeof, u === Ql) {
                t.tag = 11, t = Ar(
                  null,
                  t,
                  e,
                  l,
                  a
                );
                break l;
              } else if (u === Vl) {
                t.tag = 14, t = zr(
                  null,
                  t,
                  e,
                  l,
                  a
                );
                break l;
              }
            }
            throw t = ma(e) || e, Error(h(306, t, ""));
          }
        }
        return t;
      case 0:
        return ai(
          l,
          t,
          t.type,
          t.pendingProps,
          a
        );
      case 1:
        return e = t.type, u = Ra(
          e,
          t.pendingProps
        ), Dr(
          l,
          t,
          e,
          u,
          a
        );
      case 3:
        l: {
          if (dl(
            t,
            t.stateNode.containerInfo
          ), l === null) throw Error(h(387));
          e = t.pendingProps;
          var n = t.memoizedState;
          u = n.element, Uc(l, t), Le(t, e, null, a);
          var c = t.memoizedState;
          if (e = c.cache, $t(t, Al, e), e !== n.cache && xc(
            t,
            [Al],
            a,
            !0
          ), Ve(), e = c.element, n.isDehydrated)
            if (n = {
              element: e,
              isDehydrated: !1,
              cache: c.cache
            }, t.updateQueue.baseState = n, t.memoizedState = n, t.flags & 256) {
              t = Rr(
                l,
                t,
                e,
                a
              );
              break l;
            } else if (e !== u) {
              u = ot(
                Error(h(424)),
                t
              ), Ye(u), t = Rr(
                l,
                t,
                e,
                a
              );
              break l;
            } else {
              switch (l = t.stateNode.containerInfo, l.nodeType) {
                case 9:
                  l = l.body;
                  break;
                default:
                  l = l.nodeName === "HTML" ? l.ownerDocument.body : l;
              }
              for (ml = pt(l.firstChild), Ll = t, ll = !0, za = null, Et = !0, a = hr(
                t,
                null,
                e,
                a
              ), t.child = a; a; )
                a.flags = a.flags & -3 | 4096, a = a.sibling;
            }
          else {
            if (He(), e === u) {
              t = Bt(
                l,
                t,
                a
              );
              break l;
            }
            Ul(
              l,
              t,
              e,
              a
            );
          }
          t = t.child;
        }
        return t;
      case 26:
        return fn(l, t), l === null ? (a = Gd(
          t.type,
          null,
          t.pendingProps,
          null
        )) ? t.memoizedState = a : ll || (a = t.type, l = t.pendingProps, e = En(
          X.current
        ).createElement(a), e[Cl] = t, e[Jl] = l, ql(e, a, l), xl(e), t.stateNode = e) : t.memoizedState = Gd(
          t.type,
          l.memoizedProps,
          t.pendingProps,
          l.memoizedState
        ), null;
      case 27:
        return Cn(t), l === null && ll && (e = t.stateNode = Yd(
          t.type,
          t.pendingProps,
          X.current
        ), Ll = t, Et = !0, u = ml, sa(t.type) ? (Vi = u, ml = pt(
          e.firstChild
        )) : ml = u), Ul(
          l,
          t,
          t.pendingProps.children,
          a
        ), fn(l, t), l === null && (t.flags |= 4194304), t.child;
      case 5:
        return l === null && ll && ((u = e = ml) && (e = dy(
          e,
          t.type,
          t.pendingProps,
          Et
        ), e !== null ? (t.stateNode = e, Ll = t, ml = pt(
          e.firstChild
        ), Et = !1, u = !0) : u = !1), u || xa(t)), Cn(t), u = t.type, n = t.pendingProps, c = l !== null ? l.memoizedProps : null, e = n.children, Gi(u, n) ? e = null : c !== null && Gi(u, c) && (t.flags |= 32), t.memoizedState !== null && (u = Cc(
          l,
          t,
          jh,
          null,
          null,
          a
        ), ou._currentValue = u), fn(l, t), Ul(l, t, e, a), t.child;
      case 6:
        return l === null && ll && ((l = a = ml) && (a = oy(
          a,
          t.pendingProps,
          Et
        ), a !== null ? (t.stateNode = a, Ll = t, ml = null, l = !0) : l = !1), l || xa(t)), null;
      case 13:
        return Ur(l, t, a);
      case 4:
        return dl(
          t,
          t.stateNode.containerInfo
        ), e = t.pendingProps, l === null ? t.child = ce(
          t,
          null,
          e,
          a
        ) : Ul(
          l,
          t,
          e,
          a
        ), t.child;
      case 11:
        return Ar(
          l,
          t,
          t.type,
          t.pendingProps,
          a
        );
      case 7:
        return Ul(
          l,
          t,
          t.pendingProps,
          a
        ), t.child;
      case 8:
        return Ul(
          l,
          t,
          t.pendingProps.children,
          a
        ), t.child;
      case 12:
        return Ul(
          l,
          t,
          t.pendingProps.children,
          a
        ), t.child;
      case 10:
        return e = t.pendingProps, $t(t, t.type, e.value), Ul(
          l,
          t,
          e.children,
          a
        ), t.child;
      case 9:
        return u = t.type._context, e = t.pendingProps.children, Oa(t), u = Gl(u), e = e(u), t.flags |= 1, Ul(l, t, e, a), t.child;
      case 14:
        return zr(
          l,
          t,
          t.type,
          t.pendingProps,
          a
        );
      case 15:
        return xr(
          l,
          t,
          t.type,
          t.pendingProps,
          a
        );
      case 19:
        return qr(l, t, a);
      case 31:
        return e = t.pendingProps, a = t.mode, e = {
          mode: e.mode,
          children: e.children
        }, l === null ? (a = sn(
          e,
          a
        ), a.ref = t.ref, t.child = a, a.return = t, t = a) : (a = Dt(l.child, e), a.ref = t.ref, t.child = a, a.return = t, t = a), t;
      case 22:
        return Nr(l, t, a);
      case 24:
        return Oa(t), e = Gl(Al), l === null ? (u = jc(), u === null && (u = sl, n = Nc(), u.pooledCache = n, n.refCount++, n !== null && (u.pooledCacheLanes |= a), u = n), t.memoizedState = {
          parent: e,
          cache: u
        }, Rc(t), $t(t, Al, u)) : ((l.lanes & a) !== 0 && (Uc(l, t), Le(t, null, null, a), Ve()), u = l.memoizedState, n = t.memoizedState, u.parent !== e ? (u = { parent: e, cache: e }, t.memoizedState = u, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = u), $t(t, Al, e)) : (e = n.cache, $t(t, Al, e), e !== u.cache && xc(
          t,
          [Al],
          a,
          !0
        ))), Ul(
          l,
          t,
          t.pendingProps.children,
          a
        ), t.child;
      case 29:
        throw t.pendingProps;
    }
    throw Error(h(156, t.tag));
  }
  function Ct(l) {
    l.flags |= 4;
  }
  function Yr(l, t) {
    if (t.type !== "stylesheet" || (t.state.loading & 4) !== 0)
      l.flags &= -16777217;
    else if (l.flags |= 16777216, !Ld(t)) {
      if (t = mt.current, t !== null && ((W & 4194048) === W ? At !== null : (W & 62914560) !== W && (W & 536870912) === 0 || t !== At))
        throw Qe = Dc, _s;
      l.flags |= 8192;
    }
  }
  function rn(l, t) {
    t !== null && (l.flags |= 4), l.flags & 16384 && (t = l.tag !== 22 ? yf() : 536870912, l.lanes |= t, re |= t);
  }
  function Fe(l, t) {
    if (!ll)
      switch (l.tailMode) {
        case "hidden":
          t = l.tail;
          for (var a = null; t !== null; )
            t.alternate !== null && (a = t), t = t.sibling;
          a === null ? l.tail = null : a.sibling = null;
          break;
        case "collapsed":
          a = l.tail;
          for (var e = null; a !== null; )
            a.alternate !== null && (e = a), a = a.sibling;
          e === null ? t || l.tail === null ? l.tail = null : l.tail.sibling = null : e.sibling = null;
      }
  }
  function yl(l) {
    var t = l.alternate !== null && l.alternate.child === l.child, a = 0, e = 0;
    if (t)
      for (var u = l.child; u !== null; )
        a |= u.lanes | u.childLanes, e |= u.subtreeFlags & 65011712, e |= u.flags & 65011712, u.return = l, u = u.sibling;
    else
      for (u = l.child; u !== null; )
        a |= u.lanes | u.childLanes, e |= u.subtreeFlags, e |= u.flags, u.return = l, u = u.sibling;
    return l.subtreeFlags |= e, l.childLanes = a, t;
  }
  function Ch(l, t, a) {
    var e = t.pendingProps;
    switch (Tc(t), t.tag) {
      case 31:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return yl(t), null;
      case 1:
        return yl(t), null;
      case 3:
        return a = t.stateNode, e = null, l !== null && (e = l.memoizedState.cache), t.memoizedState.cache !== e && (t.flags |= 2048), qt(Al), Lt(), a.pendingContext && (a.context = a.pendingContext, a.pendingContext = null), (l === null || l.child === null) && (qe(t) ? Ct(t) : l === null || l.memoizedState.isDehydrated && (t.flags & 256) === 0 || (t.flags |= 1024, ys())), yl(t), null;
      case 26:
        return a = t.memoizedState, l === null ? (Ct(t), a !== null ? (yl(t), Yr(t, a)) : (yl(t), t.flags &= -16777217)) : a ? a !== l.memoizedState ? (Ct(t), yl(t), Yr(t, a)) : (yl(t), t.flags &= -16777217) : (l.memoizedProps !== e && Ct(t), yl(t), t.flags &= -16777217), null;
      case 27:
        Su(t), a = X.current;
        var u = t.type;
        if (l !== null && t.stateNode != null)
          l.memoizedProps !== e && Ct(t);
        else {
          if (!e) {
            if (t.stateNode === null)
              throw Error(h(166));
            return yl(t), null;
          }
          l = q.current, qe(t) ? os(t) : (l = Yd(u, e, a), t.stateNode = l, Ct(t));
        }
        return yl(t), null;
      case 5:
        if (Su(t), a = t.type, l !== null && t.stateNode != null)
          l.memoizedProps !== e && Ct(t);
        else {
          if (!e) {
            if (t.stateNode === null)
              throw Error(h(166));
            return yl(t), null;
          }
          if (l = q.current, qe(t))
            os(t);
          else {
            switch (u = En(
              X.current
            ), l) {
              case 1:
                l = u.createElementNS(
                  "http://www.w3.org/2000/svg",
                  a
                );
                break;
              case 2:
                l = u.createElementNS(
                  "http://www.w3.org/1998/Math/MathML",
                  a
                );
                break;
              default:
                switch (a) {
                  case "svg":
                    l = u.createElementNS(
                      "http://www.w3.org/2000/svg",
                      a
                    );
                    break;
                  case "math":
                    l = u.createElementNS(
                      "http://www.w3.org/1998/Math/MathML",
                      a
                    );
                    break;
                  case "script":
                    l = u.createElement("div"), l.innerHTML = "<script><\/script>", l = l.removeChild(l.firstChild);
                    break;
                  case "select":
                    l = typeof e.is == "string" ? u.createElement("select", { is: e.is }) : u.createElement("select"), e.multiple ? l.multiple = !0 : e.size && (l.size = e.size);
                    break;
                  default:
                    l = typeof e.is == "string" ? u.createElement(a, { is: e.is }) : u.createElement(a);
                }
            }
            l[Cl] = t, l[Jl] = e;
            l: for (u = t.child; u !== null; ) {
              if (u.tag === 5 || u.tag === 6)
                l.appendChild(u.stateNode);
              else if (u.tag !== 4 && u.tag !== 27 && u.child !== null) {
                u.child.return = u, u = u.child;
                continue;
              }
              if (u === t) break l;
              for (; u.sibling === null; ) {
                if (u.return === null || u.return === t)
                  break l;
                u = u.return;
              }
              u.sibling.return = u.return, u = u.sibling;
            }
            t.stateNode = l;
            l: switch (ql(l, a, e), a) {
              case "button":
              case "input":
              case "select":
              case "textarea":
                l = !!e.autoFocus;
                break l;
              case "img":
                l = !0;
                break l;
              default:
                l = !1;
            }
            l && Ct(t);
          }
        }
        return yl(t), t.flags &= -16777217, null;
      case 6:
        if (l && t.stateNode != null)
          l.memoizedProps !== e && Ct(t);
        else {
          if (typeof e != "string" && t.stateNode === null)
            throw Error(h(166));
          if (l = X.current, qe(t)) {
            if (l = t.stateNode, a = t.memoizedProps, e = null, u = Ll, u !== null)
              switch (u.tag) {
                case 27:
                case 5:
                  e = u.memoizedProps;
              }
            l[Cl] = t, l = !!(l.nodeValue === a || e !== null && e.suppressHydrationWarning === !0 || jd(l.nodeValue, a)), l || xa(t);
          } else
            l = En(l).createTextNode(
              e
            ), l[Cl] = t, t.stateNode = l;
        }
        return yl(t), null;
      case 13:
        if (e = t.memoizedState, l === null || l.memoizedState !== null && l.memoizedState.dehydrated !== null) {
          if (u = qe(t), e !== null && e.dehydrated !== null) {
            if (l === null) {
              if (!u) throw Error(h(318));
              if (u = t.memoizedState, u = u !== null ? u.dehydrated : null, !u) throw Error(h(317));
              u[Cl] = t;
            } else
              He(), (t.flags & 128) === 0 && (t.memoizedState = null), t.flags |= 4;
            yl(t), u = !1;
          } else
            u = ys(), l !== null && l.memoizedState !== null && (l.memoizedState.hydrationErrors = u), u = !0;
          if (!u)
            return t.flags & 256 ? (Yt(t), t) : (Yt(t), null);
        }
        if (Yt(t), (t.flags & 128) !== 0)
          return t.lanes = a, t;
        if (a = e !== null, l = l !== null && l.memoizedState !== null, a) {
          e = t.child, u = null, e.alternate !== null && e.alternate.memoizedState !== null && e.alternate.memoizedState.cachePool !== null && (u = e.alternate.memoizedState.cachePool.pool);
          var n = null;
          e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), n !== u && (e.flags |= 2048);
        }
        return a !== l && a && (t.child.flags |= 8192), rn(t, t.updateQueue), yl(t), null;
      case 4:
        return Lt(), l === null && qi(t.stateNode.containerInfo), yl(t), null;
      case 10:
        return qt(t.type), yl(t), null;
      case 19:
        if (D(zl), u = t.memoizedState, u === null) return yl(t), null;
        if (e = (t.flags & 128) !== 0, n = u.rendering, n === null)
          if (e) Fe(u, !1);
          else {
            if (gl !== 0 || l !== null && (l.flags & 128) !== 0)
              for (l = t.child; l !== null; ) {
                if (n = un(l), n !== null) {
                  for (t.flags |= 128, Fe(u, !1), l = n.updateQueue, t.updateQueue = l, rn(t, l), t.subtreeFlags = 0, l = a, a = t.child; a !== null; )
                    rs(a, l), a = a.sibling;
                  return O(
                    zl,
                    zl.current & 1 | 2
                  ), t.child;
                }
                l = l.sibling;
              }
            u.tail !== null && Tt() > hn && (t.flags |= 128, e = !0, Fe(u, !1), t.lanes = 4194304);
          }
        else {
          if (!e)
            if (l = un(n), l !== null) {
              if (t.flags |= 128, e = !0, l = l.updateQueue, t.updateQueue = l, rn(t, l), Fe(u, !0), u.tail === null && u.tailMode === "hidden" && !n.alternate && !ll)
                return yl(t), null;
            } else
              2 * Tt() - u.renderingStartTime > hn && a !== 536870912 && (t.flags |= 128, e = !0, Fe(u, !1), t.lanes = 4194304);
          u.isBackwards ? (n.sibling = t.child, t.child = n) : (l = u.last, l !== null ? l.sibling = n : t.child = n, u.last = n);
        }
        return u.tail !== null ? (t = u.tail, u.rendering = t, u.tail = t.sibling, u.renderingStartTime = Tt(), t.sibling = null, l = zl.current, O(zl, e ? l & 1 | 2 : l & 1), t) : (yl(t), null);
      case 22:
      case 23:
        return Yt(t), Yc(), e = t.memoizedState !== null, l !== null ? l.memoizedState !== null !== e && (t.flags |= 8192) : e && (t.flags |= 8192), e ? (a & 536870912) !== 0 && (t.flags & 128) === 0 && (yl(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : yl(t), a = t.updateQueue, a !== null && rn(t, a.retryQueue), a = null, l !== null && l.memoizedState !== null && l.memoizedState.cachePool !== null && (a = l.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== a && (t.flags |= 2048), l !== null && D(ja), null;
      case 24:
        return a = null, l !== null && (a = l.memoizedState.cache), t.memoizedState.cache !== a && (t.flags |= 2048), qt(Al), yl(t), null;
      case 25:
        return null;
      case 30:
        return null;
    }
    throw Error(h(156, t.tag));
  }
  function Gh(l, t) {
    switch (Tc(t), t.tag) {
      case 1:
        return l = t.flags, l & 65536 ? (t.flags = l & -65537 | 128, t) : null;
      case 3:
        return qt(Al), Lt(), l = t.flags, (l & 65536) !== 0 && (l & 128) === 0 ? (t.flags = l & -65537 | 128, t) : null;
      case 26:
      case 27:
      case 5:
        return Su(t), null;
      case 13:
        if (Yt(t), l = t.memoizedState, l !== null && l.dehydrated !== null) {
          if (t.alternate === null)
            throw Error(h(340));
          He();
        }
        return l = t.flags, l & 65536 ? (t.flags = l & -65537 | 128, t) : null;
      case 19:
        return D(zl), null;
      case 4:
        return Lt(), null;
      case 10:
        return qt(t.type), null;
      case 22:
      case 23:
        return Yt(t), Yc(), l !== null && D(ja), l = t.flags, l & 65536 ? (t.flags = l & -65537 | 128, t) : null;
      case 24:
        return qt(Al), null;
      case 25:
        return null;
      default:
        return null;
    }
  }
  function Br(l, t) {
    switch (Tc(t), t.tag) {
      case 3:
        qt(Al), Lt();
        break;
      case 26:
      case 27:
      case 5:
        Su(t);
        break;
      case 4:
        Lt();
        break;
      case 13:
        Yt(t);
        break;
      case 19:
        D(zl);
        break;
      case 10:
        qt(t.type);
        break;
      case 22:
      case 23:
        Yt(t), Yc(), l !== null && D(ja);
        break;
      case 24:
        qt(Al);
    }
  }
  function Ie(l, t) {
    try {
      var a = t.updateQueue, e = a !== null ? a.lastEffect : null;
      if (e !== null) {
        var u = e.next;
        a = u;
        do {
          if ((a.tag & l) === l) {
            e = void 0;
            var n = a.create, c = a.inst;
            e = n(), c.destroy = e;
          }
          a = a.next;
        } while (a !== u);
      }
    } catch (i) {
      il(t, t.return, i);
    }
  }
  function ta(l, t, a) {
    try {
      var e = t.updateQueue, u = e !== null ? e.lastEffect : null;
      if (u !== null) {
        var n = u.next;
        e = n;
        do {
          if ((e.tag & l) === l) {
            var c = e.inst, i = c.destroy;
            if (i !== void 0) {
              c.destroy = void 0, u = t;
              var s = a, m = i;
              try {
                m();
              } catch (_) {
                il(
                  u,
                  s,
                  _
                );
              }
            }
          }
          e = e.next;
        } while (e !== n);
      }
    } catch (_) {
      il(t, t.return, _);
    }
  }
  function Cr(l) {
    var t = l.updateQueue;
    if (t !== null) {
      var a = l.stateNode;
      try {
        zs(t, a);
      } catch (e) {
        il(l, l.return, e);
      }
    }
  }
  function Gr(l, t, a) {
    a.props = Ra(
      l.type,
      l.memoizedProps
    ), a.state = l.memoizedState;
    try {
      a.componentWillUnmount();
    } catch (e) {
      il(l, t, e);
    }
  }
  function Pe(l, t) {
    try {
      var a = l.ref;
      if (a !== null) {
        switch (l.tag) {
          case 26:
          case 27:
          case 5:
            var e = l.stateNode;
            break;
          case 30:
            e = l.stateNode;
            break;
          default:
            e = l.stateNode;
        }
        typeof a == "function" ? l.refCleanup = a(e) : a.current = e;
      }
    } catch (u) {
      il(l, t, u);
    }
  }
  function zt(l, t) {
    var a = l.ref, e = l.refCleanup;
    if (a !== null)
      if (typeof e == "function")
        try {
          e();
        } catch (u) {
          il(l, t, u);
        } finally {
          l.refCleanup = null, l = l.alternate, l != null && (l.refCleanup = null);
        }
      else if (typeof a == "function")
        try {
          a(null);
        } catch (u) {
          il(l, t, u);
        }
      else a.current = null;
  }
  function Xr(l) {
    var t = l.type, a = l.memoizedProps, e = l.stateNode;
    try {
      l: switch (t) {
        case "button":
        case "input":
        case "select":
        case "textarea":
          a.autoFocus && e.focus();
          break l;
        case "img":
          a.src ? e.src = a.src : a.srcSet && (e.srcset = a.srcSet);
      }
    } catch (u) {
      il(l, l.return, u);
    }
  }
  function ri(l, t, a) {
    try {
      var e = l.stateNode;
      cy(e, l.type, a, t), e[Jl] = t;
    } catch (u) {
      il(l, l.return, u);
    }
  }
  function Qr(l) {
    return l.tag === 5 || l.tag === 3 || l.tag === 26 || l.tag === 27 && sa(l.type) || l.tag === 4;
  }
  function di(l) {
    l: for (; ; ) {
      for (; l.sibling === null; ) {
        if (l.return === null || Qr(l.return)) return null;
        l = l.return;
      }
      for (l.sibling.return = l.return, l = l.sibling; l.tag !== 5 && l.tag !== 6 && l.tag !== 18; ) {
        if (l.tag === 27 && sa(l.type) || l.flags & 2 || l.child === null || l.tag === 4) continue l;
        l.child.return = l, l = l.child;
      }
      if (!(l.flags & 2)) return l.stateNode;
    }
  }
  function oi(l, t, a) {
    var e = l.tag;
    if (e === 5 || e === 6)
      l = l.stateNode, t ? (a.nodeType === 9 ? a.body : a.nodeName === "HTML" ? a.ownerDocument.body : a).insertBefore(l, t) : (t = a.nodeType === 9 ? a.body : a.nodeName === "HTML" ? a.ownerDocument.body : a, t.appendChild(l), a = a._reactRootContainer, a != null || t.onclick !== null || (t.onclick = Tn));
    else if (e !== 4 && (e === 27 && sa(l.type) && (a = l.stateNode, t = null), l = l.child, l !== null))
      for (oi(l, t, a), l = l.sibling; l !== null; )
        oi(l, t, a), l = l.sibling;
  }
  function dn(l, t, a) {
    var e = l.tag;
    if (e === 5 || e === 6)
      l = l.stateNode, t ? a.insertBefore(l, t) : a.appendChild(l);
    else if (e !== 4 && (e === 27 && sa(l.type) && (a = l.stateNode), l = l.child, l !== null))
      for (dn(l, t, a), l = l.sibling; l !== null; )
        dn(l, t, a), l = l.sibling;
  }
  function Zr(l) {
    var t = l.stateNode, a = l.memoizedProps;
    try {
      for (var e = l.type, u = t.attributes; u.length; )
        t.removeAttributeNode(u[0]);
      ql(t, e, a), t[Cl] = l, t[Jl] = a;
    } catch (n) {
      il(l, l.return, n);
    }
  }
  var Gt = !1, _l = !1, hi = !1, Vr = typeof WeakSet == "function" ? WeakSet : Set, Ol = null;
  function Xh(l, t) {
    if (l = l.containerInfo, Bi = jn, l = ls(l), dc(l)) {
      if ("selectionStart" in l)
        var a = {
          start: l.selectionStart,
          end: l.selectionEnd
        };
      else
        l: {
          a = (a = l.ownerDocument) && a.defaultView || window;
          var e = a.getSelection && a.getSelection();
          if (e && e.rangeCount !== 0) {
            a = e.anchorNode;
            var u = e.anchorOffset, n = e.focusNode;
            e = e.focusOffset;
            try {
              a.nodeType, n.nodeType;
            } catch {
              a = null;
              break l;
            }
            var c = 0, i = -1, s = -1, m = 0, _ = 0, E = l, g = null;
            t: for (; ; ) {
              for (var b; E !== a || u !== 0 && E.nodeType !== 3 || (i = c + u), E !== n || e !== 0 && E.nodeType !== 3 || (s = c + e), E.nodeType === 3 && (c += E.nodeValue.length), (b = E.firstChild) !== null; )
                g = E, E = b;
              for (; ; ) {
                if (E === l) break t;
                if (g === a && ++m === u && (i = c), g === n && ++_ === e && (s = c), (b = E.nextSibling) !== null) break;
                E = g, g = E.parentNode;
              }
              E = b;
            }
            a = i === -1 || s === -1 ? null : { start: i, end: s };
          } else a = null;
        }
      a = a || { start: 0, end: 0 };
    } else a = null;
    for (Ci = { focusedElem: l, selectionRange: a }, jn = !1, Ol = t; Ol !== null; )
      if (t = Ol, l = t.child, (t.subtreeFlags & 1024) !== 0 && l !== null)
        l.return = t, Ol = l;
      else
        for (; Ol !== null; ) {
          switch (t = Ol, n = t.alternate, l = t.flags, t.tag) {
            case 0:
              break;
            case 11:
            case 15:
              break;
            case 1:
              if ((l & 1024) !== 0 && n !== null) {
                l = void 0, a = t, u = n.memoizedProps, n = n.memoizedState, e = a.stateNode;
                try {
                  var G = Ra(
                    a.type,
                    u,
                    a.elementType === a.type
                  );
                  l = e.getSnapshotBeforeUpdate(
                    G,
                    n
                  ), e.__reactInternalSnapshotBeforeUpdate = l;
                } catch (H) {
                  il(
                    a,
                    a.return,
                    H
                  );
                }
              }
              break;
            case 3:
              if ((l & 1024) !== 0) {
                if (l = t.stateNode.containerInfo, a = l.nodeType, a === 9)
                  Qi(l);
                else if (a === 1)
                  switch (l.nodeName) {
                    case "HEAD":
                    case "HTML":
                    case "BODY":
                      Qi(l);
                      break;
                    default:
                      l.textContent = "";
                  }
              }
              break;
            case 5:
            case 26:
            case 27:
            case 6:
            case 4:
            case 17:
              break;
            default:
              if ((l & 1024) !== 0) throw Error(h(163));
          }
          if (l = t.sibling, l !== null) {
            l.return = t.return, Ol = l;
            break;
          }
          Ol = t.return;
        }
  }
  function Lr(l, t, a) {
    var e = a.flags;
    switch (a.tag) {
      case 0:
      case 11:
      case 15:
        aa(l, a), e & 4 && Ie(5, a);
        break;
      case 1:
        if (aa(l, a), e & 4)
          if (l = a.stateNode, t === null)
            try {
              l.componentDidMount();
            } catch (c) {
              il(a, a.return, c);
            }
          else {
            var u = Ra(
              a.type,
              t.memoizedProps
            );
            t = t.memoizedState;
            try {
              l.componentDidUpdate(
                u,
                t,
                l.__reactInternalSnapshotBeforeUpdate
              );
            } catch (c) {
              il(
                a,
                a.return,
                c
              );
            }
          }
        e & 64 && Cr(a), e & 512 && Pe(a, a.return);
        break;
      case 3:
        if (aa(l, a), e & 64 && (l = a.updateQueue, l !== null)) {
          if (t = null, a.child !== null)
            switch (a.child.tag) {
              case 27:
              case 5:
                t = a.child.stateNode;
                break;
              case 1:
                t = a.child.stateNode;
            }
          try {
            zs(l, t);
          } catch (c) {
            il(a, a.return, c);
          }
        }
        break;
      case 27:
        t === null && e & 4 && Zr(a);
      case 26:
      case 5:
        aa(l, a), t === null && e & 4 && Xr(a), e & 512 && Pe(a, a.return);
        break;
      case 12:
        aa(l, a);
        break;
      case 13:
        aa(l, a), e & 4 && kr(l, a), e & 64 && (l = a.memoizedState, l !== null && (l = l.dehydrated, l !== null && (a = Wh.bind(
          null,
          a
        ), hy(l, a))));
        break;
      case 22:
        if (e = a.memoizedState !== null || Gt, !e) {
          t = t !== null && t.memoizedState !== null || _l, u = Gt;
          var n = _l;
          Gt = e, (_l = t) && !n ? ea(
            l,
            a,
            (a.subtreeFlags & 8772) !== 0
          ) : aa(l, a), Gt = u, _l = n;
        }
        break;
      case 30:
        break;
      default:
        aa(l, a);
    }
  }
  function Kr(l) {
    var t = l.alternate;
    t !== null && (l.alternate = null, Kr(t)), l.child = null, l.deletions = null, l.sibling = null, l.tag === 5 && (t = l.stateNode, t !== null && Jn(t)), l.stateNode = null, l.return = null, l.dependencies = null, l.memoizedProps = null, l.memoizedState = null, l.pendingProps = null, l.stateNode = null, l.updateQueue = null;
  }
  var ol = null, Wl = !1;
  function Xt(l, t, a) {
    for (a = a.child; a !== null; )
      Jr(l, t, a), a = a.sibling;
  }
  function Jr(l, t, a) {
    if (Pl && typeof Pl.onCommitFiberUnmount == "function")
      try {
        Pl.onCommitFiberUnmount(Se, a);
      } catch {
      }
    switch (a.tag) {
      case 26:
        _l || zt(a, t), Xt(
          l,
          t,
          a
        ), a.memoizedState ? a.memoizedState.count-- : a.stateNode && (a = a.stateNode, a.parentNode.removeChild(a));
        break;
      case 27:
        _l || zt(a, t);
        var e = ol, u = Wl;
        sa(a.type) && (ol = a.stateNode, Wl = !1), Xt(
          l,
          t,
          a
        ), fu(a.stateNode), ol = e, Wl = u;
        break;
      case 5:
        _l || zt(a, t);
      case 6:
        if (e = ol, u = Wl, ol = null, Xt(
          l,
          t,
          a
        ), ol = e, Wl = u, ol !== null)
          if (Wl)
            try {
              (ol.nodeType === 9 ? ol.body : ol.nodeName === "HTML" ? ol.ownerDocument.body : ol).removeChild(a.stateNode);
            } catch (n) {
              il(
                a,
                t,
                n
              );
            }
          else
            try {
              ol.removeChild(a.stateNode);
            } catch (n) {
              il(
                a,
                t,
                n
              );
            }
        break;
      case 18:
        ol !== null && (Wl ? (l = ol, qd(
          l.nodeType === 9 ? l.body : l.nodeName === "HTML" ? l.ownerDocument.body : l,
          a.stateNode
        ), mu(l)) : qd(ol, a.stateNode));
        break;
      case 4:
        e = ol, u = Wl, ol = a.stateNode.containerInfo, Wl = !0, Xt(
          l,
          t,
          a
        ), ol = e, Wl = u;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        _l || ta(2, a, t), _l || ta(4, a, t), Xt(
          l,
          t,
          a
        );
        break;
      case 1:
        _l || (zt(a, t), e = a.stateNode, typeof e.componentWillUnmount == "function" && Gr(
          a,
          t,
          e
        )), Xt(
          l,
          t,
          a
        );
        break;
      case 21:
        Xt(
          l,
          t,
          a
        );
        break;
      case 22:
        _l = (e = _l) || a.memoizedState !== null, Xt(
          l,
          t,
          a
        ), _l = e;
        break;
      default:
        Xt(
          l,
          t,
          a
        );
    }
  }
  function kr(l, t) {
    if (t.memoizedState === null && (l = t.alternate, l !== null && (l = l.memoizedState, l !== null && (l = l.dehydrated, l !== null))))
      try {
        mu(l);
      } catch (a) {
        il(t, t.return, a);
      }
  }
  function Qh(l) {
    switch (l.tag) {
      case 13:
      case 19:
        var t = l.stateNode;
        return t === null && (t = l.stateNode = new Vr()), t;
      case 22:
        return l = l.stateNode, t = l._retryCache, t === null && (t = l._retryCache = new Vr()), t;
      default:
        throw Error(h(435, l.tag));
    }
  }
  function yi(l, t) {
    var a = Qh(l);
    t.forEach(function(e) {
      var u = wh.bind(null, l, e);
      a.has(e) || (a.add(e), e.then(u, u));
    });
  }
  function et(l, t) {
    var a = t.deletions;
    if (a !== null)
      for (var e = 0; e < a.length; e++) {
        var u = a[e], n = l, c = t, i = c;
        l: for (; i !== null; ) {
          switch (i.tag) {
            case 27:
              if (sa(i.type)) {
                ol = i.stateNode, Wl = !1;
                break l;
              }
              break;
            case 5:
              ol = i.stateNode, Wl = !1;
              break l;
            case 3:
            case 4:
              ol = i.stateNode.containerInfo, Wl = !0;
              break l;
          }
          i = i.return;
        }
        if (ol === null) throw Error(h(160));
        Jr(n, c, u), ol = null, Wl = !1, n = u.alternate, n !== null && (n.return = null), u.return = null;
      }
    if (t.subtreeFlags & 13878)
      for (t = t.child; t !== null; )
        $r(t, l), t = t.sibling;
  }
  var St = null;
  function $r(l, t) {
    var a = l.alternate, e = l.flags;
    switch (l.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        et(t, l), ut(l), e & 4 && (ta(3, l, l.return), Ie(3, l), ta(5, l, l.return));
        break;
      case 1:
        et(t, l), ut(l), e & 512 && (_l || a === null || zt(a, a.return)), e & 64 && Gt && (l = l.updateQueue, l !== null && (e = l.callbacks, e !== null && (a = l.shared.hiddenCallbacks, l.shared.hiddenCallbacks = a === null ? e : a.concat(e))));
        break;
      case 26:
        var u = St;
        if (et(t, l), ut(l), e & 512 && (_l || a === null || zt(a, a.return)), e & 4) {
          var n = a !== null ? a.memoizedState : null;
          if (e = l.memoizedState, a === null)
            if (e === null)
              if (l.stateNode === null) {
                l: {
                  e = l.type, a = l.memoizedProps, u = u.ownerDocument || u;
                  t: switch (e) {
                    case "title":
                      n = u.getElementsByTagName("title")[0], (!n || n[Ee] || n[Cl] || n.namespaceURI === "http://www.w3.org/2000/svg" || n.hasAttribute("itemprop")) && (n = u.createElement(e), u.head.insertBefore(
                        n,
                        u.querySelector("head > title")
                      )), ql(n, e, a), n[Cl] = l, xl(n), e = n;
                      break l;
                    case "link":
                      var c = Zd(
                        "link",
                        "href",
                        u
                      ).get(e + (a.href || ""));
                      if (c) {
                        for (var i = 0; i < c.length; i++)
                          if (n = c[i], n.getAttribute("href") === (a.href == null || a.href === "" ? null : a.href) && n.getAttribute("rel") === (a.rel == null ? null : a.rel) && n.getAttribute("title") === (a.title == null ? null : a.title) && n.getAttribute("crossorigin") === (a.crossOrigin == null ? null : a.crossOrigin)) {
                            c.splice(i, 1);
                            break t;
                          }
                      }
                      n = u.createElement(e), ql(n, e, a), u.head.appendChild(n);
                      break;
                    case "meta":
                      if (c = Zd(
                        "meta",
                        "content",
                        u
                      ).get(e + (a.content || ""))) {
                        for (i = 0; i < c.length; i++)
                          if (n = c[i], n.getAttribute("content") === (a.content == null ? null : "" + a.content) && n.getAttribute("name") === (a.name == null ? null : a.name) && n.getAttribute("property") === (a.property == null ? null : a.property) && n.getAttribute("http-equiv") === (a.httpEquiv == null ? null : a.httpEquiv) && n.getAttribute("charset") === (a.charSet == null ? null : a.charSet)) {
                            c.splice(i, 1);
                            break t;
                          }
                      }
                      n = u.createElement(e), ql(n, e, a), u.head.appendChild(n);
                      break;
                    default:
                      throw Error(h(468, e));
                  }
                  n[Cl] = l, xl(n), e = n;
                }
                l.stateNode = e;
              } else
                Vd(
                  u,
                  l.type,
                  l.stateNode
                );
            else
              l.stateNode = Qd(
                u,
                e,
                l.memoizedProps
              );
          else
            n !== e ? (n === null ? a.stateNode !== null && (a = a.stateNode, a.parentNode.removeChild(a)) : n.count--, e === null ? Vd(
              u,
              l.type,
              l.stateNode
            ) : Qd(
              u,
              e,
              l.memoizedProps
            )) : e === null && l.stateNode !== null && ri(
              l,
              l.memoizedProps,
              a.memoizedProps
            );
        }
        break;
      case 27:
        et(t, l), ut(l), e & 512 && (_l || a === null || zt(a, a.return)), a !== null && e & 4 && ri(
          l,
          l.memoizedProps,
          a.memoizedProps
        );
        break;
      case 5:
        if (et(t, l), ut(l), e & 512 && (_l || a === null || zt(a, a.return)), l.flags & 32) {
          u = l.stateNode;
          try {
            Za(u, "");
          } catch (b) {
            il(l, l.return, b);
          }
        }
        e & 4 && l.stateNode != null && (u = l.memoizedProps, ri(
          l,
          u,
          a !== null ? a.memoizedProps : u
        )), e & 1024 && (hi = !0);
        break;
      case 6:
        if (et(t, l), ut(l), e & 4) {
          if (l.stateNode === null)
            throw Error(h(162));
          e = l.memoizedProps, a = l.stateNode;
          try {
            a.nodeValue = e;
          } catch (b) {
            il(l, l.return, b);
          }
        }
        break;
      case 3:
        if (xn = null, u = St, St = An(t.containerInfo), et(t, l), St = u, ut(l), e & 4 && a !== null && a.memoizedState.isDehydrated)
          try {
            mu(t.containerInfo);
          } catch (b) {
            il(l, l.return, b);
          }
        hi && (hi = !1, Wr(l));
        break;
      case 4:
        e = St, St = An(
          l.stateNode.containerInfo
        ), et(t, l), ut(l), St = e;
        break;
      case 12:
        et(t, l), ut(l);
        break;
      case 13:
        et(t, l), ut(l), l.child.flags & 8192 && l.memoizedState !== null != (a !== null && a.memoizedState !== null) && (Si = Tt()), e & 4 && (e = l.updateQueue, e !== null && (l.updateQueue = null, yi(l, e)));
        break;
      case 22:
        u = l.memoizedState !== null;
        var s = a !== null && a.memoizedState !== null, m = Gt, _ = _l;
        if (Gt = m || u, _l = _ || s, et(t, l), _l = _, Gt = m, ut(l), e & 8192)
          l: for (t = l.stateNode, t._visibility = u ? t._visibility & -2 : t._visibility | 1, u && (a === null || s || Gt || _l || Ua(l)), a = null, t = l; ; ) {
            if (t.tag === 5 || t.tag === 26) {
              if (a === null) {
                s = a = t;
                try {
                  if (n = s.stateNode, u)
                    c = n.style, typeof c.setProperty == "function" ? c.setProperty("display", "none", "important") : c.display = "none";
                  else {
                    i = s.stateNode;
                    var E = s.memoizedProps.style, g = E != null && E.hasOwnProperty("display") ? E.display : null;
                    i.style.display = g == null || typeof g == "boolean" ? "" : ("" + g).trim();
                  }
                } catch (b) {
                  il(s, s.return, b);
                }
              }
            } else if (t.tag === 6) {
              if (a === null) {
                s = t;
                try {
                  s.stateNode.nodeValue = u ? "" : s.memoizedProps;
                } catch (b) {
                  il(s, s.return, b);
                }
              }
            } else if ((t.tag !== 22 && t.tag !== 23 || t.memoizedState === null || t === l) && t.child !== null) {
              t.child.return = t, t = t.child;
              continue;
            }
            if (t === l) break l;
            for (; t.sibling === null; ) {
              if (t.return === null || t.return === l) break l;
              a === t && (a = null), t = t.return;
            }
            a === t && (a = null), t.sibling.return = t.return, t = t.sibling;
          }
        e & 4 && (e = l.updateQueue, e !== null && (a = e.retryQueue, a !== null && (e.retryQueue = null, yi(l, a))));
        break;
      case 19:
        et(t, l), ut(l), e & 4 && (e = l.updateQueue, e !== null && (l.updateQueue = null, yi(l, e)));
        break;
      case 30:
        break;
      case 21:
        break;
      default:
        et(t, l), ut(l);
    }
  }
  function ut(l) {
    var t = l.flags;
    if (t & 2) {
      try {
        for (var a, e = l.return; e !== null; ) {
          if (Qr(e)) {
            a = e;
            break;
          }
          e = e.return;
        }
        if (a == null) throw Error(h(160));
        switch (a.tag) {
          case 27:
            var u = a.stateNode, n = di(l);
            dn(l, n, u);
            break;
          case 5:
            var c = a.stateNode;
            a.flags & 32 && (Za(c, ""), a.flags &= -33);
            var i = di(l);
            dn(l, i, c);
            break;
          case 3:
          case 4:
            var s = a.stateNode.containerInfo, m = di(l);
            oi(
              l,
              m,
              s
            );
            break;
          default:
            throw Error(h(161));
        }
      } catch (_) {
        il(l, l.return, _);
      }
      l.flags &= -3;
    }
    t & 4096 && (l.flags &= -4097);
  }
  function Wr(l) {
    if (l.subtreeFlags & 1024)
      for (l = l.child; l !== null; ) {
        var t = l;
        Wr(t), t.tag === 5 && t.flags & 1024 && t.stateNode.reset(), l = l.sibling;
      }
  }
  function aa(l, t) {
    if (t.subtreeFlags & 8772)
      for (t = t.child; t !== null; )
        Lr(l, t.alternate, t), t = t.sibling;
  }
  function Ua(l) {
    for (l = l.child; l !== null; ) {
      var t = l;
      switch (t.tag) {
        case 0:
        case 11:
        case 14:
        case 15:
          ta(4, t, t.return), Ua(t);
          break;
        case 1:
          zt(t, t.return);
          var a = t.stateNode;
          typeof a.componentWillUnmount == "function" && Gr(
            t,
            t.return,
            a
          ), Ua(t);
          break;
        case 27:
          fu(t.stateNode);
        case 26:
        case 5:
          zt(t, t.return), Ua(t);
          break;
        case 22:
          t.memoizedState === null && Ua(t);
          break;
        case 30:
          Ua(t);
          break;
        default:
          Ua(t);
      }
      l = l.sibling;
    }
  }
  function ea(l, t, a) {
    for (a = a && (t.subtreeFlags & 8772) !== 0, t = t.child; t !== null; ) {
      var e = t.alternate, u = l, n = t, c = n.flags;
      switch (n.tag) {
        case 0:
        case 11:
        case 15:
          ea(
            u,
            n,
            a
          ), Ie(4, n);
          break;
        case 1:
          if (ea(
            u,
            n,
            a
          ), e = n, u = e.stateNode, typeof u.componentDidMount == "function")
            try {
              u.componentDidMount();
            } catch (m) {
              il(e, e.return, m);
            }
          if (e = n, u = e.updateQueue, u !== null) {
            var i = e.stateNode;
            try {
              var s = u.shared.hiddenCallbacks;
              if (s !== null)
                for (u.shared.hiddenCallbacks = null, u = 0; u < s.length; u++)
                  As(s[u], i);
            } catch (m) {
              il(e, e.return, m);
            }
          }
          a && c & 64 && Cr(n), Pe(n, n.return);
          break;
        case 27:
          Zr(n);
        case 26:
        case 5:
          ea(
            u,
            n,
            a
          ), a && e === null && c & 4 && Xr(n), Pe(n, n.return);
          break;
        case 12:
          ea(
            u,
            n,
            a
          );
          break;
        case 13:
          ea(
            u,
            n,
            a
          ), a && c & 4 && kr(u, n);
          break;
        case 22:
          n.memoizedState === null && ea(
            u,
            n,
            a
          ), Pe(n, n.return);
          break;
        case 30:
          break;
        default:
          ea(
            u,
            n,
            a
          );
      }
      t = t.sibling;
    }
  }
  function vi(l, t) {
    var a = null;
    l !== null && l.memoizedState !== null && l.memoizedState.cachePool !== null && (a = l.memoizedState.cachePool.pool), l = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (l = t.memoizedState.cachePool.pool), l !== a && (l != null && l.refCount++, a != null && Ce(a));
  }
  function mi(l, t) {
    l = null, t.alternate !== null && (l = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== l && (t.refCount++, l != null && Ce(l));
  }
  function xt(l, t, a, e) {
    if (t.subtreeFlags & 10256)
      for (t = t.child; t !== null; )
        wr(
          l,
          t,
          a,
          e
        ), t = t.sibling;
  }
  function wr(l, t, a, e) {
    var u = t.flags;
    switch (t.tag) {
      case 0:
      case 11:
      case 15:
        xt(
          l,
          t,
          a,
          e
        ), u & 2048 && Ie(9, t);
        break;
      case 1:
        xt(
          l,
          t,
          a,
          e
        );
        break;
      case 3:
        xt(
          l,
          t,
          a,
          e
        ), u & 2048 && (l = null, t.alternate !== null && (l = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== l && (t.refCount++, l != null && Ce(l)));
        break;
      case 12:
        if (u & 2048) {
          xt(
            l,
            t,
            a,
            e
          ), l = t.stateNode;
          try {
            var n = t.memoizedProps, c = n.id, i = n.onPostCommit;
            typeof i == "function" && i(
              c,
              t.alternate === null ? "mount" : "update",
              l.passiveEffectDuration,
              -0
            );
          } catch (s) {
            il(t, t.return, s);
          }
        } else
          xt(
            l,
            t,
            a,
            e
          );
        break;
      case 13:
        xt(
          l,
          t,
          a,
          e
        );
        break;
      case 23:
        break;
      case 22:
        n = t.stateNode, c = t.alternate, t.memoizedState !== null ? n._visibility & 2 ? xt(
          l,
          t,
          a,
          e
        ) : lu(l, t) : n._visibility & 2 ? xt(
          l,
          t,
          a,
          e
        ) : (n._visibility |= 2, ie(
          l,
          t,
          a,
          e,
          (t.subtreeFlags & 10256) !== 0
        )), u & 2048 && vi(c, t);
        break;
      case 24:
        xt(
          l,
          t,
          a,
          e
        ), u & 2048 && mi(t.alternate, t);
        break;
      default:
        xt(
          l,
          t,
          a,
          e
        );
    }
  }
  function ie(l, t, a, e, u) {
    for (u = u && (t.subtreeFlags & 10256) !== 0, t = t.child; t !== null; ) {
      var n = l, c = t, i = a, s = e, m = c.flags;
      switch (c.tag) {
        case 0:
        case 11:
        case 15:
          ie(
            n,
            c,
            i,
            s,
            u
          ), Ie(8, c);
          break;
        case 23:
          break;
        case 22:
          var _ = c.stateNode;
          c.memoizedState !== null ? _._visibility & 2 ? ie(
            n,
            c,
            i,
            s,
            u
          ) : lu(
            n,
            c
          ) : (_._visibility |= 2, ie(
            n,
            c,
            i,
            s,
            u
          )), u && m & 2048 && vi(
            c.alternate,
            c
          );
          break;
        case 24:
          ie(
            n,
            c,
            i,
            s,
            u
          ), u && m & 2048 && mi(c.alternate, c);
          break;
        default:
          ie(
            n,
            c,
            i,
            s,
            u
          );
      }
      t = t.sibling;
    }
  }
  function lu(l, t) {
    if (t.subtreeFlags & 10256)
      for (t = t.child; t !== null; ) {
        var a = l, e = t, u = e.flags;
        switch (e.tag) {
          case 22:
            lu(a, e), u & 2048 && vi(
              e.alternate,
              e
            );
            break;
          case 24:
            lu(a, e), u & 2048 && mi(e.alternate, e);
            break;
          default:
            lu(a, e);
        }
        t = t.sibling;
      }
  }
  var tu = 8192;
  function fe(l) {
    if (l.subtreeFlags & tu)
      for (l = l.child; l !== null; )
        Fr(l), l = l.sibling;
  }
  function Fr(l) {
    switch (l.tag) {
      case 26:
        fe(l), l.flags & tu && l.memoizedState !== null && xy(
          St,
          l.memoizedState,
          l.memoizedProps
        );
        break;
      case 5:
        fe(l);
        break;
      case 3:
      case 4:
        var t = St;
        St = An(l.stateNode.containerInfo), fe(l), St = t;
        break;
      case 22:
        l.memoizedState === null && (t = l.alternate, t !== null && t.memoizedState !== null ? (t = tu, tu = 16777216, fe(l), tu = t) : fe(l));
        break;
      default:
        fe(l);
    }
  }
  function Ir(l) {
    var t = l.alternate;
    if (t !== null && (l = t.child, l !== null)) {
      t.child = null;
      do
        t = l.sibling, l.sibling = null, l = t;
      while (l !== null);
    }
  }
  function au(l) {
    var t = l.deletions;
    if ((l.flags & 16) !== 0) {
      if (t !== null)
        for (var a = 0; a < t.length; a++) {
          var e = t[a];
          Ol = e, ld(
            e,
            l
          );
        }
      Ir(l);
    }
    if (l.subtreeFlags & 10256)
      for (l = l.child; l !== null; )
        Pr(l), l = l.sibling;
  }
  function Pr(l) {
    switch (l.tag) {
      case 0:
      case 11:
      case 15:
        au(l), l.flags & 2048 && ta(9, l, l.return);
        break;
      case 3:
        au(l);
        break;
      case 12:
        au(l);
        break;
      case 22:
        var t = l.stateNode;
        l.memoizedState !== null && t._visibility & 2 && (l.return === null || l.return.tag !== 13) ? (t._visibility &= -3, on(l)) : au(l);
        break;
      default:
        au(l);
    }
  }
  function on(l) {
    var t = l.deletions;
    if ((l.flags & 16) !== 0) {
      if (t !== null)
        for (var a = 0; a < t.length; a++) {
          var e = t[a];
          Ol = e, ld(
            e,
            l
          );
        }
      Ir(l);
    }
    for (l = l.child; l !== null; ) {
      switch (t = l, t.tag) {
        case 0:
        case 11:
        case 15:
          ta(8, t, t.return), on(t);
          break;
        case 22:
          a = t.stateNode, a._visibility & 2 && (a._visibility &= -3, on(t));
          break;
        default:
          on(t);
      }
      l = l.sibling;
    }
  }
  function ld(l, t) {
    for (; Ol !== null; ) {
      var a = Ol;
      switch (a.tag) {
        case 0:
        case 11:
        case 15:
          ta(8, a, t);
          break;
        case 23:
        case 22:
          if (a.memoizedState !== null && a.memoizedState.cachePool !== null) {
            var e = a.memoizedState.cachePool.pool;
            e != null && e.refCount++;
          }
          break;
        case 24:
          Ce(a.memoizedState.cache);
      }
      if (e = a.child, e !== null) e.return = a, Ol = e;
      else
        l: for (a = l; Ol !== null; ) {
          e = Ol;
          var u = e.sibling, n = e.return;
          if (Kr(e), e === a) {
            Ol = null;
            break l;
          }
          if (u !== null) {
            u.return = n, Ol = u;
            break l;
          }
          Ol = n;
        }
    }
  }
  var Zh = {
    getCacheForType: function(l) {
      var t = Gl(Al), a = t.data.get(l);
      return a === void 0 && (a = l(), t.data.set(l, a)), a;
    }
  }, Vh = typeof WeakMap == "function" ? WeakMap : Map, tl = 0, sl = null, J = null, W = 0, al = 0, nt = null, ua = !1, se = !1, gi = !1, Qt = 0, gl = 0, na = 0, Ma = 0, bi = 0, gt = 0, re = 0, eu = null, wl = null, _i = !1, Si = 0, hn = 1 / 0, yn = null, ca = null, Ml = 0, ia = null, de = null, oe = 0, pi = 0, Ti = null, td = null, uu = 0, Ei = null;
  function ct() {
    if ((tl & 2) !== 0 && W !== 0)
      return W & -W;
    if (S.T !== null) {
      var l = Pa;
      return l !== 0 ? l : Di();
    }
    return gf();
  }
  function ad() {
    gt === 0 && (gt = (W & 536870912) === 0 || ll ? hf() : 536870912);
    var l = mt.current;
    return l !== null && (l.flags |= 32), gt;
  }
  function it(l, t, a) {
    (l === sl && (al === 2 || al === 9) || l.cancelPendingCommit !== null) && (he(l, 0), fa(
      l,
      W,
      gt,
      !1
    )), Te(l, a), ((tl & 2) === 0 || l !== sl) && (l === sl && ((tl & 2) === 0 && (Ma |= a), gl === 4 && fa(
      l,
      W,
      gt,
      !1
    )), Nt(l));
  }
  function ed(l, t, a) {
    if ((tl & 6) !== 0) throw Error(h(327));
    var e = !a && (t & 124) === 0 && (t & l.expiredLanes) === 0 || pe(l, t), u = e ? Jh(l, t) : xi(l, t, !0), n = e;
    do {
      if (u === 0) {
        se && !e && fa(l, t, 0, !1);
        break;
      } else {
        if (a = l.current.alternate, n && !Lh(a)) {
          u = xi(l, t, !1), n = !1;
          continue;
        }
        if (u === 2) {
          if (n = t, l.errorRecoveryDisabledLanes & n)
            var c = 0;
          else
            c = l.pendingLanes & -536870913, c = c !== 0 ? c : c & 536870912 ? 536870912 : 0;
          if (c !== 0) {
            t = c;
            l: {
              var i = l;
              u = eu;
              var s = i.current.memoizedState.isDehydrated;
              if (s && (he(i, c).flags |= 256), c = xi(
                i,
                c,
                !1
              ), c !== 2) {
                if (gi && !s) {
                  i.errorRecoveryDisabledLanes |= n, Ma |= n, u = 4;
                  break l;
                }
                n = wl, wl = u, n !== null && (wl === null ? wl = n : wl.push.apply(
                  wl,
                  n
                ));
              }
              u = c;
            }
            if (n = !1, u !== 2) continue;
          }
        }
        if (u === 1) {
          he(l, 0), fa(l, t, 0, !0);
          break;
        }
        l: {
          switch (e = l, n = u, n) {
            case 0:
            case 1:
              throw Error(h(345));
            case 4:
              if ((t & 4194048) !== t) break;
            case 6:
              fa(
                e,
                t,
                gt,
                !ua
              );
              break l;
            case 2:
              wl = null;
              break;
            case 3:
            case 5:
              break;
            default:
              throw Error(h(329));
          }
          if ((t & 62914560) === t && (u = Si + 300 - Tt(), 10 < u)) {
            if (fa(
              e,
              t,
              gt,
              !ua
            ), Au(e, 0, !0) !== 0) break l;
            e.timeoutHandle = Ud(
              ud.bind(
                null,
                e,
                a,
                wl,
                yn,
                _i,
                t,
                gt,
                Ma,
                re,
                ua,
                n,
                2,
                -0,
                0
              ),
              u
            );
            break l;
          }
          ud(
            e,
            a,
            wl,
            yn,
            _i,
            t,
            gt,
            Ma,
            re,
            ua,
            n,
            0,
            -0,
            0
          );
        }
      }
      break;
    } while (!0);
    Nt(l);
  }
  function ud(l, t, a, e, u, n, c, i, s, m, _, E, g, b) {
    if (l.timeoutHandle = -1, E = t.subtreeFlags, (E & 8192 || (E & 16785408) === 16785408) && (du = { stylesheets: null, count: 0, unsuspend: zy }, Fr(t), E = Ny(), E !== null)) {
      l.cancelPendingCommit = E(
        dd.bind(
          null,
          l,
          t,
          n,
          a,
          e,
          u,
          c,
          i,
          s,
          _,
          1,
          g,
          b
        )
      ), fa(l, n, c, !m);
      return;
    }
    dd(
      l,
      t,
      n,
      a,
      e,
      u,
      c,
      i,
      s
    );
  }
  function Lh(l) {
    for (var t = l; ; ) {
      var a = t.tag;
      if ((a === 0 || a === 11 || a === 15) && t.flags & 16384 && (a = t.updateQueue, a !== null && (a = a.stores, a !== null)))
        for (var e = 0; e < a.length; e++) {
          var u = a[e], n = u.getSnapshot;
          u = u.value;
          try {
            if (!tt(n(), u)) return !1;
          } catch {
            return !1;
          }
        }
      if (a = t.child, t.subtreeFlags & 16384 && a !== null)
        a.return = t, t = a;
      else {
        if (t === l) break;
        for (; t.sibling === null; ) {
          if (t.return === null || t.return === l) return !0;
          t = t.return;
        }
        t.sibling.return = t.return, t = t.sibling;
      }
    }
    return !0;
  }
  function fa(l, t, a, e) {
    t &= ~bi, t &= ~Ma, l.suspendedLanes |= t, l.pingedLanes &= ~t, e && (l.warmLanes |= t), e = l.expirationTimes;
    for (var u = t; 0 < u; ) {
      var n = 31 - lt(u), c = 1 << n;
      e[n] = -1, u &= ~c;
    }
    a !== 0 && vf(l, a, t);
  }
  function vn() {
    return (tl & 6) === 0 ? (nu(0), !1) : !0;
  }
  function Ai() {
    if (J !== null) {
      if (al === 0)
        var l = J.return;
      else
        l = J, Mt = Na = null, Qc(l), ne = null, We = 0, l = J;
      for (; l !== null; )
        Br(l.alternate, l), l = l.return;
      J = null;
    }
  }
  function he(l, t) {
    var a = l.timeoutHandle;
    a !== -1 && (l.timeoutHandle = -1, fy(a)), a = l.cancelPendingCommit, a !== null && (l.cancelPendingCommit = null, a()), Ai(), sl = l, J = a = Dt(l.current, null), W = t, al = 0, nt = null, ua = !1, se = pe(l, t), gi = !1, re = gt = bi = Ma = na = gl = 0, wl = eu = null, _i = !1, (t & 8) !== 0 && (t |= t & 32);
    var e = l.entangledLanes;
    if (e !== 0)
      for (l = l.entanglements, e &= t; 0 < e; ) {
        var u = 31 - lt(e), n = 1 << u;
        t |= l[u], e &= ~n;
      }
    return Qt = t, Yu(), a;
  }
  function nd(l, t) {
    Z = null, S.H = tn, t === Xe || t === Ku ? (t = Ts(), al = 3) : t === _s ? (t = Ts(), al = 4) : al = t === Er ? 8 : t !== null && typeof t == "object" && typeof t.then == "function" ? 6 : 1, nt = t, J === null && (gl = 1, cn(
      l,
      ot(t, l.current)
    ));
  }
  function cd() {
    var l = S.H;
    return S.H = tn, l === null ? tn : l;
  }
  function id() {
    var l = S.A;
    return S.A = Zh, l;
  }
  function zi() {
    gl = 4, ua || (W & 4194048) !== W && mt.current !== null || (se = !0), (na & 134217727) === 0 && (Ma & 134217727) === 0 || sl === null || fa(
      sl,
      W,
      gt,
      !1
    );
  }
  function xi(l, t, a) {
    var e = tl;
    tl |= 2;
    var u = cd(), n = id();
    (sl !== l || W !== t) && (yn = null, he(l, t)), t = !1;
    var c = gl;
    l: do
      try {
        if (al !== 0 && J !== null) {
          var i = J, s = nt;
          switch (al) {
            case 8:
              Ai(), c = 6;
              break l;
            case 3:
            case 2:
            case 9:
            case 6:
              mt.current === null && (t = !0);
              var m = al;
              if (al = 0, nt = null, ye(l, i, s, m), a && se) {
                c = 0;
                break l;
              }
              break;
            default:
              m = al, al = 0, nt = null, ye(l, i, s, m);
          }
        }
        Kh(), c = gl;
        break;
      } catch (_) {
        nd(l, _);
      }
    while (!0);
    return t && l.shellSuspendCounter++, Mt = Na = null, tl = e, S.H = u, S.A = n, J === null && (sl = null, W = 0, Yu()), c;
  }
  function Kh() {
    for (; J !== null; ) fd(J);
  }
  function Jh(l, t) {
    var a = tl;
    tl |= 2;
    var e = cd(), u = id();
    sl !== l || W !== t ? (yn = null, hn = Tt() + 500, he(l, t)) : se = pe(
      l,
      t
    );
    l: do
      try {
        if (al !== 0 && J !== null) {
          t = J;
          var n = nt;
          t: switch (al) {
            case 1:
              al = 0, nt = null, ye(l, t, n, 1);
              break;
            case 2:
            case 9:
              if (Ss(n)) {
                al = 0, nt = null, sd(t);
                break;
              }
              t = function() {
                al !== 2 && al !== 9 || sl !== l || (al = 7), Nt(l);
              }, n.then(t, t);
              break l;
            case 3:
              al = 7;
              break l;
            case 4:
              al = 5;
              break l;
            case 7:
              Ss(n) ? (al = 0, nt = null, sd(t)) : (al = 0, nt = null, ye(l, t, n, 7));
              break;
            case 5:
              var c = null;
              switch (J.tag) {
                case 26:
                  c = J.memoizedState;
                case 5:
                case 27:
                  var i = J;
                  if (!c || Ld(c)) {
                    al = 0, nt = null;
                    var s = i.sibling;
                    if (s !== null) J = s;
                    else {
                      var m = i.return;
                      m !== null ? (J = m, mn(m)) : J = null;
                    }
                    break t;
                  }
              }
              al = 0, nt = null, ye(l, t, n, 5);
              break;
            case 6:
              al = 0, nt = null, ye(l, t, n, 6);
              break;
            case 8:
              Ai(), gl = 6;
              break l;
            default:
              throw Error(h(462));
          }
        }
        kh();
        break;
      } catch (_) {
        nd(l, _);
      }
    while (!0);
    return Mt = Na = null, S.H = e, S.A = u, tl = a, J !== null ? 0 : (sl = null, W = 0, Yu(), gl);
  }
  function kh() {
    for (; J !== null && !vo(); )
      fd(J);
  }
  function fd(l) {
    var t = Hr(l.alternate, l, Qt);
    l.memoizedProps = l.pendingProps, t === null ? mn(l) : J = t;
  }
  function sd(l) {
    var t = l, a = t.alternate;
    switch (t.tag) {
      case 15:
      case 0:
        t = jr(
          a,
          t,
          t.pendingProps,
          t.type,
          void 0,
          W
        );
        break;
      case 11:
        t = jr(
          a,
          t,
          t.pendingProps,
          t.type.render,
          t.ref,
          W
        );
        break;
      case 5:
        Qc(t);
      default:
        Br(a, t), t = J = rs(t, Qt), t = Hr(a, t, Qt);
    }
    l.memoizedProps = l.pendingProps, t === null ? mn(l) : J = t;
  }
  function ye(l, t, a, e) {
    Mt = Na = null, Qc(t), ne = null, We = 0;
    var u = t.return;
    try {
      if (Yh(
        l,
        u,
        t,
        a,
        W
      )) {
        gl = 1, cn(
          l,
          ot(a, l.current)
        ), J = null;
        return;
      }
    } catch (n) {
      if (u !== null) throw J = u, n;
      gl = 1, cn(
        l,
        ot(a, l.current)
      ), J = null;
      return;
    }
    t.flags & 32768 ? (ll || e === 1 ? l = !0 : se || (W & 536870912) !== 0 ? l = !1 : (ua = l = !0, (e === 2 || e === 9 || e === 3 || e === 6) && (e = mt.current, e !== null && e.tag === 13 && (e.flags |= 16384))), rd(t, l)) : mn(t);
  }
  function mn(l) {
    var t = l;
    do {
      if ((t.flags & 32768) !== 0) {
        rd(
          t,
          ua
        );
        return;
      }
      l = t.return;
      var a = Ch(
        t.alternate,
        t,
        Qt
      );
      if (a !== null) {
        J = a;
        return;
      }
      if (t = t.sibling, t !== null) {
        J = t;
        return;
      }
      J = t = l;
    } while (t !== null);
    gl === 0 && (gl = 5);
  }
  function rd(l, t) {
    do {
      var a = Gh(l.alternate, l);
      if (a !== null) {
        a.flags &= 32767, J = a;
        return;
      }
      if (a = l.return, a !== null && (a.flags |= 32768, a.subtreeFlags = 0, a.deletions = null), !t && (l = l.sibling, l !== null)) {
        J = l;
        return;
      }
      J = l = a;
    } while (l !== null);
    gl = 6, J = null;
  }
  function dd(l, t, a, e, u, n, c, i, s) {
    l.cancelPendingCommit = null;
    do
      gn();
    while (Ml !== 0);
    if ((tl & 6) !== 0) throw Error(h(327));
    if (t !== null) {
      if (t === l.current) throw Error(h(177));
      if (n = t.lanes | t.childLanes, n |= mc, zo(
        l,
        a,
        n,
        c,
        i,
        s
      ), l === sl && (J = sl = null, W = 0), de = t, ia = l, oe = a, pi = n, Ti = u, td = e, (t.subtreeFlags & 10256) !== 0 || (t.flags & 10256) !== 0 ? (l.callbackNode = null, l.callbackPriority = 0, Fh(pu, function() {
        return md(), null;
      })) : (l.callbackNode = null, l.callbackPriority = 0), e = (t.flags & 13878) !== 0, (t.subtreeFlags & 13878) !== 0 || e) {
        e = S.T, S.T = null, u = j.p, j.p = 2, c = tl, tl |= 4;
        try {
          Xh(l, t, a);
        } finally {
          tl = c, j.p = u, S.T = e;
        }
      }
      Ml = 1, od(), hd(), yd();
    }
  }
  function od() {
    if (Ml === 1) {
      Ml = 0;
      var l = ia, t = de, a = (t.flags & 13878) !== 0;
      if ((t.subtreeFlags & 13878) !== 0 || a) {
        a = S.T, S.T = null;
        var e = j.p;
        j.p = 2;
        var u = tl;
        tl |= 4;
        try {
          $r(t, l);
          var n = Ci, c = ls(l.containerInfo), i = n.focusedElem, s = n.selectionRange;
          if (c !== i && i && i.ownerDocument && Pf(
            i.ownerDocument.documentElement,
            i
          )) {
            if (s !== null && dc(i)) {
              var m = s.start, _ = s.end;
              if (_ === void 0 && (_ = m), "selectionStart" in i)
                i.selectionStart = m, i.selectionEnd = Math.min(
                  _,
                  i.value.length
                );
              else {
                var E = i.ownerDocument || document, g = E && E.defaultView || window;
                if (g.getSelection) {
                  var b = g.getSelection(), G = i.textContent.length, H = Math.min(s.start, G), nl = s.end === void 0 ? H : Math.min(s.end, G);
                  !b.extend && H > nl && (c = nl, nl = H, H = c);
                  var y = If(
                    i,
                    H
                  ), o = If(
                    i,
                    nl
                  );
                  if (y && o && (b.rangeCount !== 1 || b.anchorNode !== y.node || b.anchorOffset !== y.offset || b.focusNode !== o.node || b.focusOffset !== o.offset)) {
                    var v = E.createRange();
                    v.setStart(y.node, y.offset), b.removeAllRanges(), H > nl ? (b.addRange(v), b.extend(o.node, o.offset)) : (v.setEnd(o.node, o.offset), b.addRange(v));
                  }
                }
              }
            }
            for (E = [], b = i; b = b.parentNode; )
              b.nodeType === 1 && E.push({
                element: b,
                left: b.scrollLeft,
                top: b.scrollTop
              });
            for (typeof i.focus == "function" && i.focus(), i = 0; i < E.length; i++) {
              var p = E[i];
              p.element.scrollLeft = p.left, p.element.scrollTop = p.top;
            }
          }
          jn = !!Bi, Ci = Bi = null;
        } finally {
          tl = u, j.p = e, S.T = a;
        }
      }
      l.current = t, Ml = 2;
    }
  }
  function hd() {
    if (Ml === 2) {
      Ml = 0;
      var l = ia, t = de, a = (t.flags & 8772) !== 0;
      if ((t.subtreeFlags & 8772) !== 0 || a) {
        a = S.T, S.T = null;
        var e = j.p;
        j.p = 2;
        var u = tl;
        tl |= 4;
        try {
          Lr(l, t.alternate, t);
        } finally {
          tl = u, j.p = e, S.T = a;
        }
      }
      Ml = 3;
    }
  }
  function yd() {
    if (Ml === 4 || Ml === 3) {
      Ml = 0, mo();
      var l = ia, t = de, a = oe, e = td;
      (t.subtreeFlags & 10256) !== 0 || (t.flags & 10256) !== 0 ? Ml = 5 : (Ml = 0, de = ia = null, vd(l, l.pendingLanes));
      var u = l.pendingLanes;
      if (u === 0 && (ca = null), Ln(a), t = t.stateNode, Pl && typeof Pl.onCommitFiberRoot == "function")
        try {
          Pl.onCommitFiberRoot(
            Se,
            t,
            void 0,
            (t.current.flags & 128) === 128
          );
        } catch {
        }
      if (e !== null) {
        t = S.T, u = j.p, j.p = 2, S.T = null;
        try {
          for (var n = l.onRecoverableError, c = 0; c < e.length; c++) {
            var i = e[c];
            n(i.value, {
              componentStack: i.stack
            });
          }
        } finally {
          S.T = t, j.p = u;
        }
      }
      (oe & 3) !== 0 && gn(), Nt(l), u = l.pendingLanes, (a & 4194090) !== 0 && (u & 42) !== 0 ? l === Ei ? uu++ : (uu = 0, Ei = l) : uu = 0, nu(0);
    }
  }
  function vd(l, t) {
    (l.pooledCacheLanes &= t) === 0 && (t = l.pooledCache, t != null && (l.pooledCache = null, Ce(t)));
  }
  function gn(l) {
    return od(), hd(), yd(), md();
  }
  function md() {
    if (Ml !== 5) return !1;
    var l = ia, t = pi;
    pi = 0;
    var a = Ln(oe), e = S.T, u = j.p;
    try {
      j.p = 32 > a ? 32 : a, S.T = null, a = Ti, Ti = null;
      var n = ia, c = oe;
      if (Ml = 0, de = ia = null, oe = 0, (tl & 6) !== 0) throw Error(h(331));
      var i = tl;
      if (tl |= 4, Pr(n.current), wr(
        n,
        n.current,
        c,
        a
      ), tl = i, nu(0, !1), Pl && typeof Pl.onPostCommitFiberRoot == "function")
        try {
          Pl.onPostCommitFiberRoot(Se, n);
        } catch {
        }
      return !0;
    } finally {
      j.p = u, S.T = e, vd(l, t);
    }
  }
  function gd(l, t, a) {
    t = ot(a, t), t = ti(l.stateNode, t, 2), l = Ft(l, t, 2), l !== null && (Te(l, 2), Nt(l));
  }
  function il(l, t, a) {
    if (l.tag === 3)
      gd(l, l, a);
    else
      for (; t !== null; ) {
        if (t.tag === 3) {
          gd(
            t,
            l,
            a
          );
          break;
        } else if (t.tag === 1) {
          var e = t.stateNode;
          if (typeof t.type.getDerivedStateFromError == "function" || typeof e.componentDidCatch == "function" && (ca === null || !ca.has(e))) {
            l = ot(a, l), a = pr(2), e = Ft(t, a, 2), e !== null && (Tr(
              a,
              e,
              t,
              l
            ), Te(e, 2), Nt(e));
            break;
          }
        }
        t = t.return;
      }
  }
  function Ni(l, t, a) {
    var e = l.pingCache;
    if (e === null) {
      e = l.pingCache = new Vh();
      var u = /* @__PURE__ */ new Set();
      e.set(t, u);
    } else
      u = e.get(t), u === void 0 && (u = /* @__PURE__ */ new Set(), e.set(t, u));
    u.has(a) || (gi = !0, u.add(a), l = $h.bind(null, l, t, a), t.then(l, l));
  }
  function $h(l, t, a) {
    var e = l.pingCache;
    e !== null && e.delete(t), l.pingedLanes |= l.suspendedLanes & a, l.warmLanes &= ~a, sl === l && (W & a) === a && (gl === 4 || gl === 3 && (W & 62914560) === W && 300 > Tt() - Si ? (tl & 2) === 0 && he(l, 0) : bi |= a, re === W && (re = 0)), Nt(l);
  }
  function bd(l, t) {
    t === 0 && (t = yf()), l = Wa(l, t), l !== null && (Te(l, t), Nt(l));
  }
  function Wh(l) {
    var t = l.memoizedState, a = 0;
    t !== null && (a = t.retryLane), bd(l, a);
  }
  function wh(l, t) {
    var a = 0;
    switch (l.tag) {
      case 13:
        var e = l.stateNode, u = l.memoizedState;
        u !== null && (a = u.retryLane);
        break;
      case 19:
        e = l.stateNode;
        break;
      case 22:
        e = l.stateNode._retryCache;
        break;
      default:
        throw Error(h(314));
    }
    e !== null && e.delete(t), bd(l, a);
  }
  function Fh(l, t) {
    return Xn(l, t);
  }
  var bn = null, ve = null, Oi = !1, _n = !1, ji = !1, qa = 0;
  function Nt(l) {
    l !== ve && l.next === null && (ve === null ? bn = ve = l : ve = ve.next = l), _n = !0, Oi || (Oi = !0, Ph());
  }
  function nu(l, t) {
    if (!ji && _n) {
      ji = !0;
      do
        for (var a = !1, e = bn; e !== null; ) {
          if (l !== 0) {
            var u = e.pendingLanes;
            if (u === 0) var n = 0;
            else {
              var c = e.suspendedLanes, i = e.pingedLanes;
              n = (1 << 31 - lt(42 | l) + 1) - 1, n &= u & ~(c & ~i), n = n & 201326741 ? n & 201326741 | 1 : n ? n | 2 : 0;
            }
            n !== 0 && (a = !0, Td(e, n));
          } else
            n = W, n = Au(
              e,
              e === sl ? n : 0,
              e.cancelPendingCommit !== null || e.timeoutHandle !== -1
            ), (n & 3) === 0 || pe(e, n) || (a = !0, Td(e, n));
          e = e.next;
        }
      while (a);
      ji = !1;
    }
  }
  function Ih() {
    _d();
  }
  function _d() {
    _n = Oi = !1;
    var l = 0;
    qa !== 0 && (iy() && (l = qa), qa = 0);
    for (var t = Tt(), a = null, e = bn; e !== null; ) {
      var u = e.next, n = Sd(e, t);
      n === 0 ? (e.next = null, a === null ? bn = u : a.next = u, u === null && (ve = a)) : (a = e, (l !== 0 || (n & 3) !== 0) && (_n = !0)), e = u;
    }
    nu(l);
  }
  function Sd(l, t) {
    for (var a = l.suspendedLanes, e = l.pingedLanes, u = l.expirationTimes, n = l.pendingLanes & -62914561; 0 < n; ) {
      var c = 31 - lt(n), i = 1 << c, s = u[c];
      s === -1 ? ((i & a) === 0 || (i & e) !== 0) && (u[c] = Ao(i, t)) : s <= t && (l.expiredLanes |= i), n &= ~i;
    }
    if (t = sl, a = W, a = Au(
      l,
      l === t ? a : 0,
      l.cancelPendingCommit !== null || l.timeoutHandle !== -1
    ), e = l.callbackNode, a === 0 || l === t && (al === 2 || al === 9) || l.cancelPendingCommit !== null)
      return e !== null && e !== null && Qn(e), l.callbackNode = null, l.callbackPriority = 0;
    if ((a & 3) === 0 || pe(l, a)) {
      if (t = a & -a, t === l.callbackPriority) return t;
      switch (e !== null && Qn(e), Ln(a)) {
        case 2:
        case 8:
          a = df;
          break;
        case 32:
          a = pu;
          break;
        case 268435456:
          a = of;
          break;
        default:
          a = pu;
      }
      return e = pd.bind(null, l), a = Xn(a, e), l.callbackPriority = t, l.callbackNode = a, t;
    }
    return e !== null && e !== null && Qn(e), l.callbackPriority = 2, l.callbackNode = null, 2;
  }
  function pd(l, t) {
    if (Ml !== 0 && Ml !== 5)
      return l.callbackNode = null, l.callbackPriority = 0, null;
    var a = l.callbackNode;
    if (gn() && l.callbackNode !== a)
      return null;
    var e = W;
    return e = Au(
      l,
      l === sl ? e : 0,
      l.cancelPendingCommit !== null || l.timeoutHandle !== -1
    ), e === 0 ? null : (ed(l, e, t), Sd(l, Tt()), l.callbackNode != null && l.callbackNode === a ? pd.bind(null, l) : null);
  }
  function Td(l, t) {
    if (gn()) return null;
    ed(l, t, !0);
  }
  function Ph() {
    sy(function() {
      (tl & 6) !== 0 ? Xn(
        rf,
        Ih
      ) : _d();
    });
  }
  function Di() {
    return qa === 0 && (qa = hf()), qa;
  }
  function Ed(l) {
    return l == null || typeof l == "symbol" || typeof l == "boolean" ? null : typeof l == "function" ? l : ju("" + l);
  }
  function Ad(l, t) {
    var a = t.ownerDocument.createElement("input");
    return a.name = t.name, a.value = t.value, l.id && a.setAttribute("form", l.id), t.parentNode.insertBefore(a, t), l = new FormData(l), a.parentNode.removeChild(a), l;
  }
  function ly(l, t, a, e, u) {
    if (t === "submit" && a && a.stateNode === u) {
      var n = Ed(
        (u[Jl] || null).action
      ), c = e.submitter;
      c && (t = (t = c[Jl] || null) ? Ed(t.formAction) : c.getAttribute("formAction"), t !== null && (n = t, c = null));
      var i = new Mu(
        "action",
        "action",
        null,
        e,
        u
      );
      l.push({
        event: i,
        listeners: [
          {
            instance: null,
            listener: function() {
              if (e.defaultPrevented) {
                if (qa !== 0) {
                  var s = c ? Ad(u, c) : new FormData(u);
                  wc(
                    a,
                    {
                      pending: !0,
                      data: s,
                      method: u.method,
                      action: n
                    },
                    null,
                    s
                  );
                }
              } else
                typeof n == "function" && (i.preventDefault(), s = c ? Ad(u, c) : new FormData(u), wc(
                  a,
                  {
                    pending: !0,
                    data: s,
                    method: u.method,
                    action: n
                  },
                  n,
                  s
                ));
            },
            currentTarget: u
          }
        ]
      });
    }
  }
  for (var Ri = 0; Ri < vc.length; Ri++) {
    var Ui = vc[Ri], ty = Ui.toLowerCase(), ay = Ui[0].toUpperCase() + Ui.slice(1);
    _t(
      ty,
      "on" + ay
    );
  }
  _t(es, "onAnimationEnd"), _t(us, "onAnimationIteration"), _t(ns, "onAnimationStart"), _t("dblclick", "onDoubleClick"), _t("focusin", "onFocus"), _t("focusout", "onBlur"), _t(_h, "onTransitionRun"), _t(Sh, "onTransitionStart"), _t(ph, "onTransitionCancel"), _t(cs, "onTransitionEnd"), Ga("onMouseEnter", ["mouseout", "mouseover"]), Ga("onMouseLeave", ["mouseout", "mouseover"]), Ga("onPointerEnter", ["pointerout", "pointerover"]), Ga("onPointerLeave", ["pointerout", "pointerover"]), ba(
    "onChange",
    "change click focusin focusout input keydown keyup selectionchange".split(" ")
  ), ba(
    "onSelect",
    "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(
      " "
    )
  ), ba("onBeforeInput", [
    "compositionend",
    "keypress",
    "textInput",
    "paste"
  ]), ba(
    "onCompositionEnd",
    "compositionend focusout keydown keypress keyup mousedown".split(" ")
  ), ba(
    "onCompositionStart",
    "compositionstart focusout keydown keypress keyup mousedown".split(" ")
  ), ba(
    "onCompositionUpdate",
    "compositionupdate focusout keydown keypress keyup mousedown".split(" ")
  );
  var cu = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(
    " "
  ), ey = new Set(
    "beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(cu)
  );
  function zd(l, t) {
    t = (t & 4) !== 0;
    for (var a = 0; a < l.length; a++) {
      var e = l[a], u = e.event;
      e = e.listeners;
      l: {
        var n = void 0;
        if (t)
          for (var c = e.length - 1; 0 <= c; c--) {
            var i = e[c], s = i.instance, m = i.currentTarget;
            if (i = i.listener, s !== n && u.isPropagationStopped())
              break l;
            n = i, u.currentTarget = m;
            try {
              n(u);
            } catch (_) {
              nn(_);
            }
            u.currentTarget = null, n = s;
          }
        else
          for (c = 0; c < e.length; c++) {
            if (i = e[c], s = i.instance, m = i.currentTarget, i = i.listener, s !== n && u.isPropagationStopped())
              break l;
            n = i, u.currentTarget = m;
            try {
              n(u);
            } catch (_) {
              nn(_);
            }
            u.currentTarget = null, n = s;
          }
      }
    }
  }
  function k(l, t) {
    var a = t[Kn];
    a === void 0 && (a = t[Kn] = /* @__PURE__ */ new Set());
    var e = l + "__bubble";
    a.has(e) || (xd(t, l, 2, !1), a.add(e));
  }
  function Mi(l, t, a) {
    var e = 0;
    t && (e |= 4), xd(
      a,
      l,
      e,
      t
    );
  }
  var Sn = "_reactListening" + Math.random().toString(36).slice(2);
  function qi(l) {
    if (!l[Sn]) {
      l[Sn] = !0, _f.forEach(function(a) {
        a !== "selectionchange" && (ey.has(a) || Mi(a, !1, l), Mi(a, !0, l));
      });
      var t = l.nodeType === 9 ? l : l.ownerDocument;
      t === null || t[Sn] || (t[Sn] = !0, Mi("selectionchange", !1, t));
    }
  }
  function xd(l, t, a, e) {
    switch (wd(t)) {
      case 2:
        var u = Dy;
        break;
      case 8:
        u = Ry;
        break;
      default:
        u = $i;
    }
    a = u.bind(
      null,
      t,
      a,
      l
    ), u = void 0, !ac || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (u = !0), e ? u !== void 0 ? l.addEventListener(t, a, {
      capture: !0,
      passive: u
    }) : l.addEventListener(t, a, !0) : u !== void 0 ? l.addEventListener(t, a, {
      passive: u
    }) : l.addEventListener(t, a, !1);
  }
  function Hi(l, t, a, e, u) {
    var n = e;
    if ((t & 1) === 0 && (t & 2) === 0 && e !== null)
      l: for (; ; ) {
        if (e === null) return;
        var c = e.tag;
        if (c === 3 || c === 4) {
          var i = e.stateNode.containerInfo;
          if (i === u) break;
          if (c === 4)
            for (c = e.return; c !== null; ) {
              var s = c.tag;
              if ((s === 3 || s === 4) && c.stateNode.containerInfo === u)
                return;
              c = c.return;
            }
          for (; i !== null; ) {
            if (c = Ya(i), c === null) return;
            if (s = c.tag, s === 5 || s === 6 || s === 26 || s === 27) {
              e = n = c;
              continue l;
            }
            i = i.parentNode;
          }
        }
        e = e.return;
      }
    Mf(function() {
      var m = n, _ = lc(a), E = [];
      l: {
        var g = is.get(l);
        if (g !== void 0) {
          var b = Mu, G = l;
          switch (l) {
            case "keypress":
              if (Ru(a) === 0) break l;
            case "keydown":
            case "keyup":
              b = Fo;
              break;
            case "focusin":
              G = "focus", b = cc;
              break;
            case "focusout":
              G = "blur", b = cc;
              break;
            case "beforeblur":
            case "afterblur":
              b = cc;
              break;
            case "click":
              if (a.button === 2) break l;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              b = Yf;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              b = Go;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              b = lh;
              break;
            case es:
            case us:
            case ns:
              b = Zo;
              break;
            case cs:
              b = ah;
              break;
            case "scroll":
            case "scrollend":
              b = Bo;
              break;
            case "wheel":
              b = uh;
              break;
            case "copy":
            case "cut":
            case "paste":
              b = Lo;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              b = Cf;
              break;
            case "toggle":
            case "beforetoggle":
              b = ch;
          }
          var H = (t & 4) !== 0, nl = !H && (l === "scroll" || l === "scrollend"), y = H ? g !== null ? g + "Capture" : null : g;
          H = [];
          for (var o = m, v; o !== null; ) {
            var p = o;
            if (v = p.stateNode, p = p.tag, p !== 5 && p !== 26 && p !== 27 || v === null || y === null || (p = ze(o, y), p != null && H.push(
              iu(o, p, v)
            )), nl) break;
            o = o.return;
          }
          0 < H.length && (g = new b(
            g,
            G,
            null,
            a,
            _
          ), E.push({ event: g, listeners: H }));
        }
      }
      if ((t & 7) === 0) {
        l: {
          if (g = l === "mouseover" || l === "pointerover", b = l === "mouseout" || l === "pointerout", g && a !== Pn && (G = a.relatedTarget || a.fromElement) && (Ya(G) || G[Ha]))
            break l;
          if ((b || g) && (g = _.window === _ ? _ : (g = _.ownerDocument) ? g.defaultView || g.parentWindow : window, b ? (G = a.relatedTarget || a.toElement, b = m, G = G ? Ya(G) : null, G !== null && (nl = F(G), H = G.tag, G !== nl || H !== 5 && H !== 27 && H !== 6) && (G = null)) : (b = null, G = m), b !== G)) {
            if (H = Yf, p = "onMouseLeave", y = "onMouseEnter", o = "mouse", (l === "pointerout" || l === "pointerover") && (H = Cf, p = "onPointerLeave", y = "onPointerEnter", o = "pointer"), nl = b == null ? g : Ae(b), v = G == null ? g : Ae(G), g = new H(
              p,
              o + "leave",
              b,
              a,
              _
            ), g.target = nl, g.relatedTarget = v, p = null, Ya(_) === m && (H = new H(
              y,
              o + "enter",
              G,
              a,
              _
            ), H.target = v, H.relatedTarget = nl, p = H), nl = p, b && G)
              t: {
                for (H = b, y = G, o = 0, v = H; v; v = me(v))
                  o++;
                for (v = 0, p = y; p; p = me(p))
                  v++;
                for (; 0 < o - v; )
                  H = me(H), o--;
                for (; 0 < v - o; )
                  y = me(y), v--;
                for (; o--; ) {
                  if (H === y || y !== null && H === y.alternate)
                    break t;
                  H = me(H), y = me(y);
                }
                H = null;
              }
            else H = null;
            b !== null && Nd(
              E,
              g,
              b,
              H,
              !1
            ), G !== null && nl !== null && Nd(
              E,
              nl,
              G,
              H,
              !0
            );
          }
        }
        l: {
          if (g = m ? Ae(m) : window, b = g.nodeName && g.nodeName.toLowerCase(), b === "select" || b === "input" && g.type === "file")
            var U = Jf;
          else if (Lf(g))
            if (kf)
              U = mh;
            else {
              U = yh;
              var L = hh;
            }
          else
            b = g.nodeName, !b || b.toLowerCase() !== "input" || g.type !== "checkbox" && g.type !== "radio" ? m && In(m.elementType) && (U = Jf) : U = vh;
          if (U && (U = U(l, m))) {
            Kf(
              E,
              U,
              a,
              _
            );
            break l;
          }
          L && L(l, g, m), l === "focusout" && m && g.type === "number" && m.memoizedProps.value != null && Fn(g, "number", g.value);
        }
        switch (L = m ? Ae(m) : window, l) {
          case "focusin":
            (Lf(L) || L.contentEditable === "true") && (Ja = L, oc = m, Me = null);
            break;
          case "focusout":
            Me = oc = Ja = null;
            break;
          case "mousedown":
            hc = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            hc = !1, ts(E, a, _);
            break;
          case "selectionchange":
            if (bh) break;
          case "keydown":
          case "keyup":
            ts(E, a, _);
        }
        var M;
        if (fc)
          l: {
            switch (l) {
              case "compositionstart":
                var B = "onCompositionStart";
                break l;
              case "compositionend":
                B = "onCompositionEnd";
                break l;
              case "compositionupdate":
                B = "onCompositionUpdate";
                break l;
            }
            B = void 0;
          }
        else
          Ka ? Zf(l, a) && (B = "onCompositionEnd") : l === "keydown" && a.keyCode === 229 && (B = "onCompositionStart");
        B && (Gf && a.locale !== "ko" && (Ka || B !== "onCompositionStart" ? B === "onCompositionEnd" && Ka && (M = qf()) : (kt = _, ec = "value" in kt ? kt.value : kt.textContent, Ka = !0)), L = pn(m, B), 0 < L.length && (B = new Bf(
          B,
          l,
          null,
          a,
          _
        ), E.push({ event: B, listeners: L }), M ? B.data = M : (M = Vf(a), M !== null && (B.data = M)))), (M = fh ? sh(l, a) : rh(l, a)) && (B = pn(m, "onBeforeInput"), 0 < B.length && (L = new Bf(
          "onBeforeInput",
          "beforeinput",
          null,
          a,
          _
        ), E.push({
          event: L,
          listeners: B
        }), L.data = M)), ly(
          E,
          l,
          m,
          a,
          _
        );
      }
      zd(E, t);
    });
  }
  function iu(l, t, a) {
    return {
      instance: l,
      listener: t,
      currentTarget: a
    };
  }
  function pn(l, t) {
    for (var a = t + "Capture", e = []; l !== null; ) {
      var u = l, n = u.stateNode;
      if (u = u.tag, u !== 5 && u !== 26 && u !== 27 || n === null || (u = ze(l, a), u != null && e.unshift(
        iu(l, u, n)
      ), u = ze(l, t), u != null && e.push(
        iu(l, u, n)
      )), l.tag === 3) return e;
      l = l.return;
    }
    return [];
  }
  function me(l) {
    if (l === null) return null;
    do
      l = l.return;
    while (l && l.tag !== 5 && l.tag !== 27);
    return l || null;
  }
  function Nd(l, t, a, e, u) {
    for (var n = t._reactName, c = []; a !== null && a !== e; ) {
      var i = a, s = i.alternate, m = i.stateNode;
      if (i = i.tag, s !== null && s === e) break;
      i !== 5 && i !== 26 && i !== 27 || m === null || (s = m, u ? (m = ze(a, n), m != null && c.unshift(
        iu(a, m, s)
      )) : u || (m = ze(a, n), m != null && c.push(
        iu(a, m, s)
      ))), a = a.return;
    }
    c.length !== 0 && l.push({ event: t, listeners: c });
  }
  var uy = /\r\n?/g, ny = /\u0000|\uFFFD/g;
  function Od(l) {
    return (typeof l == "string" ? l : "" + l).replace(uy, `
`).replace(ny, "");
  }
  function jd(l, t) {
    return t = Od(t), Od(l) === t;
  }
  function Tn() {
  }
  function ul(l, t, a, e, u, n) {
    switch (a) {
      case "children":
        typeof e == "string" ? t === "body" || t === "textarea" && e === "" || Za(l, e) : (typeof e == "number" || typeof e == "bigint") && t !== "body" && Za(l, "" + e);
        break;
      case "className":
        xu(l, "class", e);
        break;
      case "tabIndex":
        xu(l, "tabindex", e);
        break;
      case "dir":
      case "role":
      case "viewBox":
      case "width":
      case "height":
        xu(l, a, e);
        break;
      case "style":
        Rf(l, e, n);
        break;
      case "data":
        if (t !== "object") {
          xu(l, "data", e);
          break;
        }
      case "src":
      case "href":
        if (e === "" && (t !== "a" || a !== "href")) {
          l.removeAttribute(a);
          break;
        }
        if (e == null || typeof e == "function" || typeof e == "symbol" || typeof e == "boolean") {
          l.removeAttribute(a);
          break;
        }
        e = ju("" + e), l.setAttribute(a, e);
        break;
      case "action":
      case "formAction":
        if (typeof e == "function") {
          l.setAttribute(
            a,
            "javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')"
          );
          break;
        } else
          typeof n == "function" && (a === "formAction" ? (t !== "input" && ul(l, t, "name", u.name, u, null), ul(
            l,
            t,
            "formEncType",
            u.formEncType,
            u,
            null
          ), ul(
            l,
            t,
            "formMethod",
            u.formMethod,
            u,
            null
          ), ul(
            l,
            t,
            "formTarget",
            u.formTarget,
            u,
            null
          )) : (ul(l, t, "encType", u.encType, u, null), ul(l, t, "method", u.method, u, null), ul(l, t, "target", u.target, u, null)));
        if (e == null || typeof e == "symbol" || typeof e == "boolean") {
          l.removeAttribute(a);
          break;
        }
        e = ju("" + e), l.setAttribute(a, e);
        break;
      case "onClick":
        e != null && (l.onclick = Tn);
        break;
      case "onScroll":
        e != null && k("scroll", l);
        break;
      case "onScrollEnd":
        e != null && k("scrollend", l);
        break;
      case "dangerouslySetInnerHTML":
        if (e != null) {
          if (typeof e != "object" || !("__html" in e))
            throw Error(h(61));
          if (a = e.__html, a != null) {
            if (u.children != null) throw Error(h(60));
            l.innerHTML = a;
          }
        }
        break;
      case "multiple":
        l.multiple = e && typeof e != "function" && typeof e != "symbol";
        break;
      case "muted":
        l.muted = e && typeof e != "function" && typeof e != "symbol";
        break;
      case "suppressContentEditableWarning":
      case "suppressHydrationWarning":
      case "defaultValue":
      case "defaultChecked":
      case "innerHTML":
      case "ref":
        break;
      case "autoFocus":
        break;
      case "xlinkHref":
        if (e == null || typeof e == "function" || typeof e == "boolean" || typeof e == "symbol") {
          l.removeAttribute("xlink:href");
          break;
        }
        a = ju("" + e), l.setAttributeNS(
          "http://www.w3.org/1999/xlink",
          "xlink:href",
          a
        );
        break;
      case "contentEditable":
      case "spellCheck":
      case "draggable":
      case "value":
      case "autoReverse":
      case "externalResourcesRequired":
      case "focusable":
      case "preserveAlpha":
        e != null && typeof e != "function" && typeof e != "symbol" ? l.setAttribute(a, "" + e) : l.removeAttribute(a);
        break;
      case "inert":
      case "allowFullScreen":
      case "async":
      case "autoPlay":
      case "controls":
      case "default":
      case "defer":
      case "disabled":
      case "disablePictureInPicture":
      case "disableRemotePlayback":
      case "formNoValidate":
      case "hidden":
      case "loop":
      case "noModule":
      case "noValidate":
      case "open":
      case "playsInline":
      case "readOnly":
      case "required":
      case "reversed":
      case "scoped":
      case "seamless":
      case "itemScope":
        e && typeof e != "function" && typeof e != "symbol" ? l.setAttribute(a, "") : l.removeAttribute(a);
        break;
      case "capture":
      case "download":
        e === !0 ? l.setAttribute(a, "") : e !== !1 && e != null && typeof e != "function" && typeof e != "symbol" ? l.setAttribute(a, e) : l.removeAttribute(a);
        break;
      case "cols":
      case "rows":
      case "size":
      case "span":
        e != null && typeof e != "function" && typeof e != "symbol" && !isNaN(e) && 1 <= e ? l.setAttribute(a, e) : l.removeAttribute(a);
        break;
      case "rowSpan":
      case "start":
        e == null || typeof e == "function" || typeof e == "symbol" || isNaN(e) ? l.removeAttribute(a) : l.setAttribute(a, e);
        break;
      case "popover":
        k("beforetoggle", l), k("toggle", l), zu(l, "popover", e);
        break;
      case "xlinkActuate":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:actuate",
          e
        );
        break;
      case "xlinkArcrole":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:arcrole",
          e
        );
        break;
      case "xlinkRole":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:role",
          e
        );
        break;
      case "xlinkShow":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:show",
          e
        );
        break;
      case "xlinkTitle":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:title",
          e
        );
        break;
      case "xlinkType":
        Ot(
          l,
          "http://www.w3.org/1999/xlink",
          "xlink:type",
          e
        );
        break;
      case "xmlBase":
        Ot(
          l,
          "http://www.w3.org/XML/1998/namespace",
          "xml:base",
          e
        );
        break;
      case "xmlLang":
        Ot(
          l,
          "http://www.w3.org/XML/1998/namespace",
          "xml:lang",
          e
        );
        break;
      case "xmlSpace":
        Ot(
          l,
          "http://www.w3.org/XML/1998/namespace",
          "xml:space",
          e
        );
        break;
      case "is":
        zu(l, "is", e);
        break;
      case "innerText":
      case "textContent":
        break;
      default:
        (!(2 < a.length) || a[0] !== "o" && a[0] !== "O" || a[1] !== "n" && a[1] !== "N") && (a = Ho.get(a) || a, zu(l, a, e));
    }
  }
  function Yi(l, t, a, e, u, n) {
    switch (a) {
      case "style":
        Rf(l, e, n);
        break;
      case "dangerouslySetInnerHTML":
        if (e != null) {
          if (typeof e != "object" || !("__html" in e))
            throw Error(h(61));
          if (a = e.__html, a != null) {
            if (u.children != null) throw Error(h(60));
            l.innerHTML = a;
          }
        }
        break;
      case "children":
        typeof e == "string" ? Za(l, e) : (typeof e == "number" || typeof e == "bigint") && Za(l, "" + e);
        break;
      case "onScroll":
        e != null && k("scroll", l);
        break;
      case "onScrollEnd":
        e != null && k("scrollend", l);
        break;
      case "onClick":
        e != null && (l.onclick = Tn);
        break;
      case "suppressContentEditableWarning":
      case "suppressHydrationWarning":
      case "innerHTML":
      case "ref":
        break;
      case "innerText":
      case "textContent":
        break;
      default:
        if (!Sf.hasOwnProperty(a))
          l: {
            if (a[0] === "o" && a[1] === "n" && (u = a.endsWith("Capture"), t = a.slice(2, u ? a.length - 7 : void 0), n = l[Jl] || null, n = n != null ? n[a] : null, typeof n == "function" && l.removeEventListener(t, n, u), typeof e == "function")) {
              typeof n != "function" && n !== null && (a in l ? l[a] = null : l.hasAttribute(a) && l.removeAttribute(a)), l.addEventListener(t, e, u);
              break l;
            }
            a in l ? l[a] = e : e === !0 ? l.setAttribute(a, "") : zu(l, a, e);
          }
    }
  }
  function ql(l, t, a) {
    switch (t) {
      case "div":
      case "span":
      case "svg":
      case "path":
      case "a":
      case "g":
      case "p":
      case "li":
        break;
      case "img":
        k("error", l), k("load", l);
        var e = !1, u = !1, n;
        for (n in a)
          if (a.hasOwnProperty(n)) {
            var c = a[n];
            if (c != null)
              switch (n) {
                case "src":
                  e = !0;
                  break;
                case "srcSet":
                  u = !0;
                  break;
                case "children":
                case "dangerouslySetInnerHTML":
                  throw Error(h(137, t));
                default:
                  ul(l, t, n, c, a, null);
              }
          }
        u && ul(l, t, "srcSet", a.srcSet, a, null), e && ul(l, t, "src", a.src, a, null);
        return;
      case "input":
        k("invalid", l);
        var i = n = c = u = null, s = null, m = null;
        for (e in a)
          if (a.hasOwnProperty(e)) {
            var _ = a[e];
            if (_ != null)
              switch (e) {
                case "name":
                  u = _;
                  break;
                case "type":
                  c = _;
                  break;
                case "checked":
                  s = _;
                  break;
                case "defaultChecked":
                  m = _;
                  break;
                case "value":
                  n = _;
                  break;
                case "defaultValue":
                  i = _;
                  break;
                case "children":
                case "dangerouslySetInnerHTML":
                  if (_ != null)
                    throw Error(h(137, t));
                  break;
                default:
                  ul(l, t, e, _, a, null);
              }
          }
        Nf(
          l,
          n,
          i,
          s,
          m,
          c,
          u,
          !1
        ), Nu(l);
        return;
      case "select":
        k("invalid", l), e = c = n = null;
        for (u in a)
          if (a.hasOwnProperty(u) && (i = a[u], i != null))
            switch (u) {
              case "value":
                n = i;
                break;
              case "defaultValue":
                c = i;
                break;
              case "multiple":
                e = i;
              default:
                ul(l, t, u, i, a, null);
            }
        t = n, a = c, l.multiple = !!e, t != null ? Qa(l, !!e, t, !1) : a != null && Qa(l, !!e, a, !0);
        return;
      case "textarea":
        k("invalid", l), n = u = e = null;
        for (c in a)
          if (a.hasOwnProperty(c) && (i = a[c], i != null))
            switch (c) {
              case "value":
                e = i;
                break;
              case "defaultValue":
                u = i;
                break;
              case "children":
                n = i;
                break;
              case "dangerouslySetInnerHTML":
                if (i != null) throw Error(h(91));
                break;
              default:
                ul(l, t, c, i, a, null);
            }
        jf(l, e, u, n), Nu(l);
        return;
      case "option":
        for (s in a)
          if (a.hasOwnProperty(s) && (e = a[s], e != null))
            switch (s) {
              case "selected":
                l.selected = e && typeof e != "function" && typeof e != "symbol";
                break;
              default:
                ul(l, t, s, e, a, null);
            }
        return;
      case "dialog":
        k("beforetoggle", l), k("toggle", l), k("cancel", l), k("close", l);
        break;
      case "iframe":
      case "object":
        k("load", l);
        break;
      case "video":
      case "audio":
        for (e = 0; e < cu.length; e++)
          k(cu[e], l);
        break;
      case "image":
        k("error", l), k("load", l);
        break;
      case "details":
        k("toggle", l);
        break;
      case "embed":
      case "source":
      case "link":
        k("error", l), k("load", l);
      case "area":
      case "base":
      case "br":
      case "col":
      case "hr":
      case "keygen":
      case "meta":
      case "param":
      case "track":
      case "wbr":
      case "menuitem":
        for (m in a)
          if (a.hasOwnProperty(m) && (e = a[m], e != null))
            switch (m) {
              case "children":
              case "dangerouslySetInnerHTML":
                throw Error(h(137, t));
              default:
                ul(l, t, m, e, a, null);
            }
        return;
      default:
        if (In(t)) {
          for (_ in a)
            a.hasOwnProperty(_) && (e = a[_], e !== void 0 && Yi(
              l,
              t,
              _,
              e,
              a,
              void 0
            ));
          return;
        }
    }
    for (i in a)
      a.hasOwnProperty(i) && (e = a[i], e != null && ul(l, t, i, e, a, null));
  }
  function cy(l, t, a, e) {
    switch (t) {
      case "div":
      case "span":
      case "svg":
      case "path":
      case "a":
      case "g":
      case "p":
      case "li":
        break;
      case "input":
        var u = null, n = null, c = null, i = null, s = null, m = null, _ = null;
        for (b in a) {
          var E = a[b];
          if (a.hasOwnProperty(b) && E != null)
            switch (b) {
              case "checked":
                break;
              case "value":
                break;
              case "defaultValue":
                s = E;
              default:
                e.hasOwnProperty(b) || ul(l, t, b, null, e, E);
            }
        }
        for (var g in e) {
          var b = e[g];
          if (E = a[g], e.hasOwnProperty(g) && (b != null || E != null))
            switch (g) {
              case "type":
                n = b;
                break;
              case "name":
                u = b;
                break;
              case "checked":
                m = b;
                break;
              case "defaultChecked":
                _ = b;
                break;
              case "value":
                c = b;
                break;
              case "defaultValue":
                i = b;
                break;
              case "children":
              case "dangerouslySetInnerHTML":
                if (b != null)
                  throw Error(h(137, t));
                break;
              default:
                b !== E && ul(
                  l,
                  t,
                  g,
                  b,
                  e,
                  E
                );
            }
        }
        wn(
          l,
          c,
          i,
          s,
          m,
          _,
          n,
          u
        );
        return;
      case "select":
        b = c = i = g = null;
        for (n in a)
          if (s = a[n], a.hasOwnProperty(n) && s != null)
            switch (n) {
              case "value":
                break;
              case "multiple":
                b = s;
              default:
                e.hasOwnProperty(n) || ul(
                  l,
                  t,
                  n,
                  null,
                  e,
                  s
                );
            }
        for (u in e)
          if (n = e[u], s = a[u], e.hasOwnProperty(u) && (n != null || s != null))
            switch (u) {
              case "value":
                g = n;
                break;
              case "defaultValue":
                i = n;
                break;
              case "multiple":
                c = n;
              default:
                n !== s && ul(
                  l,
                  t,
                  u,
                  n,
                  e,
                  s
                );
            }
        t = i, a = c, e = b, g != null ? Qa(l, !!a, g, !1) : !!e != !!a && (t != null ? Qa(l, !!a, t, !0) : Qa(l, !!a, a ? [] : "", !1));
        return;
      case "textarea":
        b = g = null;
        for (i in a)
          if (u = a[i], a.hasOwnProperty(i) && u != null && !e.hasOwnProperty(i))
            switch (i) {
              case "value":
                break;
              case "children":
                break;
              default:
                ul(l, t, i, null, e, u);
            }
        for (c in e)
          if (u = e[c], n = a[c], e.hasOwnProperty(c) && (u != null || n != null))
            switch (c) {
              case "value":
                g = u;
                break;
              case "defaultValue":
                b = u;
                break;
              case "children":
                break;
              case "dangerouslySetInnerHTML":
                if (u != null) throw Error(h(91));
                break;
              default:
                u !== n && ul(l, t, c, u, e, n);
            }
        Of(l, g, b);
        return;
      case "option":
        for (var G in a)
          if (g = a[G], a.hasOwnProperty(G) && g != null && !e.hasOwnProperty(G))
            switch (G) {
              case "selected":
                l.selected = !1;
                break;
              default:
                ul(
                  l,
                  t,
                  G,
                  null,
                  e,
                  g
                );
            }
        for (s in e)
          if (g = e[s], b = a[s], e.hasOwnProperty(s) && g !== b && (g != null || b != null))
            switch (s) {
              case "selected":
                l.selected = g && typeof g != "function" && typeof g != "symbol";
                break;
              default:
                ul(
                  l,
                  t,
                  s,
                  g,
                  e,
                  b
                );
            }
        return;
      case "img":
      case "link":
      case "area":
      case "base":
      case "br":
      case "col":
      case "embed":
      case "hr":
      case "keygen":
      case "meta":
      case "param":
      case "source":
      case "track":
      case "wbr":
      case "menuitem":
        for (var H in a)
          g = a[H], a.hasOwnProperty(H) && g != null && !e.hasOwnProperty(H) && ul(l, t, H, null, e, g);
        for (m in e)
          if (g = e[m], b = a[m], e.hasOwnProperty(m) && g !== b && (g != null || b != null))
            switch (m) {
              case "children":
              case "dangerouslySetInnerHTML":
                if (g != null)
                  throw Error(h(137, t));
                break;
              default:
                ul(
                  l,
                  t,
                  m,
                  g,
                  e,
                  b
                );
            }
        return;
      default:
        if (In(t)) {
          for (var nl in a)
            g = a[nl], a.hasOwnProperty(nl) && g !== void 0 && !e.hasOwnProperty(nl) && Yi(
              l,
              t,
              nl,
              void 0,
              e,
              g
            );
          for (_ in e)
            g = e[_], b = a[_], !e.hasOwnProperty(_) || g === b || g === void 0 && b === void 0 || Yi(
              l,
              t,
              _,
              g,
              e,
              b
            );
          return;
        }
    }
    for (var y in a)
      g = a[y], a.hasOwnProperty(y) && g != null && !e.hasOwnProperty(y) && ul(l, t, y, null, e, g);
    for (E in e)
      g = e[E], b = a[E], !e.hasOwnProperty(E) || g === b || g == null && b == null || ul(l, t, E, g, e, b);
  }
  var Bi = null, Ci = null;
  function En(l) {
    return l.nodeType === 9 ? l : l.ownerDocument;
  }
  function Dd(l) {
    switch (l) {
      case "http://www.w3.org/2000/svg":
        return 1;
      case "http://www.w3.org/1998/Math/MathML":
        return 2;
      default:
        return 0;
    }
  }
  function Rd(l, t) {
    if (l === 0)
      switch (t) {
        case "svg":
          return 1;
        case "math":
          return 2;
        default:
          return 0;
      }
    return l === 1 && t === "foreignObject" ? 0 : l;
  }
  function Gi(l, t) {
    return l === "textarea" || l === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.children == "bigint" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
  }
  var Xi = null;
  function iy() {
    var l = window.event;
    return l && l.type === "popstate" ? l === Xi ? !1 : (Xi = l, !0) : (Xi = null, !1);
  }
  var Ud = typeof setTimeout == "function" ? setTimeout : void 0, fy = typeof clearTimeout == "function" ? clearTimeout : void 0, Md = typeof Promise == "function" ? Promise : void 0, sy = typeof queueMicrotask == "function" ? queueMicrotask : typeof Md < "u" ? function(l) {
    return Md.resolve(null).then(l).catch(ry);
  } : Ud;
  function ry(l) {
    setTimeout(function() {
      throw l;
    });
  }
  function sa(l) {
    return l === "head";
  }
  function qd(l, t) {
    var a = t, e = 0, u = 0;
    do {
      var n = a.nextSibling;
      if (l.removeChild(a), n && n.nodeType === 8)
        if (a = n.data, a === "/$") {
          if (0 < e && 8 > e) {
            a = e;
            var c = l.ownerDocument;
            if (a & 1 && fu(c.documentElement), a & 2 && fu(c.body), a & 4)
              for (a = c.head, fu(a), c = a.firstChild; c; ) {
                var i = c.nextSibling, s = c.nodeName;
                c[Ee] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && c.rel.toLowerCase() === "stylesheet" || a.removeChild(c), c = i;
              }
          }
          if (u === 0) {
            l.removeChild(n), mu(t);
            return;
          }
          u--;
        } else
          a === "$" || a === "$?" || a === "$!" ? u++ : e = a.charCodeAt(0) - 48;
      else e = 0;
      a = n;
    } while (a);
    mu(t);
  }
  function Qi(l) {
    var t = l.firstChild;
    for (t && t.nodeType === 10 && (t = t.nextSibling); t; ) {
      var a = t;
      switch (t = t.nextSibling, a.nodeName) {
        case "HTML":
        case "HEAD":
        case "BODY":
          Qi(a), Jn(a);
          continue;
        case "SCRIPT":
        case "STYLE":
          continue;
        case "LINK":
          if (a.rel.toLowerCase() === "stylesheet") continue;
      }
      l.removeChild(a);
    }
  }
  function dy(l, t, a, e) {
    for (; l.nodeType === 1; ) {
      var u = a;
      if (l.nodeName.toLowerCase() !== t.toLowerCase()) {
        if (!e && (l.nodeName !== "INPUT" || l.type !== "hidden"))
          break;
      } else if (e) {
        if (!l[Ee])
          switch (t) {
            case "meta":
              if (!l.hasAttribute("itemprop")) break;
              return l;
            case "link":
              if (n = l.getAttribute("rel"), n === "stylesheet" && l.hasAttribute("data-precedence"))
                break;
              if (n !== u.rel || l.getAttribute("href") !== (u.href == null || u.href === "" ? null : u.href) || l.getAttribute("crossorigin") !== (u.crossOrigin == null ? null : u.crossOrigin) || l.getAttribute("title") !== (u.title == null ? null : u.title))
                break;
              return l;
            case "style":
              if (l.hasAttribute("data-precedence")) break;
              return l;
            case "script":
              if (n = l.getAttribute("src"), (n !== (u.src == null ? null : u.src) || l.getAttribute("type") !== (u.type == null ? null : u.type) || l.getAttribute("crossorigin") !== (u.crossOrigin == null ? null : u.crossOrigin)) && n && l.hasAttribute("async") && !l.hasAttribute("itemprop"))
                break;
              return l;
            default:
              return l;
          }
      } else if (t === "input" && l.type === "hidden") {
        var n = u.name == null ? null : "" + u.name;
        if (u.type === "hidden" && l.getAttribute("name") === n)
          return l;
      } else return l;
      if (l = pt(l.nextSibling), l === null) break;
    }
    return null;
  }
  function oy(l, t, a) {
    if (t === "") return null;
    for (; l.nodeType !== 3; )
      if ((l.nodeType !== 1 || l.nodeName !== "INPUT" || l.type !== "hidden") && !a || (l = pt(l.nextSibling), l === null)) return null;
    return l;
  }
  function Zi(l) {
    return l.data === "$!" || l.data === "$?" && l.ownerDocument.readyState === "complete";
  }
  function hy(l, t) {
    var a = l.ownerDocument;
    if (l.data !== "$?" || a.readyState === "complete")
      t();
    else {
      var e = function() {
        t(), a.removeEventListener("DOMContentLoaded", e);
      };
      a.addEventListener("DOMContentLoaded", e), l._reactRetry = e;
    }
  }
  function pt(l) {
    for (; l != null; l = l.nextSibling) {
      var t = l.nodeType;
      if (t === 1 || t === 3) break;
      if (t === 8) {
        if (t = l.data, t === "$" || t === "$!" || t === "$?" || t === "F!" || t === "F")
          break;
        if (t === "/$") return null;
      }
    }
    return l;
  }
  var Vi = null;
  function Hd(l) {
    l = l.previousSibling;
    for (var t = 0; l; ) {
      if (l.nodeType === 8) {
        var a = l.data;
        if (a === "$" || a === "$!" || a === "$?") {
          if (t === 0) return l;
          t--;
        } else a === "/$" && t++;
      }
      l = l.previousSibling;
    }
    return null;
  }
  function Yd(l, t, a) {
    switch (t = En(a), l) {
      case "html":
        if (l = t.documentElement, !l) throw Error(h(452));
        return l;
      case "head":
        if (l = t.head, !l) throw Error(h(453));
        return l;
      case "body":
        if (l = t.body, !l) throw Error(h(454));
        return l;
      default:
        throw Error(h(451));
    }
  }
  function fu(l) {
    for (var t = l.attributes; t.length; )
      l.removeAttributeNode(t[0]);
    Jn(l);
  }
  var bt = /* @__PURE__ */ new Map(), Bd = /* @__PURE__ */ new Set();
  function An(l) {
    return typeof l.getRootNode == "function" ? l.getRootNode() : l.nodeType === 9 ? l : l.ownerDocument;
  }
  var Zt = j.d;
  j.d = {
    f: yy,
    r: vy,
    D: my,
    C: gy,
    L: by,
    m: _y,
    X: py,
    S: Sy,
    M: Ty
  };
  function yy() {
    var l = Zt.f(), t = vn();
    return l || t;
  }
  function vy(l) {
    var t = Ba(l);
    t !== null && t.tag === 5 && t.type === "form" ? er(t) : Zt.r(l);
  }
  var ge = typeof document > "u" ? null : document;
  function Cd(l, t, a) {
    var e = ge;
    if (e && typeof t == "string" && t) {
      var u = dt(t);
      u = 'link[rel="' + l + '"][href="' + u + '"]', typeof a == "string" && (u += '[crossorigin="' + a + '"]'), Bd.has(u) || (Bd.add(u), l = { rel: l, crossOrigin: a, href: t }, e.querySelector(u) === null && (t = e.createElement("link"), ql(t, "link", l), xl(t), e.head.appendChild(t)));
    }
  }
  function my(l) {
    Zt.D(l), Cd("dns-prefetch", l, null);
  }
  function gy(l, t) {
    Zt.C(l, t), Cd("preconnect", l, t);
  }
  function by(l, t, a) {
    Zt.L(l, t, a);
    var e = ge;
    if (e && l && t) {
      var u = 'link[rel="preload"][as="' + dt(t) + '"]';
      t === "image" && a && a.imageSrcSet ? (u += '[imagesrcset="' + dt(
        a.imageSrcSet
      ) + '"]', typeof a.imageSizes == "string" && (u += '[imagesizes="' + dt(
        a.imageSizes
      ) + '"]')) : u += '[href="' + dt(l) + '"]';
      var n = u;
      switch (t) {
        case "style":
          n = be(l);
          break;
        case "script":
          n = _e(l);
      }
      bt.has(n) || (l = N(
        {
          rel: "preload",
          href: t === "image" && a && a.imageSrcSet ? void 0 : l,
          as: t
        },
        a
      ), bt.set(n, l), e.querySelector(u) !== null || t === "style" && e.querySelector(su(n)) || t === "script" && e.querySelector(ru(n)) || (t = e.createElement("link"), ql(t, "link", l), xl(t), e.head.appendChild(t)));
    }
  }
  function _y(l, t) {
    Zt.m(l, t);
    var a = ge;
    if (a && l) {
      var e = t && typeof t.as == "string" ? t.as : "script", u = 'link[rel="modulepreload"][as="' + dt(e) + '"][href="' + dt(l) + '"]', n = u;
      switch (e) {
        case "audioworklet":
        case "paintworklet":
        case "serviceworker":
        case "sharedworker":
        case "worker":
        case "script":
          n = _e(l);
      }
      if (!bt.has(n) && (l = N({ rel: "modulepreload", href: l }, t), bt.set(n, l), a.querySelector(u) === null)) {
        switch (e) {
          case "audioworklet":
          case "paintworklet":
          case "serviceworker":
          case "sharedworker":
          case "worker":
          case "script":
            if (a.querySelector(ru(n)))
              return;
        }
        e = a.createElement("link"), ql(e, "link", l), xl(e), a.head.appendChild(e);
      }
    }
  }
  function Sy(l, t, a) {
    Zt.S(l, t, a);
    var e = ge;
    if (e && l) {
      var u = Ca(e).hoistableStyles, n = be(l);
      t = t || "default";
      var c = u.get(n);
      if (!c) {
        var i = { loading: 0, preload: null };
        if (c = e.querySelector(
          su(n)
        ))
          i.loading = 5;
        else {
          l = N(
            { rel: "stylesheet", href: l, "data-precedence": t },
            a
          ), (a = bt.get(n)) && Li(l, a);
          var s = c = e.createElement("link");
          xl(s), ql(s, "link", l), s._p = new Promise(function(m, _) {
            s.onload = m, s.onerror = _;
          }), s.addEventListener("load", function() {
            i.loading |= 1;
          }), s.addEventListener("error", function() {
            i.loading |= 2;
          }), i.loading |= 4, zn(c, t, e);
        }
        c = {
          type: "stylesheet",
          instance: c,
          count: 1,
          state: i
        }, u.set(n, c);
      }
    }
  }
  function py(l, t) {
    Zt.X(l, t);
    var a = ge;
    if (a && l) {
      var e = Ca(a).hoistableScripts, u = _e(l), n = e.get(u);
      n || (n = a.querySelector(ru(u)), n || (l = N({ src: l, async: !0 }, t), (t = bt.get(u)) && Ki(l, t), n = a.createElement("script"), xl(n), ql(n, "link", l), a.head.appendChild(n)), n = {
        type: "script",
        instance: n,
        count: 1,
        state: null
      }, e.set(u, n));
    }
  }
  function Ty(l, t) {
    Zt.M(l, t);
    var a = ge;
    if (a && l) {
      var e = Ca(a).hoistableScripts, u = _e(l), n = e.get(u);
      n || (n = a.querySelector(ru(u)), n || (l = N({ src: l, async: !0, type: "module" }, t), (t = bt.get(u)) && Ki(l, t), n = a.createElement("script"), xl(n), ql(n, "link", l), a.head.appendChild(n)), n = {
        type: "script",
        instance: n,
        count: 1,
        state: null
      }, e.set(u, n));
    }
  }
  function Gd(l, t, a, e) {
    var u = (u = X.current) ? An(u) : null;
    if (!u) throw Error(h(446));
    switch (l) {
      case "meta":
      case "title":
        return null;
      case "style":
        return typeof a.precedence == "string" && typeof a.href == "string" ? (t = be(a.href), a = Ca(
          u
        ).hoistableStyles, e = a.get(t), e || (e = {
          type: "style",
          instance: null,
          count: 0,
          state: null
        }, a.set(t, e)), e) : { type: "void", instance: null, count: 0, state: null };
      case "link":
        if (a.rel === "stylesheet" && typeof a.href == "string" && typeof a.precedence == "string") {
          l = be(a.href);
          var n = Ca(
            u
          ).hoistableStyles, c = n.get(l);
          if (c || (u = u.ownerDocument || u, c = {
            type: "stylesheet",
            instance: null,
            count: 0,
            state: { loading: 0, preload: null }
          }, n.set(l, c), (n = u.querySelector(
            su(l)
          )) && !n._p && (c.instance = n, c.state.loading = 5), bt.has(l) || (a = {
            rel: "preload",
            as: "style",
            href: a.href,
            crossOrigin: a.crossOrigin,
            integrity: a.integrity,
            media: a.media,
            hrefLang: a.hrefLang,
            referrerPolicy: a.referrerPolicy
          }, bt.set(l, a), n || Ey(
            u,
            l,
            a,
            c.state
          ))), t && e === null)
            throw Error(h(528, ""));
          return c;
        }
        if (t && e !== null)
          throw Error(h(529, ""));
        return null;
      case "script":
        return t = a.async, a = a.src, typeof a == "string" && t && typeof t != "function" && typeof t != "symbol" ? (t = _e(a), a = Ca(
          u
        ).hoistableScripts, e = a.get(t), e || (e = {
          type: "script",
          instance: null,
          count: 0,
          state: null
        }, a.set(t, e)), e) : { type: "void", instance: null, count: 0, state: null };
      default:
        throw Error(h(444, l));
    }
  }
  function be(l) {
    return 'href="' + dt(l) + '"';
  }
  function su(l) {
    return 'link[rel="stylesheet"][' + l + "]";
  }
  function Xd(l) {
    return N({}, l, {
      "data-precedence": l.precedence,
      precedence: null
    });
  }
  function Ey(l, t, a, e) {
    l.querySelector('link[rel="preload"][as="style"][' + t + "]") ? e.loading = 1 : (t = l.createElement("link"), e.preload = t, t.addEventListener("load", function() {
      return e.loading |= 1;
    }), t.addEventListener("error", function() {
      return e.loading |= 2;
    }), ql(t, "link", a), xl(t), l.head.appendChild(t));
  }
  function _e(l) {
    return '[src="' + dt(l) + '"]';
  }
  function ru(l) {
    return "script[async]" + l;
  }
  function Qd(l, t, a) {
    if (t.count++, t.instance === null)
      switch (t.type) {
        case "style":
          var e = l.querySelector(
            'style[data-href~="' + dt(a.href) + '"]'
          );
          if (e)
            return t.instance = e, xl(e), e;
          var u = N({}, a, {
            "data-href": a.href,
            "data-precedence": a.precedence,
            href: null,
            precedence: null
          });
          return e = (l.ownerDocument || l).createElement(
            "style"
          ), xl(e), ql(e, "style", u), zn(e, a.precedence, l), t.instance = e;
        case "stylesheet":
          u = be(a.href);
          var n = l.querySelector(
            su(u)
          );
          if (n)
            return t.state.loading |= 4, t.instance = n, xl(n), n;
          e = Xd(a), (u = bt.get(u)) && Li(e, u), n = (l.ownerDocument || l).createElement("link"), xl(n);
          var c = n;
          return c._p = new Promise(function(i, s) {
            c.onload = i, c.onerror = s;
          }), ql(n, "link", e), t.state.loading |= 4, zn(n, a.precedence, l), t.instance = n;
        case "script":
          return n = _e(a.src), (u = l.querySelector(
            ru(n)
          )) ? (t.instance = u, xl(u), u) : (e = a, (u = bt.get(n)) && (e = N({}, a), Ki(e, u)), l = l.ownerDocument || l, u = l.createElement("script"), xl(u), ql(u, "link", e), l.head.appendChild(u), t.instance = u);
        case "void":
          return null;
        default:
          throw Error(h(443, t.type));
      }
    else
      t.type === "stylesheet" && (t.state.loading & 4) === 0 && (e = t.instance, t.state.loading |= 4, zn(e, a.precedence, l));
    return t.instance;
  }
  function zn(l, t, a) {
    for (var e = a.querySelectorAll(
      'link[rel="stylesheet"][data-precedence],style[data-precedence]'
    ), u = e.length ? e[e.length - 1] : null, n = u, c = 0; c < e.length; c++) {
      var i = e[c];
      if (i.dataset.precedence === t) n = i;
      else if (n !== u) break;
    }
    n ? n.parentNode.insertBefore(l, n.nextSibling) : (t = a.nodeType === 9 ? a.head : a, t.insertBefore(l, t.firstChild));
  }
  function Li(l, t) {
    l.crossOrigin == null && (l.crossOrigin = t.crossOrigin), l.referrerPolicy == null && (l.referrerPolicy = t.referrerPolicy), l.title == null && (l.title = t.title);
  }
  function Ki(l, t) {
    l.crossOrigin == null && (l.crossOrigin = t.crossOrigin), l.referrerPolicy == null && (l.referrerPolicy = t.referrerPolicy), l.integrity == null && (l.integrity = t.integrity);
  }
  var xn = null;
  function Zd(l, t, a) {
    if (xn === null) {
      var e = /* @__PURE__ */ new Map(), u = xn = /* @__PURE__ */ new Map();
      u.set(a, e);
    } else
      u = xn, e = u.get(a), e || (e = /* @__PURE__ */ new Map(), u.set(a, e));
    if (e.has(l)) return e;
    for (e.set(l, null), a = a.getElementsByTagName(l), u = 0; u < a.length; u++) {
      var n = a[u];
      if (!(n[Ee] || n[Cl] || l === "link" && n.getAttribute("rel") === "stylesheet") && n.namespaceURI !== "http://www.w3.org/2000/svg") {
        var c = n.getAttribute(t) || "";
        c = l + c;
        var i = e.get(c);
        i ? i.push(n) : e.set(c, [n]);
      }
    }
    return e;
  }
  function Vd(l, t, a) {
    l = l.ownerDocument || l, l.head.insertBefore(
      a,
      t === "title" ? l.querySelector("head > title") : null
    );
  }
  function Ay(l, t, a) {
    if (a === 1 || t.itemProp != null) return !1;
    switch (l) {
      case "meta":
      case "title":
        return !0;
      case "style":
        if (typeof t.precedence != "string" || typeof t.href != "string" || t.href === "")
          break;
        return !0;
      case "link":
        if (typeof t.rel != "string" || typeof t.href != "string" || t.href === "" || t.onLoad || t.onError)
          break;
        switch (t.rel) {
          case "stylesheet":
            return l = t.disabled, typeof t.precedence == "string" && l == null;
          default:
            return !0;
        }
      case "script":
        if (t.async && typeof t.async != "function" && typeof t.async != "symbol" && !t.onLoad && !t.onError && t.src && typeof t.src == "string")
          return !0;
    }
    return !1;
  }
  function Ld(l) {
    return !(l.type === "stylesheet" && (l.state.loading & 3) === 0);
  }
  var du = null;
  function zy() {
  }
  function xy(l, t, a) {
    if (du === null) throw Error(h(475));
    var e = du;
    if (t.type === "stylesheet" && (typeof a.media != "string" || matchMedia(a.media).matches !== !1) && (t.state.loading & 4) === 0) {
      if (t.instance === null) {
        var u = be(a.href), n = l.querySelector(
          su(u)
        );
        if (n) {
          l = n._p, l !== null && typeof l == "object" && typeof l.then == "function" && (e.count++, e = Nn.bind(e), l.then(e, e)), t.state.loading |= 4, t.instance = n, xl(n);
          return;
        }
        n = l.ownerDocument || l, a = Xd(a), (u = bt.get(u)) && Li(a, u), n = n.createElement("link"), xl(n);
        var c = n;
        c._p = new Promise(function(i, s) {
          c.onload = i, c.onerror = s;
        }), ql(n, "link", a), t.instance = n;
      }
      e.stylesheets === null && (e.stylesheets = /* @__PURE__ */ new Map()), e.stylesheets.set(t, l), (l = t.state.preload) && (t.state.loading & 3) === 0 && (e.count++, t = Nn.bind(e), l.addEventListener("load", t), l.addEventListener("error", t));
    }
  }
  function Ny() {
    if (du === null) throw Error(h(475));
    var l = du;
    return l.stylesheets && l.count === 0 && Ji(l, l.stylesheets), 0 < l.count ? function(t) {
      var a = setTimeout(function() {
        if (l.stylesheets && Ji(l, l.stylesheets), l.unsuspend) {
          var e = l.unsuspend;
          l.unsuspend = null, e();
        }
      }, 6e4);
      return l.unsuspend = t, function() {
        l.unsuspend = null, clearTimeout(a);
      };
    } : null;
  }
  function Nn() {
    if (this.count--, this.count === 0) {
      if (this.stylesheets) Ji(this, this.stylesheets);
      else if (this.unsuspend) {
        var l = this.unsuspend;
        this.unsuspend = null, l();
      }
    }
  }
  var On = null;
  function Ji(l, t) {
    l.stylesheets = null, l.unsuspend !== null && (l.count++, On = /* @__PURE__ */ new Map(), t.forEach(Oy, l), On = null, Nn.call(l));
  }
  function Oy(l, t) {
    if (!(t.state.loading & 4)) {
      var a = On.get(l);
      if (a) var e = a.get(null);
      else {
        a = /* @__PURE__ */ new Map(), On.set(l, a);
        for (var u = l.querySelectorAll(
          "link[data-precedence],style[data-precedence]"
        ), n = 0; n < u.length; n++) {
          var c = u[n];
          (c.nodeName === "LINK" || c.getAttribute("media") !== "not all") && (a.set(c.dataset.precedence, c), e = c);
        }
        e && a.set(null, e);
      }
      u = t.instance, c = u.getAttribute("data-precedence"), n = a.get(c) || e, n === e && a.set(null, u), a.set(c, u), this.count++, e = Nn.bind(this), u.addEventListener("load", e), u.addEventListener("error", e), n ? n.parentNode.insertBefore(u, n.nextSibling) : (l = l.nodeType === 9 ? l.head : l, l.insertBefore(u, l.firstChild)), t.state.loading |= 4;
    }
  }
  var ou = {
    $$typeof: El,
    Provider: null,
    Consumer: null,
    _currentValue: C,
    _currentValue2: C,
    _threadCount: 0
  };
  function jy(l, t, a, e, u, n, c, i) {
    this.tag = 1, this.containerInfo = l, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = Zn(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Zn(0), this.hiddenUpdates = Zn(null), this.identifierPrefix = e, this.onUncaughtError = u, this.onCaughtError = n, this.onRecoverableError = c, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = i, this.incompleteTransitions = /* @__PURE__ */ new Map();
  }
  function Kd(l, t, a, e, u, n, c, i, s, m, _, E) {
    return l = new jy(
      l,
      t,
      a,
      c,
      i,
      s,
      m,
      E
    ), t = 1, n === !0 && (t |= 24), n = at(3, null, null, t), l.current = n, n.stateNode = l, t = Nc(), t.refCount++, l.pooledCache = t, t.refCount++, n.memoizedState = {
      element: e,
      isDehydrated: a,
      cache: t
    }, Rc(n), l;
  }
  function Jd(l) {
    return l ? (l = wa, l) : wa;
  }
  function kd(l, t, a, e, u, n) {
    u = Jd(u), e.context === null ? e.context = u : e.pendingContext = u, e = wt(t), e.payload = { element: a }, n = n === void 0 ? null : n, n !== null && (e.callback = n), a = Ft(l, e, t), a !== null && (it(a, l, t), Ze(a, l, t));
  }
  function $d(l, t) {
    if (l = l.memoizedState, l !== null && l.dehydrated !== null) {
      var a = l.retryLane;
      l.retryLane = a !== 0 && a < t ? a : t;
    }
  }
  function ki(l, t) {
    $d(l, t), (l = l.alternate) && $d(l, t);
  }
  function Wd(l) {
    if (l.tag === 13) {
      var t = Wa(l, 67108864);
      t !== null && it(t, l, 67108864), ki(l, 67108864);
    }
  }
  var jn = !0;
  function Dy(l, t, a, e) {
    var u = S.T;
    S.T = null;
    var n = j.p;
    try {
      j.p = 2, $i(l, t, a, e);
    } finally {
      j.p = n, S.T = u;
    }
  }
  function Ry(l, t, a, e) {
    var u = S.T;
    S.T = null;
    var n = j.p;
    try {
      j.p = 8, $i(l, t, a, e);
    } finally {
      j.p = n, S.T = u;
    }
  }
  function $i(l, t, a, e) {
    if (jn) {
      var u = Wi(e);
      if (u === null)
        Hi(
          l,
          t,
          e,
          Dn,
          a
        ), Fd(l, e);
      else if (My(
        u,
        l,
        t,
        a,
        e
      ))
        e.stopPropagation();
      else if (Fd(l, e), t & 4 && -1 < Uy.indexOf(l)) {
        for (; u !== null; ) {
          var n = Ba(u);
          if (n !== null)
            switch (n.tag) {
              case 3:
                if (n = n.stateNode, n.current.memoizedState.isDehydrated) {
                  var c = ga(n.pendingLanes);
                  if (c !== 0) {
                    var i = n;
                    for (i.pendingLanes |= 2, i.entangledLanes |= 2; c; ) {
                      var s = 1 << 31 - lt(c);
                      i.entanglements[1] |= s, c &= ~s;
                    }
                    Nt(n), (tl & 6) === 0 && (hn = Tt() + 500, nu(0));
                  }
                }
                break;
              case 13:
                i = Wa(n, 2), i !== null && it(i, n, 2), vn(), ki(n, 2);
            }
          if (n = Wi(e), n === null && Hi(
            l,
            t,
            e,
            Dn,
            a
          ), n === u) break;
          u = n;
        }
        u !== null && e.stopPropagation();
      } else
        Hi(
          l,
          t,
          e,
          null,
          a
        );
    }
  }
  function Wi(l) {
    return l = lc(l), wi(l);
  }
  var Dn = null;
  function wi(l) {
    if (Dn = null, l = Ya(l), l !== null) {
      var t = F(l);
      if (t === null) l = null;
      else {
        var a = t.tag;
        if (a === 13) {
          if (l = V(t), l !== null) return l;
          l = null;
        } else if (a === 3) {
          if (t.stateNode.current.memoizedState.isDehydrated)
            return t.tag === 3 ? t.stateNode.containerInfo : null;
          l = null;
        } else t !== l && (l = null);
      }
    }
    return Dn = l, null;
  }
  function wd(l) {
    switch (l) {
      case "beforetoggle":
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "toggle":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 2;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 8;
      case "message":
        switch (go()) {
          case rf:
            return 2;
          case df:
            return 8;
          case pu:
          case bo:
            return 32;
          case of:
            return 268435456;
          default:
            return 32;
        }
      default:
        return 32;
    }
  }
  var Fi = !1, ra = null, da = null, oa = null, hu = /* @__PURE__ */ new Map(), yu = /* @__PURE__ */ new Map(), ha = [], Uy = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(
    " "
  );
  function Fd(l, t) {
    switch (l) {
      case "focusin":
      case "focusout":
        ra = null;
        break;
      case "dragenter":
      case "dragleave":
        da = null;
        break;
      case "mouseover":
      case "mouseout":
        oa = null;
        break;
      case "pointerover":
      case "pointerout":
        hu.delete(t.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        yu.delete(t.pointerId);
    }
  }
  function vu(l, t, a, e, u, n) {
    return l === null || l.nativeEvent !== n ? (l = {
      blockedOn: t,
      domEventName: a,
      eventSystemFlags: e,
      nativeEvent: n,
      targetContainers: [u]
    }, t !== null && (t = Ba(t), t !== null && Wd(t)), l) : (l.eventSystemFlags |= e, t = l.targetContainers, u !== null && t.indexOf(u) === -1 && t.push(u), l);
  }
  function My(l, t, a, e, u) {
    switch (t) {
      case "focusin":
        return ra = vu(
          ra,
          l,
          t,
          a,
          e,
          u
        ), !0;
      case "dragenter":
        return da = vu(
          da,
          l,
          t,
          a,
          e,
          u
        ), !0;
      case "mouseover":
        return oa = vu(
          oa,
          l,
          t,
          a,
          e,
          u
        ), !0;
      case "pointerover":
        var n = u.pointerId;
        return hu.set(
          n,
          vu(
            hu.get(n) || null,
            l,
            t,
            a,
            e,
            u
          )
        ), !0;
      case "gotpointercapture":
        return n = u.pointerId, yu.set(
          n,
          vu(
            yu.get(n) || null,
            l,
            t,
            a,
            e,
            u
          )
        ), !0;
    }
    return !1;
  }
  function Id(l) {
    var t = Ya(l.target);
    if (t !== null) {
      var a = F(t);
      if (a !== null) {
        if (t = a.tag, t === 13) {
          if (t = V(a), t !== null) {
            l.blockedOn = t, xo(l.priority, function() {
              if (a.tag === 13) {
                var e = ct();
                e = Vn(e);
                var u = Wa(a, e);
                u !== null && it(u, a, e), ki(a, e);
              }
            });
            return;
          }
        } else if (t === 3 && a.stateNode.current.memoizedState.isDehydrated) {
          l.blockedOn = a.tag === 3 ? a.stateNode.containerInfo : null;
          return;
        }
      }
    }
    l.blockedOn = null;
  }
  function Rn(l) {
    if (l.blockedOn !== null) return !1;
    for (var t = l.targetContainers; 0 < t.length; ) {
      var a = Wi(l.nativeEvent);
      if (a === null) {
        a = l.nativeEvent;
        var e = new a.constructor(
          a.type,
          a
        );
        Pn = e, a.target.dispatchEvent(e), Pn = null;
      } else
        return t = Ba(a), t !== null && Wd(t), l.blockedOn = a, !1;
      t.shift();
    }
    return !0;
  }
  function Pd(l, t, a) {
    Rn(l) && a.delete(t);
  }
  function qy() {
    Fi = !1, ra !== null && Rn(ra) && (ra = null), da !== null && Rn(da) && (da = null), oa !== null && Rn(oa) && (oa = null), hu.forEach(Pd), yu.forEach(Pd);
  }
  function Un(l, t) {
    l.blockedOn === t && (l.blockedOn = null, Fi || (Fi = !0, f.unstable_scheduleCallback(
      f.unstable_NormalPriority,
      qy
    )));
  }
  var Mn = null;
  function lo(l) {
    Mn !== l && (Mn = l, f.unstable_scheduleCallback(
      f.unstable_NormalPriority,
      function() {
        Mn === l && (Mn = null);
        for (var t = 0; t < l.length; t += 3) {
          var a = l[t], e = l[t + 1], u = l[t + 2];
          if (typeof e != "function") {
            if (wi(e || a) === null)
              continue;
            break;
          }
          var n = Ba(a);
          n !== null && (l.splice(t, 3), t -= 3, wc(
            n,
            {
              pending: !0,
              data: u,
              method: a.method,
              action: e
            },
            e,
            u
          ));
        }
      }
    ));
  }
  function mu(l) {
    function t(s) {
      return Un(s, l);
    }
    ra !== null && Un(ra, l), da !== null && Un(da, l), oa !== null && Un(oa, l), hu.forEach(t), yu.forEach(t);
    for (var a = 0; a < ha.length; a++) {
      var e = ha[a];
      e.blockedOn === l && (e.blockedOn = null);
    }
    for (; 0 < ha.length && (a = ha[0], a.blockedOn === null); )
      Id(a), a.blockedOn === null && ha.shift();
    if (a = (l.ownerDocument || l).$$reactFormReplay, a != null)
      for (e = 0; e < a.length; e += 3) {
        var u = a[e], n = a[e + 1], c = u[Jl] || null;
        if (typeof n == "function")
          c || lo(a);
        else if (c) {
          var i = null;
          if (n && n.hasAttribute("formAction")) {
            if (u = n, c = n[Jl] || null)
              i = c.formAction;
            else if (wi(u) !== null) continue;
          } else i = c.action;
          typeof i == "function" ? a[e + 1] = i : (a.splice(e, 3), e -= 3), lo(a);
        }
      }
  }
  function Ii(l) {
    this._internalRoot = l;
  }
  qn.prototype.render = Ii.prototype.render = function(l) {
    var t = this._internalRoot;
    if (t === null) throw Error(h(409));
    var a = t.current, e = ct();
    kd(a, e, l, t, null, null);
  }, qn.prototype.unmount = Ii.prototype.unmount = function() {
    var l = this._internalRoot;
    if (l !== null) {
      this._internalRoot = null;
      var t = l.containerInfo;
      kd(l.current, 2, null, l, null, null), vn(), t[Ha] = null;
    }
  };
  function qn(l) {
    this._internalRoot = l;
  }
  qn.prototype.unstable_scheduleHydration = function(l) {
    if (l) {
      var t = gf();
      l = { blockedOn: null, target: l, priority: t };
      for (var a = 0; a < ha.length && t !== 0 && t < ha[a].priority; a++) ;
      ha.splice(a, 0, l), a === 0 && Id(l);
    }
  };
  var to = x.version;
  if (to !== "19.1.1")
    throw Error(
      h(
        527,
        to,
        "19.1.1"
      )
    );
  j.findDOMNode = function(l) {
    var t = l._reactInternals;
    if (t === void 0)
      throw typeof l.render == "function" ? Error(h(188)) : (l = Object.keys(l).join(","), Error(h(268, l)));
    return l = R(t), l = l !== null ? T(l) : null, l = l === null ? null : l.stateNode, l;
  };
  var Hy = {
    bundleType: 0,
    version: "19.1.1",
    rendererPackageName: "react-dom",
    currentDispatcherRef: S,
    reconcilerVersion: "19.1.1"
  };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var Hn = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!Hn.isDisabled && Hn.supportsFiber)
      try {
        Se = Hn.inject(
          Hy
        ), Pl = Hn;
      } catch {
      }
  }
  return bu.createRoot = function(l, t) {
    if (!Y(l)) throw Error(h(299));
    var a = !1, e = "", u = gr, n = br, c = _r, i = null;
    return t != null && (t.unstable_strictMode === !0 && (a = !0), t.identifierPrefix !== void 0 && (e = t.identifierPrefix), t.onUncaughtError !== void 0 && (u = t.onUncaughtError), t.onCaughtError !== void 0 && (n = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError), t.unstable_transitionCallbacks !== void 0 && (i = t.unstable_transitionCallbacks)), t = Kd(
      l,
      1,
      !1,
      null,
      null,
      a,
      e,
      u,
      n,
      c,
      i,
      null
    ), l[Ha] = t.current, qi(l), new Ii(t);
  }, bu.hydrateRoot = function(l, t, a) {
    if (!Y(l)) throw Error(h(299));
    var e = !1, u = "", n = gr, c = br, i = _r, s = null, m = null;
    return a != null && (a.unstable_strictMode === !0 && (e = !0), a.identifierPrefix !== void 0 && (u = a.identifierPrefix), a.onUncaughtError !== void 0 && (n = a.onUncaughtError), a.onCaughtError !== void 0 && (c = a.onCaughtError), a.onRecoverableError !== void 0 && (i = a.onRecoverableError), a.unstable_transitionCallbacks !== void 0 && (s = a.unstable_transitionCallbacks), a.formState !== void 0 && (m = a.formState)), t = Kd(
      l,
      1,
      !0,
      t,
      a ?? null,
      e,
      u,
      n,
      c,
      i,
      s,
      m
    ), t.context = Jd(null), a = t.current, e = ct(), e = Vn(e), u = wt(e), u.callback = null, Ft(a, u, e), a = e, t.current.lanes = a, Te(t, a), Nt(t), l[Ha] = t.current, qi(l), new qn(t);
  }, bu.version = "19.1.1", bu;
}
var oo;
function Ky() {
  if (oo) return lf.exports;
  oo = 1;
  function f() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(f);
      } catch (x) {
        console.error(x);
      }
  }
  return f(), lf.exports = Ly(), lf.exports;
}
var Jy = Ky(), Dl = cf();
const ho = {
  status: "anonymous",
  display_name: null,
  email: null,
  provider: null,
  finance_profile_exists: !1,
  error: null
};
function ff({
  auth: f,
  onLoginRequested: x,
  onLogoutRequested: z,
  onFinanceProfileRequested: h
}) {
  return f.status === "authenticated" ? /* @__PURE__ */ r.jsxs("div", { className: "ep-account-actions", "aria-label": "계정 메뉴", children: [
    /* @__PURE__ */ r.jsxs("span", { className: "ep-account-actions__identity", children: [
      f.display_name || f.email || "회원",
      f.provider ? /* @__PURE__ */ r.jsx("small", { children: f.provider }) : null
    ] }),
    /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-account-button", onClick: h, children: "개인 자산" }),
    /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-account-button", onClick: z, children: "로그아웃" })
  ] }) : /* @__PURE__ */ r.jsxs("div", { className: "ep-account-actions", "aria-label": "계정 메뉴", children: [
    f.status === "error" && f.error ? /* @__PURE__ */ r.jsx("span", { className: "ep-account-actions__error", children: f.error.message }) : null,
    /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-account-button ep-account-button--primary", onClick: x, children: "로그인" })
  ] });
}
function sf({ children: f }) {
  return /* @__PURE__ */ r.jsx("div", { className: "ep-shell", children: f });
}
function _u({ title: f, description: x, tone: z = "default", children: h }) {
  return /* @__PURE__ */ r.jsxs("section", { className: `ep-card ep-state-panel ep-state-panel--${z}`, "aria-live": "polite", children: [
    /* @__PURE__ */ r.jsx("h3", { children: f }),
    /* @__PURE__ */ r.jsx("p", { children: x }),
    h
  ] });
}
const ky = [
  { id: "decision", label: "종합 분석" },
  { id: "financing", label: "자금 계획" },
  { id: "risks", label: "리스크" }
];
function $y({ activeSection: f, onSelect: x }) {
  return /* @__PURE__ */ r.jsx("nav", { className: "ep-analysis-nav", "aria-label": "분석 섹션", children: ky.map((z) => /* @__PURE__ */ r.jsx(
    "button",
    {
      type: "button",
      className: `ep-analysis-nav__item${f === z.id ? " is-active" : ""}`,
      "aria-current": f === z.id ? "page" : void 0,
      onClick: () => x(z.id),
      children: z.label
    },
    z.id
  )) });
}
const Wy = [
  "required_cash",
  "expected_loan",
  "cash_shortfall",
  "monthly_payment"
];
function wy({ viewModel: f }) {
  return /* @__PURE__ */ r.jsxs("section", { className: "ep-card ep-analysis-hero", "aria-labelledby": "analysis-decision-title", children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-hero__copy", children: [
      /* @__PURE__ */ r.jsx("span", { className: `ep-badge ep-badge--status-${f.decision.decision_status}`, children: f.analysis_source === "saved" ? "저장 분석" : "신규 분석" }),
      /* @__PURE__ */ r.jsx("h2", { id: "analysis-decision-title", children: f.decision.decision_title }),
      /* @__PURE__ */ r.jsx("p", { children: f.decision.decision_description })
    ] }),
    /* @__PURE__ */ r.jsx("div", { className: "ep-analysis-metric-grid", children: Wy.map((x) => {
      const z = f.financing[x];
      return /* @__PURE__ */ r.jsxs("article", { className: "ep-analysis-metric-card", children: [
        /* @__PURE__ */ r.jsx("span", { className: "ep-meta", children: z.label }),
        /* @__PURE__ */ r.jsx("strong", { children: z.formatted })
      ] }, x);
    }) })
  ] });
}
function Fy({ items: f }) {
  return f.length === 0 ? /* @__PURE__ */ r.jsxs("div", { className: "ep-card ep-analysis-panel", children: [
    /* @__PURE__ */ r.jsx("h3", { children: "리스크" }),
    /* @__PURE__ */ r.jsx("p", { className: "ep-analysis-empty", children: "현재 표시할 리스크가 없습니다." })
  ] }) : /* @__PURE__ */ r.jsx("div", { className: "ep-analysis-risk-list", children: f.map((x, z) => {
    const h = Iy(x, z);
    return /* @__PURE__ */ r.jsxs("article", { className: "ep-card ep-analysis-risk-card", children: [
      /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-risk-card__head", children: [
        /* @__PURE__ */ r.jsx("span", { className: `ep-badge ep-badge--risk-${h.severity}`, children: h.severityLabel }),
        /* @__PURE__ */ r.jsx("strong", { children: h.title })
      ] }),
      h.description ? /* @__PURE__ */ r.jsx("p", { children: h.description }) : null
    ] }, h.key);
  }) });
}
function Iy(f, x) {
  if (typeof f == "string")
    return {
      key: `risk-${x}`,
      title: f,
      description: "",
      severity: "info",
      severityLabel: "안내"
    };
  if (f && typeof f == "object") {
    const z = f, h = Py(z.severity);
    return {
      key: String(z.code ?? z.title ?? `risk-${x}`),
      title: String(z.title ?? z.code ?? `리스크 ${x + 1}`),
      description: String(z.description ?? z.evidence ?? ""),
      severity: h,
      severityLabel: l0(h)
    };
  }
  return {
    key: `risk-${x}`,
    title: `리스크 ${x + 1}`,
    description: "",
    severity: "info",
    severityLabel: "안내"
  };
}
function Py(f) {
  const x = String(f ?? "").toLowerCase();
  return x === "high" ? "high" : x === "medium" ? "medium" : x === "low" ? "low" : "info";
}
function l0(f) {
  return f === "high" ? "주의" : f === "medium" ? "확인" : f === "low" ? "참고" : "안내";
}
function t0({
  viewModel: f,
  onSaveRequested: x,
  onComparisonRequested: z,
  onBackToSearchRequested: h,
  onRetryRequested: Y,
  auth: F = ho,
  onLoginRequested: V = () => {
  },
  onLogoutRequested: fl = () => {
  },
  onFinanceProfileRequested: R = () => {
  }
}) {
  const [T, N] = Dl.useState(f.active_section);
  return Dl.useEffect(() => {
    N(f.active_section);
  }, [f.active_section]), /* @__PURE__ */ r.jsx(sf, { children: /* @__PURE__ */ r.jsxs("div", { className: "ep-page", children: [
    /* @__PURE__ */ r.jsx("header", { className: "ep-header", children: /* @__PURE__ */ r.jsxs("div", { className: "ep-header__inner", children: [
      /* @__PURE__ */ r.jsx("span", { className: "ep-wordmark", children: "Estate Plus" }),
      /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-section-link", onClick: h, children: "단지 검색으로 돌아가기" }),
      /* @__PURE__ */ r.jsx(
        ff,
        {
          auth: F,
          onLoginRequested: V,
          onLogoutRequested: fl,
          onFinanceProfileRequested: R
        }
      )
    ] }) }),
    /* @__PURE__ */ r.jsxs("main", { className: "ep-layout ep-analysis-layout", children: [
      /* @__PURE__ */ r.jsxs("section", { className: "ep-card ep-analysis-header", "aria-labelledby": "analysis-property-title", children: [
        /* @__PURE__ */ r.jsxs("div", { children: [
          /* @__PURE__ */ r.jsxs("p", { className: "ep-meta", children: [
            "분석 #",
            f.property.analysis_id || "-"
          ] }),
          /* @__PURE__ */ r.jsx("h1", { id: "analysis-property-title", children: f.property.complex_name }),
          /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-header__meta", children: [
            /* @__PURE__ */ r.jsx("span", { children: f.property.area_label }),
            /* @__PURE__ */ r.jsx("span", { children: f.property.reference_price_label })
          ] })
        ] }),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-actions", children: [
          /* @__PURE__ */ r.jsx(
            "button",
            {
              type: "button",
              className: "ep-button ep-button--ghost",
              onClick: x,
              disabled: f.analysis_source === "saved",
              children: "저장"
            }
          ),
          /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--secondary", onClick: z, children: "비교로 이동" })
        ] })
      ] }),
      f.page_notice ? /* @__PURE__ */ r.jsx("section", { className: `ep-card ep-analysis-notice ep-analysis-notice--${f.page_notice.level}`, children: /* @__PURE__ */ r.jsx("strong", { children: f.page_notice.message }) }) : null,
      f.page_status === "error" && f.display_error ? /* @__PURE__ */ r.jsxs("section", { className: "ep-analysis-error", children: [
        /* @__PURE__ */ r.jsx(
          _u,
          {
            title: "분석 결과를 표시할 수 없습니다",
            description: f.display_error.message,
            tone: "danger"
          }
        ),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-error__actions", children: [
          /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--secondary", onClick: Y, children: "다시 시도" }),
          /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--ghost", onClick: h, children: "단지 검색으로 돌아가기" })
        ] })
      ] }) : /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
        /* @__PURE__ */ r.jsx(wy, { viewModel: f }),
        /* @__PURE__ */ r.jsx($y, { activeSection: T, onSelect: N }),
        /* @__PURE__ */ r.jsx(e0, { activeSection: T, viewModel: f })
      ] })
    ] })
  ] }) });
}
class a0 extends Dl.Component {
  state = {
    hasError: !1
  };
  static getDerivedStateFromError() {
    return { hasError: !0 };
  }
  componentDidCatch(x, z) {
  }
  render() {
    return this.state.hasError ? /* @__PURE__ */ r.jsxs("div", { className: "ep-card ep-analysis-error-boundary", children: [
      /* @__PURE__ */ r.jsx("h2", { children: "분석 화면을 불러오지 못했습니다." }),
      /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-error__actions", children: [
        /* @__PURE__ */ r.jsx(
          "button",
          {
            type: "button",
            className: "ep-button ep-button--secondary",
            onClick: () => {
              this.setState({ hasError: !1 }), this.props.onRetryRequested();
            },
            children: "다시 시도"
          }
        ),
        /* @__PURE__ */ r.jsx(
          "button",
          {
            type: "button",
            className: "ep-button ep-button--ghost",
            onClick: this.props.onBackToSearchRequested,
            children: "단지 검색으로 돌아가기"
          }
        )
      ] })
    ] }) : this.props.children;
  }
}
function e0({
  activeSection: f,
  viewModel: x
}) {
  return f === "financing" ? /* @__PURE__ */ r.jsxs("section", { className: "ep-card ep-analysis-panel", "aria-labelledby": "analysis-financing-title", children: [
    /* @__PURE__ */ r.jsx("h3", { id: "analysis-financing-title", children: "자금 계획" }),
    /* @__PURE__ */ r.jsx("dl", { className: "ep-analysis-definition-list", children: Object.values(x.financing).map((z) => /* @__PURE__ */ r.jsxs("div", { className: "ep-analysis-definition-list__row", children: [
      /* @__PURE__ */ r.jsx("dt", { children: z.label }),
      /* @__PURE__ */ r.jsx("dd", { children: z.formatted })
    ] }, z.label)) })
  ] }) : f === "risks" ? /* @__PURE__ */ r.jsx(Fy, { items: x.risks.items }) : /* @__PURE__ */ r.jsxs("section", { className: "ep-card ep-analysis-panel", "aria-labelledby": "analysis-overview-title", children: [
    /* @__PURE__ */ r.jsx("h3", { id: "analysis-overview-title", children: "종합 분석" }),
    /* @__PURE__ */ r.jsx("p", { children: x.decision.decision_description })
  ] });
}
function u0(f) {
  const x = f.trim();
  if (!x)
    return "-";
  const z = x.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!z)
    return x;
  const [, h, Y, F] = z;
  return `${h}.${Y}.${F}`;
}
function n0({ item: f, onSelect: x }) {
  const z = u0(f.analyzed_at_label || "");
  return /* @__PURE__ */ r.jsxs(
    "button",
    {
      type: "button",
      className: "ep-card ep-recent-card",
      onClick: () => x(f.analysis_id),
      "aria-label": `${f.complex_name} 최근 분석 다시 보기`,
      children: [
        /* @__PURE__ */ r.jsx("div", { className: "ep-recent-card__head", children: /* @__PURE__ */ r.jsx("span", { className: "ep-badge", children: "최근 분석" }) }),
        /* @__PURE__ */ r.jsx("strong", { className: "ep-recent-card__title", children: f.complex_name || "-" }),
        /* @__PURE__ */ r.jsx("p", { className: "ep-recent-card__meta", children: f.location_label || "-" }),
        /* @__PURE__ */ r.jsx("p", { className: "ep-recent-card__price", children: f.reference_price_label || "-" }),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-recent-card__details", children: [
          /* @__PURE__ */ r.jsx("span", { children: f.area_label || "-" }),
          /* @__PURE__ */ r.jsx("span", { children: z })
        ] }),
        /* @__PURE__ */ r.jsx("div", { className: "ep-recent-card__footer", children: /* @__PURE__ */ r.jsx("span", { className: "ep-recent-card__cta", children: "분석 다시 보기" }) })
      ]
    }
  );
}
function c0({ value: f, onChange: x, onSubmit: z, disabled: h = !1 }) {
  return /* @__PURE__ */ r.jsxs(
    "form",
    {
      className: "ep-searchbar",
      onSubmit: (Y) => {
        Y.preventDefault(), z();
      },
      children: [
        /* @__PURE__ */ r.jsx("label", { className: "ep-searchbar__label ep-visually-hidden", htmlFor: "search-home-query", children: "단지명 또는 주소" }),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-searchbar__controls", children: [
          /* @__PURE__ */ r.jsx(
            "input",
            {
              id: "search-home-query",
              type: "search",
              className: "ep-searchbar__input",
              placeholder: "단지명이나 주소를 입력하세요",
              value: f,
              onChange: (Y) => x(Y.target.value),
              disabled: h
            }
          ),
          /* @__PURE__ */ r.jsx("button", { className: "ep-button ep-button--primary", type: "submit", disabled: h, children: "검색" })
        ] })
      ]
    }
  );
}
function i0({
  viewModel: f,
  onSearchSubmitted: x,
  onRecentAnalysisSelected: z,
  onSearchResultSelected: h,
  onAnalysisRequested: Y,
  onNavigationSelected: F,
  auth: V = ho,
  onLoginRequested: fl = () => {
  },
  onLogoutRequested: R = () => {
  },
  onFinanceProfileRequested: T = () => {
  }
}) {
  const [N, w] = Dl.useState(f.search_query), [$, rl] = Dl.useState(!1), [Sl, Kl] = Dl.useState(
    f.pending_analysis?.selected_area_bucket ?? null
  ), [vl, ft] = Dl.useState(null), Fl = Dl.useRef(null), El = Dl.useRef(null), Ql = Dl.useRef(null), K = f.pending_analysis?.complex_id ?? null, Zl = f.service_description[0] ?? f.service_title, Vl = f.service_description[1] ?? "", Hl = f.recent_analyses.slice(0, 3), st = f.search_status !== "idle", Rl = yo(f.pending_analysis, Sl);
  return Dl.useEffect(() => {
    w(f.search_query);
  }, [f.search_query]), Dl.useEffect(() => {
    Kl(f.pending_analysis?.selected_area_bucket ?? null), ft(f.pending_analysis?.area_options[0]?.listing_options[0]?.listing_id ?? null);
  }, [f.pending_analysis]), Dl.useEffect(() => {
    if (!Rl) {
      ft(null);
      return;
    }
    Rl.listing_options.some((hl) => hl.listing_id === vl) || ft(Rl.listing_options[0]?.listing_id ?? null);
  }, [Rl, vl]), Dl.useEffect(() => {
    if (K === null) {
      Ql.current = null;
      return;
    }
    Ql.current !== K && (Ql.current = K, El.current?.scrollIntoView?.({ behavior: "smooth", block: "start" }));
  }, [K]), Dl.useEffect(() => {
    if (!f.pending_analysis?.auto_submit || !Rl) {
      Fl.current = null;
      return;
    }
    const hl = [
      f.pending_analysis.complex_id,
      Rl.area_bucket,
      vl ?? "transaction"
    ].join(":");
    Fl.current !== hl && (Fl.current = hl, Y({
      complex_id: f.pending_analysis.complex_id,
      area_bucket: Rl.area_bucket,
      listing_id: vl
    }));
  }, [Y, Rl, vl, f.pending_analysis]), /* @__PURE__ */ r.jsx(sf, { children: /* @__PURE__ */ r.jsxs("div", { className: "ep-page", children: [
    /* @__PURE__ */ r.jsx("header", { className: "ep-header", children: /* @__PURE__ */ r.jsxs("div", { className: "ep-header__inner", children: [
      /* @__PURE__ */ r.jsx("span", { className: "ep-wordmark", children: f.service_title }),
      /* @__PURE__ */ r.jsx(
        "button",
        {
          type: "button",
          className: "ep-nav-toggle",
          "aria-expanded": $,
          "aria-controls": "search-home-navigation",
          onClick: () => rl((hl) => !hl),
          children: "메뉴"
        }
      ),
      /* @__PURE__ */ r.jsx(
        "nav",
        {
          id: "search-home-navigation",
          className: `ep-topnav${$ ? " is-open" : ""}`,
          "aria-label": "사용자 메뉴",
          children: f.navigation.map((hl) => /* @__PURE__ */ r.jsx(
            f0,
            {
              item: hl,
              onSelect: () => {
                rl(!1), F(hl.id);
              }
            },
            hl.id
          ))
        }
      ),
      /* @__PURE__ */ r.jsx(
        ff,
        {
          auth: V,
          onLoginRequested: fl,
          onLogoutRequested: R,
          onFinanceProfileRequested: T
        }
      )
    ] }) }),
    /* @__PURE__ */ r.jsxs("main", { className: "ep-layout", children: [
      /* @__PURE__ */ r.jsxs("section", { className: "ep-hero", "aria-labelledby": "search-home-title", children: [
        /* @__PURE__ */ r.jsxs("div", { className: "ep-hero__content", children: [
          /* @__PURE__ */ r.jsx("h1", { id: "search-home-title", children: Zl }),
          /* @__PURE__ */ r.jsx("p", { className: "ep-hero__description", children: Vl })
        ] }),
        /* @__PURE__ */ r.jsx("div", { className: "ep-hero__search", children: /* @__PURE__ */ r.jsx(
          c0,
          {
            value: N,
            onChange: w,
            onSubmit: () => x(N),
            disabled: f.search_status === "loading"
          }
        ) })
      ] }),
      f.page_notice ? /* @__PURE__ */ r.jsxs("section", { className: `ep-card ep-analysis-notice ep-analysis-notice--${f.page_notice.level}`, children: [
        /* @__PURE__ */ r.jsx("strong", { children: f.page_notice.message }),
        f.page_notice.code === "auth_required" ? /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--primary", onClick: fl, children: "로그인" }) : null
      ] }) : null,
      st ? /* @__PURE__ */ r.jsx("section", { className: "ep-results-section", "aria-label": "검색 결과", children: /* @__PURE__ */ r.jsx(
        s0,
        {
          viewModel: f,
          searchQuery: f.search_query || N,
          onSearchResultSelected: h
        }
      ) }) : null,
      f.pending_analysis ? /* @__PURE__ */ r.jsx(
        d0,
        {
          panelRef: El,
          pendingAnalysis: f.pending_analysis,
          searchStatus: f.search_status,
          selectedAreaBucket: Sl,
          selectedListingId: vl,
          onAreaBucketChange: Kl,
          onListingIdChange: ft,
          onSubmit: () => {
            Rl && Y({
              complex_id: f.pending_analysis.complex_id,
              area_bucket: Rl.area_bucket,
              listing_id: vl
            });
          }
        }
      ) : null,
      /* @__PURE__ */ r.jsxs("section", { className: "ep-recent-section", "aria-labelledby": "recent-analyses-title", children: [
        /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
          /* @__PURE__ */ r.jsx("h2", { id: "recent-analyses-title", children: "최근 분석" }),
          /* @__PURE__ */ r.jsxs(
            "button",
            {
              type: "button",
              className: "ep-section-link",
              onClick: () => F("saved_analyses"),
              children: [
                "전체 보기 ",
                /* @__PURE__ */ r.jsx("span", { children: "→" })
              ]
            }
          )
        ] }),
        Hl.length > 0 ? /* @__PURE__ */ r.jsx("div", { className: "ep-recent-grid", children: Hl.map((hl) => /* @__PURE__ */ r.jsx(
          n0,
          {
            item: hl,
            onSelect: z
          },
          hl.analysis_id
        )) }) : /* @__PURE__ */ r.jsx(
          _u,
          {
            title: "저장된 최근 분석이 없습니다",
            description: "기존 분석을 저장하면 여기에서 빠르게 다시 확인할 수 있습니다."
          }
        )
      ] })
    ] })
  ] }) });
}
function f0({
  item: f,
  onSelect: x
}) {
  return /* @__PURE__ */ r.jsx(
    "button",
    {
      type: "button",
      className: `ep-topnav__item${f.active ? " is-active" : ""}`,
      "aria-current": f.active ? "page" : void 0,
      onClick: x,
      children: f.label
    }
  );
}
function s0({
  viewModel: f,
  searchQuery: x,
  onSearchResultSelected: z
}) {
  const h = x.trim();
  return f.search_status === "loading" ? /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
      /* @__PURE__ */ r.jsx("h2", { children: "검색 결과" }),
      h ? /* @__PURE__ */ r.jsxs("span", { className: "ep-meta", children: [
        "검색어: ",
        h
      ] }) : null
    ] }),
    /* @__PURE__ */ r.jsxs("div", { className: "ep-results-list", "data-testid": "loading-state", children: [
      /* @__PURE__ */ r.jsx("div", { className: "ep-skeleton-card" }),
      /* @__PURE__ */ r.jsx("div", { className: "ep-skeleton-card" }),
      /* @__PURE__ */ r.jsx("div", { className: "ep-skeleton-card" })
    ] })
  ] }) : f.search_status === "error" && f.display_error ? /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
      /* @__PURE__ */ r.jsx("h2", { children: "검색 결과" }),
      h ? /* @__PURE__ */ r.jsxs("span", { className: "ep-meta", children: [
        "검색어: ",
        h
      ] }) : null
    ] }),
    /* @__PURE__ */ r.jsx(_u, { title: "검색에 실패했습니다", description: f.display_error.message, tone: "danger" })
  ] }) : f.search_status === "no_results" ? /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
      /* @__PURE__ */ r.jsx("h2", { children: "검색 결과" }),
      h ? /* @__PURE__ */ r.jsxs("span", { className: "ep-meta", children: [
        "검색어: ",
        h
      ] }) : null
    ] }),
    /* @__PURE__ */ r.jsx(_u, { title: "검색 결과가 없습니다", description: "단지명이나 주소를 다시 확인해 주세요" })
  ] }) : /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
      /* @__PURE__ */ r.jsx("h2", { children: "검색 결과" }),
      h ? /* @__PURE__ */ r.jsxs("span", { className: "ep-meta", children: [
        "검색어: ",
        h
      ] }) : null
    ] }),
    /* @__PURE__ */ r.jsx("div", { className: "ep-results-list", children: f.search_results.map((Y) => /* @__PURE__ */ r.jsx(
      r0,
      {
        item: Y,
        onSelect: Y.result_type === "registered_complex" ? z : null
      },
      Y.result_id
    )) })
  ] });
}
function r0({
  item: f,
  onSelect: x
}) {
  return /* @__PURE__ */ r.jsxs("article", { className: "ep-card ep-result-card", children: [
    /* @__PURE__ */ r.jsxs("div", { className: "ep-result-card__head", children: [
      /* @__PURE__ */ r.jsx("span", { className: `ep-badge${f.result_type === "registered_complex" ? " ep-badge--primary" : ""}`, children: f.result_type === "registered_complex" ? "등록 단지" : "주소 검색" }),
      /* @__PURE__ */ r.jsx("span", { className: "ep-meta", children: f.meta })
    ] }),
    /* @__PURE__ */ r.jsx("strong", { children: f.title || "-" }),
    /* @__PURE__ */ r.jsx("p", { children: f.subtitle || "-" }),
    x ? /* @__PURE__ */ r.jsxs(
      "button",
      {
        type: "button",
        className: "ep-result-card__action",
        onClick: () => x(f.result_type, f.result_id),
        children: [
          f.title,
          " 분석 대상 선택"
        ]
      }
    ) : /* @__PURE__ */ r.jsx("span", { className: "ep-meta", children: "등록된 단지에서만 바로 분석할 수 있습니다." })
  ] });
}
function d0({
  panelRef: f,
  pendingAnalysis: x,
  searchStatus: z,
  selectedAreaBucket: h,
  selectedListingId: Y,
  onAreaBucketChange: F,
  onListingIdChange: V,
  onSubmit: fl
}) {
  const R = yo(x, h), T = z === "loading";
  return /* @__PURE__ */ r.jsxs(
    "section",
    {
      ref: f,
      className: "ep-card ep-pending-analysis",
      "aria-labelledby": "pending-analysis-title",
      children: [
        /* @__PURE__ */ r.jsxs("div", { className: "ep-pending-analysis__head", children: [
          /* @__PURE__ */ r.jsxs("div", { children: [
            /* @__PURE__ */ r.jsx("h2", { id: "pending-analysis-title", children: x.complex_name }),
            /* @__PURE__ */ r.jsx("p", { className: "ep-meta", children: x.finance_profile_label })
          ] }),
          T ? /* @__PURE__ */ r.jsx("span", { className: "ep-badge ep-badge--primary", children: "분석 준비 중" }) : null
        ] }),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-pending-analysis__grid", children: [
          /* @__PURE__ */ r.jsxs("label", { className: "ep-pending-analysis__field", children: [
            /* @__PURE__ */ r.jsx("span", { children: "면적" }),
            /* @__PURE__ */ r.jsx(
              "select",
              {
                value: R?.area_bucket ?? "",
                onChange: (N) => F(Number(N.target.value)),
                disabled: T,
                children: x.area_options.map((N) => /* @__PURE__ */ r.jsx("option", { value: N.area_bucket, children: N.label }, N.area_bucket))
              }
            )
          ] }),
          /* @__PURE__ */ r.jsxs("label", { className: "ep-pending-analysis__field", children: [
            /* @__PURE__ */ r.jsx("span", { children: "가격 기준" }),
            /* @__PURE__ */ r.jsx(
              "select",
              {
                value: Y === null ? "transaction" : String(Y),
                onChange: (N) => {
                  const w = N.target.value;
                  V(w === "transaction" ? null : Number(w));
                },
                disabled: T,
                children: (R?.listing_options ?? []).map((N) => /* @__PURE__ */ r.jsx(
                  "option",
                  {
                    value: N.listing_id === null ? "transaction" : String(N.listing_id),
                    children: N.label
                  },
                  N.listing_id === null ? "transaction" : N.listing_id
                ))
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ r.jsxs("div", { className: "ep-pending-analysis__footer", children: [
          /* @__PURE__ */ r.jsxs("span", { className: "ep-meta", children: [
            "거래 ",
            R?.sale_transaction_count ?? 0,
            "건 · 매물 ",
            R?.listing_count ?? 0,
            "건"
          ] }),
          /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--primary", disabled: T, onClick: fl, children: "분석 시작" })
        ] })
      ]
    }
  );
}
function yo(f, x) {
  return f ? f.area_options.find((z) => z.area_bucket === x) ?? f.area_options[0] ?? null : null;
}
function nf(f) {
  return f == null || Number.isNaN(f) ? "-" : Math.abs(f) >= 1e8 ? `${Math.round(f / 1e8 * 10) / 10}억` : new Intl.NumberFormat("ko-KR").format(f);
}
function o0({
  viewModel: f,
  auth: x,
  onSave: z,
  onBack: h,
  onLoginRequested: Y,
  onLogoutRequested: F
}) {
  const [V, fl] = Dl.useState(f.form), [R, T] = Dl.useState(!1);
  Dl.useEffect(() => {
    fl(f.form), T(f.page_status === "saving");
  }, [f.form, f.page_status]);
  const N = ($, rl) => {
    fl((Sl) => ({ ...Sl, [$]: rl === "" ? 0 : Number(rl) }));
  }, w = ($) => {
    if ($.preventDefault(), x.status !== "authenticated") {
      Y();
      return;
    }
    T(!0), z(V);
  };
  return /* @__PURE__ */ r.jsx(sf, { children: /* @__PURE__ */ r.jsxs("div", { className: "ep-page", children: [
    /* @__PURE__ */ r.jsx("header", { className: "ep-header", children: /* @__PURE__ */ r.jsxs("div", { className: "ep-header__inner", children: [
      /* @__PURE__ */ r.jsx("span", { className: "ep-wordmark", children: "Estate Plus" }),
      /* @__PURE__ */ r.jsx(ff, { auth: x, onLoginRequested: Y, onLogoutRequested: F, onFinanceProfileRequested: () => {
      } })
    ] }) }),
    /* @__PURE__ */ r.jsxs("main", { className: "ep-layout ep-finance-layout", children: [
      /* @__PURE__ */ r.jsxs("div", { className: "ep-section-head", children: [
        /* @__PURE__ */ r.jsxs("div", { children: [
          /* @__PURE__ */ r.jsx("p", { className: "ep-meta", children: "내 정보" }),
          /* @__PURE__ */ r.jsx("h1", { children: "개인 자산" })
        ] }),
        /* @__PURE__ */ r.jsx("button", { type: "button", className: "ep-button ep-button--ghost", onClick: h, children: "돌아가기" })
      ] }),
      f.notice ? /* @__PURE__ */ r.jsx("section", { className: `ep-card ep-finance-notice ep-finance-notice--${f.notice.level}`, children: f.notice.message }) : null,
      f.page_status === "auth_required" ? /* @__PURE__ */ r.jsx(_u, { title: "로그인이 필요합니다", description: "로그인 후 개인 자산을 등록하고 분석에 사용할 수 있습니다." }) : /* @__PURE__ */ r.jsxs(r.Fragment, { children: [
        /* @__PURE__ */ r.jsxs("section", { className: "ep-finance-summary", "aria-label": "자산 요약", children: [
          /* @__PURE__ */ r.jsx(Yn, { label: "총자산", value: nf(f.summary.total_assets) }),
          /* @__PURE__ */ r.jsx(Yn, { label: "총부채", value: nf(f.summary.total_debt) }),
          /* @__PURE__ */ r.jsx(Yn, { label: "순자산", value: nf(f.summary.net_worth) }),
          /* @__PURE__ */ r.jsx(Yn, { label: "보유주택", value: `${f.summary.home_count}채` })
        ] }),
        /* @__PURE__ */ r.jsxs("form", { className: "ep-card ep-finance-form", onSubmit: w, children: [
          /* @__PURE__ */ r.jsx("h2", { children: f.page_status === "empty" ? "개인 자산 등록" : "개인 자산 수정" }),
          /* @__PURE__ */ r.jsxs("div", { className: "ep-finance-grid", children: [
            /* @__PURE__ */ r.jsx(Vt, { label: "보유 현금 (억원)", field: "cash_amount_eok", value: V.cash_amount_eok, error: f.field_errors.cash_amount_eok, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "연소득 (억원)", field: "annual_income_eok", value: V.annual_income_eok, error: f.field_errors.annual_income_eok, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "연 이자율 (%)", field: "interest_rate_percent", value: V.interest_rate_percent, error: f.field_errors.interest_rate_percent, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "보유 주택 수", field: "home_count", value: V.home_count, error: f.field_errors.home_count, step: 1, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "보유 부동산 시가 (억원)", field: "owned_real_estate_value_eok", value: V.owned_real_estate_value_eok, error: f.field_errors.owned_real_estate_value_eok, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "보유 부동산 대출 (억원)", field: "owned_real_estate_debt_eok", value: V.owned_real_estate_debt_eok, error: f.field_errors.owned_real_estate_debt_eok, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "신용대출 잔액 (억원)", field: "credit_loan_balance_eok", value: V.credit_loan_balance_eok, error: f.field_errors.credit_loan_balance_eok, onChange: N }),
            /* @__PURE__ */ r.jsx(Vt, { label: "기타 대출 잔액 (억원)", field: "other_loan_balance_eok", value: V.other_loan_balance_eok, error: f.field_errors.other_loan_balance_eok, onChange: N })
          ] }),
          /* @__PURE__ */ r.jsxs("label", { className: "ep-finance-checkbox", children: [
            /* @__PURE__ */ r.jsx("input", { type: "checkbox", checked: V.use_manual_ltv, onChange: ($) => fl((rl) => ({ ...rl, use_manual_ltv: $.target.checked, manual_ltv_rate: $.target.checked ? rl.manual_ltv_rate ?? 0 : null })) }),
            "수동 LTV 사용"
          ] }),
          V.use_manual_ltv ? /* @__PURE__ */ r.jsx(Vt, { label: "수동 LTV (0~1)", field: "manual_ltv_rate", value: V.manual_ltv_rate ?? 0, error: f.field_errors.manual_ltv_rate, step: 0.05, onChange: N }) : null,
          /* @__PURE__ */ r.jsx("div", { className: "ep-finance-actions", children: /* @__PURE__ */ r.jsx("button", { type: "submit", className: "ep-button ep-button--primary", disabled: R, children: R ? "저장 중…" : "저장" }) })
        ] })
      ] })
    ] })
  ] }) });
}
function Vt({ label: f, field: x, value: z, error: h, step: Y = 0.1, onChange: F }) {
  return /* @__PURE__ */ r.jsxs("label", { className: "ep-finance-field", children: [
    /* @__PURE__ */ r.jsx("span", { children: f }),
    /* @__PURE__ */ r.jsx("input", { type: "number", min: "0", step: Y, value: z, onChange: (V) => F(x, V.target.value), "aria-invalid": !!h }),
    h ? /* @__PURE__ */ r.jsx("small", { className: "ep-finance-field__error", children: h }) : null
  ] });
}
function Yn({ label: f, value: x }) {
  return /* @__PURE__ */ r.jsxs("article", { className: "ep-card ep-finance-summary__card", children: [
    /* @__PURE__ */ r.jsx("span", { children: f }),
    /* @__PURE__ */ r.jsx("strong", { children: x })
  ] });
}
const Bn = /* @__PURE__ */ new WeakMap(), y0 = (f) => {
  const x = h0(f.parentElement), z = f.data;
  return z.page === "search-home" && x.render(
    /* @__PURE__ */ r.jsx(
      i0,
      {
        viewModel: z.view_model,
        auth: z.auth,
        onLoginRequested: () => f.setTriggerValue("login_requested", {}),
        onLogoutRequested: () => f.setTriggerValue("logout_requested", {}),
        onFinanceProfileRequested: () => f.setTriggerValue("finance_profile_requested", {}),
        onSearchSubmitted: (h) => {
          const Y = h.trim();
          Y && f.setTriggerValue("search_submitted", { query: Y });
        },
        onRecentAnalysisSelected: (h) => {
          f.setTriggerValue("recent_analysis_selected", { analysis_id: h });
        },
        onSearchResultSelected: (h, Y) => {
          f.setTriggerValue("search_result_selected", {
            result_type: h,
            result_id: Y
          });
        },
        onAnalysisRequested: (h) => {
          f.setTriggerValue("analysis_requested", h);
        },
        onNavigationSelected: (h) => {
          f.setTriggerValue("navigation_selected", { target: h });
        }
      }
    )
  ), z.page === "analysis-dashboard" && x.render(
    /* @__PURE__ */ r.jsx(
      a0,
      {
        onRetryRequested: () => {
          f.setTriggerValue("retry_requested", {});
        },
        onBackToSearchRequested: () => {
          f.setTriggerValue("back_to_search_requested", {});
        },
        children: /* @__PURE__ */ r.jsx(
          t0,
          {
            viewModel: z.view_model,
            auth: z.auth,
            onLoginRequested: () => f.setTriggerValue("login_requested", {}),
            onLogoutRequested: () => f.setTriggerValue("logout_requested", {}),
            onFinanceProfileRequested: () => f.setTriggerValue("finance_profile_requested", {}),
            onSaveRequested: () => {
              f.setTriggerValue("save_requested", {});
            },
            onComparisonRequested: () => {
              f.setTriggerValue("comparison_requested", {});
            },
            onBackToSearchRequested: () => {
              f.setTriggerValue("back_to_search_requested", {});
            },
            onRetryRequested: () => {
              f.setTriggerValue("retry_requested", {});
            }
          }
        )
      }
    )
  ), z.page === "finance-profile" && x.render(
    /* @__PURE__ */ r.jsx(
      o0,
      {
        viewModel: z.view_model,
        auth: z.auth,
        onSave: (h) => f.setTriggerValue("finance_profile_saved", h),
        onBack: () => f.setTriggerValue("finance_profile_back_requested", {}),
        onLoginRequested: () => f.setTriggerValue("login_requested", {}),
        onLogoutRequested: () => f.setTriggerValue("logout_requested", {})
      }
    )
  ), () => {
    const h = Bn.get(f.parentElement);
    h && (h.unmount(), Bn.delete(f.parentElement));
  };
};
function h0(f) {
  const x = f, z = Bn.get(x);
  if (z)
    return z;
  const h = Jy.createRoot(x);
  return Bn.set(x, h), h;
}
export {
  y0 as default
};
