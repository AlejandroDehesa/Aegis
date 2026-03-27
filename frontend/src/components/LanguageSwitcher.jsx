import { useI18n } from "../hooks/useI18n";

export function LanguageSwitcher({ compact = false }) {
  const { language, setLanguage, t } = useI18n();

  return (
    <div className={`language-switch ${compact ? "language-switch-compact" : ""}`}>
      <span className="language-switch-label">{t("common.language")}</span>
      <div className="language-switch-buttons">
        <button
          className={language === "es" ? "language-btn language-btn-active" : "language-btn"}
          onClick={() => setLanguage("es")}
          type="button"
        >
          {t("common.spanish")}
        </button>
        <button
          className={language === "en" ? "language-btn language-btn-active" : "language-btn"}
          onClick={() => setLanguage("en")}
          type="button"
        >
          {t("common.english")}
        </button>
      </div>
    </div>
  );
}
