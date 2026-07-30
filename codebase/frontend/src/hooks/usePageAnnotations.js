import { useCallback, useEffect, useMemo, useState } from "react";

export function distanceToSegment(point, start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  if (dx === 0 && dy === 0) {
    return Math.hypot(point.x - start.x, point.y - start.y);
  }
  const projection = Math.max(
    0,
    Math.min(
      1,
      ((point.x - start.x) * dx + (point.y - start.y) * dy) /
        (dx * dx + dy * dy),
    ),
  );
  const nearestX = start.x + projection * dx;
  const nearestY = start.y + projection * dy;
  return Math.hypot(point.x - nearestX, point.y - nearestY);
}

function strokeTouchesPoint(stroke, point, radius) {
  const points = stroke.points || [];
  if (points.length === 1) {
    return distanceToSegment(point, points[0], points[0]) <= radius;
  }
  for (let index = 1; index < points.length; index += 1) {
    if (distanceToSegment(point, points[index - 1], points[index]) <= radius) {
      return true;
    }
  }
  return false;
}

export function usePageAnnotations(documentId) {
  const storageKey = useMemo(
    () => (documentId ? `vlearn-annotations:${documentId}` : null),
    [documentId],
  );
  const [annotations, setAnnotations] = useState({});
  const [loadedStorageKey, setLoadedStorageKey] = useState(null);

  useEffect(() => {
    if (!storageKey) {
      setAnnotations({});
      setLoadedStorageKey(null);
      return;
    }
    try {
      const raw = localStorage.getItem(storageKey);
      setAnnotations(raw ? JSON.parse(raw) : {});
    } catch {
      setAnnotations({});
    }
    setLoadedStorageKey(storageKey);
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey || loadedStorageKey !== storageKey) return;
    localStorage.setItem(storageKey, JSON.stringify(annotations));
  }, [annotations, loadedStorageKey, storageKey]);

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
      return {
        ...current,
        [key]: (current[key] || []).slice(0, -1),
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
      const next = (current[key] || []).filter(
        (stroke) => !strokeTouchesPoint(stroke, point, radius),
      );
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
