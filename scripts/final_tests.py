"""
LojiNext AI Backend - Final Test Suite
Otomatik API testleri - CRUD, Algoritma, AI

Kullanım: python scripts/final_tests.py
"""
import asyncio
import httpx
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000/api/v1"
RESULTS = {"passed": 0, "failed": 0, "tests": []}

async def test_endpoint(client, method, url, data=None, expected_status=200, name=""):
    """Generic endpoint tester"""
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{url}")
        elif method == "POST":
            response = await client.post(f"{BASE_URL}{url}", json=data)
        elif method == "PUT":
            response = await client.put(f"{BASE_URL}{url}", json=data)
        elif method == "DELETE":
            response = await client.delete(f"{BASE_URL}{url}")
        
        success = response.status_code == expected_status
        result = {
            "name": name,
            "method": method,
            "url": url,
            "status": response.status_code,
            "expected": expected_status,
            "passed": success,
            "response": response.json() if response.status_code < 400 else response.text[:200]
        }
        RESULTS["tests"].append(result)
        if success:
            RESULTS["passed"] += 1
            print(f"✅ {name}")
        else:
            RESULTS["failed"] += 1
            print(f"❌ {name} - Got {response.status_code}, expected {expected_status}")
        return response.json() if success and response.status_code < 300 else None
    except Exception as e:
        RESULTS["failed"] += 1
        RESULTS["tests"].append({"name": name, "error": str(e), "passed": False})
        print(f"❌ {name} - Error: {e}")
        return None

async def run_tests():
    print("\n" + "="*60)
    print("🧪 LojiNext AI Backend - Final Test Suite")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # =============== 11.2 CRUD Tests ===============
        print("📝 11.2: CRUD Endpoint Testleri\n" + "-"*40)
        
        # Vehicles
        vehicle_data = {
            "plaka": "34 TEST 001",
            "marka": "Mercedes",
            "model": "Actros",
            "yil": 2022,
            "tank_kapasitesi": 600,
            "hedef_tuketim": 30.0
        }
        vehicle = await test_endpoint(client, "POST", "/vehicles/", vehicle_data, 200, "Araç Oluşturma")
        await test_endpoint(client, "GET", "/vehicles/", None, 200, "Araç Listeleme")
        
        # Drivers
        driver_data = {
            "ad_soyad": "Test Şoför",
            "telefon": "05551234567",
            "ehliyet_sinifi": "E"
        }
        driver = await test_endpoint(client, "POST", "/drivers/", driver_data, 200, "Şoför Oluşturma")
        await test_endpoint(client, "GET", "/drivers/", None, 200, "Şoför Listeleme")
        
        # Dashboard stats (Reports)
        await test_endpoint(client, "GET", "/reports/dashboard", None, 200, "Dashboard Stats")
        
        # =============== 11.3 Prediction Algorithm ===============
        print("\n🧮 11.3: Yakıt Tahmin Algoritma Testi\n" + "-"*40)
        
        if vehicle and driver:
            prediction_data = {
                "arac_id": vehicle.get("id", 1),
                "mesafe_km": 300,
                "ton": 20,
                "ascent_m": 500,
                "descent_m": 200,
                "sofor_id": driver.get("id", 1)
            }
            prediction = await test_endpoint(client, "POST", "/predictions/predict", prediction_data, 200, "Yakıt Tahmini")
            
            if prediction:
                print(f"   📊 Tahmin: {prediction.get('tahmini_tuketim', 'N/A')} L")
                print(f"   📊 Model: {prediction.get('model_used', 'N/A')}")
        
        # =============== 11.4 Physics Engine ===============
        print("\n⚙️ 11.4: Fizik Motoru Testi\n" + "-"*40)
        
        # Locations için route analizi
        loc_data = {
            "cikis_yeri": "İstanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450,
            "tahmini_sure_saat": 5.5,
            "zorluk": "Normal"
        }
        location = await test_endpoint(client, "POST", "/locations/", loc_data, 200, "Lokasyon Oluşturma")
        await test_endpoint(client, "GET", "/locations/", None, 200, "Lokasyon Listeleme")
        
        # =============== 11.5 AI Tests ===============
        print("\n🤖 11.5: AI Chat ve Öğrenme Testi\n" + "-"*40)
        
        # AI Chat - Basit soru (field: message)
        chat_data = {"message": "Merhaba, filo durumumuz nasıl?"}
        ai_response = await test_endpoint(client, "POST", "/ai/chat", chat_data, 200, "AI Chat - Basit Soru")
        if ai_response:
            response_text = ai_response.get("response", "")[:200]
            print(f"   💬 AI Yanıt: {response_text}...")
        
        # AI Status Check
        await test_endpoint(client, "GET", "/ai/status", None, 200, "AI Status Control")
        
        # =============== Summary ===============
        print("\n" + "="*60)
        print("📊 TEST SONUÇLARI")
        print("="*60)
        print(f"✅ Başarılı: {RESULTS['passed']}")
        print(f"❌ Başarısız: {RESULTS['failed']}")
        print(f"📈 Başarı Oranı: {RESULTS['passed']/(RESULTS['passed']+RESULTS['failed'])*100:.1f}%")
        print("="*60 + "\n")
        
        # Save results
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(RESULTS, f, ensure_ascii=False, indent=2)
        print("📁 Sonuçlar test_results.json dosyasına kaydedildi.\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
