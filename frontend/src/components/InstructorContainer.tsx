import { useState, useEffect } from "react";
import { CourseProps } from "../types";
import { CourseNavBar } from "./CourseNavBar/CourseNavBar";
import { CourseConfigurationSection } from "./InstructorSections/CourseConfigurationSection";
import { ChatSection } from "./ChatSection/ChatSection";
import { CourseAnalyticsSection } from "./InstructorSections/CourseAnalyticsSection";

type InstructorSectionProps = {
  selectedCourse: CourseProps;
};

export const InstructorSection: React.FC<InstructorSectionProps> = ({
  selectedCourse,
}) => {
  const [activeSection, setActiveSection] = useState("Analytics");

  useEffect(() => {
    setActiveSection("Analytics");
  }, [selectedCourse]);

  const renderContent = () => {
    switch (activeSection) {
      case "Analytics":
        return <CourseAnalyticsSection selectedCourse={selectedCourse} />;
      case "Configuration":
        return <CourseConfigurationSection selectedCourse={selectedCourse} />;
      case "Test Assistant":
        return (
          <ChatSection
            selectedCourse={selectedCourse}
            hidePastSessions={true}
            useDarkStyle={true}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-none py-5 px-4">
        <CourseNavBar
          onSectionChange={setActiveSection}
          activeSection={activeSection}
        />
      </div>
      {activeSection == "Test Assistant" && (
        <div className="flex-none pb-2 px-4 mb-2">
          <div className="bg-violet-100 border-l-4 border-indigo-950 p-4 rounded-sm">
            <p className="text-sm text-indigo-950">
              Note: Any changes to the "Included Course Content" made in the
              Configuration page for this course may take several minutes to
              apply.
            </p>
          </div>
        </div>
      )}
      <div className="flex-1 min-h-0 px-6 pb-6">{renderContent()}</div>
    </div>
  );
};
