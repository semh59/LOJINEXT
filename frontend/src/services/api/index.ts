export * from './legacy';
export * from './trip-service';
export * from './location-service';
export * from './ai-service';
export * from './vehicle-service';
export * from './driver-service';
export * from './fuel-service';
export * from './report-service';
export * from './prediction-service';
export * from './ws-service';

// Re-export api object if needed by legacy code
import * as legacy from './legacy';
export const api = legacy;
