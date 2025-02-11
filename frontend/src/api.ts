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
import { getCachedData, setCachedData } from "./utils/cache";
import { RequestManager, debounce } from "./utils/request";

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

  const cacheKey = "courses";
  const cachedData = getCachedData<CourseProps[]>(cacheKey);
  if (cachedData) return cachedData;

  const response = await fetch(`${API_BASE_URL}/ui/general/user/courses`, {
    headers: {
      Authorization: accessToken,
    },
  });
  const data = await response.json();

  // Create courses array maintaining original order from response
  const courses: CourseProps[] = Object.entries(data).flatMap(
    ([key, courses]) => {
      const userRole = key.includes("AsStudent") ? "STUDENT" : "INSTRUCTOR";
      const isAvailable = !key.includes("unavailable");

      return (courses as CourseAPIModelProps[]).map((course) => ({
        ...course,
        userCourseRole: userRole,
        isAvailable: isAvailable,
      }));
    }
  );

  setCachedData(cacheKey, courses);
  return courses;
};

export const fetchUserInfoAPI = async (): Promise<UserProps> => {
  if (!accessToken) throw new Error("Access token is not set");

  const cacheKey = "userInfo";
  const cachedData = getCachedData<UserProps>(cacheKey);
  if (cachedData) return cachedData;

  const response = await fetch(`${API_BASE_URL}/ui/general/user`, {
    headers: {
      Authorization: accessToken,
    },
  });
  const data = await response.json();
  setCachedData(cacheKey, data);
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
    `${API_BASE_URL}/ui/student/session?conversationId=${conversation}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  return response.json();
};

const questionsRequestManager = new RequestManager();
export const getTopQuestionsByPeriodAPI = debounce(
  async (course: string, num: number, period: Timeframe): Promise<string[]> => {
    if (!accessToken) throw new Error("Access token is not set");

    const cacheKey = `topQuestions-${course}-${num}-${period}`;
    const cachedData = getCachedData<string[]>(cacheKey);
    if (cachedData) return cachedData;

    const response = await fetch(
      `${API_BASE_URL}/ui/instructor/analytics/top-questions?course=${course}&num=${num}&period=${period}`,
      {
        headers: {
          Authorization: accessToken,
        },
        signal: questionsRequestManager.getSignal(),
      }
    );
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  },
  300
);

const materialRequestManager = new RequestManager();
export const getTopMaterialsByPeriodAPI = debounce(
  async (
    course: string,
    num: number,
    period: Timeframe
  ): Promise<MaterialType[]> => {
    if (!accessToken) throw new Error("Access token is not set");

    const cacheKey = `topMaterials-${course}-${num}-${period}`;
    const cachedData = getCachedData<MaterialType[]>(cacheKey);
    if (cachedData) return cachedData;

    const response = await fetch(
      `${API_BASE_URL}/ui/instructor/analytics/top-materials?course=${course}&num=${num}&period=${period}`,
      {
        headers: {
          Authorization: accessToken,
        },
        signal: materialRequestManager.getSignal(),
      }
    );
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  },
  300
);

const engagementRequestManager = new RequestManager();
export const getCourseStudentEngagementAPI = debounce(
  async (
    course: string,
    period: Timeframe
  ): Promise<CourseStudentEngagement> => {
    if (!accessToken) throw new Error("Access token is not set");

    const cacheKey = `engagement-${course}-${period}`;
    const cachedData = getCachedData<CourseStudentEngagement>(cacheKey);
    if (cachedData) return cachedData;

    const response = await fetch(
      `${API_BASE_URL}/ui/instructor/analytics/engagement?course=${course}&period=${period}`,
      {
        headers: {
          Authorization: accessToken,
        },
        signal: engagementRequestManager.getSignal(),
      }
    );
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  },
  300
);

export const getCourseConfigurationAPI = async (
  course: string
): Promise<CourseConfiguration> => {
  if (!accessToken) throw new Error("Access token is not set");

  const cacheKey = `config-${course}`;
  const cachedData = getCachedData<CourseConfiguration>(cacheKey);
  if (cachedData) return cachedData;

  const response = await fetch(
    `${API_BASE_URL}/ui/instructor/config?course=${course}`,
    {
      headers: {
        Authorization: accessToken,
      },
    }
  );
  const data = await response.json();
  setCachedData(cacheKey, data);
  return data;
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
