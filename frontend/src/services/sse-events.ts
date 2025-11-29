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
   * 🔧 MOBILE-FIX: Agregado try-catch robusto para capturar errores en móvil
   */
  searchEventsStream(
    location: string,
    onEvent: (event: StreamEvent) => void,
    options: {
      limit?: number;
      categories?: string[];
      parent_city?: string;  // ✨ Ciudad padre desde metadata del frontend
    } = {}
  ): () => void {
    console.log('📱 [SSE-DEBUG] searchEventsStream INICIO - location:', location);

    try {
      // Close existing connection if any
      this.close();
      console.log('📱 [SSE-DEBUG] Conexión anterior cerrada');

      // Build query params
      const params = new URLSearchParams({
        location,
        limit: String(options.limit || 100),
      });
      console.log('📱 [SSE-DEBUG] Params construidos:', params.toString());

      if (options.categories?.length) {
        params.append('categories', options.categories.join(','));
      }

      // ✨ Agregar ciudad padre si existe (desde metadata del barrio)
      if (options.parent_city) {
        params.append('parent_city', options.parent_city);
        console.log(`🏙️ Pasando parent_city al backend: ${options.parent_city}`);
      }

      // Use SSE streaming endpoint for real-time results
      const url = `${API_BASE_URL}/api/events/stream?${params}`;

      console.log('🔥 Starting SSE connection to:', url);

      // 🔧 MOBILE-FIX: Verificar que EventSource existe
      if (typeof EventSource === 'undefined') {
        console.error('❌ [MOBILE-ERROR] EventSource no está disponible en este navegador');
        onEvent({
          type: 'error',
          message: 'SSE not supported',
          error: 'EventSource not available in this browser'
        });
        return () => {};
      }

      // Create EventSource for SSE
      console.log('📱 [SSE-DEBUG] Creando EventSource...');
      this.eventSource = new EventSource(url);
      console.log('📱 [SSE-DEBUG] EventSource creado, readyState:', this.eventSource.readyState);

      // Flag to track if stream completed normally
      let streamCompleted = false;

      // Handle incoming events
      this.eventSource.onmessage = (event) => {
        try {
          console.log('📱 [SSE-DEBUG] onmessage recibido');
          const data = JSON.parse(event.data);
          console.log('📨 SSE Event:', data.type, data);
          onEvent(data);

          // Cerrar conexión cuando stream completa
          if (data.type === 'complete') {
            console.log('✅ Stream completed, closing connection');
            streamCompleted = true;
            this.close();
          }
        } catch (error: any) {
          console.error('❌ [MOBILE-ERROR] Error parsing SSE event:', error?.message || error);
        }
      };

      // 🔧 MOBILE-FIX: onopen para confirmar conexión
      this.eventSource.onopen = () => {
        console.log('📱 [SSE-DEBUG] Conexión SSE abierta exitosamente');
      };

      this.eventSource.onerror = (errorEvent) => {
        console.log('📱 [SSE-DEBUG] onerror disparado, streamCompleted:', streamCompleted);

        // Si el stream completó normalmente, ignorar el error de cierre
        if (streamCompleted) {
          console.log('ℹ️ SSE connection closed after completion');
          return;
        }

        // Si la conexión está cerrada o conectando, es un cierre normal
        if (this.eventSource?.readyState === EventSource.CLOSED) {
          console.log('ℹ️ SSE connection closed');
          return;
        }

        // Error real durante la conexión
        console.error('❌ SSE connection error, readyState:', this.eventSource?.readyState);
        onEvent({
          type: 'error',
          message: 'Connection error',
          error: 'Failed to connect to event stream'
        });

        this.close();
      };

      console.log('📱 [SSE-DEBUG] Event handlers configurados, retornando cleanup');
      // Return cleanup function
      return () => this.close();

    } catch (error: any) {
      // 🔧 MOBILE-FIX: Capturar cualquier error inesperado
      console.error('❌ [MOBILE-CRITICAL] Error crítico en searchEventsStream:', error?.message || error);
      console.error('❌ [MOBILE-CRITICAL] Stack:', error?.stack);

      onEvent({
        type: 'error',
        message: 'Critical error',
        error: error?.message || 'Unknown error in SSE setup'
      });

      return () => {};
    }
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