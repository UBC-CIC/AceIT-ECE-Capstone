import * as React from "react";
import { FormattedMessage, useIntl } from "react-intl";
import {
  MetricsCardProps,
  EngagementCardProps,
  Timeframe,
} from "../../../types";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import BlueArrowIcon from "../../../assets/Blue-Arrow-Icon.svg";
import MessageIcon from "../../../assets/Message-Icon.png";
import PersonIcon from "../../../assets/Person-Icon.png";
import QuestionIcon from "../../../assets/Question-Icon.png";

const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  iconSrc,
  loading,
}) => {
  return (
    <div className="flex-1 min-w-[300px] max-w-[300px]">
      <div className="flex gap-3 items-center p-2">
        <img
          loading="lazy"
          src={iconSrc}
          alt=""
          className="object-contain w-10 h-10 flex-shrink-0"
        />
        <div className="flex flex-col min-w-0 flex-1">
          <div className="text-sm font-semibold text-primary">{title}</div>
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
  const intl = useIntl();
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const displayTimeframes = [
    {
      display: intl.formatMessage({ id: "analytics.timeframe.week" }),
      value: "WEEK",
    },
    {
      display: intl.formatMessage({ id: "analytics.timeframe.month" }),
      value: "MONTH",
    },
    {
      display: intl.formatMessage({ id: "analytics.timeframe.year" }),
      value: "TERM",
    },
  ];

  const currentTimeframeDisplay =
    displayTimeframes.find((t) => t.value === timeframe)?.display || timeframe;

  return (
    <div className="flex flex-col bg-secondary rounded-lg border border-solid border-primary border-opacity-10 w-full">
      <div className="flex justify-between items-center px-6 py-4">
        <div className="text-sm font-semibold text-primary">
          <FormattedMessage id="analytics.studentEngagement" />
        </div>
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 text-sm font-semibold text-primary"
          >
            {currentTimeframeDisplay}
            <img
              loading="lazy"
              src={BlueArrowIcon}
              alt="Dropdown Arrow Icon"
              className="w-3 h-3"
            />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-1 bg-white text-primary rounded-md shadow-lg z-10">
              {displayTimeframes.map((display) => (
                <button
                  key={display.value}
                  className="block w-full px-4 py-2 text-left text-sm font-semibold hover:bg-primary hover:bg-opacity-5"
                  onClick={() => {
                    onPeriodChange(display.value as Timeframe);
                    setIsDropdownOpen(false);
                  }}
                >
                  {display.display}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap justify-evenly gap-4 p-6">
        <MetricsCard
          title={intl.formatMessage({ id: "analytics.questionsAsked" })}
          value={questionsAsked}
          iconSrc={QuestionIcon}
          loading={loading}
        />
        <MetricsCard
          title={intl.formatMessage({ id: "analytics.studentSessions" })}
          value={studentSessions}
          iconSrc={MessageIcon}
          loading={loading}
        />
        <MetricsCard
          title={intl.formatMessage({ id: "analytics.studentsUsingAceIt" })}
          value={studentsUsingAceIt}
          iconSrc={PersonIcon}
          loading={loading}
        />
      </div>
    </div>
  );
};
