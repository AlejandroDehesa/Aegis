import { useContext } from "react";

import { LanguageContext } from "../context/LanguageContext";

export function useI18n() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useI18n must be used inside LanguageProvider");
  }

  return context;
}
