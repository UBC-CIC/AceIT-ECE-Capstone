import * as React from "react";
import { CourseProps } from "../../../types";

export const CourseItem: React.FC<CourseProps & { onClick?: () => void }> = ({
  courseCode,
  name,
  isActive,
  isAvailable,
  userCourseRole,
  onClick,
}) => {
  console.log(name + ":" + isActive);
  const baseClasses =
    "flex flex-col py-2.5 pr-2.5 pl-2.5 mt-3 w-full rounded-lg border border-white border-solid transition-all duration-200";
  const stateClasses = !isAvailable
    ? "bg-neutral-200 text-neutral-600 cursor-not-allowed"
    : isActive
    ? "text-white bg-indigo-950"
    : "bg-violet-100 hover:bg-violet-200 cursor-pointer";

  return (
    <div
      className={`${baseClasses} ${stateClasses}`}
      onClick={isAvailable ? onClick : undefined}
      role={isAvailable ? "button" : undefined}
      tabIndex={isAvailable ? 0 : undefined}
      onKeyPress={(e) => {
        if (isAvailable && (e.key === "Enter" || e.key === " ")) {
          onClick?.();
        }
      }}
    >
      <div className="font-semibold">
        {courseCode} •{" "}
        {userCourseRole === "INSTRUCTOR" ? "Instructor" : "Student"}
      </div>
      <div>{name}</div>
    </div>
  );
};
