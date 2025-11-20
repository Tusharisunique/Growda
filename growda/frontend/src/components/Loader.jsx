import React from "react";

export default function Loader({ label }) {
  return (
    <div className="flex items-center justify-center space-x-2 py-8">
      <svg className="animate-spin h-6 w-6 text-blue-500" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/><path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4zm2 5.29A7.96 7.96 0 014 12H0c0 3.04 1.14 5.82 3 7.94l3-2.65z" className="opacity-75"/></svg>
      <span className="text-blue-600 font-semibold">{label || "Loading..."}</span>
    </div>
  );
}
