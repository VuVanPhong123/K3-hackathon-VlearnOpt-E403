import "@testing-library/jest-dom/vitest";

class MockPointerEvent extends MouseEvent {
  constructor(type, properties = {}) {
    super(type, properties);
    Object.defineProperties(this, {
      pointerId: { value: properties.pointerId ?? 1, configurable: true },
      isPrimary: { value: properties.isPrimary ?? true, configurable: true },
      pointerType: { value: properties.pointerType ?? "mouse", configurable: true },
    });
  }
}

globalThis.PointerEvent = MockPointerEvent;
