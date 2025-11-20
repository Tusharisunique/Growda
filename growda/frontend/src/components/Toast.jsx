import React from "react";

export default function Toast({ message, type, onClose }) {
  const bg = type === "error" ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700";
  return (
    <div className={`fixed bottom-8 right-8 rounded-xl shadow-lg max-w-sm px-6 py-4 border z-50 ${bg}`}>
      <div className="flex justify-between items-center">
        <span>{message}</span>
        <button onClick={onClose} className="ml-4 font-bold">✕</button>
      </div>
    </div>
  )
}
