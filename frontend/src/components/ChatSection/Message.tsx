import * as React from "react";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { MessageProps } from "../../types";

const deduplicateReferences = (
  references: Array<{ documentName: string; sourceUrl: string }>
) => {
  const seen = new Set<string>();
  return references.filter((ref) => {
    const key = `${ref.documentName}-${ref.sourceUrl}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

export const Message: React.FC<MessageProps> = ({
  time,
  content,
  isUserMessage,
  useDarkStyle,
  references,
}) => {
  const [isReady, setIsReady] = useState(false);
  const sender = isUserMessage ? "You" : "Ace It AI";

  useEffect(() => {
    setIsReady(false);
    requestAnimationFrame(() => setIsReady(true));
  }, [content]);

  if (!isReady) return null;

  const uniqueReferences = references ? deduplicateReferences(references) : [];

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
        <ReactMarkdown
          components={{
            p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
          }}
        >
          {content}
        </ReactMarkdown>
        {uniqueReferences.length > 0 && (
          <>
            <div className="border-b-2 border-[#030852] my-2 opacity-[0.17]" />
            <div>
              <strong>Reference Materials</strong>
              <ul className="list-disc pl-5 mt-1">
                {uniqueReferences.map((reference, index) => (
                  <li key={index}>
                    <a
                      href={reference.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {reference.documentName}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
