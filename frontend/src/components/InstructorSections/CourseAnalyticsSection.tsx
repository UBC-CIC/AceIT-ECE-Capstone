import * as React from "react";
import { useIntl } from "react-intl";
import {
  CourseAnalyticsSectionProps,
  CourseCommonQuestions,
  CourseMostReferencedMaterials,
  CourseStudentEngagement,
  Timeframe,
} from "../../types";
import { EngagementCard } from "./CourseAnalytics/EngagementCard";
import { ListStatisticCard } from "./CourseAnalytics/ListStatisticCard";
import {
  getTopQuestionsByPeriodAPI,
  getTopMaterialsByPeriodAPI,
  getCourseStudentEngagementAPI,
} from "../../api";

export const CourseAnalyticsSection: React.FC<CourseAnalyticsSectionProps> = ({
  selectedCourse,
}) => {
  const intl = useIntl();
  const [studentEngagementData, setStudentEngagementData] =
    React.useState<CourseStudentEngagement>();
  const [mostCommonQuestionsData, setMostCommonQuestionsData] =
    React.useState<CourseCommonQuestions>();
  const [mostReferencedMaterialsData, setMostReferencedMaterialsData] =
    React.useState<CourseMostReferencedMaterials>();

  // Separate loading states for each card
  const [engagementLoading, setEngagementLoading] = React.useState(true);
  const [questionsLoading, setQuestionsLoading] = React.useState(true);
  const [materialsLoading, setMaterialsLoading] = React.useState(true);

  const [studentEngagementPeriod, setStudentEngagementPeriod] =
    React.useState<Timeframe>("WEEK");
  const [mostCommonQuestionsPeriod, setMostCommonQuestionsPeriod] =
    React.useState<Timeframe>("WEEK");
  const [mostReferencedMaterialsPeriod, setMostReferencedMaterialsPeriod] =
    React.useState<Timeframe>("WEEK");

  const handlePeriodChangeEngagement = async (newTimeframe: Timeframe) => {
    setEngagementLoading(true);
    const data = await getCourseStudentEngagementAPI(
      selectedCourse.id,
      newTimeframe
    );
    setStudentEngagementData(data);
    setStudentEngagementPeriod(newTimeframe);
    setEngagementLoading(false);
  };

  const handlePeriodChangeQuestions = async (newTimeframe: Timeframe) => {
    setQuestionsLoading(true);
    const questions = await getTopQuestionsByPeriodAPI(
      selectedCourse.id,
      10,
      newTimeframe
    );
    setMostCommonQuestionsData({ questions });
    setMostCommonQuestionsPeriod(newTimeframe);
    setQuestionsLoading(false);
  };

  const handlePeriodChangeMaterials = async (newTimeframe: Timeframe) => {
    setMaterialsLoading(true);
    const materials = await getTopMaterialsByPeriodAPI(
      selectedCourse.id,
      10,
      newTimeframe
    );
    setMostReferencedMaterialsData({ materials });
    setMostReferencedMaterialsPeriod(newTimeframe);
    setMaterialsLoading(false);
  };

  React.useEffect(() => {
    const fetchData = async () => {
      setEngagementLoading(true);
      setQuestionsLoading(true);
      setMaterialsLoading(true);

      await Promise.all([
        handlePeriodChangeEngagement(studentEngagementPeriod),
        handlePeriodChangeQuestions(mostCommonQuestionsPeriod),
        handlePeriodChangeMaterials(mostReferencedMaterialsPeriod),
      ]);
    };
    fetchData();
  }, [selectedCourse]);

  return (
    <div className="flex flex-col gap-4 w-full h-full overflow-y-auto">
      <EngagementCard
        questionsAsked={studentEngagementData?.questionsAsked ?? 0}
        studentSessions={studentEngagementData?.studentSessions ?? 0}
        studentsUsingAceIt={studentEngagementData?.uniqueStudents ?? 0}
        timeframe={studentEngagementPeriod}
        onPeriodChange={handlePeriodChangeEngagement}
        loading={engagementLoading}
      />
      <div className="flex flex-wrap gap-4 justify-center items-start ">
        <ListStatisticCard
          title={intl.formatMessage({ id: "analytics.mostCommonQuestions" })}
          timeframe={mostCommonQuestionsPeriod}
          items={
            mostCommonQuestionsData?.questions.map((question) => ({
              title: question,
              link: "",
            })) ?? []
          }
          onPeriodChange={handlePeriodChangeQuestions}
          loading={questionsLoading}
        />
        <ListStatisticCard
          title={intl.formatMessage({
            id: "analytics.mostReferencedMaterials",
          })}
          timeframe={mostReferencedMaterialsPeriod}
          items={mostReferencedMaterialsData?.materials ?? []}
          onPeriodChange={handlePeriodChangeMaterials}
          loading={materialsLoading}
        />
      </div>
    </div>
  );
};
