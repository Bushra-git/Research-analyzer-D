import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import axios from "axios";
import App from "./App";

jest.mock("axios");

function createFile(name = "paper.pdf", type = "application/pdf") {
  const file = new File([new ArrayBuffer(16)], name, { type });
  return file;
}

describe("App upload flow", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    axios.post.mockReset();
    axios.get.mockReset();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test("shows error when no file is selected", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /analyze paper/i }));
    expect(
      await screen.findByText(/please select a file to analyze/i)
    ).toBeInTheDocument();
  });

  test("shows error when analysis API call fails", async () => {
    axios.post.mockRejectedValueOnce(new Error("network"));

    render(<App />);

    const input = screen.getByLabelText(/upload research paper/i, {
      selector: "input[type='file']",
    });

    fireEvent.change(input, { target: { files: [createFile()] } });
    fireEvent.click(screen.getByRole("button", { name: /analyze paper/i }));

    expect(
      await screen.findByText(/failed to analyze paper/i)
    ).toBeInTheDocument();
  });

  test("successful upload renders Overall Score", async () => {
    axios.post.mockResolvedValueOnce({
      data: { job_id: "abc" },
    });

    axios.get.mockResolvedValueOnce({
      data: {
        status: "finished",
        result: {
          score: 9.0,
          features: { word_count: 1000, sentence_count: 10, avg_word_length: 5.0 },
          summary: "summary",
          recommendations: [{ title: "t", description: "d" }],
          similar_papers: [],
          domain_stats: {
            domain: "Computer Science & AI",
            confidence: 55,
            total_venues: 10,
            matching_venues: 3,
            oa_count: 1,
            medline_count: 1,
            active_count: 2,
            publishers_count: 2,
          },
        },
      },
    });

    render(<App />);

    const input = screen.getByLabelText(/upload research paper/i, {
      selector: "input[type='file']",
    });

    fireEvent.change(input, { target: { files: [createFile()] } });
    fireEvent.click(screen.getByRole("button", { name: /analyze paper/i }));

    // flush poll timeout chain
    await waitFor(() => {
      expect(screen.getByText(/overall score/i)).toBeInTheDocument();
    });

    // Ensure timer-based polling doesn't stall
    jest.runOnlyPendingTimers();

    await waitFor(() => {
      expect(screen.getByText("9")).toBeInTheDocument();
    });
  });
});

