import { apiRequest } from "./http";

export function listAgents() {
  return apiRequest("/agents");
}
