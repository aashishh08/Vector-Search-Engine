"use client";

import { useState } from "react";
import SearchForm from "../components/SearchForm";
import ResultCard from "../components/ResultCard";

interface ChunkResult {
  text: string;
  score: number;
  match: number;
  path?: string;
}

// Remove mockResults and initialize results as an empty array

export default function Home() {
  const [results, setResults] = useState<ChunkResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [hasSearched, setHasSearched] = useState<boolean>(false); // Don't show results by default

  const handleSearch = async (url: string, query: string) => {
    if (!url || !query) {
      setError("Please enter both website URL and query.");
      return;
    }

    setLoading(true);
    setError("");
    setHasSearched(false);

    try {
      const response = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, query }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Unknown error");
      }
      const data = await response.json();
      console.log("Backend response:", data); // Debug log
      // Defensive: ensure data is an array and limit to 10
      let safeResults = Array.isArray(data)
        ? data.slice(0, 10).map((r) => ({
            text: r.chunk_content,
            match: r.match_percentage,
            path: r.path,
          }))
        : [];
      // Filter out results missing required fields
      safeResults = safeResults.filter(
        (r) =>
          typeof r.text === "string" &&
          typeof r.match !== "undefined" &&
          typeof r.path === "string"
      );
      setResults(safeResults);
      setHasSearched(true);
    } catch (e: any) {
      setError(e.message || "Error fetching results. Please try again.");
      setResults([]);
      setHasSearched(true);
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Website Content Search
          </h1>
          <p className="text-gray-600">
            Search through website content with precision
          </p>
        </div>

        {/* Search Form */}
        <SearchForm onSearch={handleSearch} loading={loading} />

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Loading Spinner/Message */}
        {loading && (
          <div className="text-center py-8 text-blue-600 font-semibold">
            Loading...
          </div>
        )}

        {/* Search Results */}
        {hasSearched &&
          !loading &&
          Array.isArray(results) &&
          results.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Search Results
              </h2>
              <div className="space-y-0">
                {results.map((chunk, idx) => (
                  <ResultCard
                    key={idx}
                    text={chunk.text}
                    match={chunk.match}
                    path={chunk.path}
                  />
                ))}
              </div>
            </div>
          )}

        {/* No Results */}
        {hasSearched &&
          !loading &&
          Array.isArray(results) &&
          results.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">
                No results found. Try a different search query.
              </p>
            </div>
          )}
      </div>
    </div>
  );
}
