"""
Backend Services Verification Script.

AI, OpenRouteService, Weather ve Report servislerini doğrular.
Timeout, selective checks ve retry desteği ile.
"""

import asyncio
import os
import sys
import time
from datetime import date, timedelta
from typing import Optional

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.infrastructure.verification.verify_utils import VerificationRunner, print_section
from app.core.services.ai_service import get_ai_service
from app.core.services.openroute_service import OpenRouteService
from app.core.services.report_service import get_report_service
from app.core.services.weather_service import WeatherService
from app.infrastructure.logging.logger import get_logger

logger = get_logger("BackendVerifier")

# Check-specific timeout (saniye)
AI_TIMEOUT = 60
ORS_TIMEOUT = 30
WEATHER_TIMEOUT = 30
REPORT_TIMEOUT = 30


async def verify_ai(runner: VerificationRunner):
    """AI Service (Qwen2.5) doğrulaması."""
    if not runner.should_run_check("ai"):
        runner.add_skipped("AI Service", "Not selected")
        return True
        
    if not runner.args.json:
        print_section("🧠 Verifying AI Service (Qwen2.5)")
    
    start_time = time.time()
    try:
        ai = get_ai_service()
        prompt = "Merhaba, sistemde kaç araç var? Kısa cevap ver."
        
        full_response = ""
        
        # Timeout ile çalıştır
        async def get_response():
            nonlocal full_response
            response_gen = ai.generate_response(prompt)
            if asyncio.iscoroutine(response_gen):
                response_gen = await response_gen

            if hasattr(response_gen, '__aiter__'):
                async for chunk in response_gen:
                    if not runner.args.json:
                        print(chunk, end="", flush=True)
                    full_response += chunk
            else:
                for chunk in response_gen:
                    if not runner.args.json:
                        print(chunk, end="", flush=True)
                    full_response += chunk
        
        try:
            await asyncio.wait_for(get_response(), timeout=AI_TIMEOUT)
        except asyncio.TimeoutError:
            runner.add_result(
                "AI Service", 
                False, 
                f"Timeout ({AI_TIMEOUT}s) - Yanıt alınamadı",
                duration=time.time() - start_time
            )
            return False

        if not runner.args.json:
            print()  # Newline ekle
            
        success = bool(full_response)
        msg = "AI Service Response Received" if success else "Response was empty"
        runner.add_result(
            "AI Service", 
            success, 
            msg, 
            {"response_length": len(full_response)}, 
            time.time() - start_time
        )
        return success
        
    except Exception as e:
        runner.add_result(
            "AI Service", 
            False, 
            f"Failed: {str(e)}", 
            duration=time.time() - start_time
        )
        return False


def verify_ors(runner: VerificationRunner):
    """OpenRouteService doğrulaması."""
    if not runner.should_run_check("ors"):
        runner.add_skipped("OpenRouteService", "Not selected")
        return True
        
    if not runner.args.json:
        print_section("🔗 Verifying OpenRouteService")
    
    start_time = time.time()
    try:
        ors = OpenRouteService()
        if not ors.is_configured():
            runner.add_result(
                "OpenRouteService", 
                True, 
                "Skipped (Not configured - API key missing)",
                {"configured": False},
                duration=time.time() - start_time
            )
            return True

        # Istanbul (Sultanahmet) to Ankara (Kizilay)
        start = (28.9784, 41.0082)
        end = (32.8597, 39.9334)

        result = ors.get_route_profile(start, end)

        if result:
            details = {
                "distance_km": result.distance_km,
                "duration_hours": result.duration_hours,
                "ascent_m": result.ascent_m
            }
            runner.add_result(
                "OpenRouteService", 
                True, 
                f"Route Found: {result.distance_km} km", 
                details, 
                time.time() - start_time
            )
            return True
        else:
            runner.add_result(
                "OpenRouteService", 
                False, 
                "Returned None. Check API Key/Quota.",
                duration=time.time() - start_time
            )
            return False
            
    except Exception as e:
        runner.add_result(
            "OpenRouteService", 
            False, 
            f"Failed: {str(e)}", 
            duration=time.time() - start_time
        )
        return False


async def verify_weather(runner: VerificationRunner):
    """Weather Service (Open-Meteo) doğrulaması."""
    if not runner.should_run_check("weather"):
        runner.add_skipped("Weather Service", "Not selected")
        return True
        
    if not runner.args.json:
        print_section("🌦️ Verifying Weather Service (Open-Meteo)")
    
    start_time = time.time()
    try:
        ws = WeatherService()
        lat, lon = 41.0082, 28.9784  # Istanbul
        
        # Timeout ile çalıştır
        try:
            weather = await asyncio.wait_for(
                ws.get_forecast_analysis(lat, lon),
                timeout=WEATHER_TIMEOUT
            )
        except asyncio.TimeoutError:
            runner.add_result(
                "Weather Service",
                False,
                f"Timeout ({WEATHER_TIMEOUT}s)",
                duration=time.time() - start_time
            )
            return False

        if weather.get('success'):
            runner.add_result(
                "Weather Service", 
                True, 
                f"Impact: {weather.get('fuel_impact_factor')}", 
                weather, 
                time.time() - start_time
            )
            return True
        else:
            runner.add_result(
                "Weather Service", 
                False, 
                f"Data failed: {weather.get('error')}",
                duration=time.time() - start_time
            )
            return False
            
    except Exception as e:
        runner.add_result(
            "Weather Service", 
            False, 
            f"Failed: {str(e)}", 
            duration=time.time() - start_time
        )
        return False


async def verify_reports(runner: VerificationRunner):
    """Report Service doğrulaması."""
    if not runner.should_run_check("reports"):
        runner.add_skipped("Report Service", "Not selected")
        return True
        
    if not runner.args.json:
        print_section("📊 Verifying Report Service")
    
    start_time = time.time()
    try:
        rs = get_report_service()
        
        try:
            summary = await asyncio.wait_for(
                rs.get_dashboard_summary(),
                timeout=REPORT_TIMEOUT
            )
        except asyncio.TimeoutError:
            runner.add_result(
                "Report Service",
                False,
                f"Timeout ({REPORT_TIMEOUT}s)",
                duration=time.time() - start_time
            )
            return False
        
        success = summary.get('toplam_sefer') is not None
        if success:
            runner.add_result(
                "Report Service", 
                True, 
                f"Dashboard OK: {summary['toplam_sefer']} sefer", 
                summary, 
                time.time() - start_time
            )
            return True
        else:
            runner.add_result(
                "Report Service", 
                False, 
                "Dashboard stats missing keys",
                duration=time.time() - start_time
            )
            return False
            
    except Exception as e:
        runner.add_result(
            "Report Service", 
            False, 
            f"Failed: {str(e)}", 
            duration=time.time() - start_time
        )
        return False


async def main():
    runner = VerificationRunner(
        "Backend Verification", 
        "Target: Application Logic & External Services"
    )
    
    # Register available checks
    runner.register_check("ai")
    runner.register_check("ors")
    runner.register_check("weather")
    runner.register_check("reports")
    
    # Run tests with interrupt checks
    if not runner.is_interrupted:
        verify_ors(runner)
    
    if not runner.is_interrupted:
        await verify_weather(runner)
    
    if not runner.is_interrupted:
        await verify_reports(runner)
    
    if not runner.is_interrupted:
        await verify_ai(runner)

    runner.finalize()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
