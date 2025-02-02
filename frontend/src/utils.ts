import { Timeframe } from "./types";

export const timeframeToDisplay = (timeframe: Timeframe): string => {
  switch (timeframe) {
    case "WEEK":
      return "This Week";
    case "MONTH":
      return "This Month";
    case "TERM":
      return "This Year";
    default:
      return "This Week";
  }
};

export const displayToTimeframe = (display: string): Timeframe => {
  switch (display) {
    case "This Week":
      return "WEEK";
    case "This Month":
      return "MONTH";
    case "This Year":
      return "TERM";
    default:
      return "WEEK";
  }
};

export const areSetsEqual = (a: Set<string>, b: Set<string>) => {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
};
