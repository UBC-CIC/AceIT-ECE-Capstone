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
      headers: new Headers({
        Authorization: String(code),
        Islocaltesting: String(isLocalMode),
        "Content-Type": "application/json",
      }),
    });

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

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
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
  }, delay - 60000); // Refresh 1 minute before expiry
};

export const handleAuthentication = async (
  setAccessTokenState: (token: string) => void
) => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");
  const error = urlParams.get("error");

  const storedAccessToken = localStorage.getItem("access_token");
  const storedRefreshToken = localStorage.getItem("refresh_token");
  const tokenExpiry = localStorage.getItem("token_expiry");

  if (storedAccessToken && storedRefreshToken && tokenExpiry) {
    const expiryTime = new Date(tokenExpiry).getTime();
    const currentTime = new Date().getTime();

    if (currentTime < expiryTime) {
      setAccessTokenState(storedAccessToken);
      setAccessToken(storedAccessToken);
      setupTokenRefreshTimer(storedRefreshToken, expiryTime - currentTime);
      window.history.replaceState({}, document.title, "/");
    } else {
      refreshAccessToken(storedRefreshToken)
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
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("token_expiry");
  window.location.reload();
};
