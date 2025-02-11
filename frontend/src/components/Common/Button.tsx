import * as React from "react";
import { ButtonProps } from "../../types";
import { formatDistanceToNow, parseISO } from "date-fns";
import BlueArrowIcon from "../../assets/Blue-Arrow-Icon.svg";

export const Button: React.FC<ButtonProps> = ({
  dropdownValues,
  text,
  className,
  onClick,
  isDisabled,
}) => {
  const [showDropdown, setShowDropdown] = React.useState(false);

  const handleButtonClick = () => {
    if (isDisabled) return;

    if (dropdownValues && dropdownValues.length > 0) {
      setShowDropdown(!showDropdown);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div className={`relative w-full flex-grow`}>
      <button
        className={`flex gap-2.5 justify-center items-center px-2.5 py-3 text-sm font-bold text-black rounded-lg border-2 border-solid border-indigo-950 h-full hover:bg-indigo-100 ${
          isDisabled ? "opacity-50 cursor-not-allowed hover:bg-transparent" : ""
        } ${className}`}
        onClick={handleButtonClick}
        disabled={isDisabled}
      >
        <span className="self-stretch my-auto">{text}</span>
        {dropdownValues && dropdownValues.length > 0 && (
          <img
            loading="lazy"
            src={BlueArrowIcon}
            alt="Dropdown Icon"
            className="object-contain shrink-0 self-stretch my-auto w-4 rounded-sm aspect-[1.33]"
          />
        )}
      </button>
      {showDropdown && dropdownValues && dropdownValues.length > 0 && (
        <div className="absolute top-full left-0 w-full bg-white border border-indigo-950 rounded-lg mt-1 z-10 max-h-96 overflow-y-auto">
          {dropdownValues.map((value, index) => (
            <div
              key={index}
              className="px-2.5 py-2 hover:bg-indigo-100 cursor-pointer"
              onClick={() => {
                setShowDropdown(false);
                if (onClick) onClick(value);
              }}
            >
              <span className="line-clamp-2">{value.title}</span>
              <div className="text-xs font-bold">
                {formatDistanceToNow(new Date(parseISO(value.subtitle)), {
                  addSuffix: true,
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
