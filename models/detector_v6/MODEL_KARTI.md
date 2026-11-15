# V6 deney sonuçları

V5, 631 İngilizce eğitim kaydı değiştirilmiş kontrol modeli ve 4.000 genel yazı eklenmiş V6, aynı sabit test metinlerini analiz etti. İki aday yeniden eğitildi. Her biri kendi doğrulama kümesinde belirlenen karar eşiğini kullandı. V6’da eşik 44,87 / 100, üslup ağırlığı yaklaşık %0,30’dur. Hiçbir değerlendirme kaydı eğitimle 18 ardışık sözcük paylaşmadı. [Deney raporu](comparison.json) · [Eğitim raporu](metrics.json)

| Ölçüm | V5 | 631 değişiklik | V6 |
|---|---:|---:|---:|
| Doğrulanmış 153 İngilizce insan pasajına yanlış AI kararı | 62 | 29 | 28 |
| Genel testte 200 insan metnine yanlış AI kararı | 94 | 91 | 6 |
| Genel testte kaçırılan AI metni / 200 | 9 | 8 | 2 |
| Bostancıoğlu testinde İngilizce insan metnine yanlış AI kararı / 125 | 114 | 73 | 75 |
| Bostancıoğlu testinde kaçırılan AI metni / 250 (iki dil) | 10 | 7 | 6 |
| Otel testinde insan yorumuna yanlış AI kararı / 250 | 43 | 30 | 36 |
| Otel testinde kaçırılan AI metni / 250 | 5 | 32 | 16 |

Genel testte V6, 400 metnin 392’sini doğru sınıflandırdı. Bu test aynı kaynak ailelerinden ayrılmış metinlere dayanır. Akademik ve teknik İngilizce insan pasajlarında 631 kayıtlık değişiklikle yanlış AI kararları azaldı. İkinci bağımsız testte V6 hâlâ 125 İngilizce insan metninin 75’ini yanlış işaretliyor. Otel yorumlarında V5’e göre 11 daha fazla AI metni kaçırdı. V6 karşılaştırma amacıyla `python app.py --model-version v6 --port 8767` komutuyla kullanılabilir.
