import { render, screen } from '@testing-library/react';
import { RouteAnalysisCard } from '../RouteAnalysisCard';
import { describe, it, expect } from 'vitest';

describe('RouteAnalysisCard', () => {
  it('renders correctly with complete analysis data', () => {
    const mockAnalysis = {
      highway: { flat: 100, up: 20, down: 10 },
      other: { flat: 50, up: 5, down: 5 }
    };

    render(<RouteAnalysisCard analysis={mockAnalysis as any} />);

    expect(screen.getByText(/Detaylı Rota Analizi/i)).toBeInTheDocument();
    expect(screen.getByText(/Düz/i)).toBeInTheDocument();
    expect(screen.getByText(/150.0 km/i)).toBeInTheDocument(); // 100 + 50
  });

  it('renders gracefully with partial or missing analysis data (defensive check)', () => {
    const partialAnalysis = {
      highway: { flat: 100 },
      // other is missing
    };

    render(<RouteAnalysisCard analysis={partialAnalysis as any} />);

    expect(screen.getByText(/Detaylı Rota Analizi/i)).toBeInTheDocument();
    // Should show 100.0 km for flat as 'other' defaults to 0
    expect(screen.getByText(/100.0 km/i)).toBeInTheDocument();
  });
  
  it('handles empty analysis without crashing', () => {
    render(<RouteAnalysisCard analysis={{} as any} />);
    expect(screen.getByText(/Detaylı Rota Analizi/i)).toBeInTheDocument();
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });
});
