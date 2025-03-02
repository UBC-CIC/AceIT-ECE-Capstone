import { useState, useEffect } from "react";
import { FormattedMessage } from "react-intl";
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
            key={`${selectedCourse.id}-${activeSection}`}
            selectedCourse={selectedCourse}
            hidePastSessions={true}
            useDarkStyle={true}
            resetTrigger={activeSection}
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
        <div className="flex-none pb-2 px-4">
          <div className="bg-secondary border-l-4 border-primary p-4 rounded-sm">
            <p className="text-sm text-primary">
              <FormattedMessage id="testAssistant.contentNote" />
            </p>
          </div>
        </div>
      )}
      <div className="flex-1 min-h-0 px-6 pb-6 overflow-y-auto">
        <div className="h-full">{renderContent()}</div>
      </div>
    </div>
  );
};
