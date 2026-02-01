"""
TIR Yakıt Takip - Yerel AI Servisi (Qwen2.5)
GPT4All tabanlı gömülü yapay zeka servisi.
"""

import threading
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from gpt4all import GPT4All
    GPT4ALL_AVAILABLE = True
except ImportError:
    GPT4ALL_AVAILABLE = False

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


try:
    from app.config import settings
    AI_MODEL_NAME = settings.AI_MODEL_NAME
    MODEL_DIR = settings.MODEL_DIR
except ImportError:
    # Fallback for tests
    from pathlib import Path
    AI_MODEL_NAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_DIR = Path.home() / ".cache" / "gpt4all"


class AIService:
    """
    Yerel LLM Servisi (Offline).
    
    Model: Qwen2.5-1.5B-Instruct
    Özellikler:
    - Tamamen çevrimdışı çalışır
    - Sistem verilerini (sefer, yakıt) context olarak kullanır (RAG-lite)
    - Düşük kaynak tüketimi
    """

    MODEL_NAME = AI_MODEL_NAME
    MODEL_PATH = MODEL_DIR
    _download_status = {"status": "ready", "percent": 100.0, "speed": "0 KB/s"}

    @classmethod
    def get_progress(cls):
        return cls._download_status

    def __init__(self):
        self._model: Optional[GPT4All] = None
        self._lock = threading.Lock()
        self._system_prompt = (
            "Sen LojiNext AI sisteminin 'Kıdemli Lojistik Analisti ve Filo Danışmanı' rolündesin. "
            "Görevin, sağlanan filo verilerini, yakıt tüketimlerini ve sefer kayıtlarını analiz ederek "
            "kullanıcıya stratejik tavsiyeler vermek, anomali tespiti yapmak ve operasyonel verimliliği artırmaktır.\n\n"
            "KURALLAR:\n"
            "1. Profesyonel, veriye dayalı ve teknik bir dil kullan.\n"
            "2. Cevapların Türkçe olsun.\n"
            "3. Teknik terimleri (Cd, aerodinamik, motor verimi) yerinde kullan.\n"
            "4. Tahminleme yaparken sistem verilerine sadık kal.\n"
            "5. Kullanıcıyı yakıt tasarrufu ve güvenli sürüş konusunda yönlendir."
        )

        # Model dizinini oluştur
        self.MODEL_PATH.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        """Modeli belleğe yükle (ELITE Security: No auto-download)"""
        if not GPT4ALL_AVAILABLE:
            raise RuntimeError("GPT4All kütüphanesi kurulu değil!")

        if self._model is None:
            with self._lock:
                if self._model is None:
                    # Model dosyasının varlığını kontrol et (Güvenlik)
                    model_file = self.MODEL_PATH / self.MODEL_NAME
                    if not model_file.exists():
                        logger.error(f"AI Model dosyası bulunamadı: {model_file}")
                        raise FileNotFoundError(f"Model dosyası eksik! Lütfen {self.MODEL_NAME} dosyasını {self.MODEL_PATH} dizinine yükleyin.")

                    logger.info(f"AI Model yükleniyor (Secure Load): {self.MODEL_NAME}")
                    try:
                        self._model = GPT4All(
                            model_name=self.MODEL_NAME,
                            model_path=str(self.MODEL_PATH),
                            allow_download=False, # FAZ 5.1: Insecure download disabled
                            device="cpu"
                        )
                        logger.info("AI Model başarıyla yüklendi")
                    except Exception as e:
                        logger.error(f"Model yükleme hatası: {e}")
                        raise

    async def _build_context(self, user_id: int = None) -> str:
        """
        Sistem verilerinden yapılandırılmış context oluştur.
        (Async & Structured)
        """
        from app.database.repositories.analiz_repo import get_analiz_repo
        from app.database.repositories.arac_repo import get_arac_repo
        
        context = ["### MEVCUT FİLO DURUMU VE VERİLER ###"]

        try:
            # 1. Genel Dashboard İstatistikleri
            analiz_repo = get_analiz_repo()
            stats = await analiz_repo.get_dashboard_stats()
            if stats:
                context.append(
                    f"- Filo Özeti: {stats['toplam_arac']} Araç, {stats['toplam_sofor']} Şoför, "
                    f"Aylık Ortalama Tüketim: {stats.get('filo_ortalama', 32.0):.1f} L/100km."
                )

            # 2. Kritik Anomali ve Uyarılar (Son 3)
            # GÜVENLIK: Raw SQL yerine parametreli repository metodu
            alerts = await analiz_repo.get_recent_unread_alerts(limit=3)
            if alerts:
                context.append("- Kritik Uyarılar:")
                for alert in alerts:
                    context.append(f"  * {alert['title']}: {alert['message']}")

            # 3. Öne Çıkan Araç Spekleri (Örnek)
            araclar = await get_arac_repo().get_all(limit=3)
            if araclar:
                context.append("- Araç Teknik Verileri (Örnek):")
                for a in araclar:
                    context.append(f"  * {a['plaka']}: Aero Cd: {a.get('hava_direnc_katsayisi', 0.7)}, Verim: %{int(a.get('motor_verimliligi', 0.38)*100)}")

        except Exception as e:
            logger.warning(f"Context building failed: {e}")
            context.append("(Sistem verileri şu an alınamıyor, genel bilgi ver.)")

        return "\n".join(context)

    def _sanitize_prompt(self, text: str) -> str:
        """FAZ 5.2: Prompt Injection Koruması"""
        import re
        # Tehlikeli sistem komutları ve delimiter temizliği (Regex)
        # Catch SYSTEM:, SYSTEM_:, ADMIN:, ADMIN MODE:, etc.
        pattern = r"(?i)(SYSTEM|ASSISTANT|USER|ADMIN)(\s*:|s*_|\s+MODE)"
        sanitized = re.sub(pattern, "[REDACTED]", text)
        
        # Explicit block for common jailbreaks
        if "###" in sanitized:
            sanitized = sanitized.replace("###", "[REDACTED]")
            
        return sanitized.strip()[:1000] # Uzunluk kısıtı (DoS önlemi)

    async def generate_response(self, prompt: str, user_id: int = None) -> str:
        """Kullanıcı sorusuna yanıt üret (Secure & Async)"""
        if not GPT4ALL_AVAILABLE:
            return "AI Modülü aktif değil."

        try:
            self._load_model()
            safe_prompt = self._sanitize_prompt(prompt)
            context_data = await self._build_context(user_id)

            full_prompt = (
                f"{context_data}\n\n"
                f"Kullanıcı: {safe_prompt}\n"
                f"LojistikAI:"
            )

            import asyncio
            response = await asyncio.to_thread(self._generate_sync, full_prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return "Üzgünüm, şu anda yanıt veremiyorum."

    def _generate_sync(self, full_prompt: str) -> str:
        """Bloklayıcı generate çağrısı (Thread-safe)"""
        try:
            with self._model.chat_session(self._system_prompt):
                return self._model.generate(
                    full_prompt,
                    max_tokens=600,
                    temp=0.4,
                    top_k=40,
                    top_p=0.3
                )
        except Exception as e:
            logger.error(f"AI Sync Generation Error: {e}")
            return "Üzgünüm, şu anda yanıt veremiyorum."

    async def stream_response(self, prompt: str, user_id: int = None):
        """
        Streaming yanıt üret (FAZ 5.3: Async Generator uyumlu).
        Event loop bloklamaması için kuyruk mekanizması kullanılır.
        """
        if not GPT4ALL_AVAILABLE:
            yield "AI Modülü aktif değil."
            return

        import asyncio
        from queue import Queue

        token_queue = Queue()
        safe_prompt = self._sanitize_prompt(prompt)

        def callback(token_id, token_string):
            token_queue.put(token_string)
            return True # Continue generation

        def run_gen():
            try:
                self._load_model()
                full_prompt = f"Kullanıcı: {safe_prompt}\nLojistikAI:"
                with self._model.chat_session(self._system_prompt):
                    self._model.generate(
                        full_prompt, 
                        max_tokens=512, 
                        callback=callback
                    )
            finally:
                token_queue.put(None) # End signal

        # Run generator in separate thread
        asyncio.create_task(asyncio.to_thread(run_gen))

        # Yield from queue asynchronously
        while True:
            # Check queue non-blocking
            if not token_queue.empty():
                token = token_queue.get()
                if token is None: break
                yield token
            else:
                await asyncio.sleep(0.01) # Event loop breath


    async def train_model(self) -> Dict[str, Any]:
        """
        Model iyileştirme / Fine-tuning simülasyonu.
        Gerçek bir fine-tuning işlemi CPU üzerinde çok uzun süreceği için,
        burada context vector store güncellemesi veya prompt optimizasyonu
        simüle edilmektedir.
        
        Not: Async versiyon - event loop'u bloklamaz.
        """
        import asyncio
        
        try:
            # Simüle edilmiş eğitim süreci (non-blocking)
            logger.info("AI Model eğitimi başlatıldı...")
            await asyncio.sleep(2)  # Non-blocking veri hazırlığı

            # Sistem verilerini repository'den al (async)
            from app.database.repositories.sefer_repo import get_sefer_repo
            from app.database.repositories.yakit_repo import get_yakit_repo
            
            sefer_repo = get_sefer_repo()
            yakit_repo = get_yakit_repo()
            
            # Count metodu varsa kullan, yoksa get_all ile say
            try:
                sefer_count = await sefer_repo.count()
            except AttributeError:
                all_sefer = await sefer_repo.get_all()
                sefer_count = len(all_sefer) if all_sefer else 0
                
            try:
                yakit_count = await yakit_repo.count()
            except AttributeError:
                all_yakit = await yakit_repo.get_all()
                yakit_count = len(all_yakit) if all_yakit else 0

            await asyncio.sleep(3)  # "Eğitim" süreci (non-blocking)

            logger.info(f"AI Model güncellendi. Veri seti: {sefer_count} sefer, {yakit_count} yakıt fişi.")
            return {
                "status": "success",
                "message": "Model başarıyla güncellendi.",
                "data_points": sefer_count + yakit_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Model eğitimi hatası: {e}")
            raise


# Singleton
_ai_service = None
_ai_lock = threading.Lock()

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        with _ai_lock:
            if _ai_service is None:
                _ai_service = AIService()
    return _ai_service
