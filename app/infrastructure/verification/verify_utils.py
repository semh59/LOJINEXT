"""
Verification Scripts için ortak utility modülü.

Özellikler:
- Standart argparse (--json, --verbose, --timeout, --retries, --dry-run, --checks, --env)
- Signal handling (graceful shutdown)
- Configurable timeout ve retry
- JSON ve human-readable output
- Uygun exit code'lar
"""

import argparse
import json
import signal
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_INTERRUPTED = 130  # Standard Unix: 128 + SIGINT(2)
EXIT_TIMEOUT = 124


@dataclass
class CheckResult:
    """Tek bir kontrol sonucunu temsil eder."""

    name: str
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    skipped: bool = False
    retry_count: int = 0


class TimeoutError(Exception):
    """Özel timeout exception."""

    pass


class VerificationRunner:
    """
    Standardize edilmiş çıktı ve argüman yönetimi sağlayan doğrulama koşucusu.

    Özellikler:
    - Signal handling (SIGINT, SIGTERM)
    - Configurable timeout ve retry
    - JSON ve human-readable output
    - Selective check running
    - Dry-run modu
    - Environment support
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.results: List[CheckResult] = []
        self.start_time = time.time()
        self._interrupted = False
        self._interrupt_signal: Optional[int] = None  # Signal thread-safety için
        self._available_checks: Set[str] = set()

        # Argparse setup
        self.parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Örnekler:
  %(prog)s                     # Tüm kontrolleri çalıştır
  %(prog)s --json              # JSON formatında çıktı ver
  %(prog)s --dry-run           # Destructive operasyonları atla
  %(prog)s --checks ai,db      # Sadece belirli kontrolleri çalıştır
  %(prog)s --env prod          # Production ortamı için çalıştır
  %(prog)s --timeout 60        # 60 saniye global timeout
  %(prog)s --retries 3         # Başarısız check'ler için 3 retry
  
Exit Codes:
  0   - Tüm kontroller başarılı
  1   - Bir veya daha fazla kontrol başarısız
  124 - Timeout
  130 - SIGINT ile durduruldu (Ctrl+C)
""",
        )
        self.parser.add_argument(
            "--json", action="store_true", help="Çıktıyı JSON formatında ver"
        )
        self.parser.add_argument(
            "--verbose", action="store_true", help="Detaylı çıktı göster"
        )
        self.parser.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Global timeout (saniye), varsayılan: 300",
        )
        self.parser.add_argument(
            "--retries",
            type=int,
            default=0,
            help="Başarısız check'ler için retry sayısı, varsayılan: 0",
        )
        self.parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Destructive operasyonları atla (simülasyon modu)",
        )
        self.parser.add_argument(
            "--checks",
            type=str,
            default=None,
            help="Virgülle ayrılmış check listesi (örn: ai,weather,db)",
        )
        self.parser.add_argument(
            "--env",
            type=str,
            default="dev",
            choices=["dev", "staging", "prod"],
            help="Ortam belirle, varsayılan: dev",
        )
        self.args = self.parser.parse_args()

        # Signal handlers setup
        self._setup_signal_handlers()

        # Header yazdır
        if not self.args.json:
            self._print_header()

    def _setup_signal_handlers(self):
        """SIGINT ve SIGTERM için graceful shutdown handler'ları.

        NOT: Signal handler içinde IO yapmak tehlikelidir (reentrant değil).
        Sadece flag set edip, mesajı main loop'a bırakıyoruz.
        """

        def signal_handler(signum, frame):
            self._interrupted = True
            self._interrupt_signal = signum
            # IO işlemini main thread'e bırak - signal handler içinde print güvensiz

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _check_interrupted_message(self):
        """Interrupt olduysa mesaj yazdırır (main thread'den çağrılacak)."""
        if (
            self._interrupted
            and self._interrupt_signal is not None
            and not self.args.json
        ):
            sig_name = (
                "SIGINT" if self._interrupt_signal == signal.SIGINT else "SIGTERM"
            )
            print(f"\n⚠️  {sig_name} alındı. Graceful shutdown...")
            self._interrupt_signal = None  # Tekrar yazdırmamak için

    def _print_header(self):
        """Verification başlığını yazdırır."""
        print("=" * 50)
        print(f"🔍 {self.name}")
        print(f"📋 {self.description}")
        if self.args.dry_run:
            print("🔒 DRY-RUN MODU: Destructive operasyonlar atlanacak")
        if self.args.checks:
            print(f"🎯 Seçili kontroller: {self.args.checks}")
        print(f"🌐 Ortam: {self.args.env}")
        print("=" * 50)

    def register_check(self, name: str):
        """Kullanılabilir check'i kaydet (selective running için)."""
        self._available_checks.add(name.lower())

    def should_run_check(self, name: str) -> bool:
        """Bu check çalıştırılmalı mı?"""
        # Interrupt mesajını main thread'de yazdır
        self._check_interrupted_message()

        if self._interrupted:
            return False
        if self.args.checks is None:
            return True
        selected = [c.strip().lower() for c in self.args.checks.split(",")]
        return name.lower() in selected

    @property
    def is_dry_run(self) -> bool:
        """Dry-run modunda mı?"""
        return self.args.dry_run

    @property
    def is_interrupted(self) -> bool:
        """Interrupted durumda mı?"""
        return self._interrupted

    def add_result(
        self,
        name: str,
        success: bool,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        skipped: bool = False,
        retry_count: int = 0,
    ):
        """Kontrol sonucu ekle."""
        result = CheckResult(
            name=name,
            success=success,
            message=message,
            details=details or {},
            duration=duration,
            skipped=skipped,
            retry_count=retry_count,
        )
        self.results.append(result)

        if not self.args.json:
            if skipped:
                status = "⏭️"
            elif success:
                status = "✅"
            else:
                status = "❌"

            duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
            retry_str = f" [retry: {retry_count}]" if retry_count > 0 else ""
            print(f"{status} {name}: {message}{duration_str}{retry_str}")

            if self.args.verbose and details:
                print(f"   📊 Details: {details}")

    def add_skipped(self, name: str, reason: str):
        """Atlanan check için sonuç ekle."""
        self.add_result(name, True, f"Skipped: {reason}", skipped=True)

    def run_with_timeout(
        self, func: Callable, timeout: Optional[int] = None, *args, **kwargs
    ) -> Any:
        """Fonksiyonu timeout ile çalıştır (sync fonksiyonlar için).

        NOT: Daemon thread kullanılır - timeout aşılırsa thread
        process bitene kadar arka planda kalır.
        """
        timeout = timeout or self.args.timeout
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        # Daemon thread - process bitince otomatik kapanır
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            # Thread hala çalışıyor - daemon olduğu için process bitince kapanacak
            raise TimeoutError(
                f"İşlem {timeout} saniye içinde tamamlanamadı (thread arka planda bırakıldı)"
            )

        if exception[0]:
            raise exception[0]

        return result[0]

    def run_with_retry(
        self, func: Callable, name: str, retries: Optional[int] = None, *args, **kwargs
    ) -> tuple:
        """Fonksiyonu retry ile çalıştır."""
        retries = retries if retries is not None else self.args.retries
        last_error = None

        for attempt in range(retries + 1):
            try:
                result = func(*args, **kwargs)
                return result, attempt
            except Exception as e:
                last_error = e
                if attempt < retries and not self.args.json:
                    print(f"   ⟳ {name}: Retry {attempt + 1}/{retries}...")
                    time.sleep(1)  # Retry öncesi kısa bekleme

        raise last_error

    def finalize(self):
        """
        Özet raporu yazdırır ve uygun exit code ile çıkar.
        """
        total_duration = time.time() - self.start_time
        success_count = sum(1 for r in self.results if r.success and not r.skipped)
        fail_count = sum(1 for r in self.results if not r.success)
        skip_count = sum(1 for r in self.results if r.skipped)

        if self.args.json:
            self._finalize_json(total_duration, success_count, fail_count, skip_count)
        else:
            self._finalize_human(total_duration, success_count, fail_count, skip_count)

        # Exit code belirle
        if self._interrupted:
            sys.exit(EXIT_INTERRUPTED)
        elif fail_count > 0:
            sys.exit(EXIT_FAILURE)
        sys.exit(EXIT_SUCCESS)

    def _finalize_json(
        self,
        total_duration: float,
        success_count: int,
        fail_count: int,
        skip_count: int,
    ):
        """JSON formatında özet rapor."""
        import decimal

        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, decimal.Decimal):
                    return float(obj)
                return super(DecimalEncoder, self).default(obj)

        report = {
            "name": self.name,
            "environment": self.args.env,
            "dry_run": self.args.dry_run,
            "interrupted": self._interrupted,
            "total_duration": round(total_duration, 2),
            "total": len(self.results),
            "success": success_count,
            "failed": fail_count,
            "skipped": skip_count,
            "results": [asdict(r) for r in self.results],
        }
        print(json.dumps(report, indent=2, ensure_ascii=False, cls=DecimalEncoder))

    def _finalize_human(
        self,
        total_duration: float,
        success_count: int,
        fail_count: int,
        skip_count: int,
    ):
        """Human-readable özet rapor."""
        print("\n" + "=" * 50)
        print(f"🏁 FINAL REPORT: {self.name}")
        print("-" * 50)
        print(
            f"📊 Total: {len(self.results)} | "
            f"✅ Success: {success_count} | "
            f"❌ Failed: {fail_count} | "
            f"⏭️ Skipped: {skip_count}"
        )
        print(f"⏱️  Total Duration: {total_duration:.2f}s")

        if self._interrupted:
            print("⚠️  Execution was interrupted")

        if fail_count > 0:
            print("\n🔴 Failed Checks:")
            for r in self.results:
                if not r.success:
                    print(f"   - {r.name}: {r.message}")

        print("=" * 50)


def print_section(title: str):
    """Bölüm başlıklarını standartlaştırır."""
    print("\n" + "=" * 40)
    print(title)
    print("=" * 40)


@contextmanager
def safe_db_operation(runner: VerificationRunner, operation_name: str):
    """
    Güvenli DB operasyonu context manager'ı.
    Dry-run modunda operasyonları atlar.
    """
    if runner.is_dry_run:
        if not runner.args.json:
            print(f"   🔒 DRY-RUN: {operation_name} atlandı")
        yield False  # Operasyon çalıştırılmadı
    else:
        yield True  # Operasyon çalıştırılabilir
