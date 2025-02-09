import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken } from "./api.ts";

export const App = () => {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);

  useEffect(() => {
    handleAuthentication((token) => {
      setAccessToken(token);
      setAccessTokenState(token);
    });
  }, []);

  return (
    <div
      className="h-screen flex flex-col overflow-hidden px-6 py-5 w-auto bg-white"
      style={{
        background: `linear-gradient(to bottom right, 
          rgba(137, 188, 255, 1) 0%,
          rgba(255, 134, 225, 0.3) 0%,
          rgba(134, 255, 213, 1) 100%,
          rgba(137, 239, 255, 0.5) 100%)`,
      }}
    >
      <StrictMode>
        <Toaster position="top-center" />
        {accessToken !== null && (
          <div className="h-full">
            <StudyAssistant />
          </div>
        )}
      </StrictMode>
    </div>
  );
};

createRoot(document.getElementById("root")!).render(<App />);
