import * as React from "react";
import { PastConversationListCardProps } from "../../../../types";
import { formatDistanceToNow } from "date-fns";

export const PastConversationListCard: React.FC<
  PastConversationListCardProps
> = ({ summary, date, className, onClick, disabled = false }) => {
  const formattedDate = formatDistanceToNow(new Date(date + "Z"), {
    addSuffix: true,
  });

  const handleClick = () => {
    if (!disabled && onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`flex flex-col justify-center px-2.5 py-2 rounded-lg border-2 border-solid border-indigo-950 min-h-[80px] min-w-[190px] w-full hover:bg-indigo-100 cursor-pointer ${
        disabled ? "opacity-50 cursor-not-allowed hover:bg-transparent" : ""
      } ${className}`}
      onClick={handleClick}
    >
      <div className="h-10 text-sm font-regular overflow-hidden flex items-center">
        <span className="line-clamp-2">{summary}</span>
      </div>
      <div className="mt-2.5 text-xs font-bold">{formattedDate}</div>
    </div>
  );
};
