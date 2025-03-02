import { Message } from "./Message";
import { SuggestionCard } from "./SuggestionCard";
import { WelcomePrompt } from "./WelcomePrompt/WelcomePrompt";
import { LoadingMessage } from "./LoadingMessage";
import {
  ChatSectionProps,
  MessageProps,
  ConversationSession,
} from "../../types";
import { useState, useEffect, useRef } from "react";
import {
  sendMessageAPI,
  restorePastSessionAPI,
  getSuggestionsAPI,
} from "../../api";
import SendIcon from "../../assets/Send-Icon.svg";
import { ThreeDots } from "react-loader-spinner";
import { FormattedMessage, useIntl } from "react-intl";

const COLOUR_PRIMARY = import.meta.env.VITE_REACT_APP_THEME_COLOUR_PRIMARY;

export const ChatSection: React.FC<ChatSectionProps> = ({
  selectedCourse,
  useDarkStyle,
  hidePastSessions,
  resetTrigger,
  preferredLanguage,
}) => {
  const intl = useIntl();
  const [messageList, setMessageList] = useState<MessageProps[]>([]);
  const [suggestionList, setSuggestionList] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const messageEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      if (messageEndRef.current) {
        messageEndRef.current.scrollIntoView({
          behavior: "smooth",
          block: "end",
        });
      }
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messageList]);

  useEffect(() => {
    // Reset all state to initial values
    setMessageList([]);
    setSuggestionList([]);
    setIsLoading(false);
    setIsInitialLoading(true);
    setConversationId(null);

    const messageInput = document.getElementById(
      "messageInput"
    ) as HTMLInputElement;
    if (messageInput) {
      messageInput.value = "";
    }

    // Fetch initial suggestions and start new conversation
    Promise.all([getSuggestionsAPI(selectedCourse.id, 4), invokeMessageAPI("")])
      .then(([suggestions, messages]) => {
        setSuggestionList(suggestions);
        setMessageList(messages);
      })
      .finally(() => {
        setIsInitialLoading(false);
      });
  }, [selectedCourse.id, resetTrigger]); // Reset when course changes or resetTrigger changes

  useEffect(() => {
    if (!isInitialLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isInitialLoading]);

  const handleSuggestionClick = (suggestion: string) => {
    const messageInput = document.getElementById(
      "messageInput"
    ) as HTMLInputElement;
    if (messageInput) {
      messageInput.value = suggestion;
    }
  };

  const invokeMessageAPI = async (message: string) => {
    const response = await sendMessageAPI(
      selectedCourse.id,
      message,
      conversationId || undefined,
      preferredLanguage
    );
    setConversationId(response.conversation_id);
    return response.messages
      .filter((msg) => msg.msg_source !== "SYSTEM")
      .map((msg) => ({
        time: new Date(msg.msg_timestamp + "Z").toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        content: msg.content,
        isUserMessage: msg.msg_source === "STUDENT",
        references: msg.references,
      }));
  };

  const handleFormSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    // Ignore message submissions if currently loading
    if (isInitialLoading || isLoading) return;

    event.preventDefault();
    const messageInput = document.getElementById(
      "messageInput"
    ) as HTMLInputElement;
    if (messageInput && messageInput.value.trim() !== "") {
      const formattedTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      const userMessage = {
        time: formattedTime,
        content: messageInput.value,
        isUserMessage: true,
        references: undefined,
      };
      setMessageList([...messageList, userMessage]);
      messageInput.value = "";
      scrollToBottom(); // Add explicit scroll after user message

      setIsLoading(true);
      setSuggestionList([]);

      const aiResponses = (await invokeMessageAPI(userMessage.content)).filter(
        (msg) => msg.isUserMessage === false
      );
      setMessageList((prevMessages) => [...prevMessages, ...aiResponses]);
      setIsLoading(false);
      scrollToBottom(); // Add explicit scroll after AI response
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const form = (event.target as HTMLInputElement).form;
      if (form) {
        handleFormSubmit(new Event("submit") as any);
      }
    }
  };

  const handleConversationSelect = async (
    conversation: ConversationSession
  ) => {
    const response = await restorePastSessionAPI(conversation.conversation_id);
    setConversationId(conversation.conversation_id);
    const restoredMessages = response.messages
      .filter((msg) => msg.msg_source !== "SYSTEM")
      .map((msg) => ({
        time: new Date(msg.msg_timestamp + "Z").toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        content: msg.content,
        isUserMessage: msg.msg_source === "STUDENT",
        references: msg.references,
      }));
    setMessageList(restoredMessages);
    setSuggestionList([]);
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex-1 overflow-y-auto min-h-0 bg-transparent">
        {isInitialLoading ? (
          <div className="flex justify-center items-center h-64">
            <ThreeDots
              height="50"
              width="50"
              radius="9"
              color={COLOUR_PRIMARY}
              ariaLabel="loading-conversation"
            />
          </div>
        ) : (
          <div className="flex flex-col h-full">
            <div className="flex flex-col justify-center items-center w-full mt-5">
              <WelcomePrompt
                selectedCourse={selectedCourse}
                hidePastSessions={hidePastSessions}
                onConversationSelect={handleConversationSelect}
              />
            </div>
            <div className="flex flex-col-reverse flex-1 mt-8">
              {isLoading && <LoadingMessage />}
              {[...messageList].reverse().map((message, index) => (
                <div key={index} className="mb-4">
                  <Message
                    {...message}
                    useDarkStyle={useDarkStyle}
                    isFirstMessage={index === messageList.length - 1}
                  />
                </div>
              ))}
            </div>
            <div ref={messageEndRef} />
          </div>
        )}
      </div>

      {!isInitialLoading && (
        <div className="flex-none bg-transparent">
          {suggestionList != null && suggestionList.length > 0 && (
            <div className="flex flex-col mb-4 w-full text-sm">
              <div className="font-bold text-primary">
                <FormattedMessage id="chat.suggestions" />
              </div>
              <div className="flex flex-wrap gap-4 items-start mt-4 w-full text-primary">
                {suggestionList.map((suggestion, index) => (
                  <SuggestionCard
                    key={index}
                    text={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                  />
                ))}
              </div>
            </div>
          )}
          <div>
            <form
              className="flex flex-wrap justify-between p-2.5 w-full bg-white rounded-lg shadow-[0px_0px_40px_rgba(137,188,255,0.45)]"
              onSubmit={handleFormSubmit}
            >
              <label htmlFor="messageInput" className="sr-only">
                <FormattedMessage id="chat.inputLabel" />
              </label>
              <input
                ref={inputRef}
                id="messageInput"
                type="text"
                className="flex-1 shrink my-auto text-sm basis-3 max-md:max-w-full outline-none"
                placeholder={intl.formatMessage({
                  id: "chat.inputPlaceholder",
                })}
                autoComplete="off"
                onKeyDown={handleKeyDown}
              />
              <button
                type="submit"
                disabled={isLoading}
                className={`flex overflow-hidden gap-2.5 justify-center items-end px-1.5 w-8 h-full ${
                  isLoading ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                <img
                  loading="lazy"
                  src={SendIcon}
                  alt={intl.formatMessage({ id: "chat.sendButton" })}
                  className={`object-contain flex-1 shrink w-5 aspect-square basis-0 ${
                    isLoading ? "opacity-50" : ""
                  }`}
                />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
