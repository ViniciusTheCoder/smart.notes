"use client";

import React from "react";
import { Mail, Github, Linkedin } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-gray-900 py-6 text-gray-400">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4">
        
        <p className="text-sm">
          &copy; 2025 Vinicius Gurski Ferraz, Powered by{" "}
          <a
            href="https://seulink-aqui.com" 
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-400"
          >
            Vinicius
          </a>
          .
        </p>

        <div className="flex items-center gap-5">
          <a
            href="mailto:seu-email@exemplo.com"
            className="hover:text-white"
            title="Email"
          >
            <Mail className="h-5 w-5" />
          </a>
          <a
            href="https://github.com/ViniciusTheCoder"
            className="hover:text-white"
            target="_blank"
            rel="noopener noreferrer"
            title="GitHub"
          >
            <Github className="h-5 w-5" />
          </a>
          <a
            href="https://www.linkedin.com/in/viniciusgferraz/"
            className="hover:text-white"
            target="_blank"
            rel="noopener noreferrer"
            title="LinkedIn"
          >
            <Linkedin className="h-5 w-5" />
          </a>
        </div>
      </div>
    </footer>
  );
}
