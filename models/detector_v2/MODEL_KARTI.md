# Türkçe ve İngilizce metin dedektörü · v2

Bu sürüm, İngilizce forum gönderilerini ve kullanıcı yorumlarını insan sınıfına dahil eder. Aynı 1.499 yeni İngilizce insan etiketli test metninde v1, 1.484 metni AI olarak işaretledi. V2’de bu sayı 10’a indi. İngilizce akademik metinlerde ve AI tarafından üretilen otel yorumlarında ise v2 daha çok hata yaptı. Skor tek başına yazarlık kanıtı olarak kullanılmamalıdır.

## Veri ve eğitim

| Aktif kayıtlar | İnsan | AI |
|---|---:|---:|
| Türkçe | 5.000 | 5.000 |
| İngilizce | 10.000 | 5.000 |

Yeni İngilizce insan metinlerinin 7.657’si 2011–2017 döneminden, 2.343’ü 2025–2026 dönemindendir. Her kayıtta yayın tarihi, düzenleme tarihi, kaynak, yazar hesabı, lisans ve kanıt türü bulunur. Güncel dönemde platformun AI içerik politikası ve hesap atfı kullanılır; kişi bazında AI kullanımı doğrulanmış değildir. [Veri ve kaynaklar](../../data/INGILIZCE_MAKALE_DISI_KAYNAKLAR.md)

Eğitim, doğrulama ve test kümelerinde sırasıyla 17.497, 3.751 ve 3.752 kayıt vardır. Önceki sürümden taşınan kayıtlar önceki kümelerinde kalır. Yeni hesaplar kümeler arasında paylaşılmaz. Bir forum başlığı veya yorumlanan eserden tek örnek seçilmiştir. V1’in İngilizce akademik insan kayıtları v2 eğitiminde ve karar eşiği seçiminde kullanılmamıştır.

Model, sabit FacebookAI/xlm-roberta-base başlangıç ağırlıklarından eğitildi. Son iki katman ve sınıflandırma başlığı iki tur güncellendi. Her metinden 50 sözcüklük parçalar kullanıldı. Eğitimde her dil ve sınıfın toplam ağırlığı eşitlendi; yeni İngilizce insan sınıfında güncel kayıtların örnek başına ağırlığı eski kayıtların yarısıdır. İkinci turdaki XLM-RoBERTa, doğrulama makro F1 puanıyla seçildi (%98,67; TF-IDF karşılaştırması %98,11). AI karar eşiği **0,60858**. Model seçimi ve kalibrasyon testlerden önce yapıldı.

## Sonuçlar

| Ölçüm | V1 | V2 |
|---|---:|---:|
| Yeni, eski dönem İngilizce insan etiketli metinlerinde yanlış AI etiketi | 1.146 / 1.155 | 4 / 1.155 |
| Yeni, güncel dönem İngilizce insan etiketli metinlerinde yanlış AI etiketi | 338 / 344 | 6 / 344 |
| Bağımsız İngilizce otel yorumlarında yanlış AI etiketi | 110 / 125 | 2 / 125 |
| Bağımsız İngilizce AI otel yorumlarında doğru AI etiketi | 123 / 125 | 49 / 125 |
| Bağımsız İngilizce otel yorumları, doğruluk | %55,20 | %68,80 |
| Önceki İngilizce akademik insan testinde yanlış AI etiketi | 7 / 751 | 632 / 751 |
| Aynı Türkçe proje testinde doğruluk | %98,20 | %98,47 |

V2’nin kendi 3.752 kayıtlık testinde doğruluk %98,64, makro F1 %98,58’dir. Eski 3.004 kayıtlık testin tamamında v2’nin doğruluğu %77,60’tır; v1’in bu testteki doğruluğu %98,47 idi. Bu farkı yorumlarken insan sınıfının kaynakları önemlidir. Aynı bağımsız otel yorumu testinde Türkçe doğruluk %73,20’den %78,40’a çıktı. Otel yorumları yalnızca dış değerlendirmede kullanıldı. [Bağımsız veri kümesi](https://huggingface.co/datasets/MichiganNLP/MAiDE-up)

Kullanıcının paylaştığı Stack Overflow sorusu eğitimde bulunmaz. V1’in AI skoru 0,997992, v2’nin skoru 0,000044 oldu. Soru için doğrulanmış yazarlık etiketi olmadığından bu örnek başarı hesabına katılmadı.

[İç test ve eğitim ölçümleri](metrics.json) · [Bağımsız test](external_test.json) · [Aynı metinlerde sürüm karşılaştırması](comparison.json) · [Çalıştırma komutları](../../README.md)
