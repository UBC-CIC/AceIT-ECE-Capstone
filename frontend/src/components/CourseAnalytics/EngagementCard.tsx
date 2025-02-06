import * as React from "react";
import { MetricsCardProps, EngagementCardProps } from "../../types";
import { timeframeToDisplay, displayToTimeframe } from "../../utils";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import BlueArrowIcon from "../../assets/Blue-Arrow-Icon.svg";
import MessageIcon from "../../assets/Message-Icon.png";
import PersonIcon from "../../assets/Person-Icon.png";
import QuestionIcon from "../../assets/Question-Icon.png";

const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  iconSrc,
  loading,
}) => {
  return (
    <div className="flex-1 min-w-[220px] max-w-[220px]">
      <div className="flex gap-3 items-center p-2">
        <img
          loading="lazy"
          src={iconSrc}
          alt=""
          className="object-contain w-10 h-10 flex-shrink-0"
        />
        <div className="flex flex-col min-w-0 flex-1">
          <div className="text-sm font-semibold truncate">{title}</div>
          {loading ? (
            <Skeleton width="100%" height={20} />
          ) : (
            <div className="text-xl">{value}</div>
          )}
        </div>
      </div>
    </div>
  );
};

export const EngagementCard: React.FC<EngagementCardProps> = ({
  questionsAsked,
  studentSessions,
  studentsUsingAceIt,
  timeframe,
  onPeriodChange,
  loading,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const displayTimeframes = ["This Week", "This Month", "This Year"];

  return (
    <div className="flex flex-col bg-violet-100 rounded-lg border border-solid border-stone-950 border-opacity-10 w-full">
      <div className="flex justify-between items-center px-6 py-4">
        <div className="text-sm font-semibold text-indigo-950">
          Student Engagement
        </div>
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 text-sm font-semibold text-indigo-950"
          >
            {timeframeToDisplay(timeframe)}
            <img
              loading="lazy"
              src={BlueArrowIcon}
              alt="Dropdown Arrow Icon"
              className="w-3 h-3"
            />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-1 bg-white text-slate-700 rounded-md shadow-lg z-10">
              {displayTimeframes.map((display) => (
                <button
                  key={display}
                  className="block w-full px-4 py-2 text-left hover:bg-slate-100"
                  onClick={() => {
                    onPeriodChange(displayToTimeframe(display));
                    setIsDropdownOpen(false);
                  }}
                >
                  {display}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap justify-evenly gap-4 p-6">
        <MetricsCard
          title="Questions Asked"
          value={questionsAsked}
          iconSrc={QuestionIcon}
          loading={loading}
        />
        <MetricsCard
          title="Student Sessions"
          value={studentSessions}
          iconSrc={MessageIcon}
          loading={loading}
        />
        <MetricsCard
          title="Students Using Ace It"
          value={studentsUsingAceIt}
          iconSrc={PersonIcon}
          loading={loading}
        />
      </div>
    </div>
  );
};
