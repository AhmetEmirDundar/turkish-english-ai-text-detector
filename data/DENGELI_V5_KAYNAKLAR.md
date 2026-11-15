# V5 veri kümesi

[Tam derleme](detector_v5_50000.jsonl) 50.000 benzersiz metin içerir. Türkçe ve İngilizcenin her birinde 12.500 insan ve 12.500 AI metni bulunur. [V5 ek dosyası](balanced_v5_addition.jsonl) V4’ün 41.923 metnine eklenen 8.077 kaydı içerir.

| Ek kaynağın adı | Dil | İnsan | AI | İçerik |
|---|---|---:|---:|---|
| Pro Git | Türkçe | 80 | 0 | Türkçe Git kitabından bölümler |
| Keskin | Türkçe | 1.167 | 0 | 2019 arşivinden film yorumları |
| Barmanbay | Türkçe | 1.682 | 0 | 2018 arşivinden ürün yorumları |
| cturan | Türkçe | 0 | 1.655 | Film, ürün ve alışveriş konulu sentetik anlatımlar |
| Uunan | Türkçe | 0 | 1.274 | Teknik soruların sentetik asistan yanıtları |
| RAID | İngilizce | 119 | 2.100 | Ansiklopedi, haber ve akademik özetler |

Pro Git’in 2022 öncesi kaynak sürümünden Türkçe bölümler seçildi. Başlıklar ve kod blokları ayıklandı, metin içi boşluklar düzenlendi. Scott Chacon ve çeviri katkıcılarının bu pasajları CC BY-NC-SA 3.0 lisansıyla sunulur. [Kaynak sürümü ve lisans bildirimi](https://github.com/progit/progit/blob/61833a527c6ac0c44cc40793c034b81599c25efc/README.original.md)

Teknik yanıtların ve anlatımların AI etiketleri derleme sahiplerinin üretim açıklamalarına dayanır. Türkçe kullanıcı yorumlarında insan etiketi arşivin tarihine ve kaynağın toplama yöntemine dayanır. RAID kayıtları müdahalesiz eğitim arşivindendir. İnsan veya AI etiketi ve üretici adı kaynağın model alanından alınır. Kaynak dosyasındaki konum, belge bölümü veya UUID her yeni kayıtta saklanır. [Türkçe sentetik kaynaklar ve lisanslar](KAYNAKLAR.md) · [Yorum arşivleri ve RAID](GERCEK_YASAM_V3_KAYNAKLAR.md)

V5 için eski veriyle, bağımsız test metinleriyle veya başka bir yeni kayıtla normalleştirilmiş 18 ardışık sözcüğü paylaşan adaylar elenir. Yeni RAID örneklerinde başlık başına tek metin kullanılır. Yeni film yorumları için önceki derlemede bulunan filmler dışarıda bırakılır. Yeni kayıtlar yalnızca eğitime girer. Doğrulama ve test listeleri korunur. Dört grubun toplam sayılarını eşitlemek, tür ve uzunluk dağılımlarını kendi başına eşitlemez.

`python build_50k_data.py` yerel arşivlerden tam dosyayı ve ek dosyayı yeniden oluşturur. Önceki sürümlerin ham verilerine ek olarak yukarıdaki Pro Git sürümünün ZIP arşivi `.training_cache/progit-61833a527c6ac0c44cc40793c034b81599c25efc.zip` yolunda bulunmalıdır. Tam dosyanın SHA-256 özeti `c8e1a0f26dbfa758c37f241323a34e595f789854729d2425597e2b54d68fe8cf`, ek dosyanın özeti `acaccf36ddacc791cff777d8216ed328e0ab5e3b5152329ceca2543d1bd3ac1b`.
