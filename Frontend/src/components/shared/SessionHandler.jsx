import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import {
  AUTH_UPDATED_EVENT,
  getAccessToken,
  getAccessTokenExpiresAtMs,
  notifySessionExpired,
  SESSION_EXPIRED_EVENT,
} from "../../repository/auth";

/**
 * Redirects to /login when the session ends (JWT expiry timer or global 401).
 */
function SessionHandler() {
  const navigate = useNavigate();
  const expiryTimerRef = useRef(null);

  useEffect(() => {
    function onSessionExpired() {
      navigate("/login", { replace: true });
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);
    return () =>
      window.removeEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);
  }, [navigate]);

  useEffect(() => {
    function clearExpiryTimer() {
      if (expiryTimerRef.current != null) {
        clearTimeout(expiryTimerRef.current);
        expiryTimerRef.current = null;
      }
    }

    function scheduleJwtExpiryLogout() {
      clearExpiryTimer();
      if (!getAccessToken()) return;
      const expMs = getAccessTokenExpiresAtMs();
      if (expMs == null) return;
      const delay = expMs - Date.now();
      if (delay <= 0) {
        notifySessionExpired();
        return;
      }
      expiryTimerRef.current = window.setTimeout(() => {
        expiryTimerRef.current = null;
        notifySessionExpired();
      }, delay);
    }

    scheduleJwtExpiryLogout();
    window.addEventListener(AUTH_UPDATED_EVENT, scheduleJwtExpiryLogout);
    return () => {
      clearExpiryTimer();
      window.removeEventListener(AUTH_UPDATED_EVENT, scheduleJwtExpiryLogout);
    };
  }, []);

  return null;
}

export default SessionHandler;
