/**
 * SSE Events Service
 * Handles Server-Sent Events streaming from API V1
 */

import { API_BASE_URL } from './api';

export interface StreamEvent {
  type: 'start' | 'info' | 'events' | 'scraper_error' | 'no_events' | 'progress' | 'complete' | 'error';
  message?: string;
  scraper?: string;
  events?: any[];
  count?: number;
  error?: string;
  scrapers?: string[];
  completed?: number;
  total?: number;
  percentage?: number;
  total_events?: number;
  timestamp?: string;
}

export interface IntentResponse {
  location: {
    city: string | null;
    state: string | null;
    country: string | null;
  };
  intent: string;
  filters: {
    date_range: string;
    categories: string[];
    keywords: string[];
  };
}

export class SSEEventsService {
  private eventSource: EventSource | null = null;
  private abortController: AbortController | null = null;

  /**
   * Detect intent from user query using Gemini AI
   */
  async detectIntent(query: string): Promise<IntentResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/intent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Intent detection failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Search events using SSE streaming
   */
  searchEventsStream(
    location: string,
    onEvent: (event: StreamEvent) => void,
    options: {
      limit?: number;
      categories?: string[];
    } = {}
  ): () => void {
    // Close existing connection if any
    this.close();

    // Build query params
    const params = new URLSearchParams({
      location,
      limit: String(options.limit || 10),
    });

    if (options.categories?.length) {
      params.append('categories', options.categories.join(','));
    }

    // Create SSE connection
    const url = `${API_BASE_URL}/api/v1/search?${params}`;
    this.eventSource = new EventSource(url);

    // Handle incoming events
    this.eventSource.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data);
        onEvent(data);
      } catch (error) {
        console.error('Error parsing SSE event:', error);
      }
    };

    // Handle errors
    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      onEvent({
        type: 'error',
        message: 'Connection lost. Retrying...',
      });
      
      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        if (this.eventSource?.readyState === EventSource.CLOSED) {
          this.searchEventsStream(location, onEvent, options);
        }
      }, 3000);
    };

    // Return cleanup function
    return () => this.close();
  }

  /**
   * Get event recommendations (non-streaming)
   */
  async getRecommendations(
    location: string,
    preferences: string[] = [],
    history: any[] = []
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        location,
        preferences,
        history,
      }),
    });

    if (!response.ok) {
      throw new Error(`Recommendations failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List available scrapers
   */
  async listScrapers(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/scrapers`);
    
    if (!response.ok) {
      throw new Error(`Failed to list scrapers: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Close SSE connection
   */
  close() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}

// Export singleton instance
export const sseEventsService = new SSEEventsService();