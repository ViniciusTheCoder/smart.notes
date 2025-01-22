"use client";

import React, {
  useState,
  ChangeEvent,
  FormEvent,
  DragEvent,
  useEffect,
  useRef,
} from "react";
import { Upload, ArrowRight } from "lucide-react";
import ReactMarkdown from "react-markdown";

type ProcessingStatus = "idle" | "processing" | "success" | "error";

export default function UploadSection() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [summaryId, setSummaryId] = useState<string | null>(null);

  const [showProgressBar, setShowProgressBar] = useState(false);
  const [summaryContent, setSummaryContent] = useState<string | null>(null);
  const timerId = useRef<number | null>(null);

  const MAX_FILE_SIZE = 500 * 1024 * 1024;
  const GET_UPLOAD_URL_ENDPOINT = process.env.NEXT_PUBLIC_GET_UPLOAD_URL_ENDPOINT || "";
  const START_PROCESSING_ENDPOINT = process.env.NEXT_PUBLIC_START_PROCESSING_ENDPOINT || "";
  const FETCH_SUMMARY_ENDPOINT = process.env.NEXT_PUBLIC_FETCH_SUMMARY_ENDPOINT || "";

  const validateAndSetFile = (selectedFile: File) => {
    const fileType = selectedFile.type;
    const fileSize = selectedFile.size;

    if (
      fileType === "audio/mpeg" ||
      fileType === "audio/mp3" ||
      fileType === "video/mp4"
    ) {
      if (fileSize <= MAX_FILE_SIZE) {
        setFile(selectedFile);
        setErrorMessage("");
        setStatus("idle");
      } else {
        setErrorMessage("This file exceeds the 500MB maximum size allowed.");
        setFile(null);
      }
    } else {
      setErrorMessage("Please select a mp3 or mp4 file.");
      setFile(null);
    }
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) return;

    setIsProcessing(true);
    setStatus("processing");
    setShowProgressBar(true);
    setSummaryContent(null);

    try {
      const getUrlResponse = await fetch(GET_UPLOAD_URL_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fileName: file.name, fileType: file.type }),
      });

      if (!getUrlResponse.ok) {
        throw new Error("Erro ao obter a URL de upload.");
      }

      const { uploadURL, summaryId } = await getUrlResponse.json();
      setSummaryId(summaryId);

      const uploadResponse = await fetch(uploadURL, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload file to s3.");
      }

      const startProcessingResponse = await fetch(START_PROCESSING_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summaryId }),
      });

      if (!startProcessingResponse.ok) {
        throw new Error("Failed to initialize processing.");
      }

      setStatus("success");

      timerId.current = window.setTimeout(() => {
        setShowProgressBar(false);
        const fetchSummary = async () => {
          if (!summaryId) return;
          try {
            const response = await fetch(FETCH_SUMMARY_ENDPOINT, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ summaryId }),
            });
            if (!response.ok) {
              throw new Error("Failed to fetch summary.");
            }
            const { content } = await response.json();
            setSummaryContent(content);
          } catch (error: unknown) {
            if (error instanceof Error) {
              setErrorMessage(error.message);
            } else {
              setErrorMessage("Failed to fetch summary.");
            }
            setStatus("error");
          }
        };
        fetchSummary();
      }, 4 * 60 * 1000);
    } catch (error: unknown) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Failed to process file.");
      }
      setStatus("error");
      setShowProgressBar(false);
    } finally {
      setIsProcessing(false);
    }
  };

  useEffect(() => {
    return () => {
      if (timerId.current) {
        clearTimeout(timerId.current);
      }
    };
  }, []);

  return (
    <div id="uploadSection" className="bg-gray-50 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Ready to Start?
          </h2>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Upload your files and let AI do their magic
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20">
          <form onSubmit={handleSubmit}>
            <div
              className={`relative rounded-lg border-2 border-dashed p-12 text-center ${
                dragActive ? "border-gray-500 bg-gray-100" : "border-gray-300"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="text-blue-600 hover:text-blue-500 font-medium">
                    Upload file
                  </span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".mp3, .mp4"
                    onChange={handleFileChange}
                    required
                  />
                </label>{" "}
                <span className="text-gray-500">or drag and drop</span>
              </div>
              <p className="text-xs leading-5 text-gray-500 mt-2">
                MP3 or MP4 - 500MB
              </p>
              {file && (
                <p className="mt-2 text-sm text-gray-500">
                  <strong>Selected:</strong> {file.name}
                </p>
              )}
            </div>

            {errorMessage && (
              <p className="mt-4 text-sm text-red-500">{errorMessage}</p>
            )}

            <div className="mt-10 flex justify-center">
              <button
                type="submit"
                disabled={isProcessing || !file}
                className={`inline-flex items-center rounded-full bg-blue-500 px-8 py-3 text-white font-semibold hover:bg-blue-600 transition ${
                  isProcessing ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                {isProcessing ? (
                  <>
                    <span>Processing...</span>
                    <div className="ml-2 w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  </>
                ) : (
                  <>
                    <span>Process File</span>
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {status === "success" && summaryContent && (
              <div className="mt-8 bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-2xl font-bold mb-4 text-black">AI Summary</h3>
                <ReactMarkdown
                  components={{
                    h1: (props) => (
                      <h1 className="text-2xl font-bold mt-4 mb-2 text-black" {...props} />
                    ),
                    h2: (props) => (
                      <h2 className="text-xl font-bold mt-3 mb-2 text-black" {...props} />
                    ),
                    h3: (props) => (
                      <h3 className="text-lg font-semibold mt-3 mb-2 text-black" {...props} />
                    ),
                    p: (props) => (
                      <p className="mb-4 leading-relaxed text-black" {...props} />
                    ),
                    ul: (props) => (
                      <ul className="list-disc list-inside mb-4" {...props} />
                    ),
                    li: (props) => <li className="mb-1 text-black" {...props} />,
                    strong: (props) => (
                      <strong className="font-semibold text-black" {...props} />
                    ),
                  }}
                >
                  {summaryContent}
                </ReactMarkdown>
              </div>
            )}

            {status === "error" && (
              <div className="mt-4 p-3 bg-red-500 text-white rounded-md text-center">
                {errorMessage || "Error :(."}
              </div>
            )}
          </form>

          {showProgressBar && (
            <div className="mt-6 flex justify-center items-center">
              <div className="w-1/2 bg-gray-200 rounded-full h-4">
                <div className="bg-blue-600 h-4 rounded-full animate-pulse w-full"></div>
              </div>
              <span className="ml-4 text-gray-700">
                Processing... Please, be patient.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
