import * as React from "react";
import { Toggle } from "../Common/Toggle";
import { CheckboxItem } from "../Common/CheckboxItem";
import {
  CourseConfiguration,
  CourseContentItem,
  CourseProps,
  SupportedQuestions,
  IncludedCourseContent,
  SupportedQuestionItem,
} from "../../types";
import toast from "react-hot-toast";
import {
  getCourseConfigurationAPI,
  updateCourseConfigurationAPI,
} from "../../api";
import { areSetsEqual } from "../../utils";

type CourseConfigurationSectionProps = {
  selectedCourse: CourseProps;
};

export const CourseConfigurationSection: React.FC<
  CourseConfigurationSectionProps
> = ({ selectedCourse }) => {
  const [initialConfig, setInitialConfig] =
    React.useState<CourseConfiguration | null>(null);
  const [isEnabled, setIsEnabled] = React.useState(false);
  const [selectedContent, setSelectedContent] = React.useState<
    Set<IncludedCourseContent>
  >(new Set());
  const [selectedQuestions, setSelectedQuestions] = React.useState<
    Set<SupportedQuestions>
  >(new Set());
  const [responseFormat, setResponseFormat] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);

  React.useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await getCourseConfigurationAPI(selectedCourse.id);
        setInitialConfig(config);
        setIsEnabled(config.studentAccessEnabled);
        setSelectedContent(new Set(config.selectedIncludedCourseContent));
        setSelectedQuestions(new Set(config.selectedSupportedQuestions));
        setResponseFormat(config.customResponseFormat);
      } catch (error) {
        console.error("Error fetching configuration:", error);
      }
    };
    fetchConfig();
  }, [selectedCourse]);

  const hasChanges = React.useMemo(() => {
    if (!initialConfig) return false;
    return (
      isEnabled !== initialConfig.studentAccessEnabled ||
      responseFormat !== initialConfig.customResponseFormat ||
      !areSetsEqual(
        selectedContent,
        new Set(initialConfig.selectedIncludedCourseContent)
      ) ||
      !areSetsEqual(
        selectedQuestions,
        new Set(initialConfig.selectedSupportedQuestions)
      )
    );
  }, [
    isEnabled,
    responseFormat,
    selectedContent,
    selectedQuestions,
    initialConfig,
  ]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasChanges || isSaving || !initialConfig) return;

    setIsSaving(true);
    try {
      const newConfig: CourseConfiguration = {
        studentAccessEnabled: isEnabled,
        selectedIncludedCourseContent: Array.from(selectedContent),
        selectedSupportedQuestions: Array.from(selectedQuestions),
        customResponseFormat: responseFormat,
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

  const courseContent: CourseContentItem[] = [
    { title: "Home", type: "HOME" },
    { title: "Announcements", type: "ANNOUNCEMENTS" },
    { title: "Syllabus", type: "SYLLABUS" },
    { title: "Assignments", type: "ASSIGNMENTS" },
    { title: "Modules", type: "MODULES" },
    { title: "Files", type: "FILES" },
    { title: "Quizzes", type: "QUIZZES" },
    { title: "Discussions", type: "DISCUSSIONS" },
    { title: "Pages", type: "PAGES" },
  ];

  const supportedQuestions: SupportedQuestionItem[] = [
    {
      title: "Learning Recommendations (Tips and Suggested Materials)",
      type: "RECOMMENDATIONS",
    },
    { title: "Practice Problem Generation", type: "PRACTICE_PROBLEMS" },
    { title: "Solution Review / Feedback", type: "SOLUTION_REVIEW" },
    { title: "Problem Explanation", type: "EXPLANATION" },
  ];

  return (
    <form onSubmit={handleSave}>
      <div className="mb-3 text-sm leading-normal text-slate-500 pt-3">
        <span className="font-semibold text-indigo-950">
          Enable Student Access
        </span>
        <br />
        <span>
          If toggled on, Students will be able to access the AI Study Assistant
          for this course.
        </span>
      </div>

      <Toggle
        isOn={isEnabled}
        onToggle={() => setIsEnabled(!isEnabled)}
        disabled={isSaving}
      />

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-8">
        <div className="mb-3 text-sm leading-normal text-slate-500">
          <span className="font-semibold text-indigo-950">
            Included Course Content
          </span>
          <br />
          <span>
            Select which sections of Canvas to include in the AI Study
            Assistant's knowledge base. Changes to which content is included in
            the knowledge base will take effect after a few minutes. Content
            changes made in Canvas later will automatically be reflected in the
            knowledge base within 24 hours.{" "}
          </span>
          <span className="underline">
            Only content which is visible to Students in Canvas (e.g. published)
          </span>
          <span> will be included in the knowledge base.</span>
        </div>

        <div className="flex flex-col gap-3 mt-3 max-sm:gap-2">
          {courseContent.map((item) => (
            <CheckboxItem
              key={item.type}
              title={item.title}
              checked={selectedContent.has(item.type)}
              onChange={() => {
                const newSelected = new Set(selectedContent);
                if (selectedContent.has(item.type)) {
                  newSelected.delete(item.type);
                } else {
                  newSelected.add(item.type);
                }
                setSelectedContent(newSelected);
              }}
            />
          ))}
        </div>
      </div>

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-8">
        <div className="mb-3 text-sm leading-normal text-slate-500">
          <span className="font-semibold text-indigo-950">
            Supported Questions
          </span>
          <br />
          <span>
            Select which types of questions the AI Study Assistant will be able
            to answer for students.
          </span>
        </div>

        <div className="flex flex-col gap-3 mt-3 max-sm:gap-2">
          {supportedQuestions.map((item) => (
            <CheckboxItem
              key={item.title}
              title={item.title}
              checked={selectedQuestions.has(item.type)}
              onChange={() => {
                const newSelected = new Set(selectedQuestions);
                if (selectedQuestions.has(item.type)) {
                  newSelected.delete(item.type);
                } else {
                  newSelected.add(item.type);
                }
                setSelectedQuestions(newSelected);
              }}
            />
          ))}
        </div>
      </div>

      <div className="mx-0 my-8 h-0.5 bg-stone-200" />

      <div className="mb-3 text-sm leading-normal text-slate-500">
        <span className="font-semibold text-indigo-950">
          Custom Response Format / Tone (Optional)
        </span>
        <br />
        <span>
          Provide instructions about how you would like the AI Study Assistant
          to respond (e.g. "answer casually with lots of emojis with as much
          detail as possible").
        </span>
      </div>

      <label htmlFor="responseFormat" className="sr-only">
        Response Format
      </label>
      <input
        id="responseFormat"
        type="text"
        value={responseFormat}
        onChange={(e) => setResponseFormat(e.target.value)}
        placeholder="e.g. answer casually with lots of emojis with as much detail as possible"
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
        Save Configuration
      </button>
    </form>
  );
};
