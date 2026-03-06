
import { render, screen } from '@testing-library/react';
import { TripTable } from '../TripTable';
import { Trip } from '../../../types';
import { describe, it, expect, vi } from 'vitest';

// Mock lucide-react to avoid icon rendering issues in tests
vi.mock('lucide-react', () => ({
  Truck: () => <div data-testid="truck-icon" />,
  User: () => <div data-testid="user-icon" />,
  Edit2: () => <div data-testid="edit-icon" />,
  Trash2: () => <div data-testid="trash-icon" />,
  Ban: () => <div data-testid="ban-icon" />
}));

describe('TripTable', () => {
  const mockTrips: Trip[] = [
    {
      id: 1,
      tarih: '2024-05-20',
      saat: '10:00',
      sefer_no: 'SN-001',
      arac_id: 1,
      plaka: '34ABC123',
      sofor_id: 1,
      sofor_adi: 'Ahmet Yılmaz',
      cikis_yeri: 'Istanbul',
      varis_yeri: 'Ankara',
      mesafe_km: 450,
      net_kg: 20000,
      ton: 20,
      bos_agirlik_kg: 8000,
      dolu_agirlik_kg: 28000,
      durum: 'Tamam',
      bos_sefer: false,
      flat_distance_km: 400
    },
    {
      id: 2,
      tarih: '2024-05-21',
      saat: '11:00',
      sefer_no: '', // Empty sefer_no
      arac_id: 1,
      plaka: '34DEF456',
      sofor_id: 2,
      sofor_adi: 'Mehmet Demir',
      cikis_yeri: 'Bursa',
      varis_yeri: 'Izmir',
      mesafe_km: 330,
      net_kg: 15000,
      ton: 15,
      bos_agirlik_kg: 8000,
      dolu_agirlik_kg: 23000,
      durum: 'Yolda',
      bos_sefer: false,
      flat_distance_km: 300
    }
  ];

  const defaultProps = {
    trips: mockTrips,
    isLoading: false,
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    selectedIds: [],
    onSelect: vi.fn(),
    onSelectAll: vi.fn()
  };

  it('renders sefer_no correctly', () => {
    render(<TripTable {...defaultProps} />);
    
    // Check for the first trip's sefer_no
    expect(screen.getByText('SN-001')).toBeInTheDocument();
    
    // Check for the second trip's empty sefer_no (should show '-')
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('renders column header "Sefer No"', () => {
    render(<TripTable {...defaultProps} />);
    expect(screen.getByText('Sefer No')).toBeInTheDocument();
  });
});
