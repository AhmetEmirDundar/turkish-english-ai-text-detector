# Türkçe ve İngilizce AI metin dedektörü · v1

Bu deneysel sınıflandırıcı, Türkçe veya İngilizce bir metne insan / AI etiketi ve bir AI skoru verir. Proje içi testte %98,47 doğruluğa ulaştı. Eğitim kaynaklarından bağımsız bir otel yorumu testinde doğruluğu %64,20 oldu. Özellikle günlük İngilizce metinlerde insan yazımını AI olarak işaretleme oranı yüksekti.

## Kullanım ve kapsam

[Çalıştırma komutları](../../README.md) · [İç test raporu](metrics.json) · [Bağımsız test raporu](external_test.json)

- En az 50 sözcük gerekir. Güncel uygulama metnin tamamını ardışık parçalarla analiz eder. Bu karttaki tarihsel ölçümlerde uzun metinlerin başından, ortasından ve sonundan en fazla üç pencere kullanılmıştır.
- AI skoru, proje doğrulama verisiyle ayarlanmıştır. Karar eşiği **0,60255**’tir. Farklı bir alanda bu skor, metnin gerçek yazarı hakkında güvenilir bir olasılık sunmayabilir. Özellikle öğrencileri veya yazarları değerlendiren kararlarda tek başına kullanılmamalıdır.
- Ağırlıklar ve metin işleyicisi `xlmr` klasöründe, kalibrasyon ve eşik `detector.json` içindedir. Paket CPU ve GPU üzerinde internet bağlantısı olmadan kullanılabilir.

## Eğitim ve model seçimi

FacebookAI/xlm-roberta-base modelinin `e73636d4f797dec63c3081bb6ed5c7b0bb3f2089` sürümü kullanıldı. İkili sınıflandırma başlığı ve son iki Transformer katmanı iki tur eğitildi. Diğer katmanlar sabit tutuldu. Eğitim RTX 4050 Laptop GPU üzerinde, 24 örneklik gruplarla yürütüldü. Her turda her eğitim kaydından bir 50 sözcüklük pencere alındı. Karşılaştırma için karakter dizilerini kullanan TF-IDF ve lojistik regresyon modeli de eğitildi. [Temel model kartı](https://huggingface.co/FacebookAI/xlm-roberta-base)

20.000 kayıt **13.994 eğitim**, **3.002 doğrulama** ve **3.004 test** kaydına ayrıldı. Aynı DOI, normalleştirilmiş ortak yazar adı veya modelin gördüğü pencerelerde 18 ardışık sözcük eşleşmesi olan kayıtlar birlikte tutuldu. Aynı AI kaynakları her üç kümede de temsil edilir. Kayıt kimlikleri ve grup atamaları `splits.jsonl` dosyasındadır.

Model seçimi doğrulama kümesindeki makro F1 puanına göre yapıldı. Her modelin karar eşiği, doğrulamada her iki dilde de insan metnini yanlış işaretleme oranı en çok %5 olacak şekilde ayarlandı. XLM-RoBERTa’nın ikinci turu %99,13 doğrulama makro F1 puanıyla seçildi. TF-IDF karşılaştırma modelinin puanı %98,37 idi. Son test ve bağımsız test, bu seçimden sonra çalıştırıldı.

| Model / proje testi | Doğruluk | Makro F1 | İnsan → AI | AI → insan |
|---|---:|---:|---:|---:|
| XLM-RoBERTa | %98,47 | %98,47 | 19 / 1.504 | 27 / 1.500 |
| TF-IDF + lojistik regresyon | %98,30 | %98,30 | 14 / 1.504 | 37 / 1.500 |

| XLM-RoBERTa testi | Kayıt | Doğruluk | İnsan metinlerinde yanlış AI etiketi |
|---|---:|---:|---:|
| Proje · Türkçe | 1.503 | %98,20 | 12 / 753 (%1,59) |
| Proje · İngilizce | 1.501 | %98,73 | 7 / 751 (%0,93) |
| Otel yorumları · Türkçe | 250 | %73,20 | 66 / 125 (%52,80) |
| Otel yorumları · İngilizce | 250 | %55,20 | 110 / 125 (%88,00) |

## Bağımsız otel yorumu testi

MichiganNLP/MAiDE-up veri kümesinden her dil ve sınıf için 125 farklı yorum seçildi. Bir yorumun olumlu ve olumsuz bölümleri birleştirildi. En az 50 sözcük koşulu uygulandı, proje metinlerinin model pencereleriyle 18 sözcüklük örtüşme kontrol edildi. Örnekler metin özetine göre sıralanarak seçildi. Kaynak etiketleri kullanıldı. Model ve eşik bu yorumlarla yeniden ayarlanmadı. Toplam 250 insan yorumunun 176’sı AI, 250 AI yorumunun 3’ü insan olarak sınıflandırıldı. Bu sonuç bu yorum örneklemi içindir. [Veri kümesi ve üretim yöntemi](https://huggingface.co/datasets/MichiganNLP/MAiDE-up)

Projedeki insan sınıfı akademik makale pasajlarından, AI sınıfı ise sentetik bilgi yanıtları, hikâyeler ve diğer metinlerden oluşur. Eşit uzunlukta pencereler ve ayrı makale grupları kullanılmasına rağmen model yazarlıkla birlikte konu, kaynak ve üslup farklarını da öğrenebilir. Bu yüzden proje testindeki yüksek başarıyı başka metin türlerine genellemek doğru olmaz.

## Veri ve yeniden kullanım

Eğitim verisinin kimlik özetleri ve metrikler `metrics.json` içindedir. Kaynak makalelerin bir bölümü **CC BY-NC 4.0** koşullarına tabidir. Ticari bir uygulama için eğitim verisinin kullanım koşulları ayrıca değerlendirilmelidir. [İnsan sınıfının kaynakları](../../data/INSAN_METINLERI_KAYNAKLAR.md) · [AI sınıfının kaynakları](../../data/KAYNAKLAR.md)
