// Compiles a dart2wasm-generated main module from `source` which can then
// instantiatable via the `instantiate` method.
//
// `source` needs to be a `Response` object (or promise thereof) e.g. created
// via the `fetch()` JS API.
export async function compileStreaming(source) {
  const builtins = {builtins: ['js-string']};
  return new CompiledApp(
      await WebAssembly.compileStreaming(source, builtins), builtins);
}

// Compiles a dart2wasm-generated wasm modules from `bytes` which is then
// instantiatable via the `instantiate` method.
export async function compile(bytes) {
  const builtins = {builtins: ['js-string']};
  return new CompiledApp(await WebAssembly.compile(bytes, builtins), builtins);
}

// DEPRECATED: Please use `compile` or `compileStreaming` to get a compiled app,
// use `instantiate` method to get an instantiated app and then call
// `invokeMain` to invoke the main function.
export async function instantiate(modulePromise, importObjectPromise) {
  var moduleOrCompiledApp = await modulePromise;
  if (!(moduleOrCompiledApp instanceof CompiledApp)) {
    moduleOrCompiledApp = new CompiledApp(moduleOrCompiledApp);
  }
  const instantiatedApp = await moduleOrCompiledApp.instantiate(await importObjectPromise);
  return instantiatedApp.instantiatedModule;
}

// DEPRECATED: Please use `compile` or `compileStreaming` to get a compiled app,
// use `instantiate` method to get an instantiated app and then call
// `invokeMain` to invoke the main function.
export const invoke = (moduleInstance, ...args) => {
  moduleInstance.exports.$invokeMain(args);
}

class CompiledApp {
  constructor(module, builtins) {
    this.module = module;
    this.builtins = builtins;
  }

  // The second argument is an options object containing:
  // `loadDeferredWasm` is a JS function that takes a module name matching a
  //   wasm file produced by the dart2wasm compiler and returns the bytes to
  //   load the module. These bytes can be in either a format supported by
  //   `WebAssembly.compile` or `WebAssembly.compileStreaming`.
  // `loadDynamicModule` is a JS function that takes two string names matching,
  //   in order, a wasm file produced by the dart2wasm compiler during dynamic
  //   module compilation and a corresponding js file produced by the same
  //   compilation. It should return a JS Array containing 2 elements. The first
  //   should be the bytes for the wasm module in a format supported by
  //   `WebAssembly.compile` or `WebAssembly.compileStreaming`. The second
  //   should be the result of using the JS 'import' API on the js file path.
  async instantiate(additionalImports, {loadDeferredWasm, loadDynamicModule} = {}) {
    let dartInstance;

    // Prints to the console
    function printToConsole(value) {
      if (typeof dartPrint == "function") {
        dartPrint(value);
        return;
      }
      if (typeof console == "object" && typeof console.log != "undefined") {
        console.log(value);
        return;
      }
      if (typeof print == "function") {
        print(value);
        return;
      }

      throw "Unable to print message: " + value;
    }

    // A special symbol attached to functions that wrap Dart functions.
    const jsWrappedDartFunctionSymbol = Symbol("JSWrappedDartFunction");

    function finalizeWrapper(dartFunction, wrapped) {
      wrapped.dartFunction = dartFunction;
      wrapped[jsWrappedDartFunctionSymbol] = true;
      return wrapped;
    }

    // Imports
    const dart2wasm = {
            _3: (o, t) => typeof o === t,
      _4: (o, c) => o instanceof c,
      _6: (o,s,v) => o[s] = v,
      _7: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._7(f,arguments.length,x0) }),
      _8: f => finalizeWrapper(f, function(x0,x1) { return dartInstance.exports._8(f,arguments.length,x0,x1) }),
      _9: (o, a) => o + a,
      _36: () => new Array(),
      _37: x0 => new Array(x0),
      _39: x0 => x0.length,
      _41: (x0,x1) => x0[x1],
      _42: (x0,x1,x2) => { x0[x1] = x2 },
      _43: x0 => new Promise(x0),
      _45: (x0,x1,x2) => new DataView(x0,x1,x2),
      _47: x0 => new Int8Array(x0),
      _48: (x0,x1,x2) => new Uint8Array(x0,x1,x2),
      _49: x0 => new Uint8Array(x0),
      _51: x0 => new Uint8ClampedArray(x0),
      _53: x0 => new Int16Array(x0),
      _55: x0 => new Uint16Array(x0),
      _57: x0 => new Int32Array(x0),
      _59: x0 => new Uint32Array(x0),
      _61: x0 => new Float32Array(x0),
      _63: x0 => new Float64Array(x0),
      _64: (x0,x1,x2,x3,x4,x5) => x0.call(x1,x2,x3,x4,x5),
      _65: (x0,x1,x2) => x0.call(x1,x2),
      _69: () => Symbol("jsBoxedDartObjectProperty"),
      _70: (decoder, codeUnits) => decoder.decode(codeUnits),
      _71: () => new TextDecoder("utf-8", {fatal: true}),
      _72: () => new TextDecoder("utf-8", {fatal: false}),
      _73: (s) => +s,
      _74: x0 => new Uint8Array(x0),
      _75: (x0,x1,x2) => x0.set(x1,x2),
      _76: (x0,x1) => x0.transferFromImageBitmap(x1),
      _77: x0 => x0.arrayBuffer(),
      _78: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._78(f,arguments.length,x0) }),
      _79: x0 => new window.FinalizationRegistry(x0),
      _80: (x0,x1,x2,x3) => x0.register(x1,x2,x3),
      _81: (x0,x1) => x0.unregister(x1),
      _82: (x0,x1,x2) => x0.slice(x1,x2),
      _83: (x0,x1) => x0.decode(x1),
      _84: (x0,x1) => x0.segment(x1),
      _85: () => new TextDecoder(),
      _87: x0 => x0.click(),
      _88: x0 => x0.buffer,
      _89: x0 => x0.wasmMemory,
      _90: () => globalThis.window._flutter_skwasmInstance,
      _91: x0 => x0.rasterStartMilliseconds,
      _92: x0 => x0.rasterEndMilliseconds,
      _93: x0 => x0.imageBitmaps,
      _120: x0 => x0.remove(),
      _121: (x0,x1) => x0.append(x1),
      _122: (x0,x1,x2) => x0.insertBefore(x1,x2),
      _123: (x0,x1) => x0.querySelector(x1),
      _125: (x0,x1) => x0.removeChild(x1),
      _203: x0 => x0.stopPropagation(),
      _204: x0 => x0.preventDefault(),
      _206: (x0,x1,x2,x3) => x0.addEventListener(x1,x2,x3),
      _251: x0 => x0.unlock(),
      _252: x0 => x0.getReader(),
      _253: (x0,x1,x2) => x0.addEventListener(x1,x2),
      _254: (x0,x1,x2) => x0.removeEventListener(x1,x2),
      _255: (x0,x1) => x0.item(x1),
      _256: x0 => x0.next(),
      _257: x0 => x0.now(),
      _258: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._258(f,arguments.length,x0) }),
      _259: (x0,x1) => x0.addListener(x1),
      _260: (x0,x1) => x0.removeListener(x1),
      _261: (x0,x1) => x0.matchMedia(x1),
      _262: (x0,x1) => x0.revokeObjectURL(x1),
      _263: x0 => x0.close(),
      _264: (x0,x1,x2,x3,x4) => ({type: x0,data: x1,premultiplyAlpha: x2,colorSpaceConversion: x3,preferAnimation: x4}),
      _265: x0 => new window.ImageDecoder(x0),
      _266: x0 => ({frameIndex: x0}),
      _267: (x0,x1) => x0.decode(x1),
      _268: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._268(f,arguments.length,x0) }),
      _269: (x0,x1) => x0.getModifierState(x1),
      _270: (x0,x1) => x0.removeProperty(x1),
      _271: (x0,x1) => x0.prepend(x1),
      _272: x0 => x0.disconnect(),
      _273: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._273(f,arguments.length,x0) }),
      _274: (x0,x1) => x0.getAttribute(x1),
      _275: (x0,x1) => x0.contains(x1),
      _276: x0 => x0.blur(),
      _277: x0 => x0.hasFocus(),
      _278: (x0,x1) => x0.hasAttribute(x1),
      _279: (x0,x1) => x0.getModifierState(x1),
      _280: (x0,x1) => x0.appendChild(x1),
      _281: (x0,x1) => x0.createTextNode(x1),
      _282: (x0,x1) => x0.removeAttribute(x1),
      _283: x0 => x0.getBoundingClientRect(),
      _284: (x0,x1) => x0.observe(x1),
      _285: x0 => x0.disconnect(),
      _286: (x0,x1) => x0.closest(x1),
      _696: () => globalThis.window.flutterConfiguration,
      _697: x0 => x0.assetBase,
      _703: x0 => x0.debugShowSemanticsNodes,
      _704: x0 => x0.hostElement,
      _705: x0 => x0.multiViewEnabled,
      _706: x0 => x0.nonce,
      _708: x0 => x0.fontFallbackBaseUrl,
      _712: x0 => x0.console,
      _713: x0 => x0.devicePixelRatio,
      _714: x0 => x0.document,
      _715: x0 => x0.history,
      _716: x0 => x0.innerHeight,
      _717: x0 => x0.innerWidth,
      _718: x0 => x0.location,
      _719: x0 => x0.navigator,
      _720: x0 => x0.visualViewport,
      _721: x0 => x0.performance,
      _723: x0 => x0.URL,
      _725: (x0,x1) => x0.getComputedStyle(x1),
      _726: x0 => x0.screen,
      _727: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._727(f,arguments.length,x0) }),
      _728: (x0,x1) => x0.requestAnimationFrame(x1),
      _733: (x0,x1) => x0.warn(x1),
      _735: (x0,x1) => x0.debug(x1),
      _736: x0 => globalThis.parseFloat(x0),
      _737: () => globalThis.window,
      _738: () => globalThis.Intl,
      _739: () => globalThis.Symbol,
      _740: (x0,x1,x2,x3,x4) => globalThis.createImageBitmap(x0,x1,x2,x3,x4),
      _742: x0 => x0.clipboard,
      _743: x0 => x0.maxTouchPoints,
      _744: x0 => x0.vendor,
      _745: x0 => x0.language,
      _746: x0 => x0.platform,
      _747: x0 => x0.userAgent,
      _748: (x0,x1) => x0.vibrate(x1),
      _749: x0 => x0.languages,
      _750: x0 => x0.documentElement,
      _751: (x0,x1) => x0.querySelector(x1),
      _754: (x0,x1) => x0.createElement(x1),
      _757: (x0,x1) => x0.createEvent(x1),
      _758: x0 => x0.activeElement,
      _761: x0 => x0.head,
      _762: x0 => x0.body,
      _764: (x0,x1) => { x0.title = x1 },
      _767: x0 => x0.visibilityState,
      _768: () => globalThis.document,
      _769: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._769(f,arguments.length,x0) }),
      _770: (x0,x1) => x0.dispatchEvent(x1),
      _778: x0 => x0.target,
      _780: x0 => x0.timeStamp,
      _781: x0 => x0.type,
      _783: (x0,x1,x2,x3) => x0.initEvent(x1,x2,x3),
      _789: x0 => x0.baseURI,
      _790: x0 => x0.firstChild,
      _792: (x0,x1) => { x0.innerText = x1 },
      _794: x0 => x0.parentElement,
      _796: (x0,x1) => { x0.textContent = x1 },
      _797: x0 => x0.parentNode,
      _799: x0 => x0.isConnected,
      _803: x0 => x0.firstElementChild,
      _805: x0 => x0.nextElementSibling,
      _806: x0 => x0.clientHeight,
      _807: x0 => x0.clientWidth,
      _808: x0 => x0.offsetHeight,
      _809: x0 => x0.offsetWidth,
      _810: x0 => x0.id,
      _811: (x0,x1) => { x0.id = x1 },
      _814: (x0,x1) => { x0.spellcheck = x1 },
      _815: x0 => x0.tagName,
      _816: x0 => x0.style,
      _818: (x0,x1) => x0.querySelectorAll(x1),
      _819: (x0,x1,x2) => x0.setAttribute(x1,x2),
      _820: x0 => x0.tabIndex,
      _821: (x0,x1) => { x0.tabIndex = x1 },
      _822: (x0,x1) => x0.focus(x1),
      _823: x0 => x0.scrollTop,
      _824: (x0,x1) => { x0.scrollTop = x1 },
      _825: x0 => x0.scrollLeft,
      _826: (x0,x1) => { x0.scrollLeft = x1 },
      _827: x0 => x0.classList,
      _829: (x0,x1) => { x0.className = x1 },
      _831: (x0,x1) => x0.getElementsByClassName(x1),
      _832: (x0,x1) => x0.attachShadow(x1),
      _835: x0 => x0.computedStyleMap(),
      _836: (x0,x1) => x0.get(x1),
      _840: (x0,x1,x2) => x0.supports(x1,x2),
      _841: () => globalThis.CSS,
      _842: (x0,x1) => x0.getPropertyValue(x1),
      _843: (x0,x1,x2,x3) => x0.setProperty(x1,x2,x3),
      _844: x0 => x0.offsetLeft,
      _845: x0 => x0.offsetTop,
      _846: x0 => x0.offsetParent,
      _848: (x0,x1) => { x0.name = x1 },
      _849: x0 => x0.content,
      _850: (x0,x1) => { x0.content = x1 },
      _854: (x0,x1) => { x0.src = x1 },
      _855: x0 => x0.naturalWidth,
      _856: x0 => x0.naturalHeight,
      _860: (x0,x1) => { x0.crossOrigin = x1 },
      _862: (x0,x1) => { x0.decoding = x1 },
      _863: x0 => x0.decode(),
      _868: (x0,x1) => { x0.nonce = x1 },
      _873: (x0,x1) => { x0.width = x1 },
      _875: (x0,x1) => { x0.height = x1 },
      _878: (x0,x1) => x0.getContext(x1),
      _937: x0 => x0.width,
      _938: x0 => x0.height,
      _940: (x0,x1) => x0.fetch(x1),
      _941: x0 => x0.status,
      _943: x0 => x0.body,
      _944: x0 => x0.arrayBuffer(),
      _946: x0 => x0.text(),
      _947: x0 => x0.read(),
      _948: x0 => x0.value,
      _949: x0 => x0.done,
      _951: x0 => x0.name,
      _952: x0 => x0.x,
      _953: x0 => x0.y,
      _956: x0 => x0.top,
      _957: x0 => x0.right,
      _958: x0 => x0.bottom,
      _959: x0 => x0.left,
      _971: x0 => x0.height,
      _972: x0 => x0.width,
      _973: x0 => x0.scale,
      _974: (x0,x1) => { x0.value = x1 },
      _977: (x0,x1) => { x0.placeholder = x1 },
      _979: (x0,x1) => { x0.name = x1 },
      _980: x0 => x0.selectionDirection,
      _981: x0 => x0.selectionStart,
      _982: x0 => x0.selectionEnd,
      _985: x0 => x0.value,
      _987: (x0,x1,x2) => x0.setSelectionRange(x1,x2),
      _988: x0 => x0.readText(),
      _989: (x0,x1) => x0.writeText(x1),
      _991: x0 => x0.altKey,
      _992: x0 => x0.code,
      _993: x0 => x0.ctrlKey,
      _994: x0 => x0.key,
      _995: x0 => x0.keyCode,
      _996: x0 => x0.location,
      _997: x0 => x0.metaKey,
      _998: x0 => x0.repeat,
      _999: x0 => x0.shiftKey,
      _1000: x0 => x0.isComposing,
      _1002: x0 => x0.state,
      _1003: (x0,x1) => x0.go(x1),
      _1005: (x0,x1,x2,x3) => x0.pushState(x1,x2,x3),
      _1006: (x0,x1,x2,x3) => x0.replaceState(x1,x2,x3),
      _1007: x0 => x0.pathname,
      _1008: x0 => x0.search,
      _1009: x0 => x0.hash,
      _1013: x0 => x0.state,
      _1016: (x0,x1) => x0.createObjectURL(x1),
      _1018: x0 => new Blob(x0),
      _1020: x0 => new MutationObserver(x0),
      _1021: (x0,x1,x2) => x0.observe(x1,x2),
      _1022: f => finalizeWrapper(f, function(x0,x1) { return dartInstance.exports._1022(f,arguments.length,x0,x1) }),
      _1025: x0 => x0.attributeName,
      _1026: x0 => x0.type,
      _1027: x0 => x0.matches,
      _1028: x0 => x0.matches,
      _1032: x0 => x0.relatedTarget,
      _1034: x0 => x0.clientX,
      _1035: x0 => x0.clientY,
      _1036: x0 => x0.offsetX,
      _1037: x0 => x0.offsetY,
      _1040: x0 => x0.button,
      _1041: x0 => x0.buttons,
      _1042: x0 => x0.ctrlKey,
      _1046: x0 => x0.pointerId,
      _1047: x0 => x0.pointerType,
      _1048: x0 => x0.pressure,
      _1049: x0 => x0.tiltX,
      _1050: x0 => x0.tiltY,
      _1051: x0 => x0.getCoalescedEvents(),
      _1054: x0 => x0.deltaX,
      _1055: x0 => x0.deltaY,
      _1056: x0 => x0.wheelDeltaX,
      _1057: x0 => x0.wheelDeltaY,
      _1058: x0 => x0.deltaMode,
      _1065: x0 => x0.changedTouches,
      _1068: x0 => x0.clientX,
      _1069: x0 => x0.clientY,
      _1072: x0 => x0.data,
      _1075: (x0,x1) => { x0.disabled = x1 },
      _1077: (x0,x1) => { x0.type = x1 },
      _1078: (x0,x1) => { x0.max = x1 },
      _1079: (x0,x1) => { x0.min = x1 },
      _1080: x0 => x0.value,
      _1081: (x0,x1) => { x0.value = x1 },
      _1082: x0 => x0.disabled,
      _1083: (x0,x1) => { x0.disabled = x1 },
      _1085: (x0,x1) => { x0.placeholder = x1 },
      _1087: (x0,x1) => { x0.name = x1 },
      _1089: (x0,x1) => { x0.autocomplete = x1 },
      _1090: x0 => x0.selectionDirection,
      _1092: x0 => x0.selectionStart,
      _1093: x0 => x0.selectionEnd,
      _1096: (x0,x1,x2) => x0.setSelectionRange(x1,x2),
      _1097: (x0,x1) => x0.add(x1),
      _1100: (x0,x1) => { x0.noValidate = x1 },
      _1101: (x0,x1) => { x0.method = x1 },
      _1102: (x0,x1) => { x0.action = x1 },
      _1103: (x0,x1) => new OffscreenCanvas(x0,x1),
      _1109: (x0,x1) => x0.getContext(x1),
      _1111: x0 => x0.convertToBlob(),
      _1128: x0 => x0.orientation,
      _1129: x0 => x0.width,
      _1130: x0 => x0.height,
      _1131: (x0,x1) => x0.lock(x1),
      _1150: x0 => new ResizeObserver(x0),
      _1153: f => finalizeWrapper(f, function(x0,x1) { return dartInstance.exports._1153(f,arguments.length,x0,x1) }),
      _1161: x0 => x0.length,
      _1162: x0 => x0.iterator,
      _1163: x0 => x0.Segmenter,
      _1164: x0 => x0.v8BreakIterator,
      _1165: (x0,x1) => new Intl.Segmenter(x0,x1),
      _1166: x0 => x0.done,
      _1167: x0 => x0.value,
      _1168: x0 => x0.index,
      _1172: (x0,x1) => new Intl.v8BreakIterator(x0,x1),
      _1173: (x0,x1) => x0.adoptText(x1),
      _1174: x0 => x0.first(),
      _1175: x0 => x0.next(),
      _1176: x0 => x0.current(),
      _1182: x0 => x0.hostElement,
      _1183: x0 => x0.viewConstraints,
      _1184: x0 => x0.initialData,
      _1186: x0 => x0.maxHeight,
      _1187: x0 => x0.maxWidth,
      _1188: x0 => x0.minHeight,
      _1189: x0 => x0.minWidth,
      _1190: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1190(f,arguments.length,x0) }),
      _1191: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1191(f,arguments.length,x0) }),
      _1192: (x0,x1) => ({addView: x0,removeView: x1}),
      _1193: x0 => x0.loader,
      _1194: () => globalThis._flutter,
      _1195: (x0,x1) => x0.didCreateEngineInitializer(x1),
      _1196: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1196(f,arguments.length,x0) }),
      _1197: f => finalizeWrapper(f, function() { return dartInstance.exports._1197(f,arguments.length) }),
      _1198: (x0,x1) => ({initializeEngine: x0,autoStart: x1}),
      _1199: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1199(f,arguments.length,x0) }),
      _1200: x0 => ({runApp: x0}),
      _1201: f => finalizeWrapper(f, function(x0,x1) { return dartInstance.exports._1201(f,arguments.length,x0,x1) }),
      _1202: x0 => x0.length,
      _1203: () => globalThis.window.ImageDecoder,
      _1204: x0 => x0.tracks,
      _1206: x0 => x0.completed,
      _1208: x0 => x0.image,
      _1214: x0 => x0.displayWidth,
      _1215: x0 => x0.displayHeight,
      _1216: x0 => x0.duration,
      _1219: x0 => x0.ready,
      _1220: x0 => x0.selectedTrack,
      _1221: x0 => x0.repetitionCount,
      _1222: x0 => x0.frameCount,
      _1265: x0 => x0.requestFullscreen(),
      _1266: x0 => x0.exitFullscreen(),
      _1267: x0 => x0.createRange(),
      _1268: (x0,x1) => x0.selectNode(x1),
      _1269: x0 => x0.getSelection(),
      _1270: x0 => x0.removeAllRanges(),
      _1271: (x0,x1) => x0.addRange(x1),
      _1272: (x0,x1) => x0.createElement(x1),
      _1273: (x0,x1) => x0.append(x1),
      _1274: (x0,x1,x2) => x0.insertRule(x1,x2),
      _1275: (x0,x1) => x0.add(x1),
      _1276: x0 => x0.preventDefault(),
      _1277: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1277(f,arguments.length,x0) }),
      _1278: (x0,x1,x2) => x0.addEventListener(x1,x2),
      _1279: () => globalThis.window.navigator.userAgent,
      _1280: (x0,x1) => x0.get(x1),
      _1281: x0 => x0.text(),
      _1283: (x0,x1,x2,x3) => x0.addEventListener(x1,x2,x3),
      _1284: (x0,x1,x2,x3) => x0.removeEventListener(x1,x2,x3),
      _1285: (x0,x1) => x0.createElement(x1),
      _1286: (x0,x1,x2) => x0.setAttribute(x1,x2),
      _1292: (x0,x1,x2,x3) => x0.open(x1,x2,x3),
      _1293: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1293(f,arguments.length,x0) }),
      _1294: (x0,x1,x2) => globalThis.jsConnect(x0,x1,x2),
      _1295: (x0,x1) => globalThis.jsSend(x0,x1),
      _1296: x0 => globalThis.jsDisconnect(x0),
      _1297: (x0,x1,x2) => x0.call(x1,x2),
      _1298: (x0,x1,x2,x3,x4,x5) => x0.call(x1,x2,x3,x4,x5),
      _1299: (x0,x1,x2,x3) => x0.call(x1,x2,x3),
      _1300: (x0,x1,x2,x3,x4) => x0.call(x1,x2,x3,x4),
      _1301: x0 => x0.call(),
      _1302: (x0,x1) => x0.append(x1),
      _1303: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1303(f,arguments.length,x0) }),
      _1304: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1304(f,arguments.length,x0) }),
      _1306: (x0,x1,x2,x3,x4,x5,x6) => x0.call(x1,x2,x3,x4,x5,x6),
      _1307: x0 => ({audio: x0}),
      _1308: (x0,x1) => x0.getUserMedia(x1),
      _1309: x0 => x0.getAudioTracks(),
      _1310: x0 => x0.stop(),
      _1311: (x0,x1) => x0.removeTrack(x1),
      _1312: x0 => x0.close(),
      _1313: (x0,x1) => x0.warn(x1),
      _1314: x0 => x0.getSettings(),
      _1315: x0 => ({sampleRate: x0}),
      _1316: x0 => new AudioContext(x0),
      _1317: () => new AudioContext(),
      _1318: x0 => x0.suspend(),
      _1319: x0 => x0.resume(),
      _1320: (x0,x1) => x0.connect(x1),
      _1321: x0 => globalThis.URL.createObjectURL(x0),
      _1322: (x0,x1) => x0.createMediaStreamSource(x1),
      _1323: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1323(f,arguments.length,x0) }),
      _1324: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1324(f,arguments.length,x0) }),
      _1325: (x0,x1) => x0.addModule(x1),
      _1326: x0 => ({parameterData: x0}),
      _1327: (x0,x1,x2) => new AudioWorkletNode(x0,x1,x2),
      _1328: x0 => x0.enumerateDevices(),
      _1329: x0 => globalThis.URL.revokeObjectURL(x0),
      _1330: x0 => x0.pause(),
      _1331: x0 => x0.resume(),
      _1332: x0 => x0.stop(),
      _1333: (x0,x1,x2) => ({mimeType: x0,audioBitsPerSecond: x1,bitsPerSecond: x2}),
      _1334: (x0,x1) => new MediaRecorder(x0,x1),
      _1335: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1335(f,arguments.length,x0) }),
      _1336: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1336(f,arguments.length,x0) }),
      _1337: (x0,x1) => x0.start(x1),
      _1338: x0 => ({type: x0}),
      _1339: (x0,x1) => new Blob(x0,x1),
      _1340: (x0,x1) => globalThis.jsFixWebmDuration(x0,x1),
      _1341: x0 => x0.createAnalyser(),
      _1342: (x0,x1) => x0.getFloatFrequencyData(x1),
      _1343: x0 => globalThis.MediaRecorder.isTypeSupported(x0),
      _1344: x0 => x0.decode(),
      _1345: (x0,x1,x2,x3) => x0.open(x1,x2,x3),
      _1346: (x0,x1,x2) => x0.setRequestHeader(x1,x2),
      _1347: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1347(f,arguments.length,x0) }),
      _1348: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1348(f,arguments.length,x0) }),
      _1349: x0 => x0.send(),
      _1350: () => new XMLHttpRequest(),
      _1351: x0 => globalThis.Wakelock.toggle(x0),
      _1353: (x0,x1) => x0.createMediaElementSource(x1),
      _1354: x0 => x0.createStereoPanner(),
      _1355: x0 => x0.load(),
      _1356: x0 => x0.remove(),
      _1357: x0 => x0.play(),
      _1358: x0 => x0.pause(),
      _1359: (x0,x1) => x0.query(x1),
      _1360: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1360(f,arguments.length,x0) }),
      _1361: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1361(f,arguments.length,x0) }),
      _1362: (x0,x1,x2) => ({enableHighAccuracy: x0,timeout: x1,maximumAge: x2}),
      _1363: (x0,x1,x2,x3) => x0.getCurrentPosition(x1,x2,x3),
      _1364: (x0,x1) => x0.clearWatch(x1),
      _1365: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1365(f,arguments.length,x0) }),
      _1366: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1366(f,arguments.length,x0) }),
      _1367: (x0,x1,x2,x3) => x0.watchPosition(x1,x2,x3),
      _1368: (x0,x1) => x0.getItem(x1),
      _1369: (x0,x1) => x0.removeItem(x1),
      _1370: (x0,x1,x2) => x0.setItem(x1,x2),
      _1371: x0 => ({frequency: x0}),
      _1372: x0 => new Accelerometer(x0),
      _1373: x0 => x0.start(),
      _1374: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1374(f,arguments.length,x0) }),
      _1375: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1375(f,arguments.length,x0) }),
      _1388: x0 => ({name: x0}),
      _1389: x0 => ({video: x0}),
      _1390: x0 => x0.getVideoTracks(),
      _1391: () => globalThis.Notification.requestPermission(),
      _1392: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1392(f,arguments.length,x0) }),
      _1393: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1393(f,arguments.length,x0) }),
      _1394: (x0,x1,x2) => x0.getCurrentPosition(x1,x2),
      _1397: (x0,x1) => x0.querySelector(x1),
      _1398: (x0,x1) => x0.item(x1),
      _1399: () => new FileReader(),
      _1401: (x0,x1) => x0.readAsArrayBuffer(x1),
      _1402: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1402(f,arguments.length,x0) }),
      _1403: (x0,x1,x2) => x0.removeEventListener(x1,x2),
      _1404: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1404(f,arguments.length,x0) }),
      _1405: (x0,x1,x2) => x0.addEventListener(x1,x2),
      _1406: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1406(f,arguments.length,x0) }),
      _1407: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1407(f,arguments.length,x0) }),
      _1408: (x0,x1) => x0.removeChild(x1),
      _1409: x0 => x0.click(),
      _1410: x0 => new Blob(x0),
      _1411: (x0,x1,x2) => x0.slice(x1,x2),
      _1412: x0 => x0.deviceMemory,
      _1414: (x0,x1) => x0.matchMedia(x1),
      _1417: x0 => x0.pyodide,
      _1418: x0 => x0.multiView,
      _1420: x0 => x0.webSocketEndpoint,
      _1421: x0 => x0.routeUrlStrategy,
      _1426: () => globalThis.flet,
      _1427: (x0,x1,x2,x3) => x0.call(x1,x2,x3),
      _1428: (x0,x1,x2,x3,x4) => x0.call(x1,x2,x3,x4),
      _1431: x0 => x0.call(),
      _1432: Date.now,
      _1434: s => new Date(s * 1000).getTimezoneOffset() * 60,
      _1435: s => {
        if (!/^\s*[+-]?(?:Infinity|NaN|(?:\.\d+|\d+(?:\.\d*)?)(?:[eE][+-]?\d+)?)\s*$/.test(s)) {
          return NaN;
        }
        return parseFloat(s);
      },
      _1436: () => {
        let stackString = new Error().stack.toString();
        let frames = stackString.split('\n');
        let drop = 2;
        if (frames[0] === 'Error') {
            drop += 1;
        }
        return frames.slice(drop).join('\n');
      },
      _1437: () => typeof dartUseDateNowForTicks !== "undefined",
      _1438: () => 1000 * performance.now(),
      _1439: () => Date.now(),
      _1440: () => {
        // On browsers return `globalThis.location.href`
        if (globalThis.location != null) {
          return globalThis.location.href;
        }
        return null;
      },
      _1441: () => {
        return typeof process != "undefined" &&
               Object.prototype.toString.call(process) == "[object process]" &&
               process.platform == "win32"
      },
      _1442: () => new WeakMap(),
      _1443: (map, o) => map.get(o),
      _1444: (map, o, v) => map.set(o, v),
      _1445: x0 => new WeakRef(x0),
      _1446: x0 => x0.deref(),
      _1447: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1447(f,arguments.length,x0) }),
      _1448: x0 => new FinalizationRegistry(x0),
      _1449: (x0,x1,x2,x3) => x0.register(x1,x2,x3),
      _1450: (x0,x1,x2) => x0.register(x1,x2),
      _1451: (x0,x1) => x0.unregister(x1),
      _1453: () => globalThis.WeakRef,
      _1454: () => globalThis.FinalizationRegistry,
      _1456: s => JSON.stringify(s),
      _1457: s => printToConsole(s),
      _1458: (o, p, r) => o.replaceAll(p, () => r),
      _1459: (o, p, r) => o.replace(p, () => r),
      _1460: Function.prototype.call.bind(String.prototype.toLowerCase),
      _1461: s => s.toUpperCase(),
      _1462: s => s.trim(),
      _1463: s => s.trimLeft(),
      _1464: s => s.trimRight(),
      _1465: (string, times) => string.repeat(times),
      _1466: Function.prototype.call.bind(String.prototype.indexOf),
      _1467: (s, p, i) => s.lastIndexOf(p, i),
      _1468: (string, token) => string.split(token),
      _1469: Object.is,
      _1470: o => o instanceof Array,
      _1471: (a, i) => a.push(i),
      _1472: (a, i) => a.splice(i, 1)[0],
      _1473: (a, i, v) => a.splice(i, 0, v),
      _1474: (a, l) => a.length = l,
      _1475: a => a.pop(),
      _1476: (a, i) => a.splice(i, 1),
      _1477: (a, s) => a.join(s),
      _1478: (a, s, e) => a.slice(s, e),
      _1479: (a, s, e) => a.splice(s, e),
      _1480: (a, b) => a == b ? 0 : (a > b ? 1 : -1),
      _1481: a => a.length,
      _1482: (a, l) => a.length = l,
      _1483: (a, i) => a[i],
      _1484: (a, i, v) => a[i] = v,
      _1486: o => {
        if (o instanceof ArrayBuffer) return 0;
        if (globalThis.SharedArrayBuffer !== undefined &&
            o instanceof SharedArrayBuffer) {
          return 1;
        }
        return 2;
      },
      _1487: (o, offsetInBytes, lengthInBytes) => {
        var dst = new ArrayBuffer(lengthInBytes);
        new Uint8Array(dst).set(new Uint8Array(o, offsetInBytes, lengthInBytes));
        return new DataView(dst);
      },
      _1489: o => o instanceof Uint8Array,
      _1490: (o, start, length) => new Uint8Array(o.buffer, o.byteOffset + start, length),
      _1491: o => o instanceof Int8Array,
      _1492: (o, start, length) => new Int8Array(o.buffer, o.byteOffset + start, length),
      _1493: o => o instanceof Uint8ClampedArray,
      _1494: (o, start, length) => new Uint8ClampedArray(o.buffer, o.byteOffset + start, length),
      _1495: o => o instanceof Uint16Array,
      _1496: (o, start, length) => new Uint16Array(o.buffer, o.byteOffset + start, length),
      _1497: o => o instanceof Int16Array,
      _1498: (o, start, length) => new Int16Array(o.buffer, o.byteOffset + start, length),
      _1499: o => o instanceof Uint32Array,
      _1500: (o, start, length) => new Uint32Array(o.buffer, o.byteOffset + start, length),
      _1501: o => o instanceof Int32Array,
      _1502: (o, start, length) => new Int32Array(o.buffer, o.byteOffset + start, length),
      _1504: (o, start, length) => new BigInt64Array(o.buffer, o.byteOffset + start, length),
      _1505: o => o instanceof Float32Array,
      _1506: (o, start, length) => new Float32Array(o.buffer, o.byteOffset + start, length),
      _1507: o => o instanceof Float64Array,
      _1508: (o, start, length) => new Float64Array(o.buffer, o.byteOffset + start, length),
      _1509: (t, s) => t.set(s),
      _1510: l => new DataView(new ArrayBuffer(l)),
      _1511: (o) => new DataView(o.buffer, o.byteOffset, o.byteLength),
      _1513: o => o.buffer,
      _1514: o => o.byteOffset,
      _1515: Function.prototype.call.bind(Object.getOwnPropertyDescriptor(DataView.prototype, 'byteLength').get),
      _1516: (b, o) => new DataView(b, o),
      _1517: (b, o, l) => new DataView(b, o, l),
      _1518: Function.prototype.call.bind(DataView.prototype.getUint8),
      _1519: Function.prototype.call.bind(DataView.prototype.setUint8),
      _1520: Function.prototype.call.bind(DataView.prototype.getInt8),
      _1521: Function.prototype.call.bind(DataView.prototype.setInt8),
      _1522: Function.prototype.call.bind(DataView.prototype.getUint16),
      _1523: Function.prototype.call.bind(DataView.prototype.setUint16),
      _1524: Function.prototype.call.bind(DataView.prototype.getInt16),
      _1525: Function.prototype.call.bind(DataView.prototype.setInt16),
      _1526: Function.prototype.call.bind(DataView.prototype.getUint32),
      _1527: Function.prototype.call.bind(DataView.prototype.setUint32),
      _1528: Function.prototype.call.bind(DataView.prototype.getInt32),
      _1529: Function.prototype.call.bind(DataView.prototype.setInt32),
      _1530: Function.prototype.call.bind(DataView.prototype.getBigUint64),
      _1532: Function.prototype.call.bind(DataView.prototype.getBigInt64),
      _1533: Function.prototype.call.bind(DataView.prototype.setBigInt64),
      _1534: Function.prototype.call.bind(DataView.prototype.getFloat32),
      _1535: Function.prototype.call.bind(DataView.prototype.setFloat32),
      _1536: Function.prototype.call.bind(DataView.prototype.getFloat64),
      _1537: Function.prototype.call.bind(DataView.prototype.setFloat64),
      _1550: (ms, c) =>
      setTimeout(() => dartInstance.exports.$invokeCallback(c),ms),
      _1551: (handle) => clearTimeout(handle),
      _1552: (ms, c) =>
      setInterval(() => dartInstance.exports.$invokeCallback(c), ms),
      _1553: (handle) => clearInterval(handle),
      _1554: (c) =>
      queueMicrotask(() => dartInstance.exports.$invokeCallback(c)),
      _1555: () => Date.now(),
      _1560: o => Object.keys(o),
      _1561: (x0,x1) => new WebSocket(x0,x1),
      _1562: (x0,x1) => x0.send(x1),
      _1563: (x0,x1,x2) => x0.close(x1,x2),
      _1565: x0 => x0.close(),
      _1566: (x0,x1) => x0.append(x1),
      _1567: x0 => ({xhrSetup: x0}),
      _1568: x0 => new Hls(x0),
      _1569: () => globalThis.Hls.isSupported(),
      _1571: (x0,x1) => x0.loadSource(x1),
      _1572: (x0,x1) => x0.attachMedia(x1),
      _1573: (x0,x1) => x0.end(x1),
      _1574: (x0,x1) => x0.item(x1),
      _1575: (x0,x1) => x0.appendChild(x1),
      _1578: (x0,x1,x2) => x0.setRequestHeader(x1,x2),
      _1579: f => finalizeWrapper(f, function(x0,x1) { return dartInstance.exports._1579(f,arguments.length,x0,x1) }),
      _1580: (x0,x1) => x0.canPlayType(x1),
      _1581: () => new AbortController(),
      _1582: x0 => x0.abort(),
      _1583: (x0,x1,x2,x3,x4,x5) => ({method: x0,headers: x1,body: x2,credentials: x3,redirect: x4,signal: x5}),
      _1584: (x0,x1) => globalThis.fetch(x0,x1),
      _1585: f => finalizeWrapper(f, function(x0,x1,x2) { return dartInstance.exports._1585(f,arguments.length,x0,x1,x2) }),
      _1586: (x0,x1) => x0.forEach(x1),
      _1587: x0 => x0.getReader(),
      _1588: x0 => x0.read(),
      _1589: x0 => x0.cancel(),
      _1597: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1597(f,arguments.length,x0) }),
      _1598: f => finalizeWrapper(f, function(x0) { return dartInstance.exports._1598(f,arguments.length,x0) }),
      _1603: (x0,x1,x2,x3) => ({method: x0,headers: x1,body: x2,credentials: x3}),
      _1604: (x0,x1,x2) => x0.fetch(x1,x2),
      _1605: (x0,x1) => x0.key(x1),
      _1614: (s, m) => {
        try {
          return new RegExp(s, m);
        } catch (e) {
          return String(e);
        }
      },
      _1615: (x0,x1) => x0.exec(x1),
      _1616: (x0,x1) => x0.test(x1),
      _1617: x0 => x0.pop(),
      _1619: o => o === undefined,
      _1621: o => typeof o === 'function' && o[jsWrappedDartFunctionSymbol] === true,
      _1623: o => {
        const proto = Object.getPrototypeOf(o);
        return proto === Object.prototype || proto === null;
      },
      _1624: o => o instanceof RegExp,
      _1625: (l, r) => l === r,
      _1626: o => o,
      _1627: o => o,
      _1628: o => o,
      _1629: b => !!b,
      _1630: o => o.length,
      _1632: (o, i) => o[i],
      _1633: f => f.dartFunction,
      _1634: () => ({}),
      _1635: () => [],
      _1637: () => globalThis,
      _1638: (constructor, args) => {
        const factoryFunction = constructor.bind.apply(
            constructor, [null, ...args]);
        return new factoryFunction();
      },
      _1639: (o, p) => p in o,
      _1640: (o, p) => o[p],
      _1641: (o, p, v) => o[p] = v,
      _1642: (o, m, a) => o[m].apply(o, a),
      _1644: o => String(o),
      _1645: (p, s, f) => p.then(s, (e) => f(e, e === undefined)),
      _1646: o => {
        if (o === undefined) return 1;
        var type = typeof o;
        if (type === 'boolean') return 2;
        if (type === 'number') return 3;
        if (type === 'string') return 4;
        if (o instanceof Array) return 5;
        if (ArrayBuffer.isView(o)) {
          if (o instanceof Int8Array) return 6;
          if (o instanceof Uint8Array) return 7;
          if (o instanceof Uint8ClampedArray) return 8;
          if (o instanceof Int16Array) return 9;
          if (o instanceof Uint16Array) return 10;
          if (o instanceof Int32Array) return 11;
          if (o instanceof Uint32Array) return 12;
          if (o instanceof Float32Array) return 13;
          if (o instanceof Float64Array) return 14;
          if (o instanceof DataView) return 15;
        }
        if (o instanceof ArrayBuffer) return 16;
        // Feature check for `SharedArrayBuffer` before doing a type-check.
        if (globalThis.SharedArrayBuffer !== undefined &&
            o instanceof SharedArrayBuffer) {
            return 17;
        }
        return 18;
      },
      _1647: o => [o],
      _1648: (o0, o1) => [o0, o1],
      _1649: (o0, o1, o2) => [o0, o1, o2],
      _1650: (o0, o1, o2, o3) => [o0, o1, o2, o3],
      _1651: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const getValue = dartInstance.exports.$wasmI8ArrayGet;
        for (let i = 0; i < length; i++) {
          jsArray[jsArrayOffset + i] = getValue(wasmArray, wasmArrayOffset + i);
        }
      },
      _1652: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const setValue = dartInstance.exports.$wasmI8ArraySet;
        for (let i = 0; i < length; i++) {
          setValue(wasmArray, wasmArrayOffset + i, jsArray[jsArrayOffset + i]);
        }
      },
      _1653: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const getValue = dartInstance.exports.$wasmI16ArrayGet;
        for (let i = 0; i < length; i++) {
          jsArray[jsArrayOffset + i] = getValue(wasmArray, wasmArrayOffset + i);
        }
      },
      _1654: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const setValue = dartInstance.exports.$wasmI16ArraySet;
        for (let i = 0; i < length; i++) {
          setValue(wasmArray, wasmArrayOffset + i, jsArray[jsArrayOffset + i]);
        }
      },
      _1655: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const getValue = dartInstance.exports.$wasmI32ArrayGet;
        for (let i = 0; i < length; i++) {
          jsArray[jsArrayOffset + i] = getValue(wasmArray, wasmArrayOffset + i);
        }
      },
      _1656: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const setValue = dartInstance.exports.$wasmI32ArraySet;
        for (let i = 0; i < length; i++) {
          setValue(wasmArray, wasmArrayOffset + i, jsArray[jsArrayOffset + i]);
        }
      },
      _1657: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const getValue = dartInstance.exports.$wasmF32ArrayGet;
        for (let i = 0; i < length; i++) {
          jsArray[jsArrayOffset + i] = getValue(wasmArray, wasmArrayOffset + i);
        }
      },
      _1658: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const setValue = dartInstance.exports.$wasmF32ArraySet;
        for (let i = 0; i < length; i++) {
          setValue(wasmArray, wasmArrayOffset + i, jsArray[jsArrayOffset + i]);
        }
      },
      _1659: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const getValue = dartInstance.exports.$wasmF64ArrayGet;
        for (let i = 0; i < length; i++) {
          jsArray[jsArrayOffset + i] = getValue(wasmArray, wasmArrayOffset + i);
        }
      },
      _1660: (jsArray, jsArrayOffset, wasmArray, wasmArrayOffset, length) => {
        const setValue = dartInstance.exports.$wasmF64ArraySet;
        for (let i = 0; i < length; i++) {
          setValue(wasmArray, wasmArrayOffset + i, jsArray[jsArrayOffset + i]);
        }
      },
      _1661: x0 => new ArrayBuffer(x0),
      _1662: s => {
        if (/[[\]{}()*+?.\\^$|]/.test(s)) {
            s = s.replace(/[[\]{}()*+?.\\^$|]/g, '\\$&');
        }
        return s;
      },
      _1663: x0 => x0.input,
      _1664: x0 => x0.index,
      _1665: x0 => x0.groups,
      _1666: x0 => x0.flags,
      _1667: x0 => x0.multiline,
      _1668: x0 => x0.ignoreCase,
      _1669: x0 => x0.unicode,
      _1670: x0 => x0.dotAll,
      _1671: (x0,x1) => { x0.lastIndex = x1 },
      _1672: (o, p) => p in o,
      _1673: (o, p) => o[p],
      _1674: (o, p, v) => o[p] = v,
      _1675: (o, p) => delete o[p],
      _1676: x0 => x0.random(),
      _1677: (x0,x1) => x0.getRandomValues(x1),
      _1678: () => globalThis.crypto,
      _1679: () => globalThis.Math,
      _1680: Function.prototype.call.bind(Number.prototype.toString),
      _1681: Function.prototype.call.bind(BigInt.prototype.toString),
      _1682: Function.prototype.call.bind(Number.prototype.toString),
      _1683: (d, digits) => d.toFixed(digits),
      _1687: () => globalThis.document,
      _1688: () => globalThis.window,
      _1693: (x0,x1) => { x0.height = x1 },
      _1695: (x0,x1) => { x0.width = x1 },
      _1698: x0 => x0.head,
      _1699: x0 => x0.classList,
      _1703: (x0,x1) => { x0.innerText = x1 },
      _1704: x0 => x0.style,
      _1706: x0 => x0.sheet,
      _1707: x0 => x0.src,
      _1708: (x0,x1) => { x0.src = x1 },
      _1709: x0 => x0.naturalWidth,
      _1710: x0 => x0.naturalHeight,
      _1717: x0 => x0.offsetX,
      _1718: x0 => x0.offsetY,
      _1719: x0 => x0.button,
      _1726: x0 => x0.status,
      _1727: (x0,x1) => { x0.responseType = x1 },
      _1729: x0 => x0.response,
      _1839: (x0,x1) => { x0.draggable = x1 },
      _1855: x0 => x0.style,
      _2212: (x0,x1) => { x0.target = x1 },
      _2214: (x0,x1) => { x0.download = x1 },
      _2239: (x0,x1) => { x0.href = x1 },
      _2332: (x0,x1) => { x0.src = x1 },
      _2427: x0 => x0.videoWidth,
      _2428: x0 => x0.videoHeight,
      _2440: (x0,x1) => { x0.kind = x1 },
      _2442: (x0,x1) => { x0.src = x1 },
      _2444: (x0,x1) => { x0.srclang = x1 },
      _2446: (x0,x1) => { x0.label = x1 },
      _2457: x0 => x0.error,
      _2459: (x0,x1) => { x0.src = x1 },
      _2464: (x0,x1) => { x0.crossOrigin = x1 },
      _2467: (x0,x1) => { x0.preload = x1 },
      _2468: x0 => x0.buffered,
      _2471: x0 => x0.currentTime,
      _2472: (x0,x1) => { x0.currentTime = x1 },
      _2473: x0 => x0.duration,
      _2474: x0 => x0.paused,
      _2477: x0 => x0.playbackRate,
      _2478: (x0,x1) => { x0.playbackRate = x1 },
      _2487: (x0,x1) => { x0.loop = x1 },
      _2489: (x0,x1) => { x0.controls = x1 },
      _2490: x0 => x0.volume,
      _2491: (x0,x1) => { x0.volume = x1 },
      _2492: x0 => x0.muted,
      _2493: (x0,x1) => { x0.muted = x1 },
      _2498: x0 => x0.textTracks,
      _2508: x0 => x0.code,
      _2509: x0 => x0.message,
      _2543: (x0,x1) => x0[x1],
      _2545: x0 => x0.length,
      _2560: (x0,x1) => { x0.mode = x1 },
      _2562: x0 => x0.activeCues,
      _2583: x0 => x0.length,
      _2779: (x0,x1) => { x0.accept = x1 },
      _2793: x0 => x0.files,
      _2819: (x0,x1) => { x0.multiple = x1 },
      _2837: (x0,x1) => { x0.type = x1 },
      _3086: x0 => x0.src,
      _3087: (x0,x1) => { x0.src = x1 },
      _3089: (x0,x1) => { x0.type = x1 },
      _3093: (x0,x1) => { x0.async = x1 },
      _3095: (x0,x1) => { x0.defer = x1 },
      _3107: (x0,x1) => { x0.charset = x1 },
      _3556: () => globalThis.window,
      _3616: x0 => x0.navigator,
      _3620: x0 => x0.screen,
      _3623: x0 => x0.innerHeight,
      _3627: x0 => x0.screenLeft,
      _3631: x0 => x0.outerHeight,
      _3879: x0 => x0.sessionStorage,
      _3880: x0 => x0.localStorage,
      _3986: x0 => x0.geolocation,
      _3989: x0 => x0.mediaDevices,
      _3991: x0 => x0.permissions,
      _3992: x0 => x0.maxTouchPoints,
      _3999: x0 => x0.appCodeName,
      _4000: x0 => x0.appName,
      _4001: x0 => x0.appVersion,
      _4002: x0 => x0.platform,
      _4003: x0 => x0.product,
      _4004: x0 => x0.productSub,
      _4005: x0 => x0.userAgent,
      _4006: x0 => x0.vendor,
      _4007: x0 => x0.vendorSub,
      _4009: x0 => x0.language,
      _4010: x0 => x0.languages,
      _4016: x0 => x0.hardwareConcurrency,
      _4056: x0 => x0.data,
      _4093: (x0,x1) => { x0.onmessage = x1 },
      _4213: x0 => x0.length,
      _4430: x0 => x0.readyState,
      _4439: x0 => x0.protocol,
      _4443: (x0,x1) => { x0.binaryType = x1 },
      _4446: x0 => x0.code,
      _4447: x0 => x0.reason,
      _5597: x0 => x0.destination,
      _5601: x0 => x0.state,
      _5602: x0 => x0.audioWorklet,
      _5704: (x0,x1) => { x0.fftSize = x1 },
      _5705: x0 => x0.frequencyBinCount,
      _5707: (x0,x1) => { x0.minDecibels = x1 },
      _5709: (x0,x1) => { x0.maxDecibels = x1 },
      _5711: (x0,x1) => { x0.smoothingTimeConstant = x1 },
      _5965: x0 => x0.port,
      _6145: x0 => x0.signal,
      _6157: x0 => x0.length,
      _6206: x0 => x0.firstChild,
      _6217: () => globalThis.document,
      _6276: x0 => x0.documentElement,
      _6297: x0 => x0.body,
      _6299: x0 => x0.head,
      _6627: x0 => x0.id,
      _6628: (x0,x1) => { x0.id = x1 },
      _6652: (x0,x1) => { x0.innerHTML = x1 },
      _6655: x0 => x0.children,
      _7973: x0 => x0.value,
      _7975: x0 => x0.done,
      _8155: x0 => x0.size,
      _8156: x0 => x0.type,
      _8163: x0 => x0.name,
      _8169: x0 => x0.length,
      _8174: x0 => x0.result,
      _8543: x0 => x0.mimeType,
      _8544: x0 => x0.state,
      _8548: (x0,x1) => { x0.onstop = x1 },
      _8550: (x0,x1) => { x0.ondataavailable = x1 },
      _8575: x0 => x0.data,
      _8664: x0 => x0.url,
      _8666: x0 => x0.status,
      _8668: x0 => x0.statusText,
      _8669: x0 => x0.headers,
      _8670: x0 => x0.body,
      _8952: x0 => x0.matches,
      _8965: x0 => x0.width,
      _8966: x0 => x0.height,
      _9057: x0 => x0.state,
      _9457: x0 => x0.active,
      _9716: x0 => x0.sampleRate,
      _9728: x0 => x0.channelCount,
      _9790: x0 => x0.deviceId,
      _9791: x0 => x0.kind,
      _9792: x0 => x0.label,
      _10367: x0 => x0.coords,
      _10368: x0 => x0.timestamp,
      _10370: x0 => x0.accuracy,
      _10371: x0 => x0.latitude,
      _10372: x0 => x0.longitude,
      _10373: x0 => x0.altitude,
      _10374: x0 => x0.altitudeAccuracy,
      _10375: x0 => x0.heading,
      _10376: x0 => x0.speed,
      _10377: x0 => x0.code,
      _10378: x0 => x0.message,
      _10786: (x0,x1) => { x0.border = x1 },
      _11064: (x0,x1) => { x0.display = x1 },
      _11228: (x0,x1) => { x0.height = x1 },
      _11918: (x0,x1) => { x0.width = x1 },
      _12286: x0 => x0.name,
      _12287: x0 => x0.message,
      _13004: () => globalThis.console,
      _13028: x0 => x0.x,
      _13029: x0 => x0.y,
      _13030: x0 => x0.z,
      _13031: (x0,x1) => { x0.onreading = x1 },
      _13032: (x0,x1) => { x0.onerror = x1 },
      _13048: x0 => x0.error,
      _13049: x0 => x0.name,
      _13050: x0 => x0.message,

    };

    const baseImports = {
      dart2wasm: dart2wasm,
      Math: Math,
      Date: Date,
      Object: Object,
      Array: Array,
      Reflect: Reflect,
      S: new Proxy({}, { get(_, prop) { return prop; } }),

    };

    const jsStringPolyfill = {
      "charCodeAt": (s, i) => s.charCodeAt(i),
      "compare": (s1, s2) => {
        if (s1 < s2) return -1;
        if (s1 > s2) return 1;
        return 0;
      },
      "concat": (s1, s2) => s1 + s2,
      "equals": (s1, s2) => s1 === s2,
      "fromCharCode": (i) => String.fromCharCode(i),
      "length": (s) => s.length,
      "substring": (s, a, b) => s.substring(a, b),
      "fromCharCodeArray": (a, start, end) => {
        if (end <= start) return '';

        const read = dartInstance.exports.$wasmI16ArrayGet;
        let result = '';
        let index = start;
        const chunkLength = Math.min(end - index, 500);
        let array = new Array(chunkLength);
        while (index < end) {
          const newChunkLength = Math.min(end - index, 500);
          for (let i = 0; i < newChunkLength; i++) {
            array[i] = read(a, index++);
          }
          if (newChunkLength < chunkLength) {
            array = array.slice(0, newChunkLength);
          }
          result += String.fromCharCode(...array);
        }
        return result;
      },
      "intoCharCodeArray": (s, a, start) => {
        if (s === '') return 0;

        const write = dartInstance.exports.$wasmI16ArraySet;
        for (var i = 0; i < s.length; ++i) {
          write(a, start++, s.charCodeAt(i));
        }
        return s.length;
      },
      "test": (s) => typeof s == "string",
    };


    

    dartInstance = await WebAssembly.instantiate(this.module, {
      ...baseImports,
      ...additionalImports,
      
      "wasm:js-string": jsStringPolyfill,
    });

    return new InstantiatedApp(this, dartInstance);
  }
}

class InstantiatedApp {
  constructor(compiledApp, instantiatedModule) {
    this.compiledApp = compiledApp;
    this.instantiatedModule = instantiatedModule;
  }

  // Call the main function with the given arguments.
  invokeMain(...args) {
    this.instantiatedModule.exports.$invokeMain(args);
  }
}
