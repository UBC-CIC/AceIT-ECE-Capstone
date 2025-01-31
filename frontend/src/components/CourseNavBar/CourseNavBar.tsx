import * as React from "react";
import { CourseNavBarItem } from "./CourseNavBarItem";

const navigationItems = [
  { label: "Analytics" },
  { label: "Configuration" },
  { label: "Test Assistant" },
];

interface CourseNavBarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export const CourseNavBar: React.FC<CourseNavBarProps> = ({
  activeSection,
  onSectionChange,
}) => {
  return (
    <div className="flex flex-col w-full border-b-[3px] border-[#160211]/10">
      <div className="flex relative gap-10 items-center px-5 py-0 max-md:gap-5 max-md:px-5 max-md:py-0 max-sm:gap-3.5 max-sm:px-4 max-sm:py-0">
        {navigationItems.map((item) => (
          <CourseNavBarItem
            key={item.label}
            label={item.label}
            isActive={activeSection === item.label}
            onClick={() => onSectionChange(item.label)}
          />
        ))}
      </div>
    </div>
  );
};
