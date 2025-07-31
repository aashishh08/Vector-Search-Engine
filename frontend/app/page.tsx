"use client";

import { useState } from "react";
import SearchForm from "../components/SearchForm";
import ResultCard from "../components/ResultCard";

interface SearchResult {
  text: string;
  html: string;
  match: number;
  path?: string;
}

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (url: string, query: string) => {
    if (!url || !query) {
      setError("Please enter both website URL and query.");
      return;
    }

    setLoading(true);
    setError("");
    setHasSearched(false);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BASE_API_URL}/search`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, query }),
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Unknown error");
      }

      const data = await response.json();

      // Process results
      const processedResults = Array.isArray(data)
        ? data.slice(0, 10).map((r) => ({
            text: r.chunk_content,
            html: r.original_html_context,
            match: r.match_percentage,
            path: r.path,
          }))
        : [];

      setResults(processedResults);
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
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Website Content Search
          </h1>
          <p className="text-gray-600">
            Search through website content with precision
          </p>
        </div>

        <SearchForm onSearch={handleSearch} loading={loading} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-8 text-blue-600 font-semibold">
            Loading...
          </div>
        )}

        {hasSearched && !loading && results.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Search Results
            </h2>
            <div className="space-y-0">
              {results.map((result, idx) => (
                <ResultCard
                  key={idx}
                  text={result.text}
                  html={result.html}
                  match={result.match}
                  path={result.path}
                />
              ))}
            </div>
          </div>
        )}

        {hasSearched && !loading && results.length === 0 && (
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
