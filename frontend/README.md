# Website Content Search - Frontend

This is the frontend for the Website Content Search application. It allows users to search the content of any website by URL and query, displaying the top 10 most relevant content chunks using semantic search.

## Features
- Built with Next.js (React)
- Form with Website URL and Search Query input fields
- Displays top 10 relevant HTML content chunks (up to 500 tokens each)
- Shows match percentage and section path for each result
- Integrates with a FastAPI backend for semantic search

## Prerequisites
- Node.js (v16+ recommended)
- pnpm (or npm/yarn)

## Setup & Run

1. Install dependencies:
   ```bash
   pnpm install
   # or
   npm install
   # or
   yarn install
   ```

2. Start the development server:
   ```bash
   pnpm dev
   # or
   npm run dev
   # or
   yarn dev
   ```

3. Open your browser and go to [http://localhost:3000](http://localhost:3000)

## Usage
- Enter a website URL and a search query in the form.
- Click "Search" to fetch and display the top 10 relevant content chunks from the site.
- Each result shows a snippet of HTML, a match percentage, and the section path.

## API Integration
- The frontend sends POST requests to the backend FastAPI server at `http://localhost:8000/search`.
- Make sure the backend is running and accessible at this address.
- The backend must return a list of results with the following fields:
  - `chunk_content`: The text chunk (≤500 tokens)
  - `match_percentage`: The semantic match score (0-100)
  - `path`: The section path/anchor

## Project Structure
- `app/` - Next.js app directory (main entry: `page.tsx`)
- `components/` - UI components (form, result card, etc.)
- `public/` - Static assets
- `styles/` - Tailwind and global CSS

## Customization
- To change the backend API URL, update the fetch URL in `app/page.tsx`.
- To adjust styling, edit Tailwind config or component styles.

---
For backend setup, see the `../backend/README.md` file. 