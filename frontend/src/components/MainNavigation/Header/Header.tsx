import * as React from "react";
import { useState, useEffect } from "react";
import { HeaderProps } from "../../../types";
import { FormattedMessage } from "react-intl";
const UBCLogoWhite = new URL(
  `../../../assets/${import.meta.env.VITE_REACT_APP_THEME_LOGO_FILE_NAME}`,
  import.meta.url
).href;
import { LanguagePopup } from "./LanguagePopup";

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
    <div className="flex flex-wrap gap-4 items-stretch w-full text-tertiary max-md:max-w-full">
      <div className="flex flex-wrap gap-3.5 items-center self-auto py-3.5 pr-3 pl-4 rounded-xl border-white border-solid bg-primary border-[3px] w-[290px]">
        <img
          loading="lazy"
          src={UBCLogoWhite}
          alt="Ace It - UBC Logo"
          className="object-contain shrink-0 self-stretch my-auto aspect-[0.75] w-[30px]"
        />
        <div className="flex flex-col flex-1 shrink justify-center self-stretch my-auto basis-0">
          <div className="text-xl font-semibold leading-snug">
            <FormattedMessage id="header.appName" defaultMessage="Ace It" />
          </div>
          <div className="text-sm font-medium leading-loose">
            <FormattedMessage
              id="header.appSubtitle"
              defaultMessage="AI Study Assistant"
            />
          </div>
        </div>
      </div>
      <div className="flex flex-wrap flex-1 shrink gap-3.5 items-start self-auto px-3 py-5 rounded-xl border-white border-solid basis-0 bg-primary border-[3px] min-w-[240px] max-md:max-w-full">
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
                className="relative flex items-center px-2 py-1 hover:text-secondary transition-colors duration-200 cursor-pointer"
              >
                <span className="sr-only">
                  <FormattedMessage
                    id="header.changeLanguage"
                    defaultMessage="Change Language"
                  />
                </span>
                🌐
                <span className="absolute hidden group-hover:block bg-gray-900 text-white text-xs px-2 py-1 rounded -translate-x-1/2 left-1/2 -top-8 whitespace-nowrap min-w-max">
                  <FormattedMessage
                    id="header.changeLanguage"
                    defaultMessage="Change Language"
                  />
                </span>
              </button>
              <LanguagePopup
                isOpen={isLanguagePopupOpen}
                onClose={() => setIsLanguagePopupOpen(false)}
                selectedLanguage={selectedLanguage}
                onLanguageChange={setSelectedLanguage}
                onConfirm={handleLanguageConfirm}
                hasLanguageChanged={hasLanguageChanged}
              />
            </div>
            <div className="self-stretch my-auto">•</div>
            <button
              onClick={onLogout}
              className="self-stretch my-auto font-semibold leading-7 w-[60px] hover:text-secondary transition-colors duration-200 hover:underline"
            >
              <FormattedMessage id="header.logout" defaultMessage="Log Out" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
