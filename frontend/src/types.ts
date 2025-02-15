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
  preferred_language: string;
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
  references?: MessageReference[];
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
  currentCourse: CourseProps | null;
  onLogout: () => void;
  onLanguageChange: (language: string) => void;
  userInfo: UserProps | null;
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

export interface PastConversationListCardProps {
  summary: string;
  date: string;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
}

export interface ButtonProps {
  isOutlined?: boolean;
  isDisabled?: boolean;
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
  resetTrigger?: string;
  preferredLanguage?: string;
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

export interface LanguageOption {
  code: string;
  displayName: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "af", displayName: "Afrikaans" },
  { code: "sq", displayName: "Albanian" },
  { code: "am", displayName: "Amharic" },
  { code: "ar", displayName: "Arabic" },
  { code: "hy", displayName: "Armenian" },
  { code: "az", displayName: "Azerbaijani" },
  { code: "bn", displayName: "Bengali" },
  { code: "bs", displayName: "Bosnian" },
  { code: "bg", displayName: "Bulgarian" },
  { code: "ca", displayName: "Catalan" },
  { code: "zh", displayName: "Chinese (Simplified)" },
  { code: "zh-TW", displayName: "Chinese (Traditional)" },
  { code: "hr", displayName: "Croatian" },
  { code: "cs", displayName: "Czech" },
  { code: "da", displayName: "Danish" },
  { code: "fa-AF", displayName: "Dari" },
  { code: "nl", displayName: "Dutch" },
  { code: "en", displayName: "English" },
  { code: "et", displayName: "Estonian" },
  { code: "fa", displayName: "Farsi (Persian)" },
  { code: "tl", displayName: "Filipino, Tagalog" },
  { code: "fi", displayName: "Finnish" },
  { code: "fr", displayName: "French" },
  { code: "fr-CA", displayName: "French (Canada)" },
  { code: "ka", displayName: "Georgian" },
  { code: "de", displayName: "German" },
  { code: "el", displayName: "Greek" },
  { code: "gu", displayName: "Gujarati" },
  { code: "ht", displayName: "Haitian Creole" },
  { code: "ha", displayName: "Hausa" },
  { code: "he", displayName: "Hebrew" },
  { code: "hi", displayName: "Hindi" },
  { code: "hu", displayName: "Hungarian" },
  { code: "is", displayName: "Icelandic" },
  { code: "id", displayName: "Indonesian" },
  { code: "ga", displayName: "Irish" },
  { code: "it", displayName: "Italian" },
  { code: "ja", displayName: "Japanese" },
  { code: "kn", displayName: "Kannada" },
  { code: "kk", displayName: "Kazakh" },
  { code: "ko", displayName: "Korean" },
  { code: "lv", displayName: "Latvian" },
  { code: "lt", displayName: "Lithuanian" },
  { code: "mk", displayName: "Macedonian" },
  { code: "ms", displayName: "Malay" },
  { code: "ml", displayName: "Malayalam" },
  { code: "mt", displayName: "Maltese" },
  { code: "mr", displayName: "Marathi" },
  { code: "mn", displayName: "Mongolian" },
  { code: "no", displayName: "Norwegian (Bokmål)" },
  { code: "ps", displayName: "Pashto" },
  { code: "pl", displayName: "Polish" },
  { code: "pt", displayName: "Portuguese (Brazil)" },
  { code: "pt-PT", displayName: "Portuguese (Portugal)" },
  { code: "pa", displayName: "Punjabi" },
  { code: "ro", displayName: "Romanian" },
  { code: "ru", displayName: "Russian" },
  { code: "sr", displayName: "Serbian" },
  { code: "si", displayName: "Sinhala" },
  { code: "sk", displayName: "Slovak" },
  { code: "sl", displayName: "Slovenian" },
  { code: "so", displayName: "Somali" },
  { code: "es", displayName: "Spanish" },
  { code: "es-MX", displayName: "Spanish (Mexico)" },
  { code: "sw", displayName: "Swahili" },
  { code: "sv", displayName: "Swedish" },
  { code: "ta", displayName: "Tamil" },
  { code: "te", displayName: "Telugu" },
  { code: "th", displayName: "Thai" },
  { code: "tr", displayName: "Turkish" },
  { code: "uk", displayName: "Ukrainian" },
  { code: "ur", displayName: "Urdu" },
  { code: "uz", displayName: "Uzbek" },
  { code: "vi", displayName: "Vietnamese" },
  { code: "cy", displayName: "Welsh" },
];
