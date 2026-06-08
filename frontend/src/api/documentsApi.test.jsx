import { deleteDocument, listDocuments, uploadDocument } from "./documentsApi";

const httpMocks = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("./http", () => httpMocks);

describe("documentsApi", () => {
  beforeEach(() => {
    httpMocks.apiRequest.mockReset();
    httpMocks.apiRequest.mockResolvedValue({});
  });

  test("listDocuments sends pagination params", async () => {
    await listDocuments({ limit: 50, offset: 20 });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/documents?limit=50&offset=20");
  });

  test("uploadDocument sends multipart form data", async () => {
    await uploadDocument({
      title: "Architecture",
      content: "FastAPI notes",
      file: null,
    });

    expect(httpMocks.apiRequest).toHaveBeenCalledTimes(1);
    const [path, options] = httpMocks.apiRequest.mock.calls[0];
    expect(path).toBe("/documents");
    expect(options.method).toBe("POST");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("title")).toBe("Architecture");
    expect(options.body.get("content")).toBe("FastAPI notes");
  });

  test("deleteDocument calls delete endpoint", async () => {
    await deleteDocument("doc-1");
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/documents/doc-1", {
      method: "DELETE",
    });
  });
});
