# V3 veri seti

[Aktif veri seti · 40.781 kayıt](detector_v3_40781.jsonl) · [Yalnızca bu sürümde eklenen 15.781 kayıt](realworld_v3_addition.jsonl)

| Dil | İnsan | AI | Toplam |
|---|---:|---:|---:|
| Türkçe | 9.000 | 9.000 | 18.000 |
| İngilizce | 12.381 | 10.400 | 22.781 |
| Toplam | 21.381 | 19.400 | 40.781 |

### Eklenen metinler

| Kaynak | Tür ve dil | İnsan | AI | İz sürme |
|---|---|---:|---:|---|
| Mustafa Keskin | Türkçe film yorumları | 2.000 | 0 | 2019'da arşivlenmiş kullanıcı yorumları. CSV veri satırı 1'den başlar. Aynı film aynı bölüme gider. [Kaggle](https://www.kaggle.com/datasets/mustfkeskin/turkish-movie-sentiment-analysis-dataset) |
| Fatih Barmanbay | Türkçe ürün yorumları | 2.000 | 0 | 22 Mart 2018 tarihli arşiv. Olumlu ve olumsuz değerlendirme dosyalarındaki satırlar 1'den başlar. Duygu etiketi yazarlık etiketi olarak kullanılmaz. [Arşiv ve lisans](https://github.com/fthbrmnby/turkish-text-data/tree/b0c2e38111f87a84b2f9a41f2a711847ec9f286b) |
| Karataş | Türkçe ürün yorumları | 0 | 2.500 | 2026 tarihli arşivin FR dosyasında açıkça GPT2 olarak etiketlenen satırlar. Çeviri, insan parçalarının birleştirilmesi ve Markov çıktıları dışarıda tutuldu. Örnek insan metninden 12 ardışık sözcük taşıyan kayıtlar elendi. `sheet1` Excel satır numarasıdır. [Kaynak ve üretim kodu](https://github.com/karatasarzu/turkish-fake-review-detection/tree/237a86940133bfa36ad293c187194c3c5992a0b2) |
| cturan | Türkçe anlatım ve açıklama | 0 | 1.500 | Önceden indirilmiş Türkçe sentetik derlemeden, birinci kişi ve sinema ile ilgili kelime filtreleriyle seçilmiş yeni metinler. Model adı kaynakta verilmemiştir. `byte` ham dosyadaki konumdur. [Sabit sürüm](https://huggingface.co/datasets/cturan/turkish-synthetic-corpus/tree/fa602a833012ba9390f573ab44828aade1a7609e) |
| RAID | İngilizce film yorumları | 781 | 1.800 | Aynı alan, farklı yazar ve üretici sınıfları |
| RAID | İngilizce Reddit metinleri | 800 | 1.800 | Aynı alan, farklı yazar ve üretici sınıfları |
| RAID | İngilizce tarifler | 800 | 1.800 | Aynı alan, farklı yazar ve üretici sınıfları |

RAID’den yalnızca yayımlanmış **eğitim** bölümünün müdahalesiz kayıtları seçildi. `source_record` RAID UUID’sidir. İnsan ve AI ayrımı yayımcının `model` alanından gelir; AI örneklerinde üretici aile adı ayrıca saklanır. Aynı alan ve başlıktan gelen tüm varyantlar tek gruptadır. Keskin veri kümesi CC0, Barmanbay CC BY-SA 4.0, cturan ODC-BY olarak yayımlanmıştır. Karataş deposu ve RAID veri kartı MIT lisansı gösterir. Kaynak içeriklerin atıf ve kullanım koşulları derleme boyunca korunmalıdır. [RAID projesi](https://github.com/liamdugan/raid) · [RAID veri kartı](https://huggingface.co/datasets/liamdugan/raid)

### Seçim ve sınırlar

Yeni kayıtlarda `period` arşivin dönemini belirtir. Yorumlara arşiv tarihini tekil yayın tarihi gibi atamadık. Önceki sürümdeki, yayın tarihi doğrulanmış `historical` ve `recent` kayıtlar ayrıca korunur. Kullanıcı yorumu etiketi kaynağın toplama yöntemine dayanır. Özellikle 2018 ve 2019 arşivleri yaygın sohbet modellerinden öncedir. Her yorumda yazar kimliği veya kişisel yazarlık beyanı yoktur.

Metinler en az 50 sözcüktür. Dil, tekrarlar, belirgin istek şablonları ve uzun ortak parçalar kontrol edildi. Yeni metinler eski veri setinden, sabit otel testi dosyasından ve ikinci dış testin uygun adaylarından 18 sözcüklük ortak parçalar varsa elendi. Her yeni metin, kaydedilen konumdan kaynak dosyası tekrar okunarak doğrulandı. V2’deki 25.000 kaydın ayrımı sabit tutuldu. Yeni 11.390 grubun her biri tek kümededir; yazar kimliği eksik kaynaklarda aynı kişinin farklı belgelerde bulunmasını tümüyle kontrol etmek mümkün değildir.

### Test verileri

MAiDE-up'tan alınan önceki 500 yorum, kaynak sürümü, seçim kuralı ve kayıtları değiştirilmeden yeniden değerlendirilir. İkinci test için Bostancıoğlu ve arkadaşlarının araştırma verisinden kaynak etiketi kullanılarak Türkçe ve İngilizcede her sınıftan 125 örnek, metin özeti sırasıyla seçildi. Bu dosyalar eğitime veya eşik seçimine dahil edilmez. İkinci çalışmanın test birimi pasajdır; sonuçlar tek tek bağımsız yazarlar için bir doğrulama değildir. [MAiDE-up](https://huggingface.co/datasets/MichiganNLP/MAiDE-up) · [İkinci testin kaynağı](https://huggingface.co/datasets/aycabostancioglu/Arabic-English-Turkish-AI-Human-Text/tree/55ad8ab14b1bc2e2510a3d66903be95da1eae4b6)
