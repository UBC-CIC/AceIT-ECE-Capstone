import * as React from "react";
import { AssignmentCardProps } from "../../../../types";
import { formatDistanceToNow, parseISO } from "date-fns"; // Import date-fns for date formatting

export const AssignmentCard: React.FC<
  AssignmentCardProps & { className?: string; onClick?: () => void }
> = ({ summary, date, className, onClick }) => {
  // Convert date to human-readable format
  const formattedDate = formatDistanceToNow(parseISO(date), {
    addSuffix: true,
  });

  return (
    <div
      className={`flex flex-col justify-center self-stretch px-2.5 py-2 rounded-lg border-2 border-solid border-indigo-950 min-h-[80px] w-[190px] hover:bg-indigo-100 cursor-pointer ${className}`}
      onClick={onClick}
    >
      <div className="h-10 text-sm font-regular overflow-hidden flex items-center">
        <span className="line-clamp-2">{summary}</span>
      </div>
      <div className="mt-2.5 text-xs font-bold">{formattedDate}</div>
    </div>
  );
};
