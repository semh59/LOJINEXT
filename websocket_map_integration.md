# LojiNext: Gerçek Zamanlı Harita (WebSocket) Entegrasyonu Altyapısı

Bu doküman, Seferler sayfasında ve ana Dashboard'da araçların harita üzerinde anlık izlenmesini sağlayacak olan **WebSocket (Socket.io/FastAPI WebSockets)** altyapısının tasarım kararlarını içerir.

## 1. Mimari Tasarım

- **Bağlantı Türü**: Stateful, bidirectional (FastAPI WebSockets).
- **Protokol Güvenliği**: Sadece JWT taşıyan ve doğrulanmış `WSS://` (Secure WebSockets) bağlantılarına izin verilecektir.
- **Yayın Stratejisi (Pub/Sub)**: Birden fazla worker (Uvicorn) çalışacağı için arka planda **Redis Pub/Sub** kullanılarak yatay ölçeklendirme sağlanacaktır.

## 2. Event İsimlendirme Formatları

- `vehicle.location.update`: Gelen anlık GPS verisi (Kordinatlar, Hız, Yön). Sunucu bu mesajı dinleyen clientlara gönderir.
- `trip.status.changed`: Bir sefer "Devam Ediyor" durumuna geçtiğinde ya da "Tamamlandı" olduğunda tetiklenir.
- `trip.anomaly.detected`: Rota sapması, ani fren veya rölanti sınırının aşılması gibi durumlarda client'a düşen bildirimler.

## 3. Data Şeması (Payload)

```json
{
  "type": "vehicle.location.update",
  "timestamp": "2026-03-04T10:00:00Z",
  "data": {
    "arac_id": 12,
    "plaka": "34 ABC 123",
    "sefer_id": 456,
    "lat": 41.0082,
    "lng": 28.9784,
    "speed": 85,
    "heading": 120
  }
}
```

## 4. Frontend Entegrasyonu (React)

- Zustand (veya provider temelli context) içerisinde bir `useWebSocket` hook'u oluşturulacaktır.
- Harita bileşeni (React Leaflet veya Mapbox) bu socket yayınlarını dinleyerek `optimistic ui` performansı ile aracın marker'ını akıcı şekilde animasyonla (Frame by frame) taşıyacaktır.
- Mevcut ping/polling asenkron API (`refetchInterval`) WebSocket bağlandığında tamamen devre dışı kalacak şekilde `queryClient` kuralları yapılandırılacaktır.
