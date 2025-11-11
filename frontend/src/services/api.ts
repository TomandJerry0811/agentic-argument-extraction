/**
 * API Service for communicating with the Flask backend
 * Handles all HTTP requests to the Argument Cartographer backend
 */


import axios, { AxiosResponse } from 'axios';
import { 
  BackendResponse, 
  BackendError, 
  ArgumentMap 
} from '../types/ArgumentMap';


// Backend configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_TIMEOUT = 150000; // 150 seconds for AI processing (backend has 120s timeout)


// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Important for CORS
});


// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);


// Add response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);


/**
 * Main API service class
 */
export class ArgumentCartographerAPI {
  
  /**
   * Check if the backend server is running
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await apiClient.get('/');
      return response.status === 200;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }


  /**
   * Analyze a question/topic and get argument map
   */
  static async analyzeQuestion(question: string): Promise<BackendResponse> {
    try {
      const requestData = { question };
      
      console.log('📤 Sending analysis request:', requestData);
      
      const response: AxiosResponse<BackendResponse | BackendError> = await apiClient.post(
        '/ask',
        requestData
      );

      // Check if response contains error
      if ('error' in response.data) {
        const errorResponse = response.data as BackendError;
        throw new Error(errorResponse.error);
      }

      // Parse successful response
      const successResponse = response.data as BackendResponse;
      
      // Validate response has argument_map
      if (!successResponse.argument_map) {
        throw new Error('Invalid response format from backend');
      }
      
      // FIXED: Ensure sources array exists (add default empty array if missing)
      if (!successResponse.sources) {
        successResponse.sources = [];
      }
      
      console.log('✅ Analysis completed:', {
        title: successResponse.argument_map.title,
        elementCount: successResponse.argument_map.elements.length,
        sourceCount: successResponse.sources.length
      });
      
      // Return FULL response with sources
      return successResponse;
      
    } catch (error) {
      console.error('💥 Analysis failed:', error);
      
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 403) {
          throw new Error('Access denied. Your IP address is not whitelisted.');
        } else if (error.response?.status === 400) {
          throw new Error('Invalid request. Please check your input.');
        } else if (error.response?.status === 422) {
          throw new Error('AI returned invalid format. Please try again.');
        } else if (error.response?.status === 500) {
          throw new Error('Backend server error. Please check if the AI model is running.');
        } else if (error.code === 'ECONNREFUSED') {
          throw new Error('Cannot connect to backend server. Please ensure it\'s running on port 5000.');
        } else if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
          throw new Error('Request timeout. The AI model may be taking too long to respond.');
        }
      }
      
      throw error;
    }
  }


  /**
   * Analyze content from URL
   */
  static async analyzeURL(url: string): Promise<BackendResponse> {
    // For now, we'll use the same endpoint but include the URL in the question
    const question = `Analyze arguments from this URL: ${url}`;
    return this.analyzeQuestion(question);
  }


  /**
   * Analyze uploaded document
   */
  static async analyzeDocument(file: File, description?: string): Promise<BackendResponse> {
    try {
      // Read file content
      const fileContent = await this.readFileContent(file);
      
      // Create question with file content
      const question = description 
        ? `${description}\n\nDocument content: ${fileContent}`
        : `Analyze the arguments in this document: ${fileContent}`;
      
      return this.analyzeQuestion(question);
      
    } catch (error) {
      console.error('Document analysis failed:', error);
      throw new Error(`Failed to analyze document: ${error}`);
    }
  }


  /**
   * Helper method to read file content
   */
  private static readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        const content = event.target?.result as string;
        resolve(content);
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      // Read as text
      reader.readAsText(file);
    });
  }


  /**
   * Validate file type for document upload
   */
  static validateFile(file: File): { isValid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'text/plain',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];


    if (file.size > maxSize) {
      return {
        isValid: false,
        error: 'File size must be less than 10MB'
      };
    }


    if (!allowedTypes.includes(file.type)) {
      return {
        isValid: false,
        error: 'File type not supported. Please use .txt, .pdf, or .doc files'
      };
    }


    return { isValid: true };
  }
}


export default ArgumentCartographerAPI;
