import urllib.request
import json
from pathlib import Path

def download_sample():
    print("Iniciando descarga de muestra de MeetingBank-transcript...")
    url = "https://datasets-server.huggingface.co/rows?dataset=lytang/MeetingBank-transcript&config=default&split=train&offset=0&limit=2"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        rows = data.get("rows", [])
        if not rows:
            print("No se encontraron filas en la respuesta.")
            return
            
        test_data_dir = Path(__file__).resolve().parent / "test_data"
        test_data_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, row_item in enumerate(rows):
            row = row_item.get("row", {})
            meeting_id = row.get("meeting_id", f"sample_{idx}")
            source = row.get("source", "")
            reference = row.get("reference", "")
            city = row.get("city", "Unknown")
            
            # Guardar la transcripción (source)
            transcript_file = test_data_dir / f"{meeting_id}_transcript.txt"
            transcript_file.write_text(source, encoding="utf-8")
            
            # Guardar la referencia/resumen (reference)
            ref_file = test_data_dir / f"{meeting_id}_reference.txt"
            ref_file.write_text(reference, encoding="utf-8")
            
            print(f"Descargada muestra {idx+1}: {meeting_id} ({city})")
            print(f"  Transcripción guardada en: {transcript_file.name}")
            print(f"  Referencia guardada en: {ref_file.name}")
            
    except Exception as e:
        print(f"Error al descargar la muestra: {e}")

if __name__ == "__main__":
    download_sample()
