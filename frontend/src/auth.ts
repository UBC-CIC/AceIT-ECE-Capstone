import { setAccessToken } from "./api.ts";

const clientId = import.meta.env.VITE_REACT_APP_CLIENT_ID;
const clientSecret = import.meta.env.VITE_REACT_APP_CLIENT_SECRET;
const redirectUri = import.meta.env.VITE_REACT_APP_HOST_URI;
const canvasUrl = import.meta.env.VITE_REACT_APP_CANVAS_URL;

let accessToken: string | null = null;

export const redirectToCanvas = () => {
  window.location.href = `${canvasUrl}/login/oauth2/auth?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&state=aceit&scope=/auth/userinfo`;
};

export const fetchAccessToken = async (code: string) => {
  try {
    const formData = new FormData();
    formData.append("grant_type", "authorization_code");
    formData.append("client_id", clientId);
    formData.append("client_secret", clientSecret);
    formData.append("redirect_uri", redirectUri);
    formData.append("code", code);

    const response = await fetch(`${canvasUrl}/login/oauth2/token`, {
      method: "POST",
      body: formData,
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
    const formData = new FormData();
    formData.append("grant_type", "refresh_token");
    formData.append("client_id", clientId);
    formData.append("client_secret", clientSecret);
    formData.append("refresh_token", refreshToken);

    const response = await fetch(`${canvasUrl}/login/oauth2/token`, {
      method: "POST",
      body: formData,
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
    } else {
      refreshAccessToken(storedRefreshToken)
        .then((newToken) => {
          setAccessTokenState(newToken);
          setAccessToken(newToken);
        })
        .catch(redirectToCanvas);
    }
  } else if (code) {
    fetchAccessToken(code)
      .then((newToken) => {
        setAccessTokenState(newToken);
        setAccessToken(newToken);
      })
      .catch(console.error);
  } else if (error) {
    console.error("OAuth2 error:", error);
  } else {
    redirectToCanvas();
  }

  accessToken = storedAccessToken;
};

export const logout = async (expireSessions: boolean = false) => {
  try {
    const url = new URL(`${canvasUrl}/login/oauth2/token`);
    if (accessToken) {
      url.searchParams.append("access_token", accessToken);
    } else {
      throw new Error("Access token is null");
    }
    if (expireSessions) {
      url.searchParams.append("expire_sessions", "1");
    }

    const response = await fetch(url.toString(), {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("token_expiry");

    if (data.forward_url) {
      window.location.href = data.forward_url;
    }
  } catch (error) {
    console.error("Failed to logout:", error);
    throw error;
  }
};
