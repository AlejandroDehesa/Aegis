import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();

function read(relativePath) {
  const absolutePath = path.join(ROOT, relativePath);
  return fs.readFileSync(absolutePath, "utf8");
}

function expectIncludes(content, expected, fileLabel) {
  if (!content.includes(expected)) {
    throw new Error(`Missing "${expected}" in ${fileLabel}`);
  }
}

function run() {
  const authPage = read("src/pages/AuthPage.jsx");
  const tasksPage = read("src/pages/TasksPage.jsx");
  const taskDetailPage = read("src/pages/TaskDetailPage.jsx");
  const appRouter = read("src/router/AppRouter.jsx");
  const appLayout = read("src/components/AppLayout.jsx");
  const languageContext = read("src/context/LanguageContext.jsx");

  expectIncludes(authPage, "LanguageSwitcher", "AuthPage.jsx");
  expectIncludes(authPage, "handleSubmit", "AuthPage.jsx");

  expectIncludes(tasksPage, "common.applyFilters", "TasksPage.jsx");
  expectIncludes(tasksPage, "createTask(", "TasksPage.jsx");
  expectIncludes(tasksPage, "executeTask(", "TasksPage.jsx");

  expectIncludes(taskDetailPage, "submitTaskFeedback", "TaskDetailPage.jsx");
  expectIncludes(taskDetailPage, "taskDetail.saveEvaluation", "TaskDetailPage.jsx");
  expectIncludes(taskDetailPage, "TaskTraceList", "TaskDetailPage.jsx");

  expectIncludes(appRouter, 'path="tasks"', "AppRouter.jsx");
  expectIncludes(appRouter, 'path="tasks/:taskId"', "AppRouter.jsx");
  expectIncludes(appRouter, 'path="insights"', "AppRouter.jsx");

  expectIncludes(appLayout, "LanguageSwitcher", "AppLayout.jsx");
  expectIncludes(languageContext, "SUPPORTED_LANGUAGES", "LanguageContext.jsx");

  console.log("Frontend smoke checks passed.");
}

run();
