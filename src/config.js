/**
 * Application Configuration
 * 
 * API_BASE: The backend API base URL
 * - Uses environment variable VITE_API_BASE if set
 * - Falls back to localhost:8000 for development
 * 
 * For production, set VITE_API_BASE in .env or build environment:
 *   VITE_API_BASE=https://api.yourserver.com
 */
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

