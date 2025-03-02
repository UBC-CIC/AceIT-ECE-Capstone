import * as React from "react";
import { FormattedMessage, useIntl } from "react-intl";
import { ListStatisticCardProps, Timeframe } from "../../../types";
import Skeleton from "react-loading-skeleton";
import WhiteArrowIcon from "../../../assets/White-Arrow-Icon.svg";

export const ListStatisticCard: React.FC<ListStatisticCardProps> = ({
  title,
  timeframe,
  items,
  onPeriodChange,
  loading,
}) => {
  const [showAll, setShowAll] = React.useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const intl = useIntl();

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

  const displayedItems = showAll ? items : items.slice(0, 5);
  const hasMoreItems = items.length > 5;

  return (
    <div className="flex flex-col flex-1 py-px text-sm bg-secondary rounded-lg border border-solid border-primary border-opacity-10 min-w-[400px] max-md:max-w-full">
      <div className="flex flex-wrap gap-5 justify-between px-6 py-4 w-full font-semibold text-tertiary rounded-lg bg-primary shadow-[0px_2px_25px_rgba(0,0,0,0.15)] max-md:px-5 max-md:max-w-full">
        <div>{title}</div>
        <div className="flex gap-2 text-right relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 text-sm"
          >
            {currentTimeframeDisplay}
            <img
              loading="lazy"
              src={WhiteArrowIcon}
              alt="Dropdown Arrow Icon"
              className="object-contain shrink-0 my-auto rounded-sm aspect-[1.22] w-[11px]"
            />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-1 bg-white text-primary rounded-md shadow-lg z-10">
              {displayTimeframes.map((display) => (
                <button
                  key={display.value}
                  className="block w-full px-4 py-2 text-left text-sm hover:bg-primary hover:bg-opacity-5"
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
      <div className="flex overflow-hidden flex-col px-5 py-2.5 max-md:max-w-full">
        {loading ? (
          <Skeleton count={5} height={20} />
        ) : (
          <>
            <ol className="text-primary list-decimal pl-5">
              {displayedItems.map((item, index) => (
                <li key={index} className="mb-1">
                  {item.link ? (
                    <a
                      href={item.link}
                      target="_blank"
                      className="hover:underline"
                    >
                      {item.title}
                    </a>
                  ) : (
                    item.title
                  )}
                </li>
              ))}
            </ol>
            {hasMoreItems && (
              <button
                className="mt-2.5 font-semibold text-primary max-md:max-w-full text-left"
                onClick={() => setShowAll(!showAll)}
              >
                <FormattedMessage
                  id={showAll ? "analytics.showLess" : "analytics.showMore"}
                />
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};
