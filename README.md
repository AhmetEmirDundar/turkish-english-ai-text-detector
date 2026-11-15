# Türkçe ve İngilizce AI metin dedektörü

Web arayüzü analiz metnini [Hugging Face Space](https://huggingface.co/spaces/AhmetEmirDundar/ai-text-detector) üzerindeki modele gönderir. Site Vercel üzerinde yayınlanır. İlk analiz Space'in uyanmasını bekleyebilir.

## Yerel arayüz

```powershell
python -m pip install -r requirements.txt
python .\app.py
```

Arayüzü `http://127.0.0.1:8765` adresinde aç. En az 50 sözcük gerekir. TXT, Markdown, PDF, Word, Excel ve PowerPoint dosyalarından metin çıkarabilir.

## Yerel model

Yerel model V6 dosyalarını kullanır. Ağırlık dosyası (`models/detector_v6/xlmr/model.safetensors`) depoda tutulmaz; yerel analiz için dosyayı bu konuma yerleştir ve `requirements-local.txt` paketlerini kur.

```powershell
python -m pip install -r requirements-local.txt
python .\detector.py --file .\metin.txt
```

## Önemli not

Sonuç olasılıksal bir model tahminidir; tek başına yazarlık kanıtı olarak kullanılmamalıdır. Girilen metin analiz için Hugging Face'e iletilir. Ayrıntılar için sitedeki Gizlilik ve Sınırlamalar sayfalarına bak.
