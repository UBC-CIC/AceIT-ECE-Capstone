export interface CourseAPIModelProps {
  id: string;
  courseCode: string;
  name: string;
}

export interface CourseProps {
  id: string;
  courseCode: string;
  name: string;
  userCourseRole: UserRole;
  isActive?: boolean;
  isAvailable?: boolean;
}

export interface UserProps {
  userId: string;
  userName: string;
}

export type UserRole = "STUDENT" | "INSTRUCTOR";

export interface SuggestionProps {
  text: string;
}

export interface MessageProps {
  time: string;
  content: React.ReactNode;
  isUserMessage?: boolean;
  useDarkStyle?: boolean;
}

export type MessageSource = "USER" | "AI";

export interface ConversationMessage {
  text: string;
  source: MessageSource;
}

export interface HeaderProps {
  userName: string;
  currentCourse: CourseProps;
  onLogout: () => void;
}

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
}

export interface CourseListProps {
  courses: CourseProps[];
  onCourseSelect: (course: CourseProps) => void;
}

export interface SuggestionCardProps {
  text: string;
  onClick: () => void;
}

export interface AssignmentCardProps {
  summary: string;
  date: string;
}

export interface ButtonProps {
  isOutlined: boolean;
  isDisabled: boolean;
  dropdownValues?: ButtonDropdown[];
  text: string;
  onClick: (selectedDropdown?: ButtonDropdown) => void;
  className?: string;
}

export interface ButtonDropdown {
  title: string;
  subtitle: string;
}

export interface PreviousConversationListProps {
  courseId: string;
  onConversationSelect: (conversation: ConversationSession) => void;
}

export interface WelcomePromptProps {
  selectedCourse: CourseProps;
  hidePastSessions: boolean;
  onConversationSelect: (conversation: ConversationSession) => void;
}

export interface ChatSectionProps {
  selectedCourse: CourseProps;
  useDarkStyle: boolean;
  hidePastSessions: boolean;
}

export interface CourseNavBarItemProps {
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

export interface CourseContentItem {
  title: string;
  type: IncludedCourseContent;
}

export interface SupportedQuestionItem {
  title: string;
  type: SupportedQuestions;
}

export interface CheckboxItemProps {
  title: string;
  checked: boolean;
  onChange: () => void;
}

export type SupportedQuestions =
  | "RECOMMENDATIONS"
  | "PRACTICE_PROBLEMS"
  | "SOLUTION_REVIEW"
  | "EXPLANATION";

export type IncludedCourseContent =
  | "HOME"
  | "ANNOUNCEMENTS"
  | "SYLLABUS"
  | "ASSIGNMENTS"
  | "MODULES"
  | "FILES"
  | "QUIZZES"
  | "DISCUSSIONS"
  | "PAGES";

export interface CourseConfiguration {
  studentAccessEnabled: boolean;
  selectedIncludedCourseContent: IncludedCourseContent[];
  selectedSupportedQuestions: SupportedQuestions[];
  customResponseFormat: string;
}

export interface ToggleProps {
  isOn: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export type Timeframe = "WEEK" | "MONTH" | "TERM";

export type ListCardItem = {
  title: string;
  link?: string;
};

export interface ListStatisticCardProps {
  title: string;
  timeframe: Timeframe;
  items: ListCardItem[];
  onPeriodChange: (newTimeframe: Timeframe) => void;
  loading: boolean;
}

export interface CourseAnalyticsSectionProps {
  selectedCourse: CourseProps;
}

export interface MetricsCardProps {
  title: string;
  value: number;
  iconSrc: string;
}

export interface EngagementCardProps {
  questionsAsked: number;
  studentSessions: number;
  studentsUsingAceIt: number;
  timeframe: Timeframe;
  onPeriodChange: (newTimeframe: Timeframe) => void;
  loading: boolean;
}

// Expected API Response Data Formats
// TODO: Expand this section to cover each of the APIs based on the known spec and align to mocked data

export interface CourseStudentEngagement {
  questionsAsked: number;
  studentSessions: number;
  uniqueStudents: number;
}

export interface CourseCommonQuestions {
  questions: string[];
}

export interface CourseMostReferencedMaterials {
  materials: MaterialType[];
}

export type MaterialType = {
  title: string;
  link: string;
};

export interface ConversationSession {
  conversation_id: string;
  last_message_timestamp: string;
  summary: string;
}
