import { setAccessToken } from "./api.ts";

const canvasUrl = import.meta.env.VITE_REACT_APP_CANVAS_URL;
const clientId = import.meta.env.VITE_REACT_APP_CLIENT_ID;
const redirectUri = import.meta.env.VITE_REACT_APP_HOST_URI;
const backendUrl = import.meta.env.VITE_REACT_APP_API_URL;
const isLocalMode = import.meta.env.VITE_REACT_APP_LOCAL_MODE;

export const redirectToCanvas = () => {
  window.location.href = `${canvasUrl}/login/oauth2/auth?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&state=aceit`;
};

export const fetchAccessToken = async (code: string) => {
  try {
    const response = await fetch(`${backendUrl}/ui/general/log-in`, {
      method: "POST",
      headers: {
        Authorization: code,
        Islocaltesting: isLocalMode,
      },
    });

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
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

export const refreshAccessToken = async (accessToken: string) => {
  try {
    const response = await fetch(`${backendUrl}/ui/general/refresh-token`, {
      method: "POST",
      headers: {
        access_token: accessToken,
        isLocalTesting: isLocalMode,
      },
    });

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

export const setupTokenRefreshTimer = (accessToken: string, delay: number) => {
  setTimeout(() => {
    refreshAccessToken(accessToken);
  }, delay - 60000); // Refresh 1 minute before expiry
};

export const handleAuthentication = async (
  setAccessTokenState: (token: string) => void
) => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");
  const error = urlParams.get("error");

  const storedAccessToken = localStorage.getItem("access_token");
  const tokenExpiry = localStorage.getItem("token_expiry");

  if (storedAccessToken && tokenExpiry) {
    const expiryTime = new Date(tokenExpiry).getTime();
    const currentTime = new Date().getTime();

    if (currentTime < expiryTime) {
      setAccessTokenState(storedAccessToken);
      setAccessToken(storedAccessToken);
      setupTokenRefreshTimer(storedAccessToken, expiryTime - currentTime);
      window.history.replaceState({}, document.title, "/");
    } else {
      refreshAccessToken(storedAccessToken)
        .then((newToken) => {
          setAccessTokenState(newToken);
          setAccessToken(newToken);
          window.history.replaceState({}, document.title, "/");
        })
        .catch(redirectToCanvas);
    }
  } else if (code) {
    fetchAccessToken(code)
      .then((newToken) => {
        setAccessTokenState(newToken);
        setAccessToken(newToken);
        window.history.replaceState({}, document.title, "/");
      })
      .catch(console.error);
  } else if (error) {
    console.error("OAuth2 error:", error);
  } else {
    redirectToCanvas();
  }
};

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_expiry");
  window.location.reload();
};
