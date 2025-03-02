import * as React from "react";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { MessageProps } from "../../types";
import { FormattedMessage } from "react-intl";

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
  isFirstMessage,
}) => {
  const [isReady, setIsReady] = useState(false);
  const sender = isUserMessage ? (
    <FormattedMessage id="message.you" defaultMessage="You" />
  ) : (
    <FormattedMessage id="message.aiName" defaultMessage="Ace It AI" />
  );

  useEffect(() => {
    setIsReady(false);
    requestAnimationFrame(() => setIsReady(true));
  }, [content]);

  if (!isReady) return null;

  const uniqueReferences = references ? deduplicateReferences(references) : [];

  return (
    <div className="flex flex-col w-full text-sm text-primary max-md:max-w-full">
      <div className={`${isUserMessage ? "text-right" : ""} max-md:max-w-full`}>
        {sender} · {time}
      </div>
      <div
        className={`${
          isUserMessage ? "self-end" : "self-start"
        } p-2.5 rounded-lg border ${
          useDarkStyle ? "border-secondary" : "border-white"
        } border-solid bg-white bg-opacity-50 max-md:max-w-full`}
      >
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p className="mb-4 last:mb-0 text-primary">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc pl-5 mb-4 text-primary">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal pl-5 mb-4 text-primary">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="mb-1 text-primary">{children}</li>
            ),
            h1: ({ children }) => (
              <h1 className="text-2xl font-bold mb-4 text-primary">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-xl font-bold mb-3 text-primary">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-lg font-bold mb-2 text-primary">
                {children}
              </h3>
            ),
            strong: ({ children }) => (
              <strong className="font-bold text-primary">{children}</strong>
            ),
            a: ({ children, href }) => (
              <a
                href={href}
                className="text-blue-600 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
        {uniqueReferences.length > 0 && !isFirstMessage && (
          <>
            <div className="border-b-2 border-secondary my-2" />
            <div>
              <strong>
                <FormattedMessage
                  id="message.referenceTitle"
                  defaultMessage="Reference Materials"
                />
              </strong>
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
