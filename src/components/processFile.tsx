"use client";

import React, {
  useState,
  ChangeEvent,
  FormEvent,
  DragEvent,
} from "react";
import { Upload, ArrowRight } from "lucide-react";

type ProcessingStatus = "idle" | "processing" | "success" | "error";

export default function UploadSection() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [summaryId, setSummaryId] = useState<string | null>(null);

  const MAX_FILE_SIZE = 500 * 1024 * 1024;
  const GET_UPLOAD_URL_ENDPOINT = process.env.NEXT_PUBLIC_GET_UPLOAD_URL_ENDPOINT || "";
  const START_PROCESSING_ENDPOINT = process.env.NEXT_PUBLIC_START_PROCESSING_ENDPOINT || "";

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
        setErrorMessage("O arquivo excede o tamanho máximo de 500MB.");
        setFile(null);
      }
    } else {
      setErrorMessage("Por favor, selecione um arquivo MP3 ou MP4.");
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

    try {
      const getUrlResponse = await fetch(GET_UPLOAD_URL_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fileName: file.name,
          fileType: file.type,
        }),
      });

      if (!getUrlResponse.ok) {
        throw new Error("Erro ao obter a URL de upload.");
      }

      const { uploadURL, summaryId } = await getUrlResponse.json();
      setSummaryId(summaryId);

      const uploadResponse = await fetch(uploadURL, {
        method: "PUT",
        headers: {
          "Content-Type": file.type,
        },
        body: file,
      });

      if (!uploadResponse.ok) {
        throw new Error("Erro ao fazer upload para o S3.");
      }

      const startProcessingResponse = await fetch(START_PROCESSING_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          summaryId: summaryId,
        }),
      });

      if (!startProcessingResponse.ok) {
        throw new Error("Erro ao iniciar o processamento.");
      }

      setStatus("success");
    } catch (error: any) {
      console.error(error);
      setErrorMessage(
        error.message || "Ocorreu um erro ao processar o arquivo."
      );
      setStatus("error");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div id="uploadSection" className="bg-gray-50 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Ready to Start?
          </h2>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Upload your files and let AI do their magic.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20">
          <form onSubmit={handleSubmit}>
            <div
              className={`relative rounded-lg border-2 border-dashed p-12 text-center 
                ${
                  dragActive
                    ? "border-gray-500 bg-gray-100"
                    : "border-gray-300"
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
                    Enviar um arquivo
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
                <span className="text-gray-500">ou arraste e solte</span>
              </div>

              <p className="text-xs leading-5 text-gray-500 mt-2">
                MP3 ou MP4 até 500MB
              </p>

              {file && (
                <p className="mt-2 text-sm text-gray-500">
                  <strong>Selecionado:</strong> {file.name}
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
                className={`inline-flex items-center rounded-full bg-blue-500 px-8 py-3 text-white font-semibold 
                  hover:bg-blue-600 transition ${
                    isProcessing ? "opacity-50 cursor-not-allowed" : ""
                  }`}
              >
                {isProcessing ? (
                  <>
                    <span>Processando...</span>
                    <div className="ml-2 w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  </>
                ) : (
                  <>
                    <span>Processar Arquivo</span>
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {status === "success" && (
              <div className="mt-4 p-3 bg-green-500 text-white rounded-md text-center">
                Conteúdo gerado com sucesso! Seu ID de resumo é: {summaryId}
              </div>
            )}
            {status === "error" && (
              <div className="mt-4 p-3 bg-red-500 text-white rounded-md text-center">
                {errorMessage || "Ocorreu um erro."}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
