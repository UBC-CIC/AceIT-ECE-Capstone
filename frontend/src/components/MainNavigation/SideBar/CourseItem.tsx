import * as React from "react";
import { useIntl } from "react-intl";
import { CourseProps } from "../../../types";

export const CourseItem: React.FC<CourseProps & { onClick?: () => void }> = ({
  courseCode,
  name,
  isActive,
  isAvailable,
  userCourseRole,
  onClick,
}) => {
  const intl = useIntl();
  const baseClasses =
    "flex flex-col py-2.5 pr-2.5 pl-2.5 mt-3 w-full rounded-lg border border-white border-solid transition-all duration-200";
  const stateClasses = !isAvailable
    ? "bg-disabled bg-opacity-50 text-disabled cursor-not-allowed"
    : isActive
    ? "text-tertiary bg-primary"
    : "bg-secondary hover:bg-primary cursor-pointer";

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
        {userCourseRole === "INSTRUCTOR"
          ? intl.formatMessage({ id: "role.instructor" })
          : intl.formatMessage({ id: "role.student" })}
      </div>
      <div>{name}</div>
    </div>
  );
};
