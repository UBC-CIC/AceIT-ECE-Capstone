import * as React from "react";
import { ToggleProps } from "../../types";

export const Toggle: React.FC<ToggleProps> = ({ isOn, onToggle, disabled }) => {
  return (
    <div className="h-[38px] mt-3">
      <button
        onClick={(e) => {
          e.preventDefault(); // Prevent form submission
          if (!disabled) {
            onToggle();
          }
        }}
        type="button" // Prevent form submission
        className={`inline-flex items-center px-1.5 rounded-2xl w-[80px] h-[38px] ${
          isOn ? "bg-primary" : "bg-secondary"
        } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
        role="switch"
        aria-checked={isOn}
        disabled={disabled}
      >
        <div className="relative w-full flex items-center">
          <div
            className={`text-sm font-semibold text-tertiary w-[28px] text-center z-10 ${
              isOn ? "ml-0" : "ml-auto"
            }`}
          >
            {isOn ? "ON" : "OFF"}
          </div>
          <div
            className={`absolute left-0 bg-tertiary rounded-2xl h-[30px] w-[30px] shadow-[0_2px_4px_rgba(0,35,11,0.2)] transition-transform duration-200 ${
              isOn ? "translate-x-[38px]" : "translate-x-[0px]"
            }`}
          />
        </div>
      </button>
    </div>
  );
};
