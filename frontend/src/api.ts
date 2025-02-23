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
  CourseMaterial,
} from "./types";
import { getCachedData, setCachedData } from "./utils/cache";
import { RequestManager, debounce } from "./utils/request";
import { forceReAuthentication } from "./auth";
import { toast } from "react-hot-toast";

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

const handleUnauthorized = (response: Response) => {
  if (response.status === 401) {
    forceReAuthentication();
  }
  return response;
};

const handleApiError = (error: any, customMessage?: string) => {
  const message =
    customMessage || "Something went wrong. Please try again later.";
  toast.error(message);
  console.error(error);
  throw error;
};

export const fetchCoursesAPI = async (): Promise<CourseProps[]> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const cacheKey = "courses";
    const cachedData = getCachedData<CourseProps[]>(cacheKey);
    if (cachedData) return cachedData;

    const response = await fetch(`${API_BASE_URL}/ui/general/user/courses`, {
      headers: {
        Authorization: accessToken,
      },
    });

    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
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
  } catch (error) {
    handleApiError(error, "Failed to fetch courses. Please try again later.");
    throw error;
  }
};

export const fetchUserInfoAPI = async (): Promise<UserProps> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const cacheKey = "userInfo";
    const cachedData = getCachedData<UserProps>(cacheKey);
    if (cachedData) return cachedData;

    const response = await fetch(`${API_BASE_URL}/ui/general/user`, {
      headers: {
        Authorization: accessToken,
      },
    });

    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  } catch (error) {
    handleApiError(
      error,
      "Failed to fetch user information. Please try again later."
    );
    throw error;
  }
};

export const sendMessageAPI = async (
  course: string,
  message: string,
  conversationId?: string,
  language?: string
): Promise<{ conversation_id: string; messages: ConversationMessage[] }> => {
  if (!accessToken) throw new Error("Access token is not set");

  // Remove language parameter if set to english to prevent translation
  if ((language && language === "") || language === "en") {
    language = undefined;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/ui/student/send-message`, {
      method: "POST",
      headers: {
        Authorization: accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        course,
        message,
        conversation_id: conversationId,
        language,
      }),
    });

    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    handleApiError(error, "Failed to send message. Please try again.");
    throw error;
  }
};

export const getPastSessionsForCourseAPI = async (
  course: string
): Promise<ConversationSession[]> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(
      `${API_BASE_URL}/ui/student/sessions?course=${course}`,
      {
        headers: {
          Authorization: accessToken,
        },
      }
    );
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    handleApiError(error, "Failed to fetch past sessions. Please try again.");
    throw error;
  }
};

export const restorePastSessionAPI = async (
  conversation: string
): Promise<{ conversation_id: string; messages: ConversationMessage[] }> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(
      `${API_BASE_URL}/ui/student/session?conversation_id=${conversation}`,
      {
        headers: {
          Authorization: accessToken,
        },
      }
    );
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    handleApiError(error, "Failed to restore past session. Please try again.");
    throw error;
  }
};

const questionsRequestManager = new RequestManager();
export const getTopQuestionsByPeriodAPI = debounce(
  async (course: string, num: number, period: Timeframe): Promise<string[]> => {
    if (!accessToken) throw new Error("Access token is not set");

    try {
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
      handleUnauthorized(response);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      handleApiError(error, "Failed to fetch top questions. Please try again.");
      throw error;
    }
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

    try {
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
      handleUnauthorized(response);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      handleApiError(error, "Failed to fetch top materials. Please try again.");
      throw error;
    }
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

    try {
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
      handleUnauthorized(response);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      handleApiError(
        error,
        "Failed to fetch student engagement. Please try again."
      );
      throw error;
    }
  },
  300
);

export const getCourseConfigurationAPI = async (
  course: string
): Promise<CourseConfiguration> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
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
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  } catch (error) {
    handleApiError(
      error,
      "Failed to fetch course configuration. Please try again."
    );
    throw error;
  }
};

export const updateCourseConfigurationAPI = async (
  course: string,
  configuration: CourseConfiguration
): Promise<void> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(`${API_BASE_URL}/ui/instructor/config`, {
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
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    handleApiError(
      error,
      "Failed to update course configuration. Please try again."
    );
    throw error;
  }
};

export const updateUserLanguageAPI = async (
  preferredLanguage: string
): Promise<void> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(`${API_BASE_URL}/ui/general/user/language`, {
      method: "PUT",
      headers: {
        Authorization: accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        preferred_language: preferredLanguage,
      }),
    });
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    handleApiError(
      error,
      "Failed to update language preference. Please try again."
    );
    throw error;
  }
};

export const getSuggestionsAPI = async (
  course: string,
  numSuggests?: number
): Promise<string[]> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const params = new URLSearchParams({
      course: course,
      ...(numSuggests && { num_suggests: numSuggests.toString() }),
    });

    const response = await fetch(
      `${API_BASE_URL}/llm/suggestions?${params.toString()}`,
      {
        headers: {
          Authorization: accessToken,
        },
      }
    );

    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    handleApiError(error, "Failed to fetch suggestions. Please try again.");
    throw error;
  }
};

export const updateCourseContentAPI = async (
  courseId: string
): Promise<void> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(`${API_BASE_URL}/llm/content/refresh`, {
      method: "POST",
      headers: {
        Authorization: accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        course: courseId,
      }),
    });

    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error("Failed to update course content");
    }
  } catch (error) {
    handleApiError(
      error,
      "Failed to refresh course content. Please try again."
    );
    throw error;
  }
};

export const getAllCourseMaterialsAPI = async (
  course: string
): Promise<CourseMaterial[]> => {
  if (!accessToken) throw new Error("Access token is not set");

  try {
    const response = await fetch(
      `${API_BASE_URL}/ui/instructor/all-materials?course=${course}`,
      {
        headers: {
          Authorization: accessToken,
        },
      }
    );
    handleUnauthorized(response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    handleApiError(
      error,
      "Failed to fetch course materials. Please try again."
    );
    throw error;
  }
};
