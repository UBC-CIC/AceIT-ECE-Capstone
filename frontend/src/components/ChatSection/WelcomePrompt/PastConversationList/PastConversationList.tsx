import * as React from "react";
import { AssignmentCard } from "./PastConversationListCard";
import { Button } from "../../../Common/Button";
import { getPastSessionsForCourseAPI } from "../../../../api";
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

  React.useEffect(() => {
    const fetchConversations = async () => {
      const data = await getPastSessionsForCourseAPI(courseId);
      setConversations(data);
    };

    fetchConversations();
  }, [courseId]);

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

  return (
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
  );
};
