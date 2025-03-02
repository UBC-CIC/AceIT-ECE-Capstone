import * as React from "react";
import { FormattedRelativeTime } from "react-intl";
import { PastConversationListCardProps } from "../../../../types";

export const PastConversationListCard: React.FC<
  PastConversationListCardProps
> = ({ summary, date, className, onClick, disabled = false }) => {
  const timestamp = new Date(date + "Z").getTime();
  const now = Date.now();
  const seconds = Math.round((timestamp - now) / 1000);

  const handleClick = () => {
    if (!disabled && onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`flex flex-col justify-center px-2.5 py-2 rounded-lg border-2 border-solid border-primary min-h-[80px] min-w-[190px] w-full hover:bg-secondary cursor-pointer ${
        disabled ? "opacity-50 cursor-not-allowed hover:bg-transparent" : ""
      } ${className}`}
      onClick={handleClick}
    >
      <div className="h-10 text-sm font-regular overflow-hidden flex items-center">
        <span className="line-clamp-2">{summary}</span>
      </div>
      <div className="mt-2.5 text-xs font-bold text-primary">
        <FormattedRelativeTime
          value={seconds}
          numeric="auto"
          style="long"
          updateIntervalInSeconds={60}
        />
      </div>
    </div>
  );
};
