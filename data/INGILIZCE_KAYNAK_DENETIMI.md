# İngilizce etiket denetimi ve kaynaklı insan metinleri

## V5 kayıtları

V5 eğitim raporundaki ek dosya özeti, incelenen `balanced_v5_addition.jsonl` dosyasının SHA-256 özetiyle eşleşti. Son eklemedeki İngilizce kayıtların tamamı UUID üzerinden yerel RAID eğitim arşiviyle karşılaştırıldı. Her satırda boşlukları düzenlenmiş özgün metin, üretici alanı ve sınıf eşleşti. 119 insan ve 2.100 AI kaydının tamamı V5’in eğitim ayrımındadır. Bu denetim kaynak etiketinin doğru aktarıldığını gösterir. Yazarlığın dayanağı RAID’in yayıncı etiketidir. [RAID](https://github.com/liamdugan/raid)

| Son İngilizce ekleme | İnsan | AI |
|---|---:|---:|
| Ansiklopedi | 42 | 736 |
| Haber | 38 | 691 |
| Akademik özet | 39 | 673 |

İkinci bağımsız testin 250 İngilizce metni de özgün çalışma kitabındaki satır, metin ve `generated` alanıyla eşleşti. İnsan pasajlarında DevOps, yazılım ölçümü ve bilgi sistemleri makalelerinden örnekler var. V5 bu 125 insan pasajının 114’üne AI etiketi verdi. Sınıfların toplamda dengeli olması, aynı türü iki sınıfta dengeli biçimde temsil etmiyor. Önceki 2.343 güncel forum/yorum kaydında ise bireysel AI kullanmama beyanı yoktur. [Önceki etiketlerin kanıt düzeyi](INGILIZCE_MAKALE_DISI_KAYNAKLAR.md)

## Yeni kaynaklar

* Europe PMC’den 2012–2017 tarihli 39 makale seçildi. PMCID ve DOI üstveriyle eşleştirildi. XML’de İngilizce dil bilgisi, yazar adları, yayın yılı ve sürümü belirli CC BY lisans bağlantısı arandı. Metinler makale gövdesindeki paragraflardan alındı. [Örnek makale](https://europepmc.org/articles/PMC3799567)
* Python projesinin 2017 sonundaki sabit PEP arşivinden 101 belge kullanıldı. Belgelerin kendi yazar, oluşturulma tarihi ve kamu malı bildirimi kontrol edildi. [Kaynak sürümü](https://github.com/python/peps/tree/6905c6ce669f4792f08149102b87b9ea9ec339b4)

Her pasajın özgün kaynak içindeki yeri, yazarları, bağlantısı ve kaynak dosyasının SHA-256 özeti saklandı. Yalnızca boşluklar düzenlendi. 784 metnin tamamı kaynak dosyalarından yeniden okunup birebir kontrol edildi. İnsan etiketinin dayanağı tarihli yayın ve adlandırılmış yazarlardır. Veri seçiminde dedektör skoru kullanılmadı.

| Dosya | Europe PMC | Python PEP | Toplam |
|---|---:|---:|---:|
| [Aday eğitim verisi](verified_english_academic_train.jsonl) | 256 | 375 | 631 |
| [Ayrı değerlendirme verisi](verified_english_academic_holdout.jsonl) | 55 | 98 | 153 |

İki bölüm arasında aynı belge ya da aynı normalleştirilmiş yazar adı bulunmaz. V5 verileriyle ve bağımsız testlerle 18 ardışık sözcük paylaşan adaylar elendi. [Sabit kaynak listesi ve özetler](verified_english_sources.json). Yerel proje verileri hazırken `python build_verified_english.py --download` eksik kaynakları indirir ve çıktıların özetini denetler.

## Yeni insan metinlerinde yanlış AI kararları

| Ayrı değerlendirme bölümü | V2 | V5 |
|---|---:|---:|
| 7 makaleden 55 pasaj | 43 | 51 |
| 22 Python belgesinden 98 pasaj | 2 | 11 |

Bu ölçüm yalnızca insan metinlerindeki hatayı sayar. Aynı belgeden birden fazla pasaj olduğu için sonuç tek tek bağımsız yazarlara genellenemez. V5 ve eşikleri bu deneyde değiştirilmedi. Sonraki eğitimde aday insan pasajlarıyla benzer konuda, bilinen üreticilerden AI pasajları birlikte değerlendirilmeli. Hem yanlış AI etiketleri hem kaçırılan AI metinleri önceki testlerde yeniden sayılmalı.
