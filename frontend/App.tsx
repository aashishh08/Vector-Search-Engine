"use client"

import { useState } from "react"
import ResultCard from "./components/ResultCard"

interface ChunkResult {
  text: string
  score: number
  match: number
  path?: string
}

// Mock data to match the screenshot
const mockResults: ChunkResult[] = [
  {
    text: `<div class="et_pb_text_inner">
  <h1>Digital Robotics for your Company 2.0</h1>
  <p>Deploy automations powered by AI, Big Data, Web Crawling and Natural Language.</p>
</div>`,
    match: 95,
    path: "/home",
  },
  {
    text: `<div class="et_pb_text_inner">
  <h3>Enterprise Solutions</h3>
  <p>AI-powered automation tools for enterprise. Streamline your workflow with intelligent solutions.</p>
</div>`,
    match: 78,
    path: "/products",
  },
]

function App() {
  const [url, setUrl] = useState<string>("https://smarter.codes")
  const [query, setQuery] = useState<string>("AI")
  const [results, setResults] = useState<ChunkResult[]>(mockResults)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>("")

  const handleSearch = async () => {
    if (!url || !query) {
      setError("Please enter both website URL and query.")
      return
    }

    setLoading(true)
    setError("")

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setResults(mockResults)
    } catch (e) {
      setError("Error fetching results. See console for details.")
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Website Content Search</h1>
          <p className="text-gray-600">Search through website content with precision</p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          {/* URL Input */}
          <div className="mb-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-400">🌐</span>
              </div>
              <input
                type="text"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Search Input and Button */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-400">🔍</span>
              </div>
              <input
                type="text"
                placeholder="Search..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">{error}</div>}

        {/* Search Results */}
        {results.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Results</h2>
            <div className="space-y-0">
              {results.map((chunk, idx) => (
                <ResultCard key={idx} text={chunk.text} match={chunk.match} path={chunk.path} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
