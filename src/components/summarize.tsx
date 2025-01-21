"use client";

import React from "react";
import FeatureCards from "./featureCards";
import UploadSection from "./processFile";
import { ArrowDown } from "lucide-react";

export function Summarize() {
  const scrollToUploadSection = () => {
    const target = document.getElementById("uploadSection");
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="relative overflow-hidden bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl font-sans">
            <span className="font-display block mb-2">Transform Your Class</span>
            <span className="font-display">Recordings into</span>
            <span className="text-primary font-display block mt-2"> Smart Notes</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600 font-secondary">
            Upload your class recordings and get instant transcriptions,
            summaries, and study questions. Perfect for students and educators.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <button
              onClick={scrollToUploadSection}
              className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 transition inline-flex items-center space-x-2 font-secondary"
            >
              <span>Start Transcribing</span>
              <ArrowDown />
            </button>
          </div>
        </div>
      </div>

      <section className="max-w-6xl mx-auto px-4 py-16 text-center">
        <FeatureCards />
      </section>

      <UploadSection />
    </div>
  );
}

export default Summarize;