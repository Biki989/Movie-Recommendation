// Central configuration for backend API endpoints
export const API_BASE = 
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && 
   window.location.hostname !== "localhost" && 
   window.location.hostname !== "127.0.0.1"
    ? "/_/backend"
    : "http://localhost:8000");
