# Отчёт по результатам бенчмаркинга моделей  
(BCI, Adaptive Supervised PatchNCE, PPT)

---

## 1. Результаты экспериментов

### 🔹 BCI
**Датасет:** BCI  
- PSNR: **18.064**  
- SSIM: **0.3674**

_Сравнение с метриками из статьи:_  
> В оригинальной статье BCI сообщалось о значительно более высоких значениях SSIM (0.477) и PSNR (21.160) на этом же датасете. Полученные результаты ниже заявленных.
 Был заметен тренд на переобчуение модели (падение метрик на эпохах > 60)

 _Пример сгенерированных и реальных изображений_  
| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/bd1d6a1c-7b1d-409c-a71a-903c9672ac84" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/e927e1c8-440d-48e9-b071-525d8905f45d" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/32c40ac2-bde1-43c0-99cf-551fde16fd54" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/7fe99d6b-4fc3-42b7-a1cb-325a49c0d728" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/0e3403bc-23e1-47db-8217-833b429701be" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/9c67e3b9-76ef-4609-b879-ed09f77f2323" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/c37caffe-e073-447e-afb6-007ba0cfd329" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/2359bfec-678d-4d0c-9582-c9a22a9f2469" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/e0a1e595-6d55-4925-afc8-9af85fe592f7" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/cb201023-c213-4072-836f-9306b176b78e" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/60e57faa-7fa3-40ef-8bdf-fe8ca7021725" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/08fd1aa7-3dc1-4a33-abf7-b722d04e51ae" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/b772fe7a-81e4-4e62-825a-8109fb896952" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/921f89ec-e262-437e-8e28-78c55f250196" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/cf7f8095-2a64-4e83-a335-fc2ce876b346" />|

---

### 🔹 PPT (MICCAI 2024)
**Датасет:** PAX5  
- SSIM: **0.2469**  
- PSNR: **12.8244**  
- LPIPS: **0.5808**  
- FID: **85.7034**

**Примечание:**  
Модель генерирует изображения **1000×1000** (дефолтный параметр обучения).  
Эталонные изображения имеют размер **2000×2000**.  
Сравнение проведено после растяжения сгенерированных изображений до 2000×2000.  
В статье не указано, каким образом авторы проводили сравнение.  
Возможно, сжатие эталонных изображений могло бы дать другие метрики.

 _Пример сгенерированных и реальных изображений_  
| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/6fe21182-07d8-4d25-8aec-029ccec17395" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/f1710028-b44d-41d1-8497-ce184d117094" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/2903c3c1-62cf-432b-99a6-15e21c03fc99" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/8cd2a92c-e5b4-436c-afbc-7fc5b6764d95" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/edeb5f74-8cda-4a40-a503-bbb7c1e5eb17" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/04d4c654-91a5-46e6-97fa-c30430681aa0" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/d9c52eac-f453-4afd-a6d4-060fa690ab5f" /> |<img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/f944871f-8be5-46f0-aa3c-b01ac895b52c" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/edd831e2-f96c-4ac5-8a95-f8e8d00fb828" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/2b875abe-176f-498b-b4c3-509fb9864793" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/d21b2a26-2cee-43ee-a8a5-4f9c87c9f473" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/7c78dd4d-d373-4580-ba8c-c1bd682a72d1" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/f2149932-0390-4b9e-a049-dad3d0ec6cc9" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/7ed972c9-c363-4adf-8722-96c6228d15d2" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/ad98c308-e9c4-4088-bc86-23a8ee449c72" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/e2d4dda0-c38e-4197-951a-0234e77f4c58" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/aa106fb8-b5c0-4139-b9b7-cf6b93c4fae5" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/63e76f4c-387f-4d66-8de3-b4620dc53009" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/ee0fc054-dad4-4678-9045-5beda2e78846" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/50a00b57-07fa-4331-8532-c0808d8fe5c9" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/52beebbc-c9cf-4808-824b-793e4e7cb07b" />|

---

### 🔹 Adaptive Supervised PatchNCE (NCE) (MICCAI 2023)
**Датасет:** MIST (папка HER2)  


- Perceptual Hash (ResNet50):  
  [0.4837, 0.4422, 0.2710, 0.8186], avg: **0.503875** 
- FID: **49.35**  
- PSNR: **14.54**  
- SSIM: **0.2161**
- KID: **11.1**

_Сравнение с метриками из статьи:_  
> Авторы NCE (LASP) заявляют:  
> - SSIM: **0.2004**  
> - PHVT = 001: layer1 = 0.4534, layer2 = 0.4150, layer3 = 0.2665, layer4 = 0.8174, avg = **0.4881**  
> - FID: **51.4**  
> - KID: **12.4**  
> Наши результаты очень похожи на заявленные.  

 _Пример сгенерированных и реальных изображений_  
| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/397bb978-efd2-4a63-ba03-31a10cc93549" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/d9f9e0b6-acfe-423d-b6eb-c2bb53ccaea5" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/8284216f-7ce9-4d07-b199-bc8fa33ac11f" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/22726c95-0ca2-4a2c-9077-c9dd0ac2e615" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/6e7c6fc4-30d0-486e-be46-1f24c9d60210" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/f73b8085-6ccf-4282-a888-c088f5207967" />|
|<img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/a5505155-ea9c-4d51-8786-699a7aee13e3" /> |<img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/2d4abe8e-e948-49a2-946c-1a95f78028d1" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/00031912-f32a-4bb1-9b6b-3dbc1025d2b1" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/969655f4-596d-4d4d-a3a4-790a65647e58" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/e0c3e9eb-3f76-4c62-a7e9-47edc3c58091" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/414e7830-d305-4195-aa25-3b574bd1f9d2" />|
| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/2019e365-4f81-41e4-bb87-fdbe60fd82db" />| <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/6dac11e6-e2b3-4172-b179-96437952ad98" /> | <img width="4096" height="4096" alt="image" src="https://github.com/user-attachments/assets/10ee01bc-ae90-47d2-98d0-1f3d7b78ec62" />|
---

## 2. Сравнительный анализ моделей

| Модель | Датасет | PSNR ↑ | SSIM ↑ | LPIPS ↓ | FID ↓ | Примечание |
|--------|---------|--------|--------|---------|-------|------------|
| **BCI (наш)** | BCI | 18.064 | 0.3674 | – | – | Последняя эпоха, переобученная |
| **BCI (статья)** | BCI | 21.160 | 0.477 | – | – | Заявленные значения |
| **PPT (наш)** | PAX5 | 12.8244 | 0.2469 | 0.5808 | 85.7034 | Сравнение с рескейлом |
| **PPT (статья)** | PAX5 | 17.4063 | 0.35480 | 0.2988 | 80 | Заявленные значения |
| **NCE (наш)** | MIST/HER2 | 14.54 | 0.2161 | – | 49.35 | KID = 11.1 avg PHVT = 0.503875 |
| **NCE (статья, LASP)** | MIST | – | 0.2004 | – | 51.4 | KID = 12.4, avg PHVT = 0.4881 |

---

## 3. Вывод
  Все модели показали результаты ниже заявленных, за исключением NCE, где метрики оказались близки к метрикам из статьи. При этом изображения NCE стремятся полностью скопировать структуру с исходного изображения. 

