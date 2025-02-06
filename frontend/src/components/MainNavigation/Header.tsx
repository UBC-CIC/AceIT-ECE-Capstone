import * as React from "react";
import { HeaderProps } from "../../types";
import UBCLogoWhite from "../../assets/UBC-logo-white.png";

export const Header: React.FC<HeaderProps> = ({
  userName,
  currentCourse,
  onLogout,
}) => {
  return (
    <div className="flex flex-wrap gap-4 items-center w-full text-white max-md:max-w-full">
      <div className="flex flex-wrap gap-3.5 items-center self-stretch py-3.5 pr-3 pl-4 my-auto rounded-xl border-white border-solid bg-indigo-950 border-[3px] min-h-[76px] min-w-[290px] w-[290px]">
        <img
          loading="lazy"
          src={UBCLogoWhite}
          alt="Ace It - UBC Logo"
          className="object-contain shrink-0 self-stretch my-auto aspect-[0.75] w-[30px]"
        />
        <div className="flex flex-col flex-1 shrink justify-center self-stretch my-auto basis-0">
          <div className="text-xl font-semibold leading-snug">Ace It</div>
          <div className="text-sm font-medium leading-loose">
            AI Study Assistant
          </div>
        </div>
      </div>
      <div className="flex flex-wrap flex-1 shrink gap-3.5 items-start self-stretch px-3 py-5 my-auto rounded-xl border-white border-solid basis-0 bg-indigo-950 border-[3px] min-h-[76px] min-w-[240px] max-md:max-w-full">
        <div className="flex overflow-hidden flex-wrap flex-1 shrink justify-between px-3 py-1.5 w-full basis-0 min-w-[240px] max-md:max-w-full">
          <div className="flex overflow-hidden flex-wrap flex-1 shrink gap-3 items-center my-auto text-xl leading-snug basis-0 min-w-[240px] max-md:max-w-full">
            <div className="self-stretch my-auto font-semibold">
              {currentCourse ? currentCourse.courseCode : ""}
            </div>
            <div className="self-stretch my-auto">
              {currentCourse ? currentCourse.name : ""}
            </div>
          </div>
          <div className="flex gap-2.5 items-center h-full text-base leading-none text-right">
            <div className="self-stretch my-auto">{userName}</div>
            <div className="self-stretch my-auto">•</div>
            <button
              onClick={onLogout}
              className="self-stretch my-auto font-semibold leading-7 w-[60px] hover:text-gray-200 transition-colors duration-200 hover:underline"
            >
              Log Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
