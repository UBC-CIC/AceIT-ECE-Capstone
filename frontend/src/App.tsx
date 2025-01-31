import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster } from "react-hot-toast";
import { testAccessToken } from "./test-data.tsx";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken } from "./api.ts";

export const App = () => {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);

  useEffect(() => {
    handleAuthentication((token) => {
      setAccessToken(token);
      setAccessTokenState(testAccessToken);
    });
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden px-6 py-5 w-auto bg-white bg-center bg-no-repeat bg-cover bg-[url(https://cdn.builder.io/api/v1/image/assets%2Fd039dd0b1f0f41589c575f1416b7b9f8%2F9e09c4389840405eb4a160b99b2ebcc4)] max-md:px-5">
      <StrictMode>
        <Toaster position="top-center" />
        {accessToken !== null && <StudyAssistant />}
      </StrictMode>
    </div>
  );
};

createRoot(document.getElementById("root")!).render(<App />);
