# Türkçe ve İngilizce AI metin dedektörü

## GitHub kopyasını kullanma

Depoda uygulama, eğitim kodu, model ayarları ve değerlendirme raporları bulunur. Yeni bir kopyada analiz çalıştırmak için Python ortamını kurup `requirements.txt` paketlerini yükle ve eğitimli V2 ağırlık dosyasını `models/detector_v2/xlmr/model.safetensors` yoluna yerleştir. V1 ve V3 için ilgili sürümün ağırlık dosyasını kendi `xlmr` klasörüne koy. Eğitimi tekrarlamak için ayrıca `data` klasöründeki kaynak notlarında açıklanan JSONL veri dosyaları gerekir. Ağırlıklar ve veri kümeleri yerel proje kopyasında tutulur.

## Web arayüzü

Proje klasöründe PowerShell açıp yerel sunucuyu başlat:

```powershell
.\.venv\Scripts\python.exe .\app.py
```

Tarayıcıda [Metin Dedektörü](http://127.0.0.1:8765) adresini aç. En az 50 sözcüklük Türkçe veya İngilizce bir metin yapıştır, örnek metin seç veya **Dosya yükle** düğmesini kullan. TXT ve Markdown (`.md`, `.markdown`) dosyaları UTF-8 olarak okunur. PDF, Word (`.docx`), Excel (`.xlsx`, `.xls`) ve PowerPoint (`.pptx`) dosyalarından metin yerel olarak çıkarılır. Bu belgeler için boyut sınırı 20 MB, düzenleme alanı için 100.000 karakterdir.

Excel’de görünür çalışma sayfalarındaki metin hücreleri satır satır okunur. PowerPoint’te başlıklar, metin kutuları ve tablolar slayt sırasıyla okunur. Taranmış PDF’lere önce OCR ile metin tanıma uygula.

Yüklenen metni kontrol edip **Metni analiz et** düğmesine bas. İlk analizde v2 modeli belleğe yüklenir. Sonuçtaki AI skoru 0–100 ölçeğindedir. Sunucuyu durdurmak için terminalde Ctrl+C kullan. Port doluysa `app.py --port 8766` ile başka bir port seçebilirsin.

## Metin analizi

Proje klasöründe PowerShell aç. `--file` ile arayüzde desteklenen dosya biçimlerinden herhangi birinin yolunu verebilirsin. Aşağıdaki örnek için kendi metnini `metin.txt` adıyla kaydet.

```powershell
.\.venv\Scripts\python.exe .\detector.py --file .\metin.txt
```

Hazır model `models/detector_v2` klasöründen yüklenir. İnternet bağlantısı gerekmez. Aynı komutta `--file` yerine `--text "…"` ile metni doğrudan verebilirsin. En az 50 sözcük gerekir. Analiz metnin tamamını sırayla, çakışmayan 50 sözcüklük parçalara böler. Örneğin 251 sözcükte beş tam parça ve bir sözcüklük son parça değerlendirilir. Bir parçanın modele sığmayan bölümü de ayrı bir geçişte incelenir. Parça sonuçları sözcük sayısına göre ağırlıklandırılır ve birleşik skora kalibrasyon uygulanır.

`word_count` incelenen sözcük sayısını, `windows` sözcük parçalarının sayısını verir. `ai_score` model skorudur. `threshold` karar eşiğini, `label` bu eşiğe göre seçilen sınıfı gösterir. Kaydedilmiş başarı ölçümleri modelin eğitildiği dönemdeki örnekleme yöntemine aittir. Eski sürümü aynı metinle karşılaştırmak için komuta `--model-dir .\models\detector_v1` ekle.

Python içinden kullanım:

```python
from pathlib import Path
from detector import Detector

model = Detector()
metin = Path("metin.txt").read_text(encoding="utf-8-sig")
print(model.predict(metin))
```

## Eğitim ve ölçüm

### Genişletilmiş veri seti ve V3

[V3 veri seti](data/detector_v3_40781.jsonl) toplam 40.781 Türkçe ve İngilizce kayıt içerir. [15.781 yeni örnek ve kaynakları](data/GERCEK_YASAM_V3_KAYNAKLAR.md) arasında ürün ve film yorumları, tarifler, forum ve anlatı metinleri vardır. [V3 model kartında](models/detector_v3/MODEL_KARTI.md) V2 ile aynı metinler üzerinde yapılan karşılaştırma yer alır.

V3, bağımsız otel yorumlarında daha fazla AI metni yakaladı ancak insan yorumlarını daha sık yanlış işaretledi. Genel kullanımda varsayılan sürüm V2’dir. V3’ü denemek için aşağıdaki komutlardan birini kullan:

```powershell
.\.venv\Scripts\python.exe .\detector.py --model-dir .\models\detector_v3 --file .\metin.txt
.\.venv\Scripts\python.exe .\app.py --model-version v3 --port 8766
```

İkinci komut V3 arayüzünü [8766 portunda](http://127.0.0.1:8766) sunar. V3 eğitimini tekrar etmek için boş çıktı klasörüyle `train_detector.py --dataset v3 --output .\models\v3_tekrar` kullan. Kaynak dosyaları ve eski ayırımlar eğitim betiği tarafından okunur.

### V2 eğitimi

Bu bilgisayardaki proje ortamı Python 3.11 ve CUDA 12.8 destekli PyTorch ile hazırlandı. Yeni bir ortamda önce donanımına uygun PyTorch 2.8.0 sürümünü, ardından `requirements.txt` içindeki paketleri kur. Eğitim komutu iki modeli karşılaştırır. Yeni bir çıktı klasörü kullan:

```powershell
.\.venv\Scripts\python.exe .\train_detector.py --dataset v2 --output .\models\tekrar
```

V2 için [insan veri seti](data/human_texts_v2_15000.jsonl) 5.000 Türkçe ve 10.000 İngilizce metin içerir. İngilizce bölümündeki tüm metinler forum gönderileri veya kullanıcı yorumlarıdır. [Yeni kayıtlar ve tarih grupları](data/INGILIZCE_MAKALE_DISI_KAYNAKLAR.md)

Eğitim kodu aynı 15.000 insan kaydını eski dosyanın Türkçe bölümünden ve İngilizce ek dosyasından okur; 10.000 AI kaydını da ekler. Önceki veri ayrımlarını korumak için `models/detector_v1/splits.jsonl` kullanılır. İngilizce akademik metinler v2 eğitimine ve model seçimine girmez. Model girdisi yalnızca metindir. Tarih ve kaynak bilgisi veri ayrımında veya eğitim ağırlıklarında kullanılır. Temel XLM-RoBERTa ağırlıkları yerel önbellekte yoksa eğitim kodu aynı sabit sürümü Hugging Face üzerinden yükler.

[V2 model kartı](models/detector_v2/MODEL_KARTI.md) · [V2 iç test sonuçları](models/detector_v2/metrics.json) · [V2 bağımsız otel yorumu testi](models/detector_v2/external_test.json) · [V1 model kartı](models/detector_v1/MODEL_KARTI.md)
