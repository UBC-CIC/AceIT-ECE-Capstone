import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster, toast } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken, fetchCoursesAPI, fetchUserInfoAPI } from "./api.ts";
import { SkeletonTheme } from "react-loading-skeleton";
import { IntlProvider } from "react-intl";
import { UserProps, CourseProps } from "./types";

const BG_FIRST = import.meta.env.VITE_REACT_APP_THEME_COLOUR_BG_FIRST;
const BG_SECOND = import.meta.env.VITE_REACT_APP_THEME_COLOUR_BG_SECOND;
const BG_THIRD = import.meta.env.VITE_REACT_APP_THEME_COLOUR_BG_THIRD;
const BG_FOURTH = import.meta.env.VITE_REACT_APP_THEME_COLOUR_BG_FOURTH;
const COLOUR_PRIMARY = import.meta.env.VITE_REACT_APP_THEME_COLOUR_PRIMARY;
const COLOUR_SECONDARY = import.meta.env.VITE_REACT_APP_THEME_COLOUR_SECONDARY;

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
        toast.loading("Loading your info from Canvas...");
        const [user, fetchedCourses] = await Promise.all([
          fetchUserInfoAPI(),
          fetchCoursesAPI(),
        ]);

        setUserInfo(user);
        setLocale(user.preferred_language);
        setCourses(fetchedCourses.sort((a, b) => a.name.localeCompare(b.name)));
      } catch (error) {
        toast.error(
          "Failed to get your info from Canvas. Please refresh and try again later."
        );
        console.error("Failed to initialize app:", error);
      } finally {
        toast.dismiss();
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
          background: `linear-gradient(to bottom right, ${BG_FIRST}, ${BG_SECOND}, ${BG_THIRD}, ${BG_FOURTH})`,
        }}
      >
        <StrictMode>
          <SkeletonTheme
            baseColor={COLOUR_PRIMARY}
            highlightColor={COLOUR_SECONDARY}
          >
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
