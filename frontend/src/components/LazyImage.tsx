/**
 * 🖼️ LAZY IMAGE - Carga progresiva y suave de imágenes
 *
 * CARACTERÍSTICAS:
 * ✅ Skeleton/placeholder mientras carga
 * ✅ Fade-in suave (0.3s transition)
 * ✅ Intersection Observer (solo carga cuando visible)
 * ✅ Fallback a placeholder si falla
 * ✅ Batch loading opcional (evita cargar todas a la vez)
 *
 * USO:
 * ```tsx
 * // Carga simple
 * <LazyImage src={event.image_url} alt={event.title} className="aspect-video" />
 *
 * // Con batch loading (50ms delay entre imágenes)
 * {events.map((event, index) => (
 *   <LazyImage
 *     key={event.id}
 *     src={event.image_url}
 *     alt={event.title}
 *     delay={index * 50}
 *     className="aspect-video"
 *   />
 * ))}
 * ```
 */

import React, { useState, useEffect, useRef } from 'react';
import '../styles/LazyImage.css';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholderSrc?: string;
  delay?: number; // Delay opcional para batch loading
  onLoad?: () => void;
  onError?: () => void;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className = '',
  placeholderSrc,
  delay = 0,
  onLoad,
  onError
}) => {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    // Crear Intersection Observer para lazy loading
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !imageSrc) {
            // Imagen es visible, cargarla con delay opcional
            setTimeout(() => {
              loadImage();
            }, delay);
          }
        });
      },
      {
        rootMargin: '50px', // Empezar a cargar 50px antes de ser visible
        threshold: 0.01
      }
    );

    // Observar elemento
    if (imgRef.current) {
      observerRef.current.observe(imgRef.current);
    }

    // Cleanup
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [delay, imageSrc]);

  const loadImage = () => {
    const img = new Image();

    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
      setHasError(false);
      onLoad?.();
    };

    img.onerror = () => {
      setIsLoading(false);
      setHasError(true);

      // Usar placeholder si hay, sino dejar skeleton
      if (placeholderSrc) {
        setImageSrc(placeholderSrc);
      }

      onError?.();
    };

    img.src = src;
  };

  return (
    <div className={`lazy-image-container ${className}`}>
      {/* Skeleton/Placeholder mientras carga */}
      {isLoading && (
        <div className="lazy-image-skeleton">
          <div className="skeleton-shimmer"></div>
        </div>
      )}

      {/* Imagen real con fade-in */}
      <img
        ref={imgRef}
        src={imageSrc || placeholderSrc || ''}
        alt={alt}
        className={`lazy-image ${!isLoading && imageSrc ? 'loaded' : ''} ${hasError ? 'error' : ''}`}
        style={{
          opacity: imageSrc && !isLoading ? 1 : 0,
          transition: 'opacity 0.3s ease-in-out'
        }}
      />

      {/* Opcional: Indicador de error */}
      {hasError && !placeholderSrc && (
        <div className="lazy-image-error">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default LazyImage;
