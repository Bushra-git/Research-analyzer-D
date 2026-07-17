import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import axios from "axios";
import VenueRecommenderEnhanced from "./VenueRecommenderEnhanced";

jest.mock("axios");

function setup({ paperText = "", paperScore = 5.0, paperTopic = "topic" } = {}) {
  return render(
    <VenueRecommenderEnhanced
      paperText={paperText}
      paperScore={paperScore}
      paperTopic={paperTopic}
    />
  );
}

describe("VenueRecommenderEnhanced", () => {
  beforeEach(() => {
    axios.post.mockReset();
  });

  test("shows error when paperText is empty", async () => {
    setup({ paperText: "" });

    fireEvent.click(screen.getByRole("button", { name: /get recommendations/i }));

    expect(
      await screen.findByText(/please upload and analyze a research paper first/i)
    ).toBeInTheDocument();
  });

  test("shows backend error when API call fails", async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { error: "Venue service down" } },
    });

    setup({ paperText: "Some paper text that is definitely long enough." });

    fireEvent.click(screen.getByRole("button", { name: /get recommendations/i }));

    expect(await screen.findByText(/venue service down/i)).toBeInTheDocument();
  });

  test("renders venues when API returns results", async () => {
    axios.post.mockResolvedValueOnce({
      data: {
        paper_domain: "Computer Science & AI",
        matches_found: 1,
        total_venues_evaluated: 1,
        paper_quality: 8.0,
        venues: [
          {
            name: "Journal X",
            match_score: 88,
            type: "journal",
            reason: "mock reason",
            publisher: "Pub",
            active_status: true,
            coverage_year_range: "2010-2020",
            open_access: true,
            medline_coverage: true,
            language: "English",
            matched_asjc_subjects: ["CS.AI"],
            sourcerecord_id: "ABC123",
            is_new_jan_2026: false,
          },
        ],
      },
    });

    setup({ paperText: "Some paper text that is definitely long enough." });

    fireEvent.click(screen.getByRole("button", { name: /get recommendations/i }));

    expect(await screen.findByText(/Journal X/i)).toBeInTheDocument();
    expect(await screen.findByText(/Why recommended:/i)).toBeInTheDocument();
    expect(await screen.findByText(/mock reason/i)).toBeInTheDocument();
  });
});

