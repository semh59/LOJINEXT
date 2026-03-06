import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { locationService, LocationFilters } from '../services/api/location-service';
import { LocationCreate, LocationUpdate } from '../types/location';
import { toast } from 'sonner';

export const useLocations = (filters: LocationFilters = {}) => {
    const queryClient = useQueryClient();

    // Tüm güzergahları getir
    const useGetLocations = () => {
        return useQuery({
            queryKey: ['locations', filters],
            queryFn: () => locationService.getAll(filters),
        });
    };

    // Tek bir güzergah getir
    const useGetLocation = (id: number) => {
        return useQuery({
            queryKey: ['location', id],
            queryFn: () => locationService.getById(id),
            enabled: !!id,
        });
    };

    // Yeni güzergah oluştur
    const useCreateLocation = () => {
        return useMutation({
            mutationFn: (data: LocationCreate) => locationService.create(data),
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['locations'] });
                toast.success('Güzergah başarıyla oluşturuldu.');
            },
            onError: (error: any) => {
                toast.error(error?.message || 'Güzergah oluşturulurken bir hata oluştu.');
            }
        });
    };

    // Güzergah güncelle
    const useUpdateLocation = () => {
        return useMutation({
            mutationFn: ({ id, data }: { id: number; data: LocationUpdate }) =>
                locationService.update(id, data),
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['locations'] });
                toast.success('Güzergah başarıyla güncellendi.');
            },
            onError: (error: any) => {
                toast.error(error?.message || 'Güzergah güncellenirken bir hata oluştu.');
            }
        });
    };

    // Güzergah sil
    const useDeleteLocation = () => {
        return useMutation({
            mutationFn: (id: number) => locationService.delete(id),
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['locations'] });
                toast.success('Güzergah başarıyla silindi.');
            },
            onError: (error: any) => {
                toast.error(error?.message || 'Güzergah silinirken bir hata oluştu.');
            }
        });
    };

    // Güzergah analizi yap
    const useAnalyzeLocation = () => {
        return useMutation({
            mutationFn: (id: number) => locationService.analyze(id),
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['locations'] });
                // Note: Analiz sonrası toast uyarısını bileşende (LocationAnalyzeModal) verebiliriz
            },
            onError: (error: any) => {
                toast.error(error?.message || 'Analiz sırasında bir hata oluştu.');
            }
        });
    };

    // Benzersiz isimleri getir
    const useLocationNames = () => {
        return useQuery({
            queryKey: ['location-names'],
            queryFn: () => locationService.getUniqueNames(),
            staleTime: 1000 * 60 * 5, // 5 dakika cache'le
        });
    };

    // Rota bilgilerini koordinatlara göre getir (Fetch)
    const useGetRouteInfo = () => {
        return useMutation({
            mutationFn: (params: {
                cikis_lat: number;
                cikis_lon: number;
                varis_lat: number;
                varis_lon: number;
            }) => locationService.getRouteInfo(params),
            onError: (error: any) => {
                toast.error(error?.message || 'Rota bilgileri çekilirken bir hata oluştu.');
            }
        });
    };

    return {
        useGetLocations,
        useGetLocation,
        useCreateLocation,
        useUpdateLocation,
        useDeleteLocation,
        useAnalyzeLocation,
        useLocationNames,
        useGetRouteInfo
    };
};
