import "./globals.css";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";

export const metadata = {
  title: "CinematIX – AI Movie Recommendations",
  description: "Advanced AI movie recommendation system using PyTorch Neural Collaborative Filtering.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Navbar />
          <main style={{ marginTop: "100px", minHeight: "calc(100vh - 200px)", paddingBottom: "3rem" }}>
            {children}
          </main>
          
          <footer className="site-footer" style={{ borderTop: "1px solid var(--border-light)", padding: "2rem 0", background: "var(--bg-secondary)", marginTop: "4rem" }}>
            <div className="container" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <span style={{ fontWeight: 800, fontSize: "1.1rem" }}>🎬 CinematIX</span>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                  AI-powered movie recommendations using Neural Collaborative Filtering.
                </p>
              </div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-dimmed)" }}>
                Built with ❤️ using PyTorch, FastAPI, and Next.js App Router
              </span>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
