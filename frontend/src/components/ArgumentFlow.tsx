import React from 'react';
import { ArgumentMap, VisualizationStyle } from '../types/ArgumentMap';
import './ArgumentFlow.css';

interface ArgumentFlowProps {
  argumentMap: ArgumentMap;
  visualizationStyle: VisualizationStyle;
  sources: string[];
}

const ArgumentFlow: React.FC<ArgumentFlowProps> = ({ argumentMap, visualizationStyle, sources }) => {
  return (
    <div className="argument-flow-container">
      <div className="flow-header">
        <h3>{argumentMap.title}</h3>
        <div className="style-info">Style: {visualizationStyle}</div>
      </div>
      
      <div className="flow-content">
        <div className="placeholder-visualization">
          <h4>🚧 Visualization Coming Soon</h4>
          <p>React Flow visualization will be implemented here</p>
          
          <div className="argument-preview">
            <h5>Argument Elements ({argumentMap.elements.length}):</h5>
            <ul>
              {argumentMap.elements.map((element, index) => (
                <li key={element.id} className={`element-${element.type.toLowerCase().replace(' ', '-')}`}>
                  <strong>{element.type}:</strong> {element.content.substring(0, 100)}
                  {element.content.length > 100 ? '...' : ''}
                </li>
              ))}
            </ul>
          </div>
          
          {sources.length > 0 && (
            <div className="sources-preview">
              <h5>Sources ({sources.length}):</h5>
              <ul>
                {sources.map((source, index) => (
                  <li key={index}>
                    <a href={source} target="_blank" rel="noopener noreferrer">
                      {source}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArgumentFlow;