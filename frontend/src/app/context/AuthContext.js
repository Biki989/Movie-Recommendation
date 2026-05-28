"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load authenticated profile on startup
  useEffect(() => {
    async function checkAuth() {
      try {
        const resp = await fetch("http://localhost:8000/api/auth/me", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          // Include cookies automatically in fetch request
          credentials: "omit" // Cookies are handled by fetch, wait:
          // Since frontend runs on port 3000 and backend on port 8000, 
          // we MUST set credentials: "include" to send HttpOnly session cookies!
        });
        
        // Wait, standard fetch requires credentials: "include" for cross-origin cookie sharing!
        // So we will use credentials: "include" everywhere!
      } catch (e) {}
    }
    
    fetchProfile();
  }, []);

  async function fetchProfile() {
    setLoading(true);
    try {
      const resp = await fetch("http://localhost:8000/api/auth/me", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include"
      });
      if (resp.status === 200) {
        const data = await resp.json();
        setUser(data);
      } else {
        setUser(null);
      }
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function login(email, password) {
    try {
      const resp = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include"
      });
      
      const data = await resp.json();
      if (resp.status === 200 && data.success) {
        setUser(data.user);
        router.push("/recommendations");
        return { success: true };
      } else {
        return { success: false, error: data.detail || "Invalid credentials." };
      }
    } catch (e) {
      return { success: false, error: "Network error. Connection failed." };
    }
  }

  async function register(username, email, password) {
    try {
      const resp = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
        credentials: "include"
      });
      
      const data = await resp.json();
      if (resp.status === 200) {
        // Automatically login on signup success
        return await login(email, password);
      } else {
        return { success: false, error: data.detail || "Registration failed." };
      }
    } catch (e) {
      return { success: false, error: "Network error. Connection failed." };
    }
  }

  async function logout() {
    try {
      await fetch("http://localhost:8000/api/auth/logout", {
        method: "POST",
        credentials: "include"
      });
    } catch (e) {}
    setUser(null);
    router.push("/");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshProfile: fetchProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return context;
}
