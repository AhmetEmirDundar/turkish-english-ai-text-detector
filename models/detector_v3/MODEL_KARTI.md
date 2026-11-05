# Türkçe ve İngilizce metin dedektörü · V3

V3, ürün ve film yorumları gibi gündelik türlerde AI yazımını yakalamaya yönelik deneysel modeldir. Genişleme sonrası eski test bölümleri aynen korunmuştur. Aşağıdaki her satırda V2 ve V3 aynı metinler üzerinde değerlendirilmiştir.

| Test | Metin | V2 doğruluk | V3 doğruluk |
|---|---:|---:|---:|
| Önceki V2 proje testi | 3.752 | %98,64 | %98,11 |
| Yeni kaynakların ayrılmış testi | 2.367 | %62,61 | %94,55 |
| MAiDE-up bağımsız otel testinin tamamı | 500 | %73,60 | %86,20 |
| Ayrı araştırmanın Türkçe–İngilizce testi | 500 | %78,40 | %77,80 |

Yeni kaynakların testinde V3’ün aynı veri kaynaklarından ayrı kayıtlarla eğitilmiş olması bir avantajdır. Bağımsız testlerdeki farklar konu ve metin türüne göre değişir. Ayrı araştırma testindeki üç kayıtlık fark tek başına genel bir gerileme kanıtı değildir.

### Otel yorumlarında hata türleri

Her dilde 125 insan ve 125 AI yorumu kullanıldı. Eşikler otel verisinde ayarlanmadı.

| Dil | V2 yanlış AI etiketi (insan) | V3 yanlış AI etiketi (insan) | V2 yakalanan AI | V3 yakalanan AI |
|---|---:|---:|---:|---:|
| Türkçe | 29 / 125 | 33 / 125 | 100 / 125 | 124 / 125 |
| İngilizce | 2 / 125 | 17 / 125 | 49 / 125 | 107 / 125 |

V2’nin 1.499 İngilizce forum/kullanıcı metninden oluşan insan testinde yanlış işaretleme 10’dan 33’e çıktı. Eski İngilizce akademik insan testinde V3 yine 751 pasajın 590’ına AI dedi. Kullanım kararı metin türüne ve yanlış suçlamanın maliyetine bağlıdır; genel arayüz varsayılanı V2 olarak bırakıldı.

### Eğitim ve yeniden üretim

Aktif 40.781 kaydın 28.544’ü eğitim, 6.118’i doğrulama, 6.119’u test içindir. XLM-RoBERTa-base’in son iki katmanı ve sınıflandırma başlığı iki tur eğitildi. Doğrulama makro F1 sonucu, ikinci tur için %96,87 ve TF-IDF karşılaştırma modeli için %94,62 oldu. V3’ün kendi genel testinde doğruluk %96,73’tür. Model kararı için eşik 0,55453’tür. Kalibrasyon ve model seçimi yalnızca proje doğrulama verisine dayanır.

İngilizce akademik insan metinleri V3 eğitimi ve model seçiminde kullanılmadı. Yeni Türkçe kullanıcı yorumları için kayıt yaşı kaynak arşivinden, yazarlık etiketi koleksiyonun oluşturulma yönteminden gelir. Her metnin bireysel üretim geçmişi bilinmez. Kısa mesajlar (50 sözcük altı), insan tarafından yeniden yazılmış AI metinleri ve tüm farklı günlük yazım türleri için başarı gösterilmiş değildir.

[Veri ve kaynaklar](../../data/GERCEK_YASAM_V3_KAYNAKLAR.md) · [İç test sonuçları](metrics.json) · [Bağımsız otel testi](external_test.json) · [Ek karşılaştırma](transfer_comparison.json) · [Kullanım](../../README.md)
