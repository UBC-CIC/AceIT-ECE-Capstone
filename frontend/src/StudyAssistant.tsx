import { Header } from "./components/MainNavigation/Header";
import { useState, useEffect, useRef } from "react";
import { SideBar } from "./components/MainNavigation/SideBar/SideBar";
import { ChatSection } from "./components/ChatSection/ChatSection";
import { InstructorSection } from "./components/InstructorContainer";
import { CourseProps, UserProps } from "./types";
import { toast } from "react-hot-toast";
import { logout } from "./auth";
import { fetchCoursesAPI, fetchUserInfoAPI } from "./api";

export const StudyAssistant = () => {
  const [courses, setCourses] = useState<CourseProps[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<CourseProps | null>(
    null
  );
  const [userInfo, setUserInfo] = useState<UserProps | null>(null);
  const hasFetchedData = useRef(false);

  useEffect(() => {
    if (hasFetchedData.current) return;
    hasFetchedData.current = true;

    const fetchData = async () => {
      toast.loading("Loading your info from Canvas...", {
        id: "loading",
      });

      try {
        const [courses, user] = await Promise.all([
          fetchCoursesAPI(),
          fetchUserInfoAPI(),
        ]);

        setCourses(courses);
        setSelectedCourse(courses[0]);
        setUserInfo(user);

        toast.dismiss();
      } catch (error) {
        toast.error("Failed to load your info from Canvas", {
          id: "loading",
        });
        console.error("Failed to load data: ", error);
      }
    };

    fetchData();
  }, []);

  const handleCourseSelect = (course: CourseProps) => {
    setSelectedCourse(course);
  };

  useEffect(() => {
    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      const chatSection = document.querySelector(".chat-section");
      if (chatSection) {
        const messageInput = document.getElementById(
          "messageInput"
        ) as HTMLInputElement;
        if (
          event.key === "Enter" &&
          messageInput &&
          messageInput.value.trim() !== ""
        ) {
          const form = messageInput.closest("form");
          if (form) {
            form.requestSubmit();
          }
        } else if (messageInput && event.key.length === 1) {
          messageInput.focus();
        }
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => {
      window.removeEventListener("keydown", handleGlobalKeyDown);
    };
  }, []);

  return (
    <div>
      {selectedCourse && userInfo && (
        <>
          <Header
            userName={userInfo.userName}
            currentCourse={selectedCourse}
            onLogout={() => logout()}
          />

          <div className="flex flex-1 overflow-hidden mt-4 gap-4">
            <SideBar
              courses={courses}
              selectedCourse={selectedCourse}
              onCourseSelect={handleCourseSelect}
            />

            {/* Display correct content view based on the user's role in a given course */}
            {/* TODO: Add support for when no courses are found for a given user - currently not supported */}
            {selectedCourse.userCourseRole === "STUDENT" && (
              <div className="flex flex-col flex-1 shrink justify-between basis-3.5 min-w-[240px] max-md:max-w-full h-full overflow-hidden">
                <ChatSection
                  selectedCourse={selectedCourse}
                  hidePastSessions={false}
                  useDarkStyle={false}
                />
              </div>
            )}
            {selectedCourse.userCourseRole === "INSTRUCTOR" && (
              <div className="flex flex-col flex-1 shrink justify-between basis-3.5 min-w-[240px] max-md:max-w-full h-full overflow-hidden rounded-xl border-white border-solid bg-white bg-opacity-50 border-[3px]">
                <InstructorSection selectedCourse={selectedCourse} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
