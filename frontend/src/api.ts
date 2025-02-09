import {
  CourseProps,
  CourseAPIModelProps,
  UserProps,
  ConversationSession,
  ConversationMessage,
  CourseConfiguration,
  CourseStudentEngagement,
  Timeframe,
  MaterialType,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_REACT_APP_API_URL;
let accessToken: string | null = null;

export const setAccessToken = (token: string) => {
  accessToken = token;
};

export const getAccessToken = () => {
  return accessToken;
};

export const isAccessTokenSet = () => {
  return accessToken !== null;
};

export const fetchCoursesAPI = async (): Promise<CourseProps[]> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(`${API_BASE_URL}/ui/general/user/courses`, {
    headers: {
      Authorization: accessToken,
    },
  });
  const data = await response.json();
  const courses = [
    ...data.availableCoursesAsStudent.map((course: CourseAPIModelProps) => ({
      ...course,
      userCourseRole: "STUDENT",
      isAvailable: true,
    })),
    ...data.availableCoursesAsInstructor.map((course: CourseAPIModelProps) => ({
      ...course,
      userCourseRole: "INSTRUCTOR",
      isAvailable: true,
    })),
    ...data.unavailableCoursesAsStudent.map((course: CourseAPIModelProps) => ({
      ...course,
      userCourseRole: "STUDENT",
      isAvailable: false,
    })),
  ];

  return courses;
};

export const fetchUserInfoAPI = async (): Promise<UserProps> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(`${API_BASE_URL}/ui/general/user`, {
    headers: {
      Authorization: accessToken,
    },
  });
  const data = await response.json();
  return data;
};

export const sendMessageAPI = async (
  course: string,
  message: string,
  conversationId?: string
): Promise<{ conversation_id: string; messages: ConversationMessage[] }> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(`${API_BASE_URL}/ui/student/send-message`, {
    method: "POST",
    headers: {
      Authorization: accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ course, message, conversation_id: conversationId }),
  });
  return response.json();
};

export const getPastSessionsForCourseAPI = async (
  course: string
): Promise<ConversationSession[]> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/student/sessions?course=${course}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const restorePastSessionAPI = async (
  conversation: string
): Promise<{ conversation_id: string; messages: ConversationMessage[] }> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/student/session?conversation=${conversation}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const getTopQuestionsByPeriodAPI = async (
  course: string,
  num: number,
  period: Timeframe
): Promise<string[]> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/instructor/analytics/top-questions?course=${course}&num=${num}&period=${period}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const getTopMaterialsByPeriodAPI = async (
  course: string,
  num: number,
  period: Timeframe
): Promise<MaterialType[]> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/instructor/analytics/top-materials?course=${course}&num=${num}&period=${period}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const getCourseStudentEngagementAPI = async (
  course: string,
  period: Timeframe
): Promise<CourseStudentEngagement> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/instructor/analytics/engagement?course=${course}&period=${period}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const getCourseConfigurationAPI = async (
  course: string
): Promise<CourseConfiguration> => {
  if (!accessToken) throw new Error("Access token is not set");
  const response = await fetch(
    `${API_BASE_URL}/ui/instructor/config?course=${course}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

export const updateCourseConfigurationAPI = async (
  course: string,
  configuration: CourseConfiguration
): Promise<void> => {
  if (!accessToken) throw new Error("Access token is not set");
  await fetch(`${API_BASE_URL}/ui/instructor/config`, {
    method: "PUT",
    headers: {
      Authorization: accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      course,
      ...configuration,
    }),
  });
};
