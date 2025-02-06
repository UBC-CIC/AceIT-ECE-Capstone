import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken } from "./api.ts";
import backgroundImage from "./assets/Background.png";

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
      className="h-screen flex flex-col overflow-hidden px-6 py-5 w-auto bg-white bg-center bg-no-repeat bg-cover"
      style={{ backgroundImage: `url(${backgroundImage})` }}
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
