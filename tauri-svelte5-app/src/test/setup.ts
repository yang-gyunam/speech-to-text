import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Tauri API
(globalThis as any).window = Object.create(window);
Object.defineProperty(window, '__TAURI__', {
  value: {
    invoke: vi.fn(),
    event: {
      listen: vi.fn(),
      emit: vi.fn(),
    },
  },
  writable: true,
});

// Mock Tauri modules
vi.mock('@tauri-apps/api/tauri', () => ({
  invoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/dialog', () => ({
  open: vi.fn(),
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(),
  emit: vi.fn(),
}));

// Mock matchMedia for theme detection
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});