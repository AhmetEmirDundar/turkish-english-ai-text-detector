# Türkçe ve İngilizce yapay zekâ metinleri

`ai_texts_tr_en_10000.jsonl` dosyasında 5.000 Türkçe ve 5.000 İngilizce metin bulunur. Her satır UTF-8 kodlamasıyla yazılmış bir JSON nesnesidir. Bütün kayıtlarda `label = 1` yapay zekâ üretimini belirtir. Etiketler, kaynak sahiplerinin açıkladığı üretim yöntemine dayanır.

| Dil | Kayıt | Kaynak ve kullanılan içerik | Üretici model | Kaynağın belirttiği lisans |
|---|---:|---|---|---|
| Türkçe | 2.500 | [Uunan / Turkish Knowledge SFT](https://huggingface.co/datasets/Uunan/turkish-knowledge-sft/tree/ee6e20f207a9ef9cadc10b00072c6ef2a02f9817) · Bilgi sorularına verilen asistan yanıtları | Belirtilmemiş | Apache 2.0 |
| Türkçe | 2.500 | [cturan / Turkish Synthetic Corpus](https://huggingface.co/datasets/cturan/turkish-synthetic-corpus/tree/fa602a833012ba9390f573ab44828aade1a7609e) · Dil modelinin Türkçe yazdığı metinler. Yazar, üretimde [Hugging Face SmolLM Corpus](https://huggingface.co/datasets/HuggingFaceTB/smollm-corpus) sorularından ve üretim yönteminden yararlandığını belirtiyor. | Belirtilmemiş | [ODC Attribution 1.0](https://opendatacommons.org/licenses/by/1-0/) |
| İngilizce | 2.500 | [Hugging Face TB / Cosmopedia-100k](https://huggingface.co/datasets/HuggingFaceTB/cosmopedia-100k/tree/8fdb6dada238c1d46dd8cf61da2fb4f9c36f654d) · Hikâye, blog yazısı ve öğretici metin gibi türler | Mixtral-8x7B-Instruct-v0.1 | Apache 2.0 |
| İngilizce | 2.500 | [Hugging Face TB / SmolTalk](https://huggingface.co/datasets/HuggingFaceTB/smoltalk/tree/5feaf2fd3ffca7c237fc38d1861bc30365d48ffa) · Smol-Magpie-Ultra alt kümesinden asistan yanıtları | Llama-3.1-405B-Instruct | Apache 2.0 |

Apache lisansı bu klasördeki `Apache-2.0.txt` dosyasındadır. Alt kümelerden yapılan seçme, alan ayıklama ve biçim değişikliği bu derlemeye aittir. Her kaynağın atıf ve lisans bilgisi kendi kayıtları için geçerlidir.

## Kayıtları kullanma

Sınıflandırıcının girdisi `text`, hedefi `label` alanıdır. `language` alanı `tr` veya `en` değerini alır. `generator` alanında model adı biliniyorsa adı, bilinmiyorsa JSON `null` değeri bulunur. `word_count` boşlukla ayrılmış sözcüklerin sayısıdır.

Her metin özgün kaynağına kadar izlenebilir. `source` veri kümesini, `source_revision` sabit sürümü, `source_file` dosyayı belirtir. `source_record` içindeki `byte:` değeri JSONL dosyasında satırın başladığı bayt konumudur. `row:` değeri Parquet dosyasında sıfırdan başlayan satır numarasıdır.

## Seçim ve doğrulama

- Türkçe örnekler kaynak dosyalarının farklı bölgelerinden, İngilizce örnekler her alt kümenin ilk eğitim dosyasından seçildi. Seçim ve son karıştırma için rastgelelik tohumu 42 kullanıldı.
- Her belgeden veya konuşmadan bir metin alındı. Sohbet kayıtlarında yalnızca ilk asistan yanıtı alındı. Kullanıcı soruları ve ayrı akıl yürütme alanları dışarıda bırakıldı.
- Metinler 50–900 sözcükle sınırlandı. Üç ters tırnak içeren kod blokları ve bazı açık model öz referansları elendi. Metinlerin başındaki ve sonundaki boşluklar temizlendi.
- Her metnin baskın dili Lingua 2.2.0 ile kontrol edildi. Aynı metnin büyük-küçük harf, boşluk veya Unicode biçimi farkıyla yinelenmesini önlemek için NFKC normalleştirmesi, harf katlama ve boşluk birleştirme uygulandı. `id` bu biçimin SHA-256 özetidir. Soru veya komut mevcut olduğunda onun da normalleştirilmiş tekrarı elendi.
- Aynı konunun farklı ifadeleri kalabilir. Eğitim ve test kümelerini oluştururken benzer konu ve kaynak kayıtlarını birlikte tutmak, ezberlemenin başarı ölçümünü şişirmesini önlemeye yardımcı olur.

Bu dosya dedektörün yapay zekâ sınıfını karşılar. İnsan sınıfını eklerken her iki dilde de benzer konulara, metin türlerine ve uzunluklara sahip örnekler seçmek, modelin yazarlıkla ilgisiz ipuçlarını öğrenme riskini azaltır.
