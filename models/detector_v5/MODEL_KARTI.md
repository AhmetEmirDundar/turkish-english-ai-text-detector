# V5 değerlendirmesi

50.000 belgede eğitim, doğrulama ve test sayıları sırasıyla 37.763, 6.118 ve 6.119’dur. İki tur sonunda doğrulama ölçümüne göre ikinci turdaki XLM-RoBERTa seçildi. Birleşik skorun karar eşiği 48,4 / 100’dür. Ayrı doğrulama örnekleminde ortalama karesel hatayı en aza indiren üslup ağırlığı sıfır çıktı. V5’in genel skorunu ana model belirler. [Eğitim ve iç test ölçümleri](metrics.json) · [Sabit skor ayarları](detector.json)

İç testte ana model eğitim sırasındaki parça örneklemesiyle 6.119 metnin 5.929’unu doğru sınıflandırdı (%96,9). Aşağıdaki bağımsız karşılaştırmalarda her iki sürüm de web uygulamasındaki gibi metnin tamamını ve kendi sabit karar eşiğini kullandı. Her sette 250 insan, 250 AI metni vardır.

| Bağımsız test | Sürüm | Doğru / 500 | İnsan metnine AI kararı | Kaçırılan AI metni |
|---|---|---:|---:|---:|
| MAiDE-up otel yorumları | V2 | 372 | 18 | 110 |
| MAiDE-up otel yorumları | V5 | 452 | 43 | 5 |
| Bostancıoğlu ve arkadaşları | V2 | 402 | 87 | 11 |
| Bostancıoğlu ve arkadaşları | V5 | 366 | 124 | 10 |

V5 otel yorumlarında daha fazla AI metnini yakaladı. Her iki testte de insan metinlerine daha sık AI etiketi verdi. İkinci testin İngilizce bölümünde V5, 125 insan metninin 114’ünü AI olarak işaretledi. Genel kullanımda V2 varsayılan sürüm olarak tutuldu. V5 bağımsız olarak seçilebilir. [Otel testi](external_test.json) · [İkinci test ve dil bazında karşılaştırma](transfer_comparison.json)
