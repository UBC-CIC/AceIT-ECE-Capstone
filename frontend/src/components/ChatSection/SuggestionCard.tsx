import * as React from "react";
import { SuggestionCardProps } from "../../types";

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  text,
  onClick,
}) => {
  return (
    <div
      className="flex-1 text-primary grow shrink gap-2.5 self-stretch p-2.5 rounded-lg border border-white border-solid bg-white bg-opacity-50 hover:bg-opacity-90 transition-all duration-200 cursor-pointer min-w-[240px] w-[201px]"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          onClick();
        }
      }}
    >
      {text}
    </div>
  );
};
