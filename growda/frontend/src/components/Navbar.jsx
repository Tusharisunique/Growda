import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();
  return (
    <nav className="w-full bg-white/80 border-b backdrop-blur-md drop-shadow-xl fixed z-20">
      <div className="max-w-7xl mx-auto flex items-center justify-between p-5">
        <Link to="/" className="flex items-center space-x-3 text-blue-700 font-bold tracking-tight text-2xl">
          <span className="inline-flex items-center">
            <svg width="32" height="32" fill="none" viewBox="0 0 32 32" className="mr-1">
              <rect width="32" height="32" rx="9" fill="#2563eb"/>
              <path d="M9 21c6-1 8.6-6.5 11-8.5C23 11 23 19 23 19s-2.5 2-7 2-7-0.5-7-0.5z" fill="#fff"/>
              <circle cx="16" cy="16" r="2.2" fill="#2563eb" fillOpacity=".9"/>
            </svg>
            <span>Growda AI</span>
          </span>
        </Link>
        <div className="flex space-x-10 text-lg">
          <NavLink to="/" label="Dashboard" active={location.pathname === "/"} />
          <NavLink to="/diagnosis" label="Diagnosis" active={location.pathname === "/diagnosis"} />
        </div>
      </div>
    </nav>
  );
}

function NavLink({ to, label, active }) {
  return (
    <Link
      to={to}
      className={`relative px-2 py-2 font-medium transition text-blue-900 hover:text-blue-700 ${
        active ? "text-blue-700" : ""
      }`}
    >
      {label}
      {active && <span className="absolute left-1/2 -bottom-1.5 -translate-x-1/2 w-9 h-1 rounded-full bg-blue-500 animate-pulse" />}
    </Link>
  );
}
