import React, { useState, useCallback } from 'react';
import { ArgumentMap, InputMethod, VisualizationStyle, BackendResponse } from './types/ArgumentMap';
import ArgumentCartographerAPI from './services/api';
import ArgumentFlow from './components/ArgumentFlow';
import InputPanel from './components/InputPanel';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorDisplay from './components/ErrorDisplay';
import './App.css';


function App() {
  // State management
  const [argumentMap, setArgumentMap] = useState<ArgumentMap | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStyle, setCurrentStyle] = useState<VisualizationStyle>('Classic Tree');
  const [sources, setSources] = useState<string[]>([]);
  const [skippedUrls, setSkippedUrls] = useState<string[]>([]);


  // Handle analysis request
  const handleAnalyze = useCallback(async (
    question: string,
    inputMethod: InputMethod,
    additionalData?: { url?: string; file?: File; content?: string }
  ) => {
    setIsLoading(true);
    setError(null);
    setArgumentMap(null);
    setSources([]);
    setSkippedUrls([]);


    try {
      let apiResponse: BackendResponse;


      switch (inputMethod) {
        case 'text':
          const textQuestion = additionalData?.content 
            ? `${question}\n\nText to analyze: ${additionalData.content}`
            : question;
          apiResponse = await ArgumentCartographerAPI.analyzeQuestion(textQuestion);
          break;


        case 'url':
          if (!additionalData?.url) {
            throw new Error('URL is required for URL analysis');
          }
          apiResponse = await ArgumentCartographerAPI.analyzeURL(additionalData.url);
          break;


        case 'document':
          if (!additionalData?.file) {
            throw new Error('File is required for document analysis');
          }
          apiResponse = await ArgumentCartographerAPI.analyzeDocument(additionalData.file, question);
          break;


        default:
          throw new Error('Invalid input method');
      }


      // Extract data from response
      setArgumentMap(apiResponse.argument_map);
      setSources(apiResponse.sources || []);
      setSkippedUrls([]);  // Backend doesn't provide skipped_urls yet


      console.log('Analysis completed:', apiResponse.argument_map);


    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      console.error('Analysis failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);


  // Handle visualization style change
  const handleStyleChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentStyle(event.target.value as VisualizationStyle);
  }, []);


  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">🗺️ Argument Cartographer</h1>
        <select
          className="style-selector"
          value={currentStyle}
          onChange={handleStyleChange}
          disabled={!argumentMap}
        >
          <option value="Classic Tree">Classic Tree</option>
          <option value="Org Chart">Org Chart</option>
          <option value="Pillar View">Pillar View</option>
        </select>
      </header>


      <main className="main-content">
        <div className="left-panel">
          <InputPanel
            onAnalyze={handleAnalyze}
            isLoading={isLoading}
          />
        </div>


        <div className="visualization-area">
          {isLoading && <LoadingSpinner />}


          {error && (
            <ErrorDisplay
              error={error}
              onRetry={() => setError(null)}
            />
          )}


          {argumentMap && !isLoading && !error && (
            <>
              <ArgumentFlow
                argumentMap={argumentMap}
                visualizationStyle={currentStyle}
                sources={sources}
              />
              {sources.length > 0 && (
                <div className="sources-panel">
                  <h4>Sources:</h4>
                  <ul>
                    {sources.map((src, idx) => (
                      <li key={idx}><a href={src} target="_blank" rel="noreferrer">{src}</a></li>
                    ))}
                  </ul>
                </div>
              )}
              {skippedUrls.length > 0 && (
                <div className="skipped-urls-panel">
                  <h4>Skipped URLs (timed out):</h4>
                  <ul>
                    {skippedUrls.map((src, idx) => (
                      <li key={idx}><a href={src} target="_blank" rel="noreferrer">{src}</a></li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}


          {!argumentMap && !isLoading && !error && (
            <div className="empty-state">
              <h3>Welcome to Argument Cartographer</h3>
              <p>
                Analyze any topic, article, or document to visualize its logical structure.
                <br />
                Enter your question or content in the panel on the left to get started.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}


export default App;
