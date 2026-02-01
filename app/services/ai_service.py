try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

import os
import threading
import time
import urllib.request

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SecurityError(Exception):
    """Güvenlik ihlali hatası"""
    pass

class LocalAIService:
    _instance = None
    _instance_lock = threading.Lock()
    _model = None
    _download_status = {"status": "idle", "percent": 0.0, "speed": "0 KB/s"}

    @classmethod
    def get_progress(cls):
        return cls._download_status

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(LocalAIService, cls).__new__(cls)
                    cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """
        Initialize the Local LLM. Downloads if not present.
        """
        if not Llama:
            logger.warning("llama-cpp-python not installed. AI features disabled.")
            return

        settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = settings.MODEL_DIR / settings.AI_MODEL_NAME

        if not model_path.exists():
            logger.info(f"Model not found at {model_path}. Downloading...")
            try:
                self._download_model(str(model_path))
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                self._download_status["status"] = "error"
                return
        else:
            # GÜVENLİK: Mevcut modelin bütünlüğünü doğrula
            if not self._verify_model_checksum(str(model_path)):
                logger.warning("Existing model checksum failed! Deleting and redownloading...")
                model_path.unlink()
                try:
                    self._download_model(str(model_path))
                except Exception as e:
                    logger.error(f"Failed to redownload model: {e}")
                    self._download_status["status"] = "error"
                    return


        try:
            # Context window 4096'ya çıkarıldı (modern GGUF modelleri için ideal)
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=4096,
                n_threads=4,
                n_gpu_layers=0, # CPU-only default, if GPU available change to -1
                verbose=False
            )
            logger.info(f"Local AI Model loaded: {settings.AI_MODEL_NAME} (ctx: 4096)")
            self._download_status["status"] = "ready"
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._download_status["status"] = "error"

    def _verify_model_checksum(self, path: str) -> bool:
        """Model dosyasının SHA256 checksum'ını doğrula"""
        import hashlib
        expected_hash = os.getenv("AI_MODEL_SHA256", "")
        if not expected_hash:
            logger.warning("AI_MODEL_SHA256 env not set, skipping checksum verification")
            return True  # Hash tanımlı değilse atla (geliştirme ortamı)
        
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        actual_hash = sha256.hexdigest()
        if actual_hash != expected_hash:
            logger.error(f"Model checksum mismatch! Expected {expected_hash[:16]}..., got {actual_hash[:16]}...")
            return False
        
        logger.info("Model checksum verified successfully")
        return True

    # GÜVENLİK: İzin verilen model domain'leri (tam eşleşme)
    TRUSTED_DOMAINS = frozenset([
        "huggingface.co",
        "gpt4all.io",
        "ollama.ai",
    ])
    
    def _validate_model_url(self, url: str) -> bool:
        """
        Model URL'i güvenilir domain listesiyle doğrula (Secure).
        
        Subdomain spoofing ve HTTP downgrade saldırılarını engeller.
        Örnek: https://huggingface.co.evil.com/ engellenir.
        """
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            
            # HTTPS zorunlu (HTTP downgrade engelleme)
            if parsed.scheme != "https":
                logger.warning(f"Model URL HTTPS değil: {url}")
                return False
            
            # Tam domain eşleşmesi (subdomain spoofing engellenir)
            domain = parsed.netloc.lower()
            
            # www prefix'i kaldır
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Port varsa kaldır
            if ":" in domain:
                domain = domain.split(":")[0]
            
            if domain not in self.TRUSTED_DOMAINS:
                logger.warning(f"Güvenilmeyen domain: {domain}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    def _download_model(self, dest_path: str):
        """Model indir - URL whitelist ve zorunlu checksum ile güvenli"""
        # GÜVENLİK: URL Whitelist kontrolü
        model_url = settings.AI_MODEL_URL
        if not self._validate_model_url(model_url):
            logger.error(f"Güvenilmeyen model URL reddedildi: {model_url}")
            self._download_status["status"] = "error"
            raise SecurityError(f"Model URL güvenilir listede değil: {model_url}")
        
        # GÜVENLİK: Checksum kontrolü zorunlu
        expected_hash = os.getenv("AI_MODEL_SHA256")
        if not expected_hash:
            logger.error("AI_MODEL_SHA256 environment variable ZORUNLUDUR!")
            self._download_status["status"] = "error"
            raise SecurityError("AI_MODEL_SHA256 env tanımlanmadı. Model indirme iptal.")
        
        start_time = time.time()
        
        def reporthook(blocknum, blocksize, totalsize):
            read_so_far = blocknum * blocksize
            if totalsize > 0:
                percent = min(100.0, read_so_far * 100 / totalsize)
                elapsed = time.time() - start_time
                speed = (read_so_far / 1024) / max(1, elapsed) # KB/s
                
                self._download_status.update({
                    "status": "downloading",
                    "percent": round(percent, 1),
                    "speed": f"{speed:.1f} KB/s" if speed < 1024 else f"{speed/1024:.1f} MB/s"
                })

        logger.info(f"Model indiriliyor: {model_url}")
        urllib.request.urlretrieve(model_url, dest_path, reporthook)
        
        # Checksum doğrulama
        if not self._verify_model_checksum(dest_path):
            os.remove(dest_path)
            self._download_status["status"] = "error"
            raise ValueError("Model checksum verification failed! Download aborted.")
        
        self._download_status["status"] = "ready"
        self._download_status["percent"] = 100.0

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: str = "TIR yakıt ve lojistik uzmanısın.",
        max_tokens: int = 512
    ) -> str:
        """
        AI yanıtı üret (Context Guard ile).
        """
        import asyncio
        if not self._model:
            return "AI sistemi şu an çevrimdışı."

        # Guard: Context window taşma kontrolü (Basit karakter tahmini)
        # 1 token ~= 4 karakter (Türkçe için kabaca)
        estimated_tokens = (len(prompt) + len(system_prompt)) // 3
        if estimated_tokens > 3500:
            logger.warning("Context length guard triggered! Truncating prompt.")
            prompt = prompt[:10000] # Çok uzunsa kırp

        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        output = await asyncio.to_thread(
            self._model,
            formatted_prompt,
            max_tokens=max_tokens,
            stop=["<|im_end|>", "<|endoftext|>"],
            echo=False,
            temperature=0.3 # Daha deterministik teknik analizler için
        )

        return output['choices'][0]['text'].strip()

    async def analyze_consumption(self, trip_data: dict) -> str:
        """
        Fizik motoru ve PIML kalibrasyonu ile teknik tüketim analizi.
        """
        prompt = (
            f"Sefer Teknik Analizi:\n"
            f"- Mesafe: {trip_data.get('mesafe_km')} km\n"
            f"- Yük: {trip_data.get('ton')} ton\n"
            f"- Ölçülen Tüketim: {trip_data.get('tuketim')} L/100km\n"
            f"- Rota: {trip_data.get('cikis_yeri')} → {trip_data.get('varis_yeri')}\n"
            f"\nBu verileri aracın teknik spesifikasyonları ve hava direnci faktörleri (PIML) ile analiz et."
            f"Anomali var mı? Sürücü performansı nasıl?"
        )
        return await self.generate_response(prompt, max_tokens=1024)
