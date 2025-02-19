import { Header } from "./components/MainNavigation/Header/Header";
import { useState } from "react";
import { SideBar } from "./components/MainNavigation/SideBar/SideBar";
import { ChatSection } from "./components/ChatSection/ChatSection";
import { InstructorSection } from "./components/InstructorContainer";
import { CourseProps, UserProps, StudyAssistantProps } from "./types";
import { toast } from "react-hot-toast";
import { logout } from "./auth";
import { updateUserLanguageAPI } from "./api";

export const StudyAssistant = ({
  onLocaleChange,
  initialUserInfo,
  initialCourses,
}: StudyAssistantProps) => {
  const [courses] = useState<CourseProps[]>(initialCourses);
  const [selectedCourse, setSelectedCourse] = useState<CourseProps | null>(
    initialCourses.length > 0 ? initialCourses[0] : null
  );
  const [userInfo, setUserInfo] = useState<UserProps>(initialUserInfo);

  const handleCourseSelect = (course: CourseProps) => {
    setSelectedCourse(course);
  };

  const handleLanguageChange = async (language: string) => {
    try {
      await updateUserLanguageAPI(language);

      if (!userInfo) return;

      // Update the language preference in the local state
      const newUserInfo = userInfo;
      userInfo.preferred_language = language;
      setUserInfo(newUserInfo);
      onLocaleChange(language);
      toast.success("Language preference updated successfully");
    } catch (error) {
      console.error("Failed to update language preference:", error);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {userInfo ? (
        <>
          <Header
            currentCourse={selectedCourse}
            onLogout={() => logout()}
            onLanguageChange={handleLanguageChange}
            userInfo={userInfo}
          />

          <div className="flex-1 flex gap-4 mt-4 min-h-0">
            <SideBar
              courses={courses}
              selectedCourse={selectedCourse}
              onCourseSelect={handleCourseSelect}
            />

            {selectedCourse ? (
              <>
                {selectedCourse.userCourseRole === "STUDENT" && (
                  <div className="flex-1 flex flex-col min-h-0">
                    <ChatSection
                      key={selectedCourse.id}
                      selectedCourse={selectedCourse}
                      hidePastSessions={false}
                      useDarkStyle={false}
                      resetTrigger={selectedCourse.id}
                      preferredLanguage={userInfo.preferred_language}
                    />
                  </div>
                )}
                {selectedCourse.userCourseRole === "INSTRUCTOR" && (
                  <div className="flex-1 flex flex-col rounded-xl border-white border-solid bg-white bg-opacity-50 border-[3px]">
                    <InstructorSection selectedCourse={selectedCourse} />
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex flex-col rounded-xl border-white border-solid bg-white bg-opacity-50 border-[3px] items-center justify-start pt-32 p-8">
                <p className="text-center text-xl text-gray-600">
                  <span className="font-bold">
                    Uh oh... Looks like you have no courses in Canvas.
                  </span>
                  <br />
                  Please make sure you are enrolled in active Canvas courses and
                  refresh the page.
                </p>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
};
