---

# Отчёт по результатам бенчмаркинга моделей

(BCI, Adaptive Supervised PatchNCE, PPT, PSPStain)

---
Сноска за 03.10.2025: 

* Проведено переобучение модели BCI (PyramidPix2Pix) с разрешением изображения **1024x1024** (вместо изначального с сжатием изображения до **324x324** и последующей обрезкой до **256x256**). После чего был проведён перерасчёт метрик. При повторном тестировании метрики не увеличились (если запускать без изменения параметров). Однако, значения скрипта тестирования по умолчанию также работает с изображениями по той же схеме (сжимает до размерности **256x256**). Был проведён перетест с отключением сжатия изображений. В результате удалось добиться метрики SSIM, указанной в статье (**0.47**). PSNR при этом остался на том же уровне (18.0).

* Было произведено обучение модели из статьи PSPStain https://arxiv.org/pdf/2407.03655 . Обучение проводилось на датасете **MIST**. Метрики PSNR и SSIM, указанные в статье, были достигнуты (SSIM **0.198** при заявленных **0.187**, PSNR **14.31** при заявленных **14.19**)


https://jupyter-zh.skoltech.ru/hub/user-redirect/lab/tree/benchmarking/PSPStain/results/MIST/val_pretrained/images

* Ниже обновлённый репорт за предыдущие недели (добавлено небольшое описание моделей с вырезками из статьи и инструкции по воспроизведению экспериментов (в данный момент не получится воспроизвести, т.к. требуется перенос виртуальной среды Conda на общую среду Zhores)
---


## 1. Результаты экспериментов

### 🔹 BCI

#### Ссылка на статью: https://arxiv.org/pdf/2204.11425

#### Принцип работы модели

Для генерации изображений использовалась модель **PyramidPix2Pix**, которая расширяет классическую архитектуру Pix2Pix за счёт многоуровневой пирамидальной структуры.  
Основная идея заключается в том, что генератор строит изображение поэтапно: сначала на низком разрешении формируется грубая структура сцены, затем на каждом последующем уровне пирамиды добавляются детали и уточняются текстуры.  

<img width="730" height="334" alt="image" src="https://github.com/user-attachments/assets/56166070-f85c-4a5f-b131-ad5b59f2661f" />


---

**Датасет:** BCI

* PSNR: **18.064**
* SSIM: **0.3674**

*Сравнение с метриками из статьи:*

> В оригинальной статье BCI сообщалось о значительно более высоких значениях SSIM (0.477) и PSNR (21.160) на этом же датасете. Полученные результаты ниже заявленных.
> Был заметен тренд на переобчуение модели (падение метрик на эпохах > 60)

---

#### Воспроизведение результатов

```python
cd /gpfs/gpfs0/gubanov-lab/benchmarking/BCI/PyramidPix2pix
sbatch train_BCI.sh
# По завершении
cat logs/train_test_eval_bci_{job_num}.out

```

---

*Пример сгенерированных и реальных изображений*

| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/bd1d6a1c-7b1d-409c-a71a-903c9672ac84" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/e927e1c8-440d-48e9-b071-525d8905f45d" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/32c40ac2-bde1-43c0-99cf-551fde16fd54" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/7fe99d6b-4fc3-42b7-a1cb-325a49c0d728" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/0e3403bc-23e1-47db-8217-833b429701be" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/9c67e3b9-76ef-4609-b879-ed09f77f2323" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/c37caffe-e073-447e-afb6-007ba0cfd329" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/2359bfec-678d-4d0c-9582-c9a22a9f2469" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/e0a1e595-6d55-4925-afc8-9af85fe592f7" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/cb201023-c213-4072-836f-9306b176b78e" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/60e57faa-7fa3-40ef-8bdf-fe8ca7021725" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/08fd1aa7-3dc1-4a33-abf7-b722d04e51ae" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/b772fe7a-81e4-4e62-825a-8109fb896952" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/921f89ec-e262-437e-8e28-78c55f250196" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/cf7f8095-2a64-4e83-a335-fc2ce876b346" />|

---

### 🔹 PPT (MICCAI 2024)

#### Ссылка на статью: https://papers.miccai.org/miccai-2024/paper/0817_paper.pdf


#### Принцип работы модели


<img width="496" height="300" alt="image" src="https://github.com/user-attachments/assets/3823481a-b976-47f4-b8a1-f218ad8e000c" />


**Датасет:** PAX5

* SSIM: **0.2469**
* PSNR: **12.8244**
* LPIPS: **0.5808**
* FID: **85.7034**

**Примечание:**
Модель генерирует изображения **1000×1000** (дефолтный параметр обучения).
Эталонные изображения имеют размер **2000×2000**.
Сравнение проведено после растяжения сгенерированных изображений до 2000×2000.
В статье не указано, каким образом авторы проводили сравнение.
Возможно, сжатие эталонных изображений могло бы дать другие метрики.



---

#### Воспроизведение результатов

```bash
# Код воспроизведения PPT
cd /gpfs/gpfs0/gubanov-lab/benchmarking/PPT
sbatch train_ppt.sh
# по завершении тренировки
sbatch test_all_epochs.sh
# по завершении тестирования
sbatch evaluate_all.sh
cat logs/evaluate_all.out
 
```
---

*Пример сгенерированных и реальных изображений*

| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/6fe21182-07d8-4d25-8aec-029ccec17395" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f1710028-b44d-41d1-8497-ce184d117094" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/2903c3c1-62cf-432b-99a6-15e21c03fc99" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/8cd2a92c-e5b4-436c-afbc-7fc5b6764d95" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/edeb5f74-8cda-4a40-a503-bbb7c1e5eb17" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/04d4c654-91a5-46e6-97fa-c30430681aa0" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/d9c52eac-f453-4afd-a6d4-060fa690ab5f" /> |<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f944871f-8be5-46f0-aa3c-b01ac895b52c" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/edd831e2-f96c-4ac5-8a95-f8e8d00fb828" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/2b875abe-176f-498b-b4c3-509fb9864793" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/d21b2a26-2cee-43ee-a8a5-4f9c87c9f473" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/7c78dd4d-d373-4580-ba8c-c1bd682a72d1" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f2149932-0390-4b9e-a049-dad3d0ec6cc9" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/7ed972c9-c363-4adf-8722-96c6228d15d2" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/ad98c308-e9c4-4088-bc86-23a8ee449c72" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/e2d4dda0-c38e-4197-951a-0234e77f4c58" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/aa106fb8-b5c0-4139-b9b7-cf6b93c4fae5" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/63e76f4c-387f-4d66-8de3-b4620dc53009" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/ee0fc054-dad4-4678-9045-5beda2e78846" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/50a00b57-07fa-4331-8532-c0808d8fe5c9" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/52beebbc-c9cf-4808-824b-793e4e7cb07b" />|

---

### 🔹 Adaptive Supervised PatchNCE (NCE) (MICCAI 2023)

#### Ссылка на статью: https://arxiv.org/pdf/2303.06193

#### Принцип работы модели

<img width="518" height="337" alt="image" src="https://github.com/user-attachments/assets/68e78c33-3c4f-432b-840d-d38f7568be6a" />


**Датасет:** MIST (папка HER2)

* Perceptual Hash (ResNet50):
  [0.4837, 0.4422, 0.2710, 0.8186], avg: **0.503875**
* FID: **49.35**
* PSNR: **14.54**
* SSIM: **0.2161**
* KID: **11.1**

*Сравнение с метриками из статьи:*

> Авторы NCE (LASP) заявляют:
>
> * SSIM: **0.2004**
> * PHVT = 001: layer1 = 0.4534, layer2 = 0.4150, layer3 = 0.2665, layer4 = 0.8174, avg = **0.4881**
> * FID: **51.4**
> * KID: **12.4**
>   Наши результаты очень похожи на заявленные.


---

#### Воспроизведение результатов

```bash
# Код воспроизведения NCE
cd /gpfs/gpfs0/gubanov-lab/benchmarking/NCE
sbatch train_nce.sh
# по завершении тренировки
sbatch test_nce.sh
# по завершении тестирования
sbatch eval_nce.sh
cat logs/eval_nce_cascade_{job_num}.out
 
```

---

*Пример сгенерированных и реальных изображений*

| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/397bb978-efd2-4a63-ba03-31a10cc93549" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/d9f9e0b6-acfe-423d-b6eb-c2bb53ccaea5" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/8284216f-7ce9-4d07-b199-bc8fa33ac11f" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/22726c95-0ca2-4a2c-9077-c9dd0ac2e615" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/6e7c6fc4-30d0-486e-be46-1f24c9d60210" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f73b8085-6ccf-4282-a888-c088f5207967" />|
|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/a5505155-ea9c-4d51-8786-699a7aee13e3" /> |<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/2d4abe8e-e948-49a2-946c-1a95f78028d1" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/00031912-f32a-4bb1-9b6b-3dbc1025d2b1" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/969655f4-596d-4d4d-a3a4-790a65647e58" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/e0c3e9eb-3f76-4c62-a7e9-47edc3c58091" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/414e7830-d305-4195-aa25-3b574bd1f9d2" />|
| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/2019e365-4f81-41e4-bb87-fdbe60fd82db" />| <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/6dac11e6-e2b3-4172-b179-96437952ad98" /> | <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/10ee01bc-ae90-47d2-98d0-1f3d7b78ec62" />|


---

### PSPStain

#### Cсылка на статью: https://arxiv.org/pdf/2407.03655

#### Принцип работы модели

<img width="861" height="535" alt="image" src="https://github.com/user-attachments/assets/ace06e23-ec49-401a-8e86-70ffd2432ac8" />

**Датасет:** MIST (папка HER2)


*Пример сгенерированных и реальных изображений*

| H&E | HER2_Gen | HER2_Real |
|-----|----------|-----------|
|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/171f1983-7ade-4fc6-af35-d9b0ae9b9bd9" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/17c73a02-0482-46fd-a170-422124425e61" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/cda99b2c-dce4-48df-89d5-ecfde35288f0" />|
|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/ab36eff0-9485-4b46-a52a-02baf45992c8" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/97d6b351-bd46-4d7a-ac6e-fc3c1bd8f868" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/fe4d5cdc-15f2-4b42-8641-5d99dc6bd738" />|
|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/09790256-e999-4da3-92c0-652bcd4b3a59" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/178ea1a3-cecc-4ae5-bfcf-ea54fcfccc81" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/d0ba0ff3-fe34-48d2-8f4e-09a32cf22d59" />|
|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/895fd3d8-3811-496d-87a8-78f16525b494" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/c01e8133-d276-4912-8354-d7d6be02f8c1" />|<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/72216ac0-e606-4374-84ac-3041338467e3" />|


## 2. Сравнительный анализ моделей

| Модель                 | Датасет   | PSNR ↑  | SSIM ↑  | LPIPS ↓ | FID ↓   | Примечание                         |
| ---------------------- | --------- | ------- | ------- | ------- | ------- | -----------------------------------|
| **BCI (наш)**          | BCI       | 18.064  | 0.3674  | –       | –       | Последняя эпоха, переобученная     |
| **BCI (наш)**          | BCI       | 18.659  | 0.4771  | –       | –       | Значения при размере 1024x1024     |
| **BCI (статья)**       | BCI       | 21.160  | 0.4770  | –       | –       | Заявленные значения                |
| **BCI (наш)**          | MIST      | 15.1452 | 0.2179  | –       | –       | 65 эпоха                           |
| **BCI (Статья)**       | MIST      | 14.9122 | 0.1995  | –       | –       | Значения из замеров в PSPStain     |
| **PPT (наш)**          | PAX5      | 12.8244 | 0.2469  | 0.5808  | 85.7034 | Сравнение с даунскейлом лейблов    |
| **PPT (наш)**          | PAX5      | 12.6126 | 0.3420  | 0.5792  | 88.3416 | Сравнение с апскейлом предсказаний |
| **PPT (статья)**       | PAX5      | 17.4063 | 0.3548  | 0.2988  | 80      | Заявленные значения                |
| **NCE (наш)**          | MIST/HER2 | 14.54   | 0.2161  | –       | 49.35   | KID = 11.1, avg PHVT = 0.503875    |
| **NCE (статья)**       | MIST      | –       | 0.2004  | –       | 51.4    | KID = 12.4, avg PHVT = 0.4881      |
| **PSPStain (наш)**     | MIST      | 14.3160 | 0.1983  | –       | -       | -                                  |
| **PSPStain (статья)**  | MIST      | 14.1948 | 0.1876  | –       | -       | -                                  |
| **PSPStain (наш)**     | BCI       | 19.3078 | 0.4553  | –       | -       | -                                  |
| **PSPStain (статья)**  | BCI       | 18.6220 | 0.4498  | –       | -       | -                                  |
---

### Сравнение по датасетам
| Модель                 | Датасет   | PSNR ↑  | PSNR (статья) ↑  | SSIM ↑  | SSIM (статья) ↑  |
| ---------------------- | --------- | ------- | ---------------- | ------- | ---------------- | 
| **BCI**                | MIST      | 15.1452 |   14.9122        | 0.2179  | 0.1995           | 
| **NCE**                | MIST      | 14.54   |-                 | 0.2161  | 0.2004           |
| **PSPStain**           | MIST      | 14.3160 |  14.1948         | 0.1983  | 0.1876           | 
| **PPT**                | MIST      | 13.2422 |  14.1948         | 0.1744  | 0.1876           | 
---

## 3. Вывод

Большинство моделей повторяет метрики из статей.

---
