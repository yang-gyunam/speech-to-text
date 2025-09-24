// Auto-generated build information types
export interface BuildInfo {
  name: string;
  version: string;
  description: string;
  build: {
    timestamp: string;
    environment: string;
    target: string;
    nodeVersion: string;
    platform: string;
    arch: string;
    git: {
      commit: string;
      branch: string;
      tag: string;
    };
  };
  features: {
    audioFormats: string[];
    languages: string[];
    models: string[];
    exportFormats: string[];
  };
}

export const buildInfo: BuildInfo = {
  "name": "speech-to-text-desktop",
  "version": "0.1.0",
  "description": "Speech to Text Desktop Application built with Tauri, Svelte, and Rust",
  "build": {
    "timestamp": "2025-09-24T10:41:41.920Z",
    "environment": "development",
    "target": "development",
    "nodeVersion": "v24.5.0",
    "platform": "darwin",
    "arch": "arm64",
    "git": {
      "commit": "20dbedba8f26981cf9243f4f977b74ef211cc928",
      "branch": "main",
      "tag": "unknown"
    }
  },
  "features": {
    "audioFormats": [
      "m4a",
      "wav",
      "mp3",
      "aac",
      "flac"
    ],
    "languages": [
      "ko",
      "en"
    ],
    "models": [
      "tiny",
      "base",
      "small",
      "medium",
      "large"
    ],
    "exportFormats": [
      "txt",
      "docx",
      "pdf"
    ]
  }
};
