import React from "react";
import { FormattedMessage } from "react-intl";
import { CourseItem } from "./CourseItem";
import { CourseProps } from "../../../types";
import InfoIcon from "../../../assets/Info-Icon.png";

interface SideBarProps {
  courses: CourseProps[];
  selectedCourse: CourseProps | null;
  onCourseSelect: (course: CourseProps) => void;
}

export const SideBar: React.FC<SideBarProps> = ({
  courses,
  selectedCourse,
  onCourseSelect,
}) => {
  const availableCourses = courses.filter((course) => course.isAvailable);
  const unavailableCourses = courses.filter((course) => !course.isAvailable);

  return (
    <div className="flex flex-wrap gap-3 items-start px-4 py-5 h-full text-sm rounded-xl border-white border-solid bg-white bg-opacity-50 border-[3px] min-w-[290px] text-primary w-[290px] overflow-y-auto">
      <div className="flex flex-col flex-1 shrink w-full basis-0 min-w-[240px]">
        {selectedCourse && availableCourses.length > 0 && (
          <>
            <div className="font-bold">
              <FormattedMessage id="sidebar.availableCourses" />
            </div>
            {availableCourses.map((course, index) => (
              <CourseItem
                key={index}
                {...course}
                isActive={course.courseCode === selectedCourse.courseCode}
                onClick={() => onCourseSelect(course)}
              />
            ))}
          </>
        )}
        {unavailableCourses.length > 0 && (
          <>
            <div className="flex gap-1.5 items-center mt-3 max-w-full font-bold w-[180px] relative group">
              <div className="self-stretch my-auto w-[160px]">
                <FormattedMessage id="sidebar.unavailableCourses" />
              </div>
              <img
                loading="lazy"
                src={InfoIcon}
                alt="Info Icon"
                className="object-contain shrink-0 self-stretch my-auto w-4 aspect-square"
              />
              <div className="absolute top-full mt-2 hidden group-hover:block bg-primary text-tertiary text-xs rounded py-1 px-2 w-64">
                <FormattedMessage id="sidebar.unavailableTooltip" />
              </div>
            </div>
            {unavailableCourses.map((course, index) => (
              <CourseItem key={index} {...course} />
            ))}
          </>
        )}
      </div>
    </div>
  );
};
