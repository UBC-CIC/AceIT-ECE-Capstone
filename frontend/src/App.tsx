import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken } from "./api.ts";
import { SkeletonTheme } from "react-loading-skeleton";
import { IntlProvider } from "react-intl";

// Import all translation files
import enMessages from "./translations/en.json";
import zhMessages from "./translations/zh.json";
import zhTWMessages from "./translations/zh-TW.json";
import frMessages from "./translations/fr.json";
import frCAMessages from "./translations/fr-CA.json";
import deMessages from "./translations/de.json";
import ruMessages from "./translations/ru.json";
import esMessages from "./translations/es.json";

// Create a messages object that will hold all translations
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const messages: { [key: string]: any } = {
  en: enMessages,
  zh: zhMessages,
  "zh-TW": zhTWMessages,
  fr: frMessages,
  "fr-CA": frCAMessages,
  de: deMessages,
  ru: ruMessages,
  es: esMessages,
};

export const App = () => {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);
  const [locale, setLocale] = useState("en"); // Default to English

  useEffect(() => {
    handleAuthentication((token) => {
      setAccessToken(token);
      setAccessTokenState(token);
    });
  }, []);

  return (
    <IntlProvider
      messages={messages[locale]}
      locale={locale}
      defaultLocale="en"
    >
      <div
        className="h-screen flex flex-col px-6 py-5 w-auto bg-white"
        style={{
          background: `linear-gradient(to bottom right, 
            rgba(137, 188, 255, 1) 0%,
            rgba(255, 134, 225, 0.3) 0%,
            rgba(134, 255, 213, 1) 100%,
            rgba(137, 239, 255, 0.5) 100%)`,
        }}
      >
        <StrictMode>
          <SkeletonTheme baseColor="#a6a3d1" highlightColor="#9e9adb">
            <Toaster position="top-center" />
            {accessToken !== null && (
              <StudyAssistant onLocaleChange={setLocale} />
            )}
          </SkeletonTheme>
        </StrictMode>
      </div>
    </IntlProvider>
  );
};

createRoot(document.getElementById("root")!).render(<App />);
