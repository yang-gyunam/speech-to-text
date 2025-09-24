import { Document, Packer, Paragraph, TextRun } from 'docx';
import jsPDF from 'jspdf';
import { invoke } from '@tauri-apps/api/core';
import type { TranscriptionResult } from '../types';

export type ExportFormat = 'txt' | 'docx' | 'pdf';

export interface ExportOptions {
  includeMetadata?: boolean;
  fontSize?: number;
  fontFamily?: string;
  pageMargins?: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
}

export class ExportManager {
  /**
   * Export transcription result to specified format
   */
  static async exportToFile(
    result: TranscriptionResult,
    text: string,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<string> {
    const {
      includeMetadata = true,
      fontSize = 12,
      fontFamily = 'Arial',
      pageMargins = { top: 20, bottom: 20, left: 20, right: 20 }
    } = options;

    const filename = this.generateFilename(result.originalFile.name, format);
    
    try {
      switch (format) {
        case 'txt':
          return await this.exportToTxt(result, text, filename, includeMetadata);
        case 'docx':
          return await this.exportToDocx(result, text, filename, includeMetadata, fontSize, fontFamily);
        case 'pdf':
          return await this.exportToPdf(result, text, filename, includeMetadata, fontSize, fontFamily, pageMargins);
        default:
          throw new Error(`Unsupported export format: ${format}`);
      }
    } catch (error) {
      console.error(`Failed to export to ${format}:`, error);
      throw new Error(`Failed to export to ${format}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Copy text to clipboard
   */
  static async copyToClipboard(text: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      throw new Error('Failed to copy to clipboard');
    }
  }

  /**
   * Share file using system sharing
   */
  static async shareFile(filePath: string): Promise<void> {
    try {
      // Use Tauri's system integration to reveal file in explorer/finder
      await invoke('reveal_file_in_explorer', { filePath });
    } catch (error) {
      console.error('Failed to share file:', error);
      throw new Error('Failed to share file');
    }
  }

  /**
   * Open file with default application
   */
  static async openFile(filePath: string): Promise<void> {
    try {
      await invoke('open_file_with_default_app', { filePath });
    } catch (error) {
      console.error('Failed to open file:', error);
      throw new Error('Failed to open file');
    }
  }

  /**
   * Export to plain text format
   */
  private static async exportToTxt(
    result: TranscriptionResult,
    text: string,
    filename: string,
    includeMetadata: boolean
  ): Promise<string> {
    let content = '';

    if (includeMetadata) {
      content += this.generateMetadataHeader(result);
      content += '\n' + '='.repeat(50) + '\n\n';
    }

    content += text;

    // Use Tauri command to save file
    const outputPath = await this.saveFileWithDialog(filename, content);
    return outputPath;
  }

  /**
   * Export to DOCX format
   */
  private static async exportToDocx(
    result: TranscriptionResult,
    text: string,
    filename: string,
    includeMetadata: boolean,
    fontSize: number,
    fontFamily: string
  ): Promise<string> {
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          // Add metadata if requested
          ...(includeMetadata ? this.createDocxMetadata(result, fontSize, fontFamily) : []),
          
          // Add separator if metadata is included
          ...(includeMetadata ? [
            new Paragraph({
              children: [new TextRun({ text: '', break: 2 })]
            })
          ] : []),

          // Add main content
          ...this.createDocxContent(text, fontSize, fontFamily)
        ]
      }]
    });

    // Generate buffer
    const buffer = await Packer.toBuffer(doc);
    
    // Convert to base64 for Tauri
    const base64 = this.arrayBufferToBase64(buffer);
    
    // Use Tauri command to save file
    const outputPath = await this.saveFileWithDialog(filename, base64, true);
    return outputPath;
  }

  /**
   * Export to PDF format
   */
  private static async exportToPdf(
    result: TranscriptionResult,
    text: string,
    filename: string,
    includeMetadata: boolean,
    fontSize: number,
    fontFamily: string,
    margins: { top: number; bottom: number; left: number; right: number }
  ): Promise<string> {
    const pdf = new jsPDF();
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    
    let yPosition = margins.top;
    const lineHeight = fontSize * 1.2;
    const maxWidth = pageWidth - margins.left - margins.right;

    // Set font
    pdf.setFont(fontFamily.toLowerCase());
    pdf.setFontSize(fontSize);

    // Add metadata if requested
    if (includeMetadata) {
      const metadataLines = this.generateMetadataHeader(result).split('\n');
      
      pdf.setFontSize(fontSize + 2);
      pdf.text('Transcription Details', margins.left, yPosition);
      yPosition += lineHeight * 1.5;
      
      pdf.setFontSize(fontSize - 1);
      for (const line of metadataLines) {
        if (yPosition > pageHeight - margins.bottom) {
          pdf.addPage();
          yPosition = margins.top;
        }
        pdf.text(line, margins.left, yPosition);
        yPosition += lineHeight * 0.8;
      }
      
      yPosition += lineHeight;
      
      // Add separator
      pdf.line(margins.left, yPosition, pageWidth - margins.right, yPosition);
      yPosition += lineHeight * 1.5;
    }

    // Add main content
    pdf.setFontSize(fontSize);
    const textLines = pdf.splitTextToSize(text, maxWidth);
    
    for (const line of textLines) {
      if (yPosition > pageHeight - margins.bottom) {
        pdf.addPage();
        yPosition = margins.top;
      }
      pdf.text(line, margins.left, yPosition);
      yPosition += lineHeight;
    }

    // Convert to base64
    const pdfBase64 = pdf.output('datauristring').split(',')[1];
    
    // Use Tauri command to save file
    const outputPath = await this.saveFileWithDialog(filename, pdfBase64, true);
    return outputPath;
  }

  /**
   * Generate filename with proper extension
   */
  private static generateFilename(originalName: string, format: ExportFormat): string {
    const baseName = originalName.replace(/\.[^/.]+$/, '');
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    return `${baseName}_transcription_${timestamp}.${format}`;
  }

  /**
   * Generate metadata header text
   */
  private static generateMetadataHeader(result: TranscriptionResult): string {
    const metadata = result.metadata;
    const file = result.originalFile;
    
    return [
      `File: ${file.name}`,
      `Size: ${this.formatFileSize(file.size)}`,
      `Format: ${file.format.toUpperCase()}`,
      `Duration: ${this.formatDuration(file.duration || 0)}`,
      '',
      `Language: ${metadata.language}`,
      `Model: ${metadata.modelSize}`,
      `Processing Time: ${this.formatDuration(result.processingTime)}`,
      `Confidence: ${result.confidence ? Math.round(result.confidence) + '%' : 'N/A'}`,
      `Timestamp: ${new Date(metadata.timestamp).toLocaleString()}`,
      '',
      `Audio Properties:`,
      `  Sample Rate: ${metadata.audioInfo.sampleRate} Hz`,
      `  Channels: ${metadata.audioInfo.channels}`,
      `  Duration: ${this.formatDuration(metadata.audioInfo.duration)}`
    ].join('\n');
  }

  /**
   * Create DOCX metadata paragraphs
   */
  private static createDocxMetadata(result: TranscriptionResult, fontSize: number, fontFamily: string): Paragraph[] {
    const metadataText = this.generateMetadataHeader(result);
    const lines = metadataText.split('\n');
    
    return [
      new Paragraph({
        children: [
          new TextRun({
            text: 'Transcription Details',
            bold: true,
            size: (fontSize + 4) * 2, // DOCX uses half-points
            font: fontFamily
          })
        ]
      }),
      new Paragraph({ children: [new TextRun({ text: '' })] }), // Empty line
      ...lines.map(line => 
        new Paragraph({
          children: [
            new TextRun({
              text: line,
              size: (fontSize - 1) * 2,
              font: fontFamily
            })
          ]
        })
      )
    ];
  }

  /**
   * Create DOCX content paragraphs
   */
  private static createDocxContent(text: string, fontSize: number, fontFamily: string): Paragraph[] {
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    
    return paragraphs.map(paragraph => 
      new Paragraph({
        children: [
          new TextRun({
            text: paragraph.trim(),
            size: fontSize * 2, // DOCX uses half-points
            font: fontFamily
          })
        ]
      })
    );
  }

  /**
   * Convert ArrayBuffer to base64
   */
  private static arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Save file using Tauri dialog
   */
  private static async saveFileWithDialog(filename: string, content: string, isBase64: boolean = false): Promise<string> {
    try {
      if (isBase64) {
        return await invoke('save_binary_file', { 
          filename, 
          content,
          isBase64: true
        });
      } else {
        return await invoke('save_text_file', { 
          content, 
          filePath: filename 
        });
      }
    } catch (error) {
      throw new Error(`Failed to save file: ${error}`);
    }
  }

  /**
   * Format file size in human readable format
   */
  private static formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Format duration in MM:SS format
   */
  private static formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
}