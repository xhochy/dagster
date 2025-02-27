import { Toaster, Position, Intent } from "@blueprintjs/core";

export const DEFAULT_RESULT_NAME = "result";

// The address to the dagit server (eg: http://localhost:5000) based
// on our current "GRAPHQL_URI" env var. Note there is no trailing slash.
export const ROOT_SERVER_URI = (process.env.REACT_APP_GRAPHQL_URI || "")
  .replace("wss://", "https://")
  .replace("ws://", "http://")
  .replace("/graphql", "");

export const WEBSOCKET_URI =
  process.env.REACT_APP_GRAPHQL_URI ||
  `${document.location.protocol === "https:" ? "wss" : "ws"}://${
    document.location.host
  }/graphql`;

export const SharedToaster = Toaster.create(
  { position: Position.TOP },
  document.body
);

export async function copyValue(event: React.MouseEvent<any>, value: string) {
  event.preventDefault();

  const el = document.createElement("input");
  document.body.appendChild(el);
  el.value = value;
  el.select();
  document.execCommand("copy");
  el.remove();

  SharedToaster.show({
    message: "Copied to clipboard!",
    icon: "clipboard",
    intent: Intent.NONE
  });
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait = 100
): T {
  let timeout: any | null = null;
  let args: any[] | null = null;
  let timestamp = 0;
  let result: ReturnType<T>;

  function later() {
    const last = Date.now() - timestamp;

    if (last < wait && last >= 0) {
      timeout = setTimeout(later, wait - last);
    } else {
      timeout = null;
      // eslint-disable-next-line
      result = func.apply(null, args);
      args = null;
    }
  }

  const debounced = function(...newArgs: any[]) {
    timestamp = Date.now();
    args = newArgs;
    if (!timeout) {
      timeout = setTimeout(later, wait);
    }

    return result;
  };

  return (debounced as any) as T;
}

function twoDigit(v: number) {
  return `${v < 10 ? "0" : ""}${v}`;
}

export function formatStepKey(stepKey: string | null | false) {
  return (stepKey || "").replace(/\.compute$/, "");
}

export function formatElapsedTime(msec: number) {
  let text = "";

  if (msec < 0) {
    text = `0 msec`;
  } else if (msec < 1000) {
    // < 1 second, show "X msec"
    text = `${Math.ceil(msec)} msec`;
  } else {
    // < 1 hour, show "42:12"
    const sec = Math.round(msec / 1000) % 60;
    const min = Math.floor(msec / 1000 / 60) % 60;
    const hours = Math.floor(msec / 1000 / 60 / 60);

    if (hours > 0) {
      text = `${hours}:${twoDigit(min)}:${twoDigit(sec)}`;
    } else {
      text = `${min}:${twoDigit(sec)}`;
    }
  }
  return text;
}

// Simple memoization function for methods that take a single object argument.
// Returns a memoized copy of the provided function which retrieves the result
// from a cache after the first invocation with a given object.
//
// Uses WeakMap to tie the lifecycle of the cache to the lifecycle of the
// object argument.
//
export function weakmapMemoize<T extends object, R>(
  fn: (arg: T, ...rest: any[]) => R
): (arg: T, ...rest: any[]) => R {
  const cache = new WeakMap();
  return (arg: T, ...rest: any[]) => {
    if (cache.has(arg)) {
      return cache.get(arg);
    }
    const r = fn(arg, ...rest);
    cache.set(arg, r);
    return r;
  };
}

export function titleOfIO(i: {
  solid: { name: string };
  definition: { name: string };
}) {
  return i.solid.name !== DEFAULT_RESULT_NAME
    ? `${i.solid.name}:${i.definition.name}`
    : i.solid.name;
}

export function assertUnreachable(_: never): never {
  throw new Error("Didn't expect to get here");
}
