import * as React from "react";
import { FormattedMessage } from "react-intl";
import { SUPPORTED_LANGUAGES, LanguagePopupProps } from "../../../types";

export const LanguagePopup: React.FC<LanguagePopupProps> = ({
  isOpen,
  onClose,
  selectedLanguage,
  onLanguageChange,
  onConfirm,
  hasLanguageChanged,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="w-[480px] bg-white rounded-lg shadow-lg z-50 text-primary"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="text-left">
            <h2 className="text-xl font-bold text-primary mb-1">
              <FormattedMessage
                id="header.languagePopupTitle"
                defaultMessage="Change Preferred Response Language"
              />
            </h2>
            <p className="text-sm text-primary mb-4">
              <FormattedMessage
                id="header.languagePopupDescription"
                defaultMessage="Select your preferred language for Ace It. This will impact both the language of the AI responses and user interface."
              />
            </p>
          </div>
          <select
            value={selectedLanguage}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="w-full p-2 border rounded mb-4 text-sm"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.displayName}
              </option>
            ))}
          </select>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 text-sm font-bold text-primary rounded-lg bg-gray-100 hover:bg-gray-200"
            >
              <FormattedMessage id="header.cancel" defaultMessage="Cancel" />
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={!hasLanguageChanged}
              className={`px-6 py-3 text-sm font-bold text-white rounded-lg ${
                hasLanguageChanged
                  ? "bg-primary hover:bg-primary hover:bg-opacity-85"
                  : "bg-primary opacity-50 cursor-not-allowed"
              }`}
            >
              <FormattedMessage id="header.confirm" defaultMessage="Confirm" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
