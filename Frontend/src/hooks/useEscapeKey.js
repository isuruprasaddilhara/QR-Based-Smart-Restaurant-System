import { useEffect, useRef } from "react";

export function useEscapeKey(enabled, onEscape) {
  const cbRef = useRef(onEscape);
  cbRef.current = onEscape;

  useEffect(() => {
    if (!enabled) return;
    function onKeyDown(e) {
      if (e.key !== "Escape") return;
      e.preventDefault();
      cbRef.current?.();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [enabled]);
}
