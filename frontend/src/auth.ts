import { setAccessToken, getAccessToken } from "./api.ts";

const canvasUrl = import.meta.env.VITE_REACT_APP_CANVAS_URL;
const clientId = import.meta.env.VITE_REACT_APP_CLIENT_ID;
const redirectUri = import.meta.env.VITE_REACT_APP_HOST_URI;
const backendUrl = import.meta.env.VITE_REACT_APP_API_URL;
const isLocalMode = import.meta.env.VITE_REACT_APP_LOCAL_MODE;

const REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes in milliseconds

export const redirectToCanvas = () => {
  window.location.href = `${canvasUrl}/login/oauth2/auth?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&state=aceit`;
};

export const fetchAccessToken = async (code: string) => {
  try {
    const response = await fetch(`${backendUrl}/ui/general/log-in`, {
      method: "POST",
      headers: new Headers({
        Authorization: String(code),
        Islocaltesting: String(isLocalMode),
        "Content-Type": "application/json",
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.body}`);
    }

    const data = await response.json();

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    const expiryTime = new Date(
      new Date().getTime() + data.expires_in * 1000
    ).toString();
    localStorage.setItem("token_expiry", expiryTime);
    return data.access_token;
  } catch (error) {
    console.error("Failed to fetch access token:", error);
    throw error;
  }
};

export const refreshAccessToken = async (refreshToken: string) => {
  try {
    const response = await fetch(`${backendUrl}/ui/general/refresh-token`, {
      method: "POST",
      headers: {
        Authorization: refreshToken,
        Islocaltesting: String(isLocalMode),
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.body}`);
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    const expiryTime = new Date(
      new Date().getTime() + data.expires_in * 1000
    ).toString();
    localStorage.setItem("token_expiry", expiryTime);
    return data.access_token;
  } catch (error) {
    console.error("Failed to refresh access token:", error);
    throw error;
  }
};

export const setupTokenRefreshTimer = (refreshToken: string, delay: number) => {
  setTimeout(() => {
    refreshAccessToken(refreshToken);
  }, delay - REFRESH_THRESHOLD);
};

const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("token_expiry");
};

const handleTokenRefresh = async (
  refreshToken: string,
  setAccessTokenState: (token: string) => void
) => {
  const newToken = await refreshAccessToken(refreshToken);
  setAccessTokenState(newToken);
  setAccessToken(newToken);
  return true;
};

export const forceReAuthentication = () => {
  clearTokens();
  redirectToCanvas();
};

export const logout = () => {
  fetch(`${backendUrl}/ui/general/log-in`, {
    method: "POST",
    headers: new Headers({
      Authorization: String(getAccessToken()),
      "Content-Type": "application/json",
    }),
  }).finally(() => {
    clearTokens();
    window.location.reload();
  });
};

export const handleAuthentication = async (
  setAccessTokenState: (token: string) => void
) => {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const error = urlParams.get("error");

    if (error) {
      throw new Error(`OAuth2 error: ${error}`);
    }

    // Handle authentication code flow
    if (code) {
      const newToken = await fetchAccessToken(code);
      setAccessTokenState(newToken);
      setAccessToken(newToken);
      window.history.replaceState({}, document.title, "/");
      return;
    }

    // Handle stored token flow
    const storedAccessToken = localStorage.getItem("access_token");
    const storedRefreshToken = localStorage.getItem("refresh_token");
    const tokenExpiry = localStorage.getItem("token_expiry");

    if (!storedAccessToken || !storedRefreshToken || !tokenExpiry) {
      throw new Error("Missing expected stored tokens");
    }

    const expiryTime = new Date(tokenExpiry).getTime();
    const currentTime = new Date().getTime();
    const timeUntilExpiry = expiryTime - currentTime;

    if (timeUntilExpiry <= 0) {
      // Token expired, attempt refresh
      const success = await handleTokenRefresh(
        storedRefreshToken,
        setAccessTokenState
      );
      if (!success) throw new Error("Token refresh failed");
    } else {
      // Token valid, set up refresh timer if needed
      setAccessTokenState(storedAccessToken);
      setAccessToken(storedAccessToken);

      if (timeUntilExpiry < REFRESH_THRESHOLD) {
        const success = await handleTokenRefresh(
          storedRefreshToken,
          setAccessTokenState
        );
        if (!success) throw new Error("Token refresh failed");
      } else {
        setupTokenRefreshTimer(storedRefreshToken, timeUntilExpiry);
      }
    }

    window.history.replaceState({}, document.title, "/");
  } catch (error) {
    console.error("Authentication error:", error);
    clearTokens();
    redirectToCanvas();
  }
};
