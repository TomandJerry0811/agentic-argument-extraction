/**
 * InputPanel Component
 * Handles the three input methods: text, URL, and document upload
 */

import React, { useState, useCallback, useRef } from 'react';
import { InputMethod } from '../types/ArgumentMap';
import ArgumentCartographerAPI from '../services/api';
import './InputPanel.css';

// Props interface
interface InputPanelProps {
  onAnalyze: (
    question: string,
    inputMethod: InputMethod,
    additionalData?: { url?: string; file?: File; content?: string }
  ) => Promise<void>;
  isLoading: boolean;
}

const InputPanel: React.FC<InputPanelProps> = ({ onAnalyze, isLoading }) => {
  // State
  const [activeTab, setActiveTab] = useState<InputMethod>('text');
  const [question, setQuestion] = useState('');
  const [textContent, setTextContent] = useState('');
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle tab change
  const handleTabChange = useCallback((method: InputMethod) => {
    setActiveTab(method);
    setError(null);
  }, []);

  // Handle file selection
  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const validation = ArgumentCartographerAPI.validateFile(file);
      if (!validation.isValid) {
        setError(validation.error || 'Invalid file');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  }, []);

  // Handle form submission
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    // Validation
    if (!question.trim()) {
      setError('Please enter a question or topic to analyze');
      return;
    }

    if (activeTab === 'url' && !url.trim()) {
      setError('Please enter a URL to analyze');
      return;
    }

    if (activeTab === 'document' && !selectedFile) {
      setError('Please select a document to analyze');
      return;
    }

    try {
      let additionalData: { url?: string; file?: File; content?: string } = {};
      
      switch (activeTab) {
        case 'text':
          if (textContent.trim()) {
            additionalData.content = textContent;
          }
          break;
        case 'url':
          additionalData.url = url;
          break;
        case 'document':
          additionalData.file = selectedFile!;
          break;
      }

      await onAnalyze(question, activeTab, additionalData);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMessage);
    }
  }, [question, activeTab, textContent, url, selectedFile, onAnalyze]);

  return (
    <div className="input-panel">
      <h2 className="section-title">Analyze Arguments</h2>
      
      <div className="input-method-tabs">
        <button
          className={`tab ${activeTab === 'text' ? 'active' : ''}`}
          onClick={() => handleTabChange('text')}
          type="button"
        >
          📝 Text
        </button>
        <button
          className={`tab ${activeTab === 'url' ? 'active' : ''}`}
          onClick={() => handleTabChange('url')}
          type="button"
        >
          🔗 URL
        </button>
        <button
          className={`tab ${activeTab === 'document' ? 'active' : ''}`}
          onClick={() => handleTabChange('document')}
          type="button"
        >
          📄 Document
        </button>
      </div>

      <form onSubmit={handleSubmit} className="analysis-form">
        <div className="form-container">
          <div className="input-group">
            <label htmlFor="question" className="label">Question or Topic *</label>
            <input
              id="question"
              type="text"
              className="text-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What are the arguments about AI regulation?"
              disabled={isLoading}
              required
            />
            <div className="help-text">
              Describe what you want to analyze or ask a specific question
            </div>
          </div>

          {activeTab === 'text' && (
            <div className="input-group">
              <label htmlFor="textContent" className="label">Text Content (Optional)</label>
              <textarea
                id="textContent"
                className="text-area"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Paste the text you want to analyze here..."
                disabled={isLoading}
              />
              <div className="help-text">
                Paste an article, essay, or any text content. Leave empty to search the web for your topic.
              </div>
            </div>
          )}

          {activeTab === 'url' && (
            <div className="input-group">
              <label htmlFor="url" className="label">URL *</label>
              <input
                id="url"
                type="url"
                className="text-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/article"
                disabled={isLoading}
                required
              />
              <div className="help-text">
                Enter the URL of an article, blog post, or webpage to analyze
              </div>
            </div>
          )}

          {activeTab === 'document' && (
            <div className="input-group">
              <label htmlFor="document" className="label">Document *</label>
              <input
                ref={fileInputRef}
                id="document"
                type="file"
                className="file-input"
                accept=".txt,.pdf,.doc,.docx"
                onChange={handleFileChange}
                disabled={isLoading}
                required
              />
              {selectedFile && (
                <div className="file-selected">
                  ✅ Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
              <div className="help-text">
                Upload a document (.txt, .pdf, .doc, .docx) up to 10MB
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            className={`analyze-button ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? '🔄 Analyzing...' : '🚀 Analyze Arguments'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default InputPanel;