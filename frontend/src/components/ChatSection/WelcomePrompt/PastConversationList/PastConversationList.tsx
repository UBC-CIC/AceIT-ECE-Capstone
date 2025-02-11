import * as React from "react";
import { AssignmentCard } from "./PastConversationListCard";
import { Button } from "../../../Common/Button";
import { getPastSessionsForCourseAPI } from "../../../../api";
import { ThreeDots } from "react-loader-spinner";
import {
  PreviousConversationListProps,
  ConversationSession,
} from "../../../../types";

export const PreviousConversationList: React.FC<
  PreviousConversationListProps
> = ({ courseId, onConversationSelect }) => {
  const [conversations, setConversations] = React.useState<
    ConversationSession[]
  >([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [isLoadingConversation, setIsLoadingConversation] =
    React.useState(false);

  React.useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      try {
        const data = await getPastSessionsForCourseAPI(courseId);
        setConversations(data);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [courseId]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <ThreeDots
          height="50"
          width="50"
          radius="9"
          color="#1e1b4b"
          ariaLabel="loading-conversations"
        />
      </div>
    );
  }

  const handleConversationSelect = async (
    conversation: ConversationSession
  ) => {
    setSelectedId(conversation.conversation_id);
    setIsLoadingConversation(true);
    try {
      await onConversationSelect(conversation);
    } catch (error) {
      console.error("Failed to load conversation:", error);
    } finally {
      setIsLoadingConversation(false);
      setSelectedId(null);
    }
  };

  const isInteractionDisabled = isLoadingConversation;

  return conversations === null || conversations.length === 0 ? null : (
    <div>
      <div className="mt-5 text-sm font-bold text-center text-stone-950 pb-4">
        Resume Past Conversation
      </div>
      <div className="flex flex-wrap gap-5 justify-center items-stretch text-black">
        {conversations.slice(0, 3).map((conversation, index) => (
          <div key={index} className="flex-grow relative">
            <AssignmentCard
              summary={conversation.summary}
              date={conversation.last_message_timestamp}
              className="flex-grow"
              onClick={() =>
                !isInteractionDisabled && handleConversationSelect(conversation)
              }
              disabled={isInteractionDisabled}
            />
            {selectedId === conversation.conversation_id && (
              <div className="absolute inset-0 flex items-center justify-center bg-indigo-100 rounded-lg">
                <ThreeDots
                  height="20"
                  width="20"
                  radius="9"
                  color="#1e1b4b"
                  ariaLabel="loading-conversation"
                />
              </div>
            )}
          </div>
        ))}
        <div className="flex-grow flex items-stretch">
          <Button
            text="Older Conversations"
            isOutlined={true}
            isDisabled={isInteractionDisabled}
            dropdownValues={conversations.slice(3).map((conversation) => ({
              title: conversation.summary,
              subtitle: conversation.last_message_timestamp,
            }))}
            className="w-full flex-grow"
            onClick={(selected) =>
              selected &&
              handleConversationSelect(
                conversations.find(
                  (conv) =>
                    conv.summary === selected.title &&
                    conv.last_message_timestamp === selected.subtitle
                )!
              )
            }
          />
        </div>
      </div>
    </div>
  );
};
