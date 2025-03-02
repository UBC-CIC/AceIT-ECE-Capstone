import * as React from "react";
import { useIntl } from "react-intl";
import { CourseNavBarItem } from "./CourseNavBarItem";

const navigationItems = [
  { label: "Analytics", messageId: "nav.analytics" },
  { label: "Configuration", messageId: "nav.configuration" },
  { label: "Test Assistant", messageId: "nav.testAssistant" },
];

interface CourseNavBarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export const CourseNavBar: React.FC<CourseNavBarProps> = ({
  activeSection,
  onSectionChange,
}) => {
  const intl = useIntl();

  return (
    <div className="flex flex-col w-full border-b-[3px] border-primary border-opacity-20">
      <div className="flex relative gap-10 items-center px-5 py-0 max-md:gap-5 max-md:px-5 max-md:py-0 max-sm:gap-3.5 max-sm:px-4 max-sm:py-0">
        {navigationItems.map((item) => (
          <CourseNavBarItem
            key={item.label}
            label={intl.formatMessage({ id: item.messageId })}
            isActive={activeSection === item.label}
            onClick={() => onSectionChange(item.label)}
          />
        ))}
      </div>
    </div>
  );
};
