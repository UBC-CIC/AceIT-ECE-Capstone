import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken, fetchCoursesAPI, fetchUserInfoAPI } from "./api.ts";
import { SkeletonTheme } from "react-loading-skeleton";
import { IntlProvider } from "react-intl";
import { UserProps, CourseProps } from "./types";

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
  const [accessToken, setAccessTokenState] = useState<string>();
  const [locale, setLocale] = useState("en");
  const [userInfo, setUserInfo] = useState<UserProps>();
  const [courses, setCourses] = useState<CourseProps[]>();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Perform authentication
        await handleAuthentication((token) => {
          setAccessToken(token);
          setAccessTokenState(token);
        });

        // Fetch user info and courses
        const [user, fetchedCourses] = await Promise.all([
          fetchUserInfoAPI(),
          fetchCoursesAPI(),
        ]);

        setUserInfo(user);
        setLocale(user.preferred_language);
        setCourses(fetchedCourses.sort((a, b) => a.name.localeCompare(b.name)));
      } catch (error) {
        console.error("Failed to initialize app:", error);
      }
    };

    initializeApp();
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
            {accessToken !== null && userInfo && courses && (
              <StudyAssistant
                onLocaleChange={setLocale}
                initialUserInfo={userInfo}
                initialCourses={courses}
              />
            )}
          </SkeletonTheme>
        </StrictMode>
      </div>
    </IntlProvider>
  );
};

createRoot(document.getElementById("root")!).render(<App />);
