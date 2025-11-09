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
  async detectIntent(query: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/ai/analyze-intent`, {
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
   * Search events using SSE (Server-Sent Events) for real-time streaming
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
      limit: String(options.limit || 100),
    });

    if (options.categories?.length) {
      params.append('categories', options.categories.join(','));
    }

    // Use SSE streaming endpoint for real-time results
    const url = `${API_BASE_URL}/api/events/stream?${params}`;

    console.log('🔥 Starting SSE connection to:', url);

    // Create EventSource for SSE
    this.eventSource = new EventSource(url);

    // Handle incoming events
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 SSE Event:', data.type, data);
        onEvent(data);
      } catch (error) {
        console.error('Error parsing SSE event:', error);
      }
    };

    this.eventSource.onerror = (error) => {
      // Solo mostrar error si la conexión falló antes de establecerse
      // Si readyState es CLOSED, es normal (el stream completó)
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        console.log('✅ SSE stream closed normally');
        return;
      }

      console.error('❌ SSE Error:', error);
      onEvent({
        type: 'error',
        message: 'Connection error',
        error: 'Failed to connect to event stream'
      });
      this.close();
    };

    // Return cleanup function
    return () => this.close();
  }

  /**
   * Get event recommendations (non-streaming)
   * 🔴 ELIMINADO - Ya no se usa recommendations
   */
  // async getRecommendations(
  //   location: string,
  //   preferences: string[] = [],
  //   history: any[] = []
  // ): Promise<any> {
  //   const response = await fetch(`${API_BASE_URL}/api/ai/recommend`, {
  //     method: 'POST',
  //     headers: {
  //       'Content-Type': 'application/json',
  //     },
  //     body: JSON.stringify({
  //       location,
  //       preferences,
  //       history,
  //     }),
  //   });

  //   if (!response.ok) {
  //     throw new Error(`Recommendations failed: ${response.statusText}`);
  //   }

  //   return response.json();
  // }

  /**
   * List available scrapers
   */
  async listScrapers(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/debug/scrapers-status`);
    
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