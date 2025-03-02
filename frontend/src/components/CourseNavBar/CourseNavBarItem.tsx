import * as React from "react";
import { CourseNavBarItemProps } from "../../types";

export const CourseNavBarItem: React.FC<CourseNavBarItemProps> = ({
  label,
  isActive,
  onClick,
}) => {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      className={`relative px-0 py-3 text-sm font-bold text-center transition-all cursor-pointer duration-[0.3s] ease-[ease] ${
        isActive
          ? 'text-primary after:content-[""] after:absolute after:bottom-[-4px] after:left-0 after:w-full after:h-[5px] after:bg-primary after:rounded-full'
          : "text-primary text-opacity-60 hover:text-primary"
      } `}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      {label}
    </div>
  );
};
