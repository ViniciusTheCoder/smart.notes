"use client";

import React from "react";
import { Mic2, BookOpen, Brain, MessageSquare } from "lucide-react";

export default function FeatureCards() {
  const features = [
    {
      name: "Audio Transcription",
      description: "Convert any class recording into accurate, searchable text.",
      icon: Mic2,
    },
    {
      name: "Smart Summaries",
      description: "Get concise summaries of key lecture points and topics.",
      icon: BookOpen,
    },
    {
      name: "AI-Generated Questions",
      description: "Practice with automatically generated study questions.",
      icon: Brain,
    },
    {
      name: "Discussion Points",
      description: "Identify main discussion topics and important moments.",
      icon: MessageSquare,
    },
  ];

  return (
    <div className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-secondary font-semibold leading-7 text-primary uppercase tracking-wider">
            Powerful Features
          </h2>
          <p className="mt-4 text-3xl font-display font-bold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to enhance your learning
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-12 gap-y-16 lg:max-w-none lg:grid-cols-4">
            {features.map((feature) => (
              <div
                key={feature.name}
                className="flex flex-col items-center text-center group hover:transform hover:scale-105 transition-all duration-300"
              >
                <div className="mb-6 rounded-xl bg-primary/10 p-4 group-hover:bg-primary/20 transition-colors duration-300">
                  <feature.icon
                    className="h-6 w-6 text-primary"
                    aria-hidden="true"
                  />
                </div>
                <dt className="text-xl font-display font-semibold leading-7 text-gray-900">
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                  <p className="flex-auto font-secondary">{feature.description}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}