import React from "react";
import { PreviousConversationList } from "./PastConversationList/PastConversationList";
import { WelcomePromptProps } from "../../../types";
import SparkleIcon from "../../../assets/Sparkle-Icon.svg";

export const WelcomePrompt: React.FC<WelcomePromptProps> = ({
  selectedCourse,
  hidePastSessions,
  onConversationSelect,
}) => {
  return (
    <div className="flex flex-col justify-center items-center px-24 w-full max-md:px-5 max-md:max-w-full space-y-5 pt-20">
      <img
        loading="lazy"
        src={SparkleIcon}
        alt=""
        className="object-contain w-9 aspect-[0.95]"
      />
      <div className="mt-5 text-2xl text-center text-stone-950">
        How can I help you with {selectedCourse.courseCode} today?
      </div>
      {!hidePastSessions && (
        <>
          <PreviousConversationList
            courseId={selectedCourse.id}
            onConversationSelect={onConversationSelect}
          />
        </>
      )}
    </div>
  );
};
