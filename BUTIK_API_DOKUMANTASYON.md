# ButikSistem RESTful WebService V1.1.14

**Resmi dokümantasyon (Postman):** https://documenter.getpostman.com/view/7476028/TVYGde1H

Kaynak: Gelistir Information Techs.  
Base URL (test): `https://test.butiksistem.com/rest/`  
Canlı (Tuba): `BUTIK_API_URL` ile (örn. `https://tm2.butiksistem.com/rest/`). Giriş: `BUTIK_API_USER`, `BUTIK_API_PASS`.

Tüm isteklerde gövde örneği:
```json
{
  "auth": {
    "userName": "test",
    "password": "9UFsuDYfsN5EKmUS"
  },
  "arguments": { ... }
}
```

---

## Product (Ürün)

### AddBrand
- **POST** `https://test.butiksistem.com/rest/product/addBrand`
- Parametreler: `name` (string), `code` (string)

### UpdateCategory
- **POST** `https://test.butiksistem.com/rest/product/updateCategory`
- selectArguments: `id`; updateArguments: `sortNum`, `parentId`, `name`, `visibility`, `status`, `description`

### DeleteCategory
- **POST** `https://test.butiksistem.com/rest/product/deleteCategory`
- Parametreler: `id`

### ProductAdd
- **POST** `https://test.butiksistem.com/rest/product/add`
- Ürün ekler. Gerekli: `modelCode`, `name`, `colorId`, `typeId`, `brandId`, `salePrice`, `taxRate`, `variants` (variantName, quantity). Opsiyonel: `description`, `images`, `status`, vb.
- Cevap: `batchRequestId` (asenkron işlem)

### ProductGet
- **POST** `{BUTIK_API_URL}product/get`
- **Gövde:** `{ "auth": { "userName": "...", "password": "..." }, "arguments": { ... } }`
- **Parametreler (arguments; hepsi opsiyonel filtre):** `ids`, `status` (1=aktif), `typeId`, `colorId`, `brandId`, `modelCode`, `modelCodes` (dizi), `productCode`, `colorCode`, `responseType` ("json"|"xml"). **Ürün kodu eşleşmesi:** Sitedeki "Ürün Kodu" (örn. 2209-t1) Butik'te **ayrı iki alan**: `modelCode` (2209) ve `colorCode` (t1). Tek parametreyle "2209-t1" gönderirsen `recordNotFound` dönebilir; `arguments: { "modelCode": "2209", "colorCode": "t1" }` ile ara. Parametre yoksa veya sadece `status: 1` ile tüm aktif ürünler istenebilir (XML alternatifi).
- **Cevap:** `{ "status": true, "result": { "total": N, "data": [ { "id", "name", "modelCode", "salePrice"/"price", "variants"/"variantsList", "quantity"/"stock"/"totalQuantity", ... } ] } }`

### ProductUpdate
- **POST** `https://test.butiksistem.com/rest/product/update`
- selectArguments: `ids`, `status`, `typeIds`, `brandIds`, `modelCodes`
- updateArguments: `name`, `price`, `details`, `taxRate`, `status`, `costPrice`, `images`, `brandId`, `categoryId`, vb.

---

## Order (Sipariş)

### GetSituations
- **POST** `https://test.butiksistem.com/rest/order/getSituations`
- Sipariş durumları listesi (orderStatusId değerleri).
- Örnek cevap: 1=Ödeme Bekliyor, 2=Sipariş alındı, 3=Onaylandı, 4=Onaylanmadı, 5=Kargoya Verildi, 6=Teslim edildi, 7=İade edildi, 8=İptal edildi.

### GetCustomSituations
- **POST** `https://test.butiksistem.com/rest/order/getCustomSituations`
- Özel durum listesi (orderCustomStatusId).

### OrderAdd (Sipariş oluştur)
- **POST** `https://test.butiksistem.com/rest/order/add`
- Yeni sipariş ekler.
- **arguments (doğrudan, selectArguments yok):**
  - **customOrderId** (string) – Sizin sipariş numaranız.
  - **orderDate** (string) – YYYY-MM-DD veya YYYY-MM-DD HH:mm:ss.
  - **orderPaymentTypeId** (int) – GetPaymentType ile alınır.
  - **orderShippingValue** (float), **orderProductsValue** (float) – Toplam ürün tutarı.
  - **description** (string), **orderPaymentConfirmStat** (0|1, opsiyonel), **orderStatusId** (opsiyonel), **orderCustomStatusId** (opsiyonel).
  - **delivery:** name, surName, mail, phone, address, city, district; opsiyonel: cargoCompanyId, cargoCompanyCode, cargoPlaceOfDelivery ("branch"|"home"), **whoPaysShipping** ("recipient"|"sender"), cargoCampaignCode, phoneCode.
  - **billing:** name, surName, mail, phone, address, city, district; opsiyonel: taxOffice, taxNumber, phoneCode.
  - **items:** liste; her eleman: **variantId**, **quantity**, price (opsiyonel).

Müşteri kargo ödemeli (değişim) için: `delivery.whoPaysShipping: "recipient"`.

Örnek istek:
```json
{
  "auth": { "userName": "test", "password": "9UFsuDYfsN5EKmUS" },
  "arguments": {
    "customOrderId": "2416",
    "orderDate": "2020-10-15",
    "orderPaymentTypeId": 6,
    "orderShippingValue": 10,
    "orderProductsValue": 249.99,
    "orderPaymentConfirmStat": 1,
    "orderStatusId": 3,
    "orderCustomStatusId": 2,
    "description": "test order",
    "delivery": {
      "name": "Ali",
      "surName": "UNSAL",
      "mail": "test@butiksistem.com",
      "phone": "5068942626",
      "address": "atakent mah. 241. sok. terrace tema",
      "city": "Eskişehir",
      "district": "Odunpazarı",
      "cargoCompanyId": "3",
      "cargoCampaignCode": "XYASTBFDF",
      "phoneCode": 92
    },
    "billing": {
      "name": "Hasan",
      "surName": "Basri",
      "mail": "test2@butiksistem.com",
      "phone": "5068942626",
      "address": "atakent mah. 241. sok. terrace tema",
      "city": "Eskişehir",
      "district": "Odunpazarı",
      "phoneCode": 85
    },
    "items": [
      { "variantId": "5287", "quantity": 1 }
    ]
  }
}
```

Örnek cevap: `{ "status": true, "result": 1580 }` – result = oluşan siparişin id’si.

### OrderGet
- **POST** `https://test.butiksistem.com/rest/order/get`
- Sipariş listesi. **arguments:** `id` (int), `customOrderId` (string), `orderStatusId` (int), `orderPaymentTypeId` (int), `startTime` (YYYY-MM-DD HH:MM), `endTime` (YYYY-MM-DD HH:MM). Start/end kullanılıyorsa aralık en fazla 30 gün olmalı. Genel filtreler (orderStatusId, orderPaymentTypeId) zaman argümanı olmadan kullanılamaz.
- **Cevap:** `result.total`, `result.data[]` – her sipariş: `id`, `customOrderId`, `deliveryFirstName`, `deliveryLastName`, `deliveryCity`, `deliveryDistrict`, `deliveryAddress`, `deliveryPhone`, `billingFirstName`, `billingLastName`, `billingCity`, `billingDistrict`, `billingAddress`, `billingPhone`, `orderEmail`, `orderDateTime`, `orderDeliveryDateTime`, `orderProductsValue`, `orderShippingValue`, `orderAmount`, `orderStatusId`, `orderCustomStatusId`, `orderPaymentTypeId`, `shippingCargoCompanyId`, `shippingBarcodeCreateDateTime`, `shippingTrackCode`, `items[]` (id, productId, variantName, qty, price, statusId, productModelCode, productColorCode).

Örnek istek: `arguments: { "customOrderId": "388" }`  
Örnek cevap yapısı:
```json
{
  "status": true,
  "result": {
    "total": 1,
    "data": [
      {
        "id": 1621,
        "customOrderId": "388",
        "deliveryFirstName": "Ali",
        "deliveryLastName": "UNSAL",
        "deliveryCity": "Eskişehir",
        "deliveryDistrict": "Odunpazarı",
        "deliveryAddress": "atakent mah. 241. sok. terrace tema",
        "deliveryPhone": "5068942626",
        "billingFirstName": "5068942626",
        "billingLastName": "Basri",
        "billingCity": "Eskişehir",
        "billingDistrict": "Odunpazarı",
        "billingAddress": "atakent mah. 241. sok. terrace tema",
        "billingPhone": "5068942626",
        "orderEmail": "test@butiksistem.com",
        "orderDateTime": "2021-10-17 01:48:04",
        "orderProductsValue": 249.99,
        "orderShippingValue": 10,
        "orderAmount": 259.99,
        "orderStatusId": 3,
        "orderCustomStatusId": 2,
        "orderPaymentTypeId": 6,
        "shippingCargoCompanyId": 3,
        "items": [
          {
            "id": 658,
            "productId": 1550,
            "variantName": "STD",
            "qty": 7,
            "price": 111.8,
            "productModelCode": "10-0016",
            "productColorCode": "815"
          }
        ]
      }
    ]
  }
}
```

### OrderUpdate
- **POST** `https://test.butiksistem.com/rest/order/update`
- Sipariş günceller. Gönderilen alanlar güncellenir; diğerleri değişmez.
- **selectArguments:** `customOrderId` (string) – sizin sipariş numaranız (zorunlu).
- **updateArguments** (hepsi opsiyonel):
  - `orderDate` (string, YYYY-MM-DD HH:mm:ss)
  - `orderPaymentTypeId` (int – GetPaymentType)
  - `orderShippingValue`, `orderProductsValue` (float), `description` (string)
  - `orderPaymentConfirmStat` (0|1, ön ödemede onay)
  - `orderStatusId` (GetSituations), `orderCustomStatusId` (GetCustomSituations)
  - **delivery:** name, surName, mail, phone, address, city, district; opsiyonel: cargoCompanyId, cargoCompanyCode, cargoPlaceOfDelivery ("branch"|"home"), **whoPaysShipping** ("recipient"|"sender")
  - **billing:** name, surName, mail, phone, address, city, district; opsiyonel: taxOffice, taxNumber
  - **items:** liste; her eleman: variantId, quantity, price (opsiyonel). Sayısal alanlarda otomatik tip dönüşümü vardır.

Değişimde müşteri kargo ödemesi için: `delivery.whoPaysShipping: "recipient"` kullanılır.

Örnek istek gövdesi:
```json
{
  "auth": { "userName": "test", "password": "9UFsuDYfsN5EKmUS" },
  "arguments": {
    "selectArguments": { "customOrderId": "390" },
    "updateArguments": {
      "delivery": {
        "city": "Eskişehir",
        "district": "Odunpazarı",
        "address": "test delivery address",
        "cargoCompanyId": 1,
        "cargoPlaceOfDelivery": "branch",
        "whoPaysShipping": "recipient",
        "phone": "5554443322",
        "mail": "test@test.com"
      },
      "billing": {
        "name": "ali",
        "city": "Eskişehir",
        "address": "test billing address",
        "district": "Tepebaşı",
        "taxOffice": "Halkalı",
        "taxNumber": "38035351544",
        "phone": "5554443322",
        "mail": "test@test.com"
      },
      "orderProductsValue": 150,
      "orderShippingValue": 50,
      "orderStatusId": 3,
      "orderPaymentTypeId": 1,
      "orderCustomStatusId": 2
    }
  }
}
```

---

## Address
(Dökümanda bölüm adı var; detay bu paste’te yok.)

---

## Cargo

### GetBarcode (Kargo barkod listesi)
- **POST** `https://test.butiksistem.com/rest/cargo/getBarcodes`
- Siparişe ait kargo barkodlarını listeler. **En az bir** argument zorunlu.
- **arguments:** `id` (int) veya `customOrderId` (string).

Örnek istek:
```json
{
  "auth": { "userName": "test", "password": "9UFsuDYfsN5EKmUS" },
  "arguments": { "customOrderId": "1473" }
}
```

Örnek cevap:
```json
{
  "status": true,
  "result": {
    "total": 1,
    "data": [
      {
        "id": 306,
        "orderId": 1473,
        "customOrderId": null,
        "cargoCompanyName": "mng",
        "cargoBarcodeValue": "1473309",
        "cargoBarcodeGlobalValue": "994797439747",
        "cargoBarcodeDeciValue": null,
        "cargoRecordCreateDateTime": "2019-08-07 14:36:51"
      }
    ]
  }
}
```

---

## BatchRequest, AffiliateAccount, WhatsappClient, WhatsappQueue
(Dökümanda bölüm adları var; detay bu paste’te yok.)

---

## WhatsappClient

### Get
- **POST** `https://test.butiksistem.com/rest/whatsappClient/get`
- Parametreler: `id` (opsiyonel)
- Mesaj kuyruğu listesi. Cevap gövdesi dokümanda boş bırakılmış.

---

## Proje İhtiyaçları (Referans)

- **Sipariş oluşturma:** **OrderAdd** (`POST /rest/order/add`) ile yeni sipariş oluşturulur; `customOrderId`, `delivery`, `billing`, `items` (variantId, quantity) zorunlu. Değişim siparişinde müşteri kargo ödemeli için `delivery.whoPaysShipping: "recipient"` kullan.
- **Kargo (müşteri ödemeli değişim):** **OrderAdd** ve **OrderUpdate** içinde `delivery.whoPaysShipping: "recipient"` ile kargo bedelini müşteriye yüklenir.
- **Kargo barkod:** **Cargo GetBarcode** (`POST /rest/cargo/getBarcodes`) ile `customOrderId` veya `id` verilerek siparişin kargo barkodları (cargoCompanyName, cargoBarcodeValue, cargoBarcodeGlobalValue, shippingTrackCode vb.) alınır.
- **Mevcut kod:** `butiksistem_client.py` içinde sadece sipariş okuma (get_orders, check_order_by_phone) var; `order/add` ve `order/update` entegrasyonu eklenmedi.

Bu dosya sipariş/kargo/ürün entegrasyonu yaparken başvuru için güncellenebilir.
