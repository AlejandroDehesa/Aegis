import { apiRequest } from "./http";

export function getInsightsOverview() {
  return apiRequest("/insights/overview");
}
