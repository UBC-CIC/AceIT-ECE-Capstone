import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { StudyAssistant } from "./StudyAssistant.tsx";
import { Toaster, toast } from "react-hot-toast";
import { handleAuthentication } from "./auth.ts";
import { setAccessToken, fetchCoursesAPI, fetchUserInfoAPI } from "./api.ts";
import { SkeletonTheme } from "react-loading-skeleton";
import { IntlProvider } from "react-intl";
import { UserProps, CourseProps, UserRole } from "./types";
import { colors, bg_gradient } from "../theme.ts";

// Import all translation files
import enMessages from "./translations/en.json";
import zhMessages from "./translations/zh.json";
import zhTWMessages from "./translations/zh-TW.json";
import frMessages from "./translations/fr.json";
import frCAMessages from "./translations/fr-CA.json";
import deMessages from "./translations/de.json";
import ruMessages from "./translations/ru.json";
import esMessages from "./translations/es.json";

const USE_MOCK_DATA = import.meta.env.VITE_REACT_APP_USE_MOCK_DATA === "true";

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

const mockData = {
  user: {
    userId: "123",
    userName: "Zane",
    preferred_language: "en",
  },
  fetchedCourses: [
    {
      id: "1",
      courseCode: "TEST101",
      name: "Test Instructor Course",
      userCourseRole: "INSTRUCTOR" as UserRole,
      isAvailable: true,
    },
    {
      id: "2",
      courseCode: "TEST202",
      name: "Test Student Course",
      userCourseRole: "STUDENT" as UserRole,
      isAvailable: true,
    },
    {
      id: "2",
      courseCode: "TEST302",
      name: "Test Student Course",
      userCourseRole: "STUDENT" as UserRole,
      isAvailable: false,
    },
  ],
};

export const App = () => {
  const [accessToken, setAccessTokenState] = useState<string>();
  const [locale, setLocale] = useState("en");
  const [userInfo, setUserInfo] = useState<UserProps>();
  const [courses, setCourses] = useState<CourseProps[]>();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        let user: UserProps, fetchedCourses: CourseProps[];

        // Authenticate and load initial application data
        if (USE_MOCK_DATA) {
          setAccessToken("123");
          setAccessTokenState("123");
          user = mockData.user;
          fetchedCourses = mockData.fetchedCourses;
        } else {
          // Perform authentication
          await handleAuthentication((token) => {
            setAccessToken(token);
            setAccessTokenState(token);
          });

          toast.loading("Loading your info from Canvas...");
          [user, fetchedCourses] = await Promise.all([
            fetchUserInfoAPI(),
            fetchCoursesAPI(),
          ]);
        }

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
          background: `linear-gradient(to bottom right, ${bg_gradient.first}, ${bg_gradient.second}, ${bg_gradient.third}, ${bg_gradient.fourth})`,
        }}
      >
        <StrictMode>
          <SkeletonTheme
            baseColor={colors.secondary}
            highlightColor={colors.tertiary}
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
