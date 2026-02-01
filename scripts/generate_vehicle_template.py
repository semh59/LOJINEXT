
import pandas as pd
import os

def generate_vehicle_template():
    # ExcelService'deki kolon isimlerine uygun olarak
    columns = ["plaka", "marka", "model", "yil", "tank_kapasitesi", "bos_agirlik_kg", "motor_verimliligi"]
    
    data = [
        ["34ABC123", "Mercedes", "Actros", 2023, 600, 8000.0, 0.38],
        ["06DEF456", "Volvo", "FH16", 2022, 700, 8500.0, 0.36],
        ["35GHI789", "Scania", "R500", 2024, 650, 8200.0, 0.37]
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Hedef dizini kontrol et
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "arac_sablon.xlsx")
    
    # Excel olarak kaydet
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"Şablon başarıyla oluşturuldu: {output_path}")

if __name__ == "__main__":
    generate_vehicle_template()
