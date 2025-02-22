import { IntlShape } from "react-intl";
import { Timeframe } from "./types";

export const timeframeToDisplay = (
  timeframe: Timeframe,
  intl: IntlShape
): string => {
  switch (timeframe) {
    case "WEEK":
      return intl.formatMessage({ id: "analytics.timeframe.week" });
    case "MONTH":
      return intl.formatMessage({ id: "analytics.timeframe.month" });
    case "TERM":
      return intl.formatMessage({ id: "analytics.timeframe.year" });
    default:
      return intl.formatMessage({ id: "analytics.timeframe.week" });
  }
};

export const displayToTimeframe = (
  display: string,
  intl: IntlShape
): Timeframe => {
  if (display === intl.formatMessage({ id: "analytics.timeframe.week" })) {
    return "WEEK";
  }
  if (display === intl.formatMessage({ id: "analytics.timeframe.month" })) {
    return "MONTH";
  }
  if (display === intl.formatMessage({ id: "analytics.timeframe.year" })) {
    return "TERM";
  }
  return "WEEK";
};

export const areSetsEqual = (a: Set<string>, b: Set<string>) => {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
};
