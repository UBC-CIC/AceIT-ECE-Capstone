import * as React from "react";
import { useState, useEffect } from "react";
import { HeaderProps, SUPPORTED_LANGUAGES } from "../../types";
import UBCLogoWhite from "../../assets/UBC-logo-white.png";

export const Header: React.FC<HeaderProps> = ({
  currentCourse,
  onLogout,
  onLanguageChange,
  userInfo,
}) => {
  const [isLanguagePopupOpen, setIsLanguagePopupOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(
    userInfo?.preferred_language || ""
  );

  useEffect(() => {
    if (userInfo?.preferred_language) {
      setSelectedLanguage(userInfo.preferred_language);
    }
  }, [userInfo?.preferred_language]);

  const hasLanguageChanged = userInfo?.preferred_language !== selectedLanguage;

  const handleLanguageConfirm = () => {
    if (!hasLanguageChanged) return;
    onLanguageChange(selectedLanguage);
    setIsLanguagePopupOpen(false);
  };

  return (
    <div className="flex flex-wrap gap-4 items-stretch w-full text-white max-md:max-w-full">
      <div className="flex flex-wrap gap-3.5 items-center self-auto py-3.5 pr-3 pl-4 rounded-xl border-white border-solid bg-indigo-950 border-[3px] w-[290px]">
        <img
          loading="lazy"
          src={UBCLogoWhite}
          alt="Ace It - UBC Logo"
          className="object-contain shrink-0 self-stretch my-auto aspect-[0.75] w-[30px]"
        />
        <div className="flex flex-col flex-1 shrink justify-center self-stretch my-auto basis-0">
          <div className="text-xl font-semibold leading-snug">Ace It</div>
          <div className="text-sm font-medium leading-loose">
            AI Study Assistant
          </div>
        </div>
      </div>
      <div className="flex flex-wrap flex-1 shrink gap-3.5 items-start self-auto px-3 py-5 rounded-xl border-white border-solid basis-0 bg-indigo-950 border-[3px] min-w-[240px] max-md:max-w-full">
        <div className="flex overflow-hidden flex-wrap flex-1 shrink justify-between px-3 py-1.5 w-full basis-0 min-w-[240px] max-md:max-w-full">
          <div className="flex overflow-hidden flex-wrap flex-1 shrink gap-3 items-center my-auto text-xl leading-snug basis-0 min-w-[240px] max-md:max-w-full">
            <div className="self-stretch my-auto font-semibold">
              {currentCourse ? currentCourse.courseCode : ""}
            </div>
            <div className="self-stretch my-auto">
              {currentCourse ? currentCourse.name : ""}
            </div>
          </div>
          <div className="flex gap-2.5 items-center h-full text-base leading-none text-right">
            <div className="self-stretch my-auto">{userInfo?.userName}</div>
            <div className="self-stretch my-auto">•</div>
            <div className="relative group z-[100]">
              <button
                onClick={() => setIsLanguagePopupOpen(true)}
                className="relative flex items-center px-2 py-1 hover:text-gray-200 transition-colors duration-200 cursor-pointer"
              >
                <span className="sr-only">Change Language</span>
                🌐
                <span className="absolute hidden group-hover:block bg-gray-900 text-white text-xs px-2 py-1 rounded -translate-x-1/2 left-1/2 -top-8 whitespace-nowrap min-w-max">
                  Change Response Language
                </span>
              </button>
              {isLanguagePopupOpen && (
                <div
                  className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center"
                  onClick={() => setIsLanguagePopupOpen(false)}
                >
                  <div
                    className="w-[480px] bg-white rounded-lg shadow-lg z-50 text-gray-800"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="p-6">
                      <div className="text-left">
                        <h2 className="text-xl font-bold text-gray-900 mb-1">
                          Change Preferred Response Language
                        </h2>
                        <p className="text-sm text-gray-600 mb-4">
                          Select your preferred language for Ace It. This will
                          impact both the language of the AI responses and user
                          interface.
                        </p>
                      </div>
                      <select
                        value={selectedLanguage}
                        onChange={(e) => setSelectedLanguage(e.target.value)}
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
                          onClick={() => setIsLanguagePopupOpen(false)}
                          className="px-6 py-3 text-sm font-bold text-black rounded-lg bg-gray-100 hover:bg-gray-200"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={handleLanguageConfirm}
                          disabled={!hasLanguageChanged}
                          className={`px-6 py-3 text-sm font-bold text-white rounded-lg ${
                            hasLanguageChanged
                              ? "bg-indigo-950 hover:bg-indigo-900"
                              : "bg-indigo-950 opacity-50 cursor-not-allowed"
                          }`}
                        >
                          Confirm
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="self-stretch my-auto">•</div>
            <button
              onClick={onLogout}
              className="self-stretch my-auto font-semibold leading-7 w-[60px] hover:text-gray-200 transition-colors duration-200 hover:underline"
            >
              Log Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
