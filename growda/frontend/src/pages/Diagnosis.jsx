import React, { useRef, useState } from "react";
import apiService from "../services/api";
import Loader from "../components/Loader";
import Toast from "../components/Toast";

export default function Diagnosis() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const inputRef = useRef();
  const [submitted, setSubmitted] = useState(false);

  const handleFile = (ev) => {
    setFile(ev.target.files[0] || null);
    setResult(null);
    setSubmitted(false);
  };

  const submit = async () => {
    if (!file) { setToast({ message: "Please upload an X-ray image.", type: "error" }); return;}
    setLoading(true);
    setSubmitted(true);
    try {
      setResult(await apiService.predictImage(file));
    } catch {
      setToast({ message: "Prediction failed. Try again.", type: "error" });
      setResult(null);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto pt-36 px-4 pb-24 fadein font-sans">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <h2 className="text-4xl sm:text-5xl font-extrabold mb-2 tracking-tight text-brown-700 dark:text-brown-50 font-sans">AI Pneumonia Diagnosis</h2>
      <p className="text-lg text-brown-800 dark:text-brown-100 mb-7 font-sans">Upload a chest X-ray. Results powered by Growda AI.</p>
      <div className="bg-brown-50 dark:bg-brown-800 p-8 rounded-xl mb-10 fadein">
        <label className="block text-lg font-semibold text-brown-900 dark:text-brown-100 mb-2 font-sans">X-ray Upload</label>
        <input type="file" accept="image/*" ref={inputRef} onChange={handleFile} />
        <button className="btn-cta" onClick={()=>inputRef.current.click()}>
          {file ? 'Change Image' : 'Select X-ray Image'}
        </button>
        {file && (<span className="ml-4 text-brown-700 dark:text-brown-100 font-semibold">{file.name}</span>)}
        {file && (
          <div className="mt-8 mb-4">
            <img src={URL.createObjectURL(file)} alt="X-ray preview" className="max-h-72 rounded-xl border border-brown-200 dark:border-brown-700"/>
          </div>
        )}
        <button
          onClick={submit}
          disabled={loading || !file}
          className="btn-cta w-full mt-2 mb-1"
        >Analyze X-ray</button>
        {loading && <Loader label="Analyzing X-ray..." />}
        {result && (
          <div className="mt-7 bg-brown-100 dark:bg-brown-900 rounded-xl p-6 fadein">
            <div className="mb-2 text-lg font-bold text-brown-900 dark:text-brown-100">Prediction: {result.prediction}</div>
            <div className="mb-2 text-sm text-brown-800 dark:text-brown-100">Confidence: <span className="font-mono text-base font-bold text-brown-700 dark:text-brown-50">{(result.confidence*100).toFixed(1)}%</span></div>
            <div className="mb-1 text-sm font-sans">Severity: <span className={`px-2 py-1 rounded bg-brown-200 dark:bg-brown-800 text-brown-800 dark:text-brown-50 font-bold ml-2`}>{result.severity_level}</span></div>
            <div className="text-xs text-brown-400 mt-5">This result is for reference only. Not a medical diagnosis.</div>
          </div>
        )}
        {submitted && !result && !loading && (
          <div className="text-center text-brown-500 mt-3">There was a problem analyzing your image.<br/>Please check your X-ray and try again.</div>
        )}
      </div>
    </div>
  );
}
