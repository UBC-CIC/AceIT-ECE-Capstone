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
}) => {
  const [messageList, setMessageList] = useState<MessageProps[]>([]);
  const [suggestionList, setSuggestionList] = useState<string[]>(suggestions);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const messageEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messageList]);

  useEffect(() => {
    setSuggestionList(suggestions);
    const messageInput = document.getElementById(
      "messageInput"
    ) as HTMLInputElement;
    if (messageInput) {
      messageInput.value = "";
    }

    setIsInitialLoading(true);

    // Invoke the message API to generate the conversationId and get the initial AI message prompt
    invokeMessageAPI("")
      .then((messages) => {
        setMessageList(messages);
      })
      .finally(() => {
        setIsInitialLoading(false);
      });
  }, [selectedCourse]);

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
      }));
    setMessageList(restoredMessages);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 min-h-0 overflow-y-auto">
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
            <div className="flex-1 min-h-0">
              <div className="flex flex-col w-full max-w-full">
                <div>
                  <div className="flex flex-col justify-center items-center w-full max-w-full mt-5">
                    <WelcomePrompt
                      selectedCourse={selectedCourse}
                      hidePastSessions={hidePastSessions}
                      onConversationSelect={handleConversationSelect}
                    />
                  </div>
                  <div className="mt-8" />
                  {messageList.map((message, index) => (
                    <div key={index} className="mb-4 last:mb-0">
                      <Message {...message} useDarkStyle={useDarkStyle} />
                    </div>
                  ))}
                  <div ref={messageEndRef} />
                  {isLoading && <LoadingMessage />}
                  {suggestionList != null && suggestionList.length > 0 && (
                    <div className="flex flex-col mt-5 w-full text-sm max-w-full">
                      <div className="font-bold text-slate-500 max-w-full">
                        Suggestions on what to ask
                      </div>
                      <div className="flex flex-wrap gap-4 items-start mt-4 w-full text-indigo-950 max-w-full">
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
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      {isInitialLoading ? null : (
        <div className="flex-none mt-5">
          <form
            className="flex flex-wrap justify-between p-2.5 w-full bg-white rounded-lg shadow-[0px_0px_40px_rgba(137,188,255,0.45)] max-md:max-w-full"
            onSubmit={handleFormSubmit}
          >
            <label htmlFor="messageInput" className="sr-only">
              Ask me anything about your class
            </label>
            <input
              id="messageInput"
              type="text"
              className="flex-1 shrink my-auto text-sm basis-3  max-md:max-w-full outline-none"
              placeholder="Ask me anything about your class"
              autoComplete="off"
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
      )}
    </div>
  );
};
