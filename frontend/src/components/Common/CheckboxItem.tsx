import * as React from "react";
import { CheckboxItemProps } from "../../types";

export const CheckboxItem: React.FC<CheckboxItemProps> = ({
  title,
  checked,
  onChange,
}) => {
  return (
    <label className="flex gap-3 items-center cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="w-4 h-4"
        aria-label={title}
      />
      <div className="text-sm font-medium text-primary">{title}</div>
    </label>
  );
};
