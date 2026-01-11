# 🎓 Üniversite Ders Kayıt Simülasyon Sistemi

![Lisans](https://img.shields.io/badge/license-MIT-blue.svg) ![Node.js](https://img.shields.io/badge/node-%3E%3D16.0.0-green) ![Durum](https://img.shields.io/badge/status-aktif-success)

> Önkoşullar, ders çakışmaları, öncelik algoritmaları ve kota yönetimi gibi karmaşık üniversite kayıt dinamiklerini modelleyen full-stack bir simülasyon motoru.

## 📖 Proje Hakkında

Bu proje, gerçek dünyadaki akademik kayıt senaryolarını simüle etmek ve analiz etmek için tasarlanmış kapsamlı bir **Ders Kayıt Sistemi**dir. Standart kayıt portallarının aksine, bu sistem; zaman çakışmaları, yoğun yük ve karmaşık önkoşul zincirleri gibi çeşitli kısıtlamalara karşı kayıt mantığını "stres testine" tabi tutabilen özel bir simülasyon motoruna sahiptir.

Hem işlevsel bir web uygulaması hem de akademik araştırmalar, sistem davranışı analizi ve algoritmik optimizasyon çalışmaları için bir araç olarak hizmet verir.

## ✨ Temel Özellikler

### Çekirdek Simülasyon Mantığı
* **Çakışma Tespit Motoru:** Öğrenci ders programlarındaki zamansal örtüşmelerin gerçek zamanlı analizi.
* **Önkoşul Zinciri Doğrulama:** Akademik uygunluğu sağlamak için yinelemeli (recursive) tarama.
* **Öncelik Tabanlı Kayıt:** Kıdem, GPA veya bölüm gereksinimlerine göre ağırlıklandırılmış sıralama algoritmaları.
* **Dinamik Kota Yönetimi:** Ders kapasiteleri ve bekleme listelerinin (Waitlist) tutarlı ve güvenli yönetimi.

### Analiz ve Raporlama
* **Performans Metrikleri:** Kayıt başarı oranları ve sistem tıkanıklıkları hakkında detaylı istatistikler.
* **Bekleme Listesi Mantığı:** Otomatik yükseltme özellikli FIFO (İlk Giren İlk Çıkar) işleme yapısı.

## 🏗 Sistem Mimarisi

Proje, simülasyon mantığını API katmanından ve arayüz sunumundan ayıran modüler bir **MVC (Model-View-Controller)** yapısını takip eder.

```bash
course-reg-sim/
├── server/
│   ├── src/
│   │   ├── core/           # 🧠 Beyin: Simülasyon Algoritmaları
│   │   │   ├── catalog.js  # Ders yönetimi
│   │   │   ├── conflict.js # Zaman çakışması tespiti
│   │   │   ├── prereq.js   # Gereksinim mantık grafiği
│   │   │   ├── priority.js # Sıralama algoritmaları
│   │   │   └── simulate.js # Ana simülasyon döngüsü
│   │   ├── routes/         # REST API Uç Noktaları
│   │   ├── config/         # Ortam ve Yetkilendirme Ayarları
│   │   └── index.js        # Sunucu Giriş Noktası
│   └── client/             # 🖥️ Hafif Ön Yüz (Vanilla JS)
└── package.json

