# Güncel insan yazımı metinler

`human_texts_tr_en_10000.jsonl` dosyası, yazarlarının metin yazımında üretken yapay zekâ kullanmadıklarını açıkça beyan ettikleri akademik makalelerden seçilen 10.000 pasajı içerir. Her JSONL satırı bir pasajdır. İnsan yazımı için `label = 0` kullanılır. Kanıt türü yazar beyanıdır.

| Dil | Pasaj | Ayrı makale | Dergi | İlk ve son yayın tarihi | Ortanca sözcük sayısı |
|---|---:|---:|---:|---|---:|
| Türkçe | 5.000 | 120 | 7 | 2025-09-15 – 2026-10-20 | 85 |
| İngilizce | 5.000 | 370 | 11 | 2026-09-02 – 2026-10-20 | 88 |

5 Kasım 2026 itibarıyla son 12 ayda yayımlanmış pasaj sayısı **9.338**. Tarih, alındığı makalenin ilk yayın tarihidir. İlk olarak son 12 aydaki çalışmalardan seçim yapıldı. Kalan yerler, önceki ayların en yeni yayınlarından tamamlandı.

## Kaynak ve doğrulama

- Türkçe pasajlar DergiPark’taki tam sayı PDF’lerinden alındı. Makale başlığı, DOI ve sayfa aralığı derginin içindekiler kaydıyla eşleştirildi. Yazarın kullanmama beyanı aynı makalenin sayfalarında arandı. [DergiPark](https://dergipark.org.tr/) · [Millî Eğitim Dergisi yayın politikası](https://dergipark.org.tr/tr/pub/milliegitim/page/20029)
- İngilizce pasajlar Europe PMC’de yayımlanan tam metinlerin makale gövdesinden alındı. Her makalede yazımda üretken yapay zekâ kullanılmadığını bildiren bölüm ve CC BY 4.0 lisansı kontrol edildi. [Europe PMC](https://europepmc.org/)
- Yayın tarihi için DOI kaydındaki basılı ve çevrim içi yayın tarihleri arasından en erken tarih seçildi. Dizin güncelleme tarihleri kullanılmadı. [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- Başlıklar, kaynakça, lisans ve beyan metinleri yerine makale gövdesinden açıklayıcı pasajlar seçilmeye çalışıldı. PDF satır sonları ve satır sonundaki sözcük bölünmeleri temizlendi. Uzun paragraflar cümle sonlarında bölündü. Bazı kısa, bitişik metin blokları birleştirildi. Atıflar, tablo göndermeleri ve metin içi alıntılar bulunabilir.
- Her pasajın baskın dili Lingua ile kontrol edildi. Harf büyüklüğü, boşluk ve Unicode biçimi farkları giderilerek tekrarlar elendi. Seçilen iki pasajın art arda aynı 18 sözcüğü taşımasına izin verilmedi. Önceki AI dosyasıyla da tam metin eşleşmesi kontrol edildi.

Son JSONL dosyası yeniden okunarak 10.000 pasajın tamamı bağlantısı verilen PDF blokları veya XML paragraflarıyla karşılaştırıldı. Eşleşmeyen pasaj sayısı sıfırdı.

## Alanlar

| Alan | Ne gösterir? |
|---|---|
| `text`, `label`, `language`, `word_count` | Pasaj, insan etiketi, dil kodu ve boşlukla ayrılmış sözcük sayısı. |
| `id` | Normalleştirilmiş pasajın SHA-256 özeti. |
| `group_id`, `article_url` | Makalenin DOI’si ve yayına giden bağlantı. |
| `authors`, `title`, `journal`, `publication_date` | Yazarlar, makale adı, dergi ve yayın tarihi. |
| `source`, `source_file`, `source_record` | Arşiv, kaynak dosya bağlantısı, pasajın PDF sayfası/metin bloğu veya XML paragrafı. Sözcük aralığında başlangıç dahil ve bitiş hariçtir. |
| `authorship_evidence`, `declaration_location`, `declaration_match` | Etiketin dayanağı, yazar beyanının yeri ve aramada eşleşen normalleştirilmiş ifade. |
| `license`, `license_url` | Kaynak makalenin lisansı ve ilgili bağlantı. |

## Kullanım

Eğitim, doğrulama ve test ayrımını `group_id` üzerinden yap. Aynı makalenin pasajları tek kümede kalsın. Dedektörün girdisi yalnızca `text` olmalı. Tarih, yazar adı ve kaynak gibi alanlar değerlendirme ve izlenebilirlik içindir.

Bu sınıf akademik yayınlardan oluşur. Önceki AI dosyasındaki konuları, metin türlerini ve uzunlukları eşleştirmek, modelin yazarlık yerine akademik üslubu veya uzunluğu öğrenmesi riskini azaltır. Resmî yazar beyanı, yazım sürecinin bağımsız denetimi değildir.

Yeniden kullanım koşulları kayda göre değişir. CC BY-NC 4.0 kaynakları ticari olmayan kullanım koşulu taşır. Yazar, makale adı, DOI, lisans ve yapılan biçim değişikliklerine ilişkin bilgiler korunmalıdır. [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Dosya SHA-256 özeti: `99b725541090cfe22ab033fddcc273a6bdf705b50c0a6b348eed7062809668af`.
