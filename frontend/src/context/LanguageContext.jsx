import { createContext, useEffect, useMemo, useState } from "react";

import {
  DEFAULT_LANGUAGE,
  LANGUAGE_TO_LOCALE,
  SUPPORTED_LANGUAGES,
  translate,
} from "../constants/i18n";
import { LANGUAGE_STORAGE_KEY } from "../constants/storage";

export const LanguageContext = createContext(null);

function getStoredLanguage() {
  try {
    const value = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (!value || !SUPPORTED_LANGUAGES.includes(value)) {
      return DEFAULT_LANGUAGE;
    }
    return value;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

function setStoredLanguage(language) {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    // no-op: keep runtime state even when localStorage is unavailable
  }
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(getStoredLanguage);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  function setLanguage(nextLanguage) {
    if (!SUPPORTED_LANGUAGES.includes(nextLanguage)) {
      return;
    }

    setLanguageState(nextLanguage);
    setStoredLanguage(nextLanguage);
  }

  const value = useMemo(
    () => ({
      language,
      locale: LANGUAGE_TO_LOCALE[language] || LANGUAGE_TO_LOCALE[DEFAULT_LANGUAGE],
      setLanguage,
      t: (key, params) => translate(language, key, params),
    }),
    [language],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}
