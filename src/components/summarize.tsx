"use client";

import React from "react";
import FeatureCards from "./featureCards";
import UploadSection from "./processFile";

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
          <h1 className="text-4xl font-bold tracking-wilder text-gray-900 sm:text-6xl">
            Transform Your Class Recordings into
            <span className="text-primary"> Smart Notes</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Upload your class recordings and get instant transcriptions, 
            summaries, and study questions. Perfect for students and educators.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <button
              onClick={scrollToUploadSection}
              className="bg-blue-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-blue-700 transition"
            >
              Start Transcribing
            </button>
            <button className="border border-gray-300 text-gray-700 px-6 py-3 rounded-md font-semibold hover:bg-gray-100 transition">
              Learn More
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
