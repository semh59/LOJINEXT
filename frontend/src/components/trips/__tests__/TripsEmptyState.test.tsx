import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TripTable } from "../TripTable";

// Mock framer-motion
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Mock @tanstack/react-virtual
vi.mock("@tanstack/react-virtual", () => ({
  useVirtualizer: (args: any) => {
    const count = args?.count ?? 0;
    return {
      getTotalSize: () => count * 140,
      getVirtualItems: () =>
        Array.from({ length: count }).map((_, index) => ({
          key: `row-${index}`,
          index,
          size: 140,
          start: index * 140,
        })),
    };
  },
}));

const noop = () => {};

describe("TripTable — Empty State Render", () => {
  it('renders "Henüz Sefer Bulunmuyor" when trips array is empty', () => {
    render(
      <TripTable trips={[]} isLoading={false} onEdit={noop} onDelete={noop} />,
    );

    expect(screen.getByText("Henüz Sefer Bulunmuyor")).toBeInTheDocument();
    expect(
      screen.getByText(/Yeni bir sefer girişi yaparak operasyonu başlatın/i),
    ).toBeInTheDocument();
  });

  it("renders skeleton loader when isLoading is true", () => {
    const { container } = render(
      <TripTable trips={[]} isLoading={true} onEdit={noop} onDelete={noop} />,
    );

    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBe(5);
  });

  it("does not render skeleton when isLoading is false and trips are empty", () => {
    const { container } = render(
      <TripTable trips={[]} isLoading={false} onEdit={noop} onDelete={noop} />,
    );

    // Only the decorative pulse in empty state, not skeleton rows
    const skeletonRows = container.querySelectorAll(".h-32.animate-pulse");
    expect(skeletonRows.length).toBe(0);
  });

  it("does not render pagination when trips are empty", () => {
    render(
      <TripTable trips={[]} isLoading={false} onEdit={noop} onDelete={noop} />,
    );

    // Pagination elements should not exist
    expect(screen.queryByText(/Onceki/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Sonraki/i)).not.toBeInTheDocument();
  });

  it("renders the empty state icon (PackageOpen)", () => {
    const { container } = render(
      <TripTable trips={[]} isLoading={false} onEdit={noop} onDelete={noop} />,
    );

    // The empty state has a dashed border container
    const emptyContainer = container.querySelector(".border-dashed");
    expect(emptyContainer).toBeInTheDocument();
  });

  it("renders trip rows when trips are provided", () => {
    const mockTrip = {
      id: 1,
      tarih: "2026-01-01",
      saat: "10:00",
      arac_id: 1,
      sofor_id: 1,
      guzergah_id: 1,
      cikis_yeri: "İstanbul",
      varis_yeri: "Ankara",
      mesafe_km: 450,
      bos_agirlik_kg: 8000,
      dolu_agirlik_kg: 18000,
      net_kg: 10000,
      ton: 10,
      durum: "Tamam",
      is_real: true,
    };

    render(
      <TripTable
        trips={[mockTrip as any]}
        isLoading={false}
        onEdit={noop}
        onDelete={noop}
      />,
    );

    // Empty state should NOT appear
    expect(
      screen.queryByText("Henüz Sefer Bulunmuyor"),
    ).not.toBeInTheDocument();

    // Trip data should be visible
    expect(screen.getByText(/İstanbul → Ankara/)).toBeInTheDocument();
  });
});
