import * as React from "react";
import { AssignmentCard } from "./PastConversationListCard";
import { Button } from "../../../Common/Button";
import { getPastSessionsForCourseAPI } from "../../../../api";
import { ThreeDots } from "react-loader-spinner";
import {
  PreviousConversationListProps,
  ConversationSession,
  ButtonDropdown,
} from "../../../../types";

export const PreviousConversationList: React.FC<
  PreviousConversationListProps
> = ({ courseId, onConversationSelect }) => {
  const [conversations, setConversations] = React.useState<
    ConversationSession[]
  >([]);
  const [isLoading, setIsLoading] = React.useState(true);

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

  const handleDropdownSelect = (selected?: ButtonDropdown) => {
    if (!selected) return;

    const conversation = conversations.find(
      (conv) =>
        conv.summary === selected.title &&
        conv.last_message_timestamp === selected.subtitle
    );
    if (conversation) {
      onConversationSelect(conversation);
    }
  };

  return conversations === null || conversations.length === 0 ? null : (
    <div>
      <div className="mt-5 text-sm font-bold text-center text-stone-950 pb-4">
        Resume Past Conversation
      </div>
      <div className="flex flex-wrap gap-5 justify-center items-stretch text-black">
        {conversations.slice(0, 3).map((Conversation, index) => (
          <AssignmentCard
            key={index}
            summary={Conversation.summary}
            date={Conversation.last_message_timestamp}
            className="flex-grow"
            onClick={() => onConversationSelect(Conversation)}
          />
        ))}
        <div className="flex-grow flex items-stretch">
          <Button
            text="Older Conversations"
            isOutlined={true}
            isDisabled={false}
            dropdownValues={conversations.slice(3).map((conversation) => ({
              title: conversation.summary,
              subtitle: conversation.last_message_timestamp,
            }))}
            className="w-full flex-grow"
            onClick={handleDropdownSelect}
          />
        </div>
      </div>
    </div>
  );
};
