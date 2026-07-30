import { useCallback, useEffect, useMemo, useState } from "react";

const emptyAnnotations = {};

export function usePageAnnotations(documentId) {
  const storageKey = useMemo(
    () => (documentId ? `vlearn-annotations:${documentId}` : null),
    [documentId],
  );
  const [annotations, setAnnotations] = useState(emptyAnnotations);

  useEffect(() => {
    if (!storageKey) {
      setAnnotations(emptyAnnotations);
      return;
    }
    try {
      const raw = localStorage.getItem(storageKey);
      setAnnotations(raw ? JSON.parse(raw) : {});
    } catch {
      setAnnotations({});
    }
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey) return;
    localStorage.setItem(storageKey, JSON.stringify(annotations));
  }, [annotations, storageKey]);

  const getStrokes = useCallback(
    (pageNumber) => annotations[String(pageNumber)] || [],
    [annotations],
  );

  const addStroke = useCallback((pageNumber, stroke) => {
    setAnnotations((current) => {
      const key = String(pageNumber);
      return {
        ...current,
        [key]: [...(current[key] || []), stroke],
      };
    });
  }, []);

  const undoPage = useCallback((pageNumber) => {
    setAnnotations((current) => {
      const key = String(pageNumber);
      const strokes = current[key] || [];
      return {
        ...current,
        [key]: strokes.slice(0, -1),
      };
    });
  }, []);

  const clearPage = useCallback((pageNumber) => {
    setAnnotations((current) => ({
      ...current,
      [String(pageNumber)]: [],
    }));
  }, []);

  const eraseNearPoint = useCallback((pageNumber, point, radius = 0.025) => {
    setAnnotations((current) => {
      const key = String(pageNumber);
      const strokes = current[key] || [];
      const next = strokes.filter((stroke) => {
        return !stroke.points.some((candidate) => {
          const dx = candidate.x - point.x;
          const dy = candidate.y - point.y;
          return Math.sqrt(dx * dx + dy * dy) <= radius;
        });
      });
      return { ...current, [key]: next };
    });
  }, []);

  return {
    getStrokes,
    addStroke,
    undoPage,
    clearPage,
    eraseNearPoint,
  };
}
