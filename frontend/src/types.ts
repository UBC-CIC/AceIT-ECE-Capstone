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
  content: string; // Markdown formatted string
  isUserMessage?: boolean;
  useDarkStyle?: boolean;
}

export type MessageSource = "STUDENT" | "AI" | "SYSTEM";

export interface MessageReference {
  documentName: string;
  sourceUrl: string;
  documentContent: string;
}

export interface ConversationMessage {
  message_id: string;
  content: string; // Markdown formatted string
  msg_source: MessageSource;
  course_id: string;
  msg_timestamp: string;
  references?: MessageReference[];
  student_id?: string;
}

export interface HeaderProps {
  userName: string;
  currentCourse: CourseProps | null;
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

export type IncludedCourseContentType = keyof IncludedCourseContent;
export type SupportedQuestionsType = keyof SupportedQuestions;

export interface CourseContentItem {
  title: string;
  type: IncludedCourseContentType;
}

export interface SupportedQuestionItem {
  title: string;
  type: SupportedQuestionsType;
}

export interface CheckboxItemProps {
  title: string;
  checked: boolean;
  onChange: () => void;
}

export interface IncludedCourseContent {
  HOME: boolean;
  ANNOUNCEMENTS: boolean;
  SYLLABUS: boolean;
  ASSIGNMENTS: boolean;
  MODULES: boolean;
  FILES: boolean;
  QUIZZES: boolean;
  DISCUSSIONS: boolean;
  PAGES: boolean;
}

export interface SupportedQuestions {
  RECOMMENDATIONS: boolean;
  PRACTICE_PROBLEMS: boolean;
  SOLUTION_REVIEW: boolean;
  EXPLANATION: boolean;
}

export interface CourseConfiguration {
  studentAccessEnabled: boolean;
  selectedIncludedCourseContent: IncludedCourseContent;
  selectedSupportedQuestions: SupportedQuestions;
  customResponseFormat: string;
  systemPrompt?: string;
  materialLastUpdatedTime?: string;
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
  loading: boolean;
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
