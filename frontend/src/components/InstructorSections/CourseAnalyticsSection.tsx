import * as React from "react";
import {
  CourseAnalyticsSectionProps,
  CourseCommonQuestions,
  CourseMostReferencedMaterials,
  CourseStudentEngagement,
  Timeframe,
} from "../../types";
import { EngagementCard } from "../CourseAnalytics/EngagementCard";
import { ListStatisticCard } from "../CourseAnalytics/ListStatisticCard";
import {
  getTopQuestionsByPeriodAPI,
  getTopMaterialsByPeriodAPI,
  getCourseStudentEngagementAPI,
} from "../../api";

export const CourseAnalyticsSection: React.FC<CourseAnalyticsSectionProps> = ({
  selectedCourse,
}) => {
  const [studentEngagementData, setStudentEngagementData] =
    React.useState<CourseStudentEngagement>();
  const [mostCommonQuestionsData, setMostCommonQuestionsData] =
    React.useState<CourseCommonQuestions>();
  const [mostReferencedMaterialsData, setMostReferencedMaterialsData] =
    React.useState<CourseMostReferencedMaterials>();
  const [loading, setLoading] = React.useState(true);

  const [studentEngagementPeriod, setStudentEngagementPeriod] =
    React.useState<Timeframe>("WEEK");
  const [mostCommonQuestionsPeriod, setMostCommonQuestionsPeriod] =
    React.useState<Timeframe>("WEEK");
  const [mostReferencedMaterialsPeriod, setMostReferencedMaterialsPeriod] =
    React.useState<Timeframe>("WEEK");

  const handlePeriodChangeEngagement = async (newTimeframe: Timeframe) => {
    setLoading(true);
    const data = await getCourseStudentEngagementAPI(
      selectedCourse.id,
      newTimeframe
    );
    setStudentEngagementData(data);
    setStudentEngagementPeriod(newTimeframe);
    setLoading(false);
  };

  const handlePeriodChangeQuestions = async (newTimeframe: Timeframe) => {
    setLoading(true);
    const questions = await getTopQuestionsByPeriodAPI(
      selectedCourse.id,
      5,
      newTimeframe
    );
    setMostCommonQuestionsData({ questions });
    setMostCommonQuestionsPeriod(newTimeframe);
    setLoading(false);
  };

  const handlePeriodChangeMaterials = async (newTimeframe: Timeframe) => {
    setLoading(true);
    const materials = await getTopMaterialsByPeriodAPI(
      selectedCourse.id,
      5,
      newTimeframe
    );
    setMostReferencedMaterialsData({ materials });
    setMostReferencedMaterialsPeriod(newTimeframe);
    setLoading(false);
  };

  React.useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await handlePeriodChangeEngagement(studentEngagementPeriod);
      await handlePeriodChangeQuestions(mostCommonQuestionsPeriod);
      await handlePeriodChangeMaterials(mostReferencedMaterialsPeriod);
      setLoading(false);
    };
    fetchData();
  }, [selectedCourse]);

  return (
    <div className="flex flex-col gap-4 w-full">
      <EngagementCard
        questionsAsked={studentEngagementData?.questionsAsked ?? 0}
        studentSessions={studentEngagementData?.studentSessions ?? 0}
        studentsUsingAceIt={studentEngagementData?.uniqueStudents ?? 0}
        timeframe={studentEngagementPeriod}
        onPeriodChange={handlePeriodChangeEngagement}
        loading={loading}
      />
      <div className="flex flex-wrap gap-4 justify-center items-start ">
        <ListStatisticCard
          title="Most Common Questions"
          timeframe={mostCommonQuestionsPeriod}
          items={
            mostCommonQuestionsData?.questions.map((question) => ({
              title: question,
              link: "",
            })) ?? []
          }
          onPeriodChange={handlePeriodChangeQuestions}
          loading={loading}
        />
        <ListStatisticCard
          title="Most Referenced Materials"
          timeframe={mostReferencedMaterialsPeriod}
          items={mostReferencedMaterialsData?.materials ?? []}
          onPeriodChange={handlePeriodChangeMaterials}
          loading={loading}
        />
      </div>
    </div>
  );
};
