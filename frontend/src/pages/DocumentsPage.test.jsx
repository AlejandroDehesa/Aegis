import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { DocumentsPage } from "./DocumentsPage";
import { renderWithProviders } from "../test/testUtils";

const mockListDocuments = vi.fn();

vi.mock("../api/documentsApi", () => ({
  listDocuments: (...args) => mockListDocuments(...args),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
}));

describe("DocumentsPage", () => {
  test("renders upload section and document list", async () => {
    mockListDocuments.mockResolvedValueOnce([
      {
        id: "doc-1",
        title: "Architecture Notes",
        source_type: "text",
        chunk_count: 4,
        content_preview: "FastAPI architecture summary",
        created_at: "2026-05-16T20:00:00Z",
      },
    ]);

    renderWithProviders(<DocumentsPage />);

    expect(await screen.findByText("Contexto documental para tareas asistidas por recuperacion")).toBeInTheDocument();
    expect(screen.getByText("Architecture Notes")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Subir documento" })).toBeInTheDocument();
  });
});
