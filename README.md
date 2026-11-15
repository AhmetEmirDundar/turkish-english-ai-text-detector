# Türkçe ve İngilizce AI metin dedektörü

## GitHub kopyasını kullanma

Depoda uygulama, eğitim kodu, model ayarları ve değerlendirme raporları bulunur. Web arayüzü analiz metnini Hugging Face Space'e iletir; büyük model ağırlıkları Vercel'e yüklenmez. Yerel model eğitimi ve analiz için `requirements-local.txt` paketlerini kurup model ağırlıklarını `models/detector_v6/xlmr/model.safetensors` yoluna yerleştir. Eğitimi tekrarlamak için `data` klasöründeki kaynak notlarında açıklanan JSONL dosyaları da gerekir.

## Web arayüzü

Arayüz, analizleri [Hugging Face Space](https://huggingface.co/spaces/AhmetEmirDundar/ai-text-detector) üzerindeki modele gönderir. İnternet bağlantısı gerekir; Space uykudan uyanıyorsa ilk yanıt gecikebilir. Girilen metin analiz için Hugging Face'e iletilir. Vercel bu siteyi ücretsiz kişisel kullanımda barındırır; analiz servisi Hugging Face Space'te çalışır.

Proje klasöründe PowerShell açıp temel paketleri yükleyerek yerel sunucuyu başlat:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\app.py
```

Tarayıcıda [Metin Dedektörü](http://127.0.0.1:8765) adresini aç. En az 50 sözcüklük Türkçe veya İngilizce bir metin yapıştır, örnek metin seç veya **Dosya yükle** düğmesini kullan. TXT ve Markdown (`.md`, `.markdown`) dosyaları UTF-8 olarak okunur. PDF, Word (`.docx`), Excel (`.xlsx`, `.xls`) ve PowerPoint (`.pptx`) dosyalarından metin yerel olarak çıkarılır. Bu belgeler için boyut sınırı 20 MB, düzenleme alanı için 100.000 karakterdir.

Yerel model analizi, eğitim ve değerlendirme komutları için ek paketleri kur: `python -m pip install -r requirements-local.txt`.

Excel’de görünür çalışma sayfalarındaki metin hücreleri satır satır okunur. PowerPoint’te başlıklar, metin kutuları ve tablolar slayt sırasıyla okunur. Taranmış PDF’lere önce OCR ile metin tanıma uygula.

Yüklenen metni kontrol edip **Metni analiz et** düğmesine bas. İlk istek Hugging Face Space'i uyandırabilir ve bekletebilir. Sonuçtaki AI skoru 0–100 ölçeğindedir. Sunucuyu durdurmak için terminalde Ctrl+C kullan. Port doluysa `app.py --port 8766` ile başka bir port seçebilirsin.

## Metin analizi

Proje klasöründe PowerShell aç. `--file` ile arayüzde desteklenen dosya biçimlerinden herhangi birinin yolunu verebilirsin. Aşağıdaki örnek için kendi metnini `metin.txt` adıyla kaydet.

```powershell
.\.venv\Scripts\python.exe .\detector.py --file .\metin.txt
```

Hazır model `models/detector_v6` klasöründen yüklenir. İnternet bağlantısı gerekmez. Aynı komutta `--file` yerine `--text "…"` ile metni doğrudan verebilirsin. En az 50 sözcük gerekir. Analiz metnin tamamını sırayla, çakışmayan 50 sözcüklük parçalara böler. Örneğin 251 sözcükte beş tam parça ve bir sözcüklük son parça değerlendirilir. Bir parçanın modele sığmayan bölümü de ayrı bir geçişte incelenir. Parça sonuçları sözcük sayısına göre ağırlıklandırılır ve birleşik skora kalibrasyon uygulanır.

`word_count` incelenen sözcük sayısını, `windows` sözcük parçalarının sayısını verir. `ai_score` model skorudur. `threshold` karar eşiğini, `label` bu eşiğe göre seçilen sınıfı gösterir. Kaydedilmiş başarı ölçümleri modelin eğitildiği dönemdeki örnekleme yöntemine aittir. Eski sürümü aynı metinle karşılaştırmak için komuta `--model-dir .\models\detector_v1` ekle.

Python içinden kullanım:

```python
from pathlib import Path
from detector import Detector

model = Detector()
metin = Path("metin.txt").read_text(encoding="utf-8-sig")
print(model.predict(metin))
```

### Destekleyici üslup analizi

Web arayüzü, komut satırı ve API aynı 0–100 ölçeğinde tek skor ve aynı model sürümünün sabit karar eşiğini kullanır (API'de ölçek 0–1). Üslup skoru üretilebildiğinde birleşik skor `(1 − w) × ana skor + w × üslup skoru` formülüyle hesaplanır. Bu ağırlık seçilen sürümde her metin için aynıdır. 50 alfabetik sözcük yoksa, üslup modeli veya kalibre edilmiş ağırlık eksikse ana skor kullanılır.

Eğitim sonunda her sürüm için `w` yalnızca kayıtlı doğrulama ayrımından belirlenir. Türkçe/İngilizce ve insan/AI gruplarından kimliğe göre sıralanmış eşit sayıda kayıt alınır (grup başına en fazla 256). İki model belgelerin tamamını puanlar. Ortalama karesel hatayı en aza indiren ağırlık 0–0,5 aralığında seçilir ve `detector.json` içine kaydedilir. Eğitimli bir sürüm için bu adımı yerel veri dosyalarıyla yeniden çalıştırabilirsin: `python calibrate_fusion.py --model-dir models/detector_v2`.

Yalnızca üslup modelini yeniden eğitmek için yerel eğitim verileriyle `train_detector.py --dataset v2 --style-only --output .\models\uslup_tekrar` çalıştır. Boş çıktı klasörüne `style.json`, ölçüm raporu ve kullanılan veri ayrımları yazılır.

## Eğitim ve ölçüm

### V6 genel yazı verisi

50.000 kayıtlık İngilizce değişiklik deneyi ve 54.000 kayıtlık genel yazı adayı ayrı ayrı eğitilir. V6, kitaplar, haberler, gündelik topluluk yanıtları ve kaynağı belirtilmiş sentetik anlatılar içerir. [Veri dosyaları, kaynaklar ve yeniden üretme](data/GENEL_METINLER_V6_KAYNAKLAR.md)

Eğitimli V6’yı `python app.py --model-version v6 --port 8767` ile deneyebilirsin. [Üç sürümün karşılaştırması](models/detector_v6/MODEL_KARTI.md)

### V5 eğitim verisi

V5 toplam 50.000 benzersiz metin içerir. Eğitimde 37.763, doğrulamada 6.118, testte 6.119 kayıt kullanılır. Eğitim komutu `python train_detector.py --dataset v5 --output models/detector_v5` boş bir çıktı klasörü gerektirir. [V5 kaynakları ve sınıf dağılımı](data/DENGELI_V5_KAYNAKLAR.md)

Eğitimli V5’i `python app.py --model-version v5 --port 8766` ile açabilirsin. Bağımsız otel testinde V5 daha başarılı oldu. İkinci bağımsız testte insan metinlerini daha sık AI olarak işaretlediği için bu sürümün değerlendirmesi sırasında V2 tercih edilmişti. [V5 model kartı ve iki testin sonuçları](models/detector_v5/MODEL_KARTI.md)

### V4 eğitim verisi

V3’ün 40.781 kaydına Türkçe programlama belgelerinden ve sentetik teknik soru yanıtlarından 1.142 eğitim kaydı eklendi. Toplam 41.923 kaydın 29.686’sı eğitim, 6.118’i doğrulama ve 6.119’u test içindir. Bu veriyle aday model eğitmek için boş bir çıktı klasörüyle `python train_detector.py --dataset v4 --output models/detector_v4` kullan. [Kaynaklar, lisanslar ve seçim yöntemi](data/TEKNIK_EGITIM_V4_KAYNAKLAR.md)

### Genişletilmiş veri seti ve V3

[V3 veri seti](data/detector_v3_40781.jsonl) toplam 40.781 Türkçe ve İngilizce kayıt içerir. [15.781 yeni örnek ve kaynakları](data/GERCEK_YASAM_V3_KAYNAKLAR.md) arasında ürün ve film yorumları, tarifler, forum ve anlatı metinleri vardır. [V3 model kartında](models/detector_v3/MODEL_KARTI.md) V2 ile aynı metinler üzerinde yapılan karşılaştırma yer alır.

V3, bağımsız otel yorumlarında daha fazla AI metni yakaladı ancak insan yorumlarını daha sık yanlış işaretledi. O değerlendirmede V2 tercih edilmişti. V3’ü denemek için aşağıdaki komutlardan birini kullan:

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
