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
import { sendMessageAPI, restorePastSessionAPI } from "../../api";
import SendIcon from "../../assets/Send-Icon.svg";
import { ThreeDots } from "react-loader-spinner";

// TODO: Replace in the future with dynamic suggestions from the backend (generated via AI)
const suggestions: string[] = [
  "Give me the link to the course syllabus in Canvas",
  "Give me a summary of the past class",
  "Review my answers for the upcoming homework",
  "Generate some practice problems for the last lecture",
];

export const ChatSection: React.FC<ChatSectionProps> = ({
  selectedCourse,
  useDarkStyle,
  hidePastSessions,
  resetTrigger,
}) => {
  const [messageList, setMessageList] = useState<MessageProps[]>([]);
  const [suggestionList, setSuggestionList] = useState<string[]>(suggestions);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const messageEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messageList]);

  useEffect(() => {
    // Reset all state to initial values
    setMessageList([]);
    setSuggestionList(suggestions);
    setIsLoading(false);
    setIsInitialLoading(true);
    setConversationId(null);

    const messageInput = document.getElementById(
      "messageInput"
    ) as HTMLInputElement;
    if (messageInput) {
      messageInput.value = "";
    }

    // Start a new conversation by invoking API to get AI welcome prompt
    invokeMessageAPI("")
      .then((messages) => {
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
      conversationId || undefined
    );
    setConversationId(response.conversation_id);
    return response.messages
      .filter((msg) => msg.msg_source !== "SYSTEM")
      .map((msg) => ({
        time: new Date(msg.msg_timestamp).toLocaleTimeString([], {
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

      setIsLoading(true);
      setSuggestionList([]);

      const aiResponses = (await invokeMessageAPI(userMessage.content)).filter(
        (msg) => msg.isUserMessage === false
      );
      setMessageList((prevMessages) => [...prevMessages, ...aiResponses]);
      setIsLoading(false);
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
    setConversationId(response.conversation_id);
    const restoredMessages = response.messages
      .filter((msg) => msg.msg_source !== "SYSTEM")
      .map((msg) => ({
        time: new Date(msg.msg_timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        content: msg.content,
        isUserMessage: msg.msg_source === "STUDENT",
        references: msg.references,
      }));
    setMessageList(restoredMessages);
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
              color="#1e1b4b"
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
                  <Message {...message} useDarkStyle={useDarkStyle} />
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
              <div className="font-bold text-slate-500">
                Suggestions on what to ask
              </div>
              <div className="flex flex-wrap gap-4 items-start mt-4 w-full text-indigo-950">
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
                Ask me anything about your class
              </label>
              <input
                ref={inputRef}
                id="messageInput"
                type="text"
                className="flex-1 shrink my-auto text-sm basis-3  max-md:max-w-full outline-none"
                placeholder="Ask me anything about your class"
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
                  alt="Send message"
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
