import * as React from "react";
import { Toggle } from "../Common/Toggle";
import { CheckboxItem } from "../Common/CheckboxItem";
import { FormattedMessage, useIntl } from "react-intl";
import {
  CourseConfiguration,
  CourseContentItem,
  CourseProps,
  SupportedQuestions,
  IncludedCourseContent,
  SupportedQuestionItem,
  IncludedCourseContentType,
  SupportedQuestionsType,
} from "../../types";
import toast from "react-hot-toast";
import {
  getCourseConfigurationAPI,
  updateCourseConfigurationAPI,
  updateCourseContentAPI,
} from "../../api";
import { ThreeDots } from "react-loader-spinner";
import { MaterialsAccordion } from "./MaterialsAccordion";

type CourseConfigurationSectionProps = {
  selectedCourse: CourseProps;
};

export const CourseConfigurationSection: React.FC<
  CourseConfigurationSectionProps
> = ({ selectedCourse }) => {
  const intl = useIntl();
  const [initialConfig, setInitialConfig] =
    React.useState<CourseConfiguration | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isEnabled, setIsEnabled] = React.useState(false);
  const [selectedContent, setSelectedContent] =
    React.useState<IncludedCourseContent>({
      HOME: false,
      ANNOUNCEMENTS: false,
      SYLLABUS: false,
      ASSIGNMENTS: false,
      MODULES: false,
      FILES: false,
      QUIZZES: false,
      DISCUSSIONS: false,
      PAGES: false,
    });
  const [selectedQuestions, setSelectedQuestions] =
    React.useState<SupportedQuestions>({
      RECOMMENDATIONS: false,
      PRACTICE_PROBLEMS: false,
      SOLUTION_REVIEW: false,
      EXPLANATION: false,
    });
  const [responseFormat, setResponseFormat] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);
  const [autoUpdateOn, setAutoUpdateOn] = React.useState(false);
  const [isUpdating, setIsUpdating] = React.useState(false);

  React.useEffect(() => {
    const fetchConfig = async () => {
      setIsLoading(true);
      try {
        const config = await getCourseConfigurationAPI(selectedCourse.id);
        setInitialConfig(config);
        setIsEnabled(config.studentAccessEnabled);
        setSelectedContent(config.selectedIncludedCourseContent);
        setSelectedQuestions(config.selectedSupportedQuestions);
        setResponseFormat(config.customResponseFormat);
        setAutoUpdateOn(config.autoUpdateOn);
      } catch (error) {
        console.error("Error fetching configuration:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchConfig();
  }, [selectedCourse]);

  const hasChanges = React.useMemo(() => {
    if (!initialConfig) return false;
    return (
      isEnabled !== initialConfig.studentAccessEnabled ||
      responseFormat !== initialConfig.customResponseFormat ||
      JSON.stringify(selectedContent) !==
        JSON.stringify(initialConfig.selectedIncludedCourseContent) ||
      JSON.stringify(selectedQuestions) !==
        JSON.stringify(initialConfig.selectedSupportedQuestions) ||
      autoUpdateOn !== initialConfig.autoUpdateOn
    );
  }, [
    isEnabled,
    responseFormat,
    selectedContent,
    selectedQuestions,
    autoUpdateOn,
    initialConfig,
  ]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasChanges || isSaving || !initialConfig) return;

    setIsSaving(true);
    try {
      const newConfig: CourseConfiguration = {
        studentAccessEnabled: isEnabled,
        selectedIncludedCourseContent: selectedContent,
        selectedSupportedQuestions: selectedQuestions,
        customResponseFormat: responseFormat,
        autoUpdateOn: autoUpdateOn,
      };
      await updateCourseConfigurationAPI(selectedCourse.id, newConfig);
      setInitialConfig(newConfig);
      toast.success("Configuration saved successfully!");
    } catch (error) {
      console.error("Error saving configuration:", error);
      toast.error("Failed to save configuration");
    } finally {
      setIsSaving(false);
    }
  };

  const handleContentChange = (type: IncludedCourseContentType) => {
    setSelectedContent((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  const handleQuestionChange = (type: SupportedQuestionsType) => {
    setSelectedQuestions((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  const handleResponseFormatChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setResponseFormat(e.target.value);
  };

  const handleUpdateContent = async () => {
    setIsUpdating(true);
    try {
      await updateCourseContentAPI(selectedCourse.id);
      toast.success("Course content updated successfully!");
    } catch (error) {
      console.error("Error updating course content:", error);
      toast.error("Failed to update course content");
    } finally {
      setIsUpdating(false);
    }
  };

  const courseContent: CourseContentItem[] = [
    { title: "Home", type: "HOME" as IncludedCourseContentType },
    {
      title: "Announcements",
      type: "ANNOUNCEMENTS" as IncludedCourseContentType,
    },
    { title: "Syllabus", type: "SYLLABUS" as IncludedCourseContentType },
    { title: "Assignments", type: "ASSIGNMENTS" as IncludedCourseContentType },
    { title: "Modules", type: "MODULES" as IncludedCourseContentType },
    { title: "Files", type: "FILES" as IncludedCourseContentType },
    { title: "Quizzes", type: "QUIZZES" as IncludedCourseContentType },
    { title: "Discussions", type: "DISCUSSIONS" as IncludedCourseContentType },
    { title: "Pages", type: "PAGES" as IncludedCourseContentType },
  ];

  const supportedQuestions: SupportedQuestionItem[] = [
    {
      title: "Learning Recommendations (Tips and Suggested Materials)",
      type: "RECOMMENDATIONS" as SupportedQuestionsType,
    },
    {
      title: "Practice Problem Generation",
      type: "PRACTICE_PROBLEMS" as SupportedQuestionsType,
    },
    {
      title: "Solution Review / Feedback",
      type: "SOLUTION_REVIEW" as SupportedQuestionsType,
    },
    {
      title: "Problem Explanation",
      type: "EXPLANATION" as SupportedQuestionsType,
    },
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <ThreeDots
          height="50"
          width="50"
          radius="9"
          color="#1e1b4b"
          ariaLabel="loading-configuration"
        />
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="h-full overflow-y-auto">
      <div className="mb-3 text-sm leading-normal text-slate-500 pt-3">
        <span className="font-semibold text-indigo-950">
          <FormattedMessage id="configuration.enableAccess" />
        </span>
        <br />
        <span>
          <FormattedMessage id="configuration.enableAccessDescription" />
        </span>
      </div>

      <Toggle
        isOn={isEnabled}
        onToggle={() => setIsEnabled(!isEnabled)}
        disabled={isSaving}
      />

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-3 text-sm leading-normal text-slate-500">
        <span className="font-semibold text-indigo-950">
          <FormattedMessage id="configuration.refreshContent" />
        </span>
        <br />
        <span>
          <FormattedMessage id="configuration.refreshContentDescription" />
        </span>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500 my-auto">
              <FormattedMessage id="configuration.autoUpdate" />
            </span>
            <Toggle
              isOn={autoUpdateOn}
              onToggle={() => setAutoUpdateOn(!autoUpdateOn)}
              disabled={isSaving}
            />
          </div>
          <div className="h-6 bg-indigo-950 mx-4" style={{ width: "2px" }} />
          <button
            type="button"
            onClick={handleUpdateContent}
            disabled={isUpdating}
            className={`px-6 py-3 text-sm font-bold text-white rounded-lg cursor-pointer ${
              !isUpdating
                ? "bg-indigo-950 hover:bg-indigo-900"
                : "bg-indigo-950 bg-opacity-40 cursor-not-allowed"
            } border-[none] w-fit`}
          >
            <FormattedMessage
              id={
                isUpdating
                  ? "configuration.updating"
                  : "configuration.updateNow"
              }
            />
          </button>
        </div>
      </div>

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-8">
        <div className="mb-3 text-sm leading-normal text-slate-500">
          <span className="font-semibold text-indigo-950">
            <FormattedMessage id="configuration.includedContent" />
          </span>
          <br />
          <span>
            <FormattedMessage id="configuration.includedContentDescription" />{" "}
            <span className="underline">
              <FormattedMessage id="configuration.visibleOnly" />
            </span>{" "}
            <FormattedMessage id="configuration.visibleOnlyEnd" />
          </span>
        </div>

        <div className="flex flex-col gap-3 mt-3 mb-4 max-sm:gap-2">
          {courseContent.map((item) => (
            <CheckboxItem
              key={item.type}
              title={item.title}
              checked={selectedContent[item.type]}
              onChange={() => handleContentChange(item.type)}
            />
          ))}
        </div>

        <MaterialsAccordion courseId={selectedCourse.id} />
      </div>

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-8">
        <div className="mb-3 text-sm leading-normal text-slate-500">
          <span className="font-semibold text-indigo-950">
            <FormattedMessage id="configuration.supportedQuestions" />
          </span>
          <br />
          <span>
            <FormattedMessage id="configuration.supportedQuestionsDescription" />
          </span>
        </div>

        <div className="flex flex-col gap-3 mt-3 max-sm:gap-2">
          {supportedQuestions.map((item) => (
            <CheckboxItem
              key={item.type}
              title={item.title}
              checked={selectedQuestions[item.type]}
              onChange={() => handleQuestionChange(item.type)}
            />
          ))}
        </div>
      </div>

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-3 text-sm leading-normal text-slate-500">
        <span className="font-semibold text-indigo-950">
          <FormattedMessage id="configuration.customFormat" />
        </span>
        <br />
        <span>
          <FormattedMessage id="configuration.customFormatDescription" />
        </span>
      </div>

      <label htmlFor="responseFormat" className="sr-only">
        <FormattedMessage id="configuration.customFormat" />
      </label>
      <input
        id="responseFormat"
        type="text"
        value={responseFormat}
        onChange={handleResponseFormatChange}
        placeholder={intl.formatMessage({
          id: "configuration.responseFormatPlaceholder",
        })}
        className="p-2.5 w-full text-sm rounded-lg border border-solid border-stone-950 border-opacity-30 text-indigo-950"
      />

      <button
        type="submit"
        disabled={!hasChanges || isSaving}
        className={`px-6 py-3 mt-8 text-sm font-bold text-white rounded-lg cursor-pointer ${
          hasChanges && !isSaving
            ? "bg-indigo-950 hover:bg-indigo-900"
            : "bg-indigo-950 bg-opacity-40 cursor-not-allowed"
        } border-[none] max-sm:w-full`}
      >
        <FormattedMessage id="configuration.saveButton" />
      </button>
    </form>
  );
};
