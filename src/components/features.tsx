import { FileAudio, BookOpen, BrainCircuit, MessageSquare } from "lucide-react";

const features = [
  {
    name: "Audio Transcription",
    description: "Convert any class recording into accurate, searchable text",
    icon: FileAudio,
  },
  {
    name: "Smart Summaries",
    description: "Get concise summaries of key lecture points and topics",
    icon: BookOpen,
  },
  {
    name: "AI-Generated Questions",
    description: "Practice with automatically generated study questions",
    icon: BrainCircuit,
  },
  {
    name: "Discussion Points",
    description: "Identify main discussion topics and important moments",
    icon: MessageSquare,
  },
];

export const Features = () => {
  return (
    <div className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-semibold leading-7 text-primary">
            Powerful Features
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to enhance your learning
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-4">
            {features.map((feature) => (
              <div key={feature.name} className="flex flex-col items-center text-center">
                <div className="mb-6 rounded-lg bg-primary/10 p-4">
                  <feature.icon className="h-6 w-6 text-primary" aria-hidden="true" />
                </div>
                <dt className="text-xl font-semibold leading-7 text-gray-900">
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
};