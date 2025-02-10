import * as React from "react";
import ReactMarkdown from "react-markdown";
import { MessageProps } from "../../types";

export const Message: React.FC<MessageProps> = ({
  time,
  content,
  isUserMessage,
  useDarkStyle,
}) => {
  const sender = isUserMessage ? "You" : "Ace It AI";

  return (
    <div className="flex flex-col w-full text-sm text-indigo-950 max-md:max-w-full">
      <div className={`${isUserMessage ? "text-right" : ""} max-md:max-w-full`}>
        {sender} · {time}
      </div>
      <div
        className={`${
          isUserMessage ? "self-end" : "self-start"
        } p-2.5 rounded-lg border ${
          useDarkStyle ? "border-indigo-300" : "border-white"
        } border-solid bg-white bg-opacity-50 max-md:max-w-full`}
      >
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
};
