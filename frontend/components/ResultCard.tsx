"use client";

import { useState } from "react";

interface Props {
  text: string;
  html: string;
  match: number;
  path?: string;
}

const ResultCard: React.FC<Props> = ({ text, html, match, path }) => {
  const [showHTML, setShowHTML] = useState(false);

  const getTitle = () => {
    if (typeof window === "undefined") return text.slice(0, 100);

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = text;

    // Try to find a heading first
    const heading = tempDiv.querySelector("h1,h2,h3,h4,h5,h6");
    if (heading && heading.textContent) {
      return heading.textContent;
    }

    // Fallback to first sentence
    const plainText = tempDiv.textContent || "";
    const firstSentence = plainText.split(". ")[0];
    return firstSentence || text.slice(0, 100);
  };

  const title = getTitle();

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1 pr-4">
          <h3 className="text-gray-900 font-medium leading-relaxed">
            {title.length > 150 ? title.slice(0, 150) + "..." : title}
          </h3>
        </div>
        <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-sm font-medium whitespace-nowrap">
          {match}% match
        </div>
      </div>

      {path && <div className="text-sm text-gray-600 mb-3">Path: {path}</div>}

      <button
        className="text-blue-600 text-sm hover:text-blue-800 focus:outline-none flex items-center gap-1"
        onClick={() => setShowHTML(!showHTML)}
      >
        <span className="text-xs">{"<>"}</span>
        {showHTML ? "Hide HTML" : "View HTML"}
        <span className="text-xs ml-1">{showHTML ? "▲" : "▼"}</span>
      </button>

      {showHTML && (
        <div className="mt-3">
          <pre className="bg-gray-50 border border-gray-200 rounded p-3 text-xs overflow-auto max-h-48 text-gray-700 font-mono">
            {html}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ResultCard;
