# MS-IA — Plan de Implementación Técnica

> **Rol en el sistema:** Microservicio de inteligencia artificial. Procesa imágenes del chofer y del bus antes de iniciar un viaje, ejecuta modelos de machine learning para predicción de demanda, segmentación de clientes y detección de anomalías en ventas. Expone endpoints REST para la app móvil y el frontend Angular.

---

## 1. Stack Tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.11+ |
| Framework | Flask | 3.0.x |
| WSGI Server | Gunicorn | 21.x |
| Visión — Identidad y estado | AWS Rekognition | boto3 1.34.x |
| Visión — Detección objetos | Roboflow API | inference-sdk latest |
| Visión — OCR texto | Google Vision API | google-cloud-vision 3.x |
| ML Supervisado | XGBoost + scikit-learn | 2.x + 1.4.x |
| ML No supervisado | scikit-learn (K-Means, Isolation Forest) | 1.4.x |
| Serialización modelos | joblib | 1.3.x |
| Scheduler reentrenamiento | APScheduler | 3.10.x |
| Storage | boto3 (S3) | 1.34.x |
| DynamoDB | boto3 | 1.34.x |
| HTTP client | requests | 2.31.x |
| Validación | Pydantic v2 | 2.x |
| Variables de entorno | python-dotenv | 1.0.x |
| Estándar de código | PEP 8 + Black + type hints | — |
| Contenedor | Docker | — |
| Despliegue | Azure Container Apps | — |

---

## 2. Estructura del Proyecto

```
ms-ia/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Entry point Flask
│   ├── config.py                        # Variables de entorno
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py                    # GET /health
│   │   ├── verificacion.py              # Verificación chofer y bus
│   │   ├── prediccion.py                # Predicción de demanda
│   │   ├── segmentacion.py              # Segmentación de clientes
│   │   └── anomalias.py                 # Detección de anomalías
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rekognition_service.py       # AWS Rekognition (facial + estado)
│   │   ├── roboflow_service.py          # Roboflow (detección placa y daños)
│   │   ├── vision_service.py            # Google Vision API (OCR placa)
│   │   ├── s3_service.py                # Subida y lectura de imágenes en S3
│   │   ├── dynamo_service.py            # Guardar inferencias y predicciones
│   │   ├── mscore_service.py            # Consultar datos de MS-Core
│   │   ├── prediccion_service.py        # XGBoost predicción demanda
│   │   ├── segmentacion_service.py      # K-Means segmentación clientes
│   │   ├── anomalia_service.py          # Isolation Forest anomalías
│   │   └── notificacion_service.py      # Push notifications (mock/real)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── demand_model.pkl             # XGBoost serializado (generado al entrenar)
│   │   ├── kmeans_model.pkl             # K-Means serializado
│   │   ├── isolation_forest_model.pkl   # Isolation Forest serializado
│   │   └── train/
│   │       ├── train_demand.py          # Script entrenar XGBoost
│   │       ├── train_segmentacion.py    # Script entrenar K-Means
│   │       └── train_anomalias.py       # Script entrenar Isolation Forest
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── verificacion.py              # Pydantic models request/response
│   │   ├── prediccion.py
│   │   ├── segmentacion.py
│   │   └── anomalias.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py               # Helpers: base64, crop, resize
│       └── datetime_utils.py            # Helpers Bolivia UTC-4
│
├── scripts/
│   └── create_dynamo_tables.py          # Crear tablas DynamoDB
│
├── docker-compose.yml                   # LocalStack para DynamoDB local
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt                 # black, flake8
└── .env.example
```

---

## 3. DynamoDB — Tablas

MS-IA usa dos tablas en DynamoDB.

### Tabla: `inferencias_ia`

Guarda el log de cada inferencia realizada para auditoría.

| Atributo | Tipo | Rol | Descripción |
|---|---|---|---|
| tipo_fecha | String | PK | `FACIAL#2026-05-22`, `BUS#2026-05-22` |
| timestamp_id | String | SK | `2026-05-22T21:30:00Z#req-uuid` |
| tipo | String | Atributo | `FACIAL`, `BUS_PLACA`, `BUS_DANOS` |
| viaje_id | String | Atributo | ID del viaje relacionado |
| chofer_id | String | Atributo | ID del chofer |
| bus_id | String | Atributo | ID del bus |
| input_s3_key | String | Atributo | Key de la imagen en S3 |
| resultado | Map | Atributo | JSON con el resultado completo |
| confianza | Number | Atributo | Nivel de confianza 0-1 |
| modelo_usado | String | Atributo | Nombre del servicio/modelo |
| tiempo_ms | Number | Atributo | Tiempo de inferencia en ms |
| created_at | String | Atributo | ISO timestamp |

**GSI:**
- `chofer-fecha-index`: PK=`chofer_id`, SK=`created_at` — historial por chofer

---

### Tabla: `predicciones_ml`

Cache de predicciones para no recalcular en cada request del dashboard.

| Atributo | Tipo | Rol | Descripción |
|---|---|---|---|
| tipo_entidad | String | PK | `DEMANDA#ruta-uuid`, `SEGMENTO#cliente-uuid` |
| fecha | String | SK | `2026-05-22` |
| valor_predicho | Number | Atributo | Ocupación esperada 0-1 |
| precio_sugerido | Number | Atributo | Precio en BOB |
| confianza | Number | Atributo | Confianza del modelo 0-1 |
| modelo_version | String | Atributo | `xgboost-v1`, `kmeans-v2` |
| generado_en | String | Atributo | ISO timestamp |
| expira_en | String | Atributo | ISO timestamp (TTL) |
| metadata | Map | Atributo | Datos adicionales del modelo |

---

## 4. API REST — Endpoints

Todos requieren `Authorization: Bearer <JWT>` excepto `/health`.

### Health

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | Público | Health check |

---

### Verificación — Chofer y Bus

| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| POST | `/verificacion/chofer` | CHOFER | Verificar identidad y estado del chofer |
| POST | `/verificacion/bus` | CHOFER | Verificar placa y daños del bus |
| GET | `/verificacion/viaje/{viaje_id}/estado` | CHOFER, ADMIN, SUPERVISOR | Estado de verificación del viaje |

---

**POST `/verificacion/chofer` — Body:**
```json
{
  "viaje_id": "uuid",
  "chofer_id": "uuid",
  "imagen_base64": "base64_de_la_selfie"
}
```

**POST `/verificacion/chofer` — Response exitosa:**
```json
{
  "verificado": true,
  "identidad": {
    "coincide": true,
    "confianza": 0.97
  },
  "estado": {
    "ojos_abiertos": true,
    "confianza_ojos": 0.98,
    "somnolencia_detectada": false,
    "estado_emocional": "CALM"
  },
  "puede_iniciar_viaje": true,
  "mensaje": "Verificación exitosa"
}
```

**POST `/verificacion/chofer` — Response con somnolencia:**
```json
{
  "verificado": false,
  "identidad": {
    "coincide": true,
    "confianza": 0.96
  },
  "estado": {
    "ojos_abiertos": false,
    "confianza_ojos": 0.91,
    "somnolencia_detectada": true,
    "estado_emocional": "CONFUSED"
  },
  "puede_iniciar_viaje": false,
  "mensaje": "Somnolencia detectada. Notificando al supervisor."
}
```

---

**POST `/verificacion/bus` — Body:**
```json
{
  "viaje_id": "uuid",
  "bus_id": "uuid",
  "chofer_id": "uuid",
  "imagenes_base64": [
    "base64_foto_1",
    "base64_foto_2",
    "base64_foto_3"
  ]
}
```

**POST `/verificacion/bus` — Response:**
```json
{
  "verificado": true,
  "placa": {
    "detectada": "3421-ABC",
    "esperada": "3421-ABC",
    "coincide": true,
    "confianza": 0.94
  },
  "danos": {
    "detectados": false,
    "alertas": []
  },
  "puede_iniciar_viaje": true,
  "mensaje": "Bus verificado correctamente",
  "imagenes_s3_keys": [
    "evidencias/viaje-uuid/bus-foto-1.jpg",
    "evidencias/viaje-uuid/bus-foto-2.jpg"
  ]
}
```

**POST `/verificacion/bus` — Response con daño detectado:**
```json
{
  "verificado": true,
  "placa": {
    "detectada": "3421-ABC",
    "esperada": "3421-ABC",
    "coincide": true,
    "confianza": 0.94
  },
  "danos": {
    "detectados": true,
    "alertas": [
      {
        "tipo": "damage",
        "confianza": 0.87,
        "imagen_s3_key": "evidencias/viaje-uuid/bus-foto-2.jpg"
      }
    ]
  },
  "puede_iniciar_viaje": true,
  "mensaje": "Daño detectado. Supervisor notificado. El viaje puede continuar."
}
```

> **Nota:** daño detectado NO bloquea el viaje, solo alerta al supervisor.
> Placa incorrecta SÍ bloquea el viaje.

---

**GET `/verificacion/viaje/{viaje_id}/estado` — Response:**
```json
{
  "viaje_id": "uuid",
  "chofer_verificado": true,
  "bus_verificado": true,
  "puede_iniciar": true,
  "detalle": {
    "chofer": {
      "identidad_ok": true,
      "estado_ok": true,
      "timestamp": "2026-05-22T20:45:00Z"
    },
    "bus": {
      "placa_ok": true,
      "danos_ok": true,
      "timestamp": "2026-05-22T20:40:00Z"
    }
  }
}
```

---

### Predicción de Demanda

| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/prediccion/demanda` | ADMIN, SUPERVISOR | Predicción de ocupación y precio sugerido |
| POST | `/prediccion/aprobar` | ADMIN | Aprobar precio sugerido → crea tarifa en MS-Core |
| POST | `/modelos/reentrenar` | ADMIN | Disparar reentrenamiento manual |

**GET `/prediccion/demanda?rutaId=uuid&fecha=2026-05-22` — Response:**
```json
{
  "ruta_id": "uuid",
  "fecha": "2026-05-22",
  "ocupacion_predicha": 0.94,
  "precio_base_actual": 85.00,
  "precio_sugerido": 98.00,
  "ajuste_porcentaje": 15.3,
  "confianza": 0.88,
  "factores": {
    "dia_semana": "viernes",
    "es_feriado": false,
    "temporada": "alta",
    "historico_promedio": 0.78
  },
  "desde_cache": false
}
```

**POST `/prediccion/aprobar` — Body:**
```json
{
  "ruta_id": "uuid",
  "fecha": "2026-05-22",
  "precio_aprobado": 98.00
}
```

> Al aprobar, MS-IA llama a MS-Core para crear una tarifa `TEMPORADA_ALTA` para esa fecha.

---

### Segmentación de Clientes

| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/segmentacion/clientes` | ADMIN | Segmentos de clientes con K-Means |
| GET | `/segmentacion/cliente/{cliente_id}` | ADMIN | Segmento de un cliente específico |

**GET `/segmentacion/clientes` — Response:**
```json
{
  "total_clientes": 245,
  "segmentos": [
    {
      "id": 0,
      "nombre": "Viajero frecuente",
      "descripcion": "Viaja 3+ veces al mes, gasto alto",
      "total_clientes": 45,
      "porcentaje": 18.4,
      "caracteristicas": {
        "frecuencia_promedio_mensual": 4.2,
        "gasto_promedio": 340.00,
        "ruta_preferida": "CBBA → SCZ"
      }
    },
    {
      "id": 1,
      "nombre": "Viajero ocasional",
      "descripcion": "Viaja 1-2 veces al mes",
      "total_clientes": 120,
      "porcentaje": 49.0
    },
    {
      "id": 2,
      "nombre": "Comerciante",
      "descripcion": "Rutas y días fijos, patrón regular",
      "total_clientes": 80,
      "porcentaje": 32.6
    }
  ],
  "modelo_version": "kmeans-v1",
  "generado_en": "2026-05-22T03:00:00Z"
}
```

---

### Detección de Anomalías

| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/anomalias/ventas` | ADMIN | Anomalías detectadas en ventas |
| GET | `/anomalias/vendedor/{usuario_id}` | ADMIN | Análisis de un vendedor específico |

**GET `/anomalias/ventas` — Response:**
```json
{
  "total_anomalias": 2,
  "anomalias": [
    {
      "vendedor_id": "uuid",
      "vendedor_nombre": "Carlos López",
      "tipo": "ALTA_TASA_CANCELACIONES",
      "valor_detectado": 0.23,
      "valor_promedio": 0.03,
      "score_anomalia": -0.45,
      "periodo": "últimos 7 días",
      "nivel_alerta": "ALTO"
    }
  ],
  "modelo_version": "isolation-forest-v1",
  "analizado_en": "2026-05-22T06:00:00Z"
}
```

---

## 5. Lógica de los Servicios

### 5.1 Flujo de verificación del chofer

```python
def verificar_chofer(viaje_id, chofer_id, imagen_base64):
    # 1. Subir imagen a S3
    s3_key = s3_service.subir_imagen(imagen_base64, f"facial/{viaje_id}/selfie.jpg")

    # 2. Obtener foto registrada del chofer desde MS-Core
    chofer = mscore_service.get_chofer(chofer_id)
    foto_registrada_s3_key = chofer["fotoFacialS3Key"]

    # 3. Comparar con AWS Rekognition
    resultado_identidad = rekognition_service.comparar_caras(
        s3_key_fuente=foto_registrada_s3_key,
        s3_key_objetivo=s3_key,
        umbral_confianza=90.0
    )

    # 4. Analizar estado del chofer (misma imagen)
    resultado_estado = rekognition_service.analizar_estado(s3_key)

    # 5. Determinar si puede iniciar viaje
    puede_iniciar = resultado_identidad["coincide"] and not resultado_estado["somnolencia"]

    # 6. Si hay problema → notificar supervisor
    if not puede_iniciar:
        notificacion_service.alertar_supervisor(viaje_id, resultado_identidad, resultado_estado)

    # 7. Guardar inferencia en DynamoDB
    dynamo_service.guardar_inferencia(tipo="FACIAL", viaje_id=viaje_id, resultado=...)

    return response
```

---

### 5.2 Flujo de verificación del bus

```python
def verificar_bus(viaje_id, bus_id, imagenes_base64):
    placa_detectada = None
    danos_detectados = []

    for i, imagen_base64 in enumerate(imagenes_base64):
        # 1. Subir cada imagen a S3
        s3_key = s3_service.subir_imagen(imagen_base64, f"evidencias/{viaje_id}/bus-{i}.jpg")

        # 2. Roboflow → detectar placa en la imagen
        resultado_placa = roboflow_service.detectar_placa(imagen_base64)
        if resultado_placa["encontrada"] and not placa_detectada:
            # 3. Recortar región de la placa
            imagen_recortada = image_utils.crop(imagen_base64, resultado_placa["bounding_box"])
            # 4. Google Vision → leer texto de la placa
            placa_detectada = vision_service.leer_texto(imagen_recortada)

        # 5. Roboflow → detectar daños
        resultado_danos = roboflow_service.detectar_danos(imagen_base64)
        if resultado_danos["danos"]:
            danos_detectados.extend(resultado_danos["danos"])

    # 6. Validar placa contra bus asignado
    bus = mscore_service.get_bus(bus_id)
    placa_coincide = placa_detectada == bus["placa"]

    # 7. Si daños detectados → notificar supervisor (no bloquear)
    if danos_detectados:
        notificacion_service.alertar_dano_bus(viaje_id, bus_id, danos_detectados)

    # 8. Si placa incorrecta → bloquear
    puede_iniciar = placa_coincide

    # 9. Guardar inferencias en DynamoDB
    dynamo_service.guardar_inferencia(tipo="BUS_PLACA", viaje_id=viaje_id, resultado=...)
    dynamo_service.guardar_inferencia(tipo="BUS_DANOS", viaje_id=viaje_id, resultado=...)

    return response
```

---

### 5.3 Predicción de demanda con XGBoost

**Features del modelo:**
- `dia_semana` — 0 (lunes) a 6 (domingo)
- `es_feriado` — 0 o 1
- `mes` — 1 a 12
- `semana_del_anio` — 1 a 52
- `es_temporada_alta` — 0 o 1 (vacaciones de julio, enero)
- `ocupacion_semana_anterior` — promedio histórico
- `ocupacion_mismo_dia_semana_pasada` — histórico

**Target:** `ocupacion` (0.0 a 1.0)

**Datos de entrenamiento para el MVP:**
Generar datos sintéticos con `scripts/generate_synthetic_data.py` que simule:
- Picos de ocupación los viernes y sábados
- Picos en feriados bolivianos (6 de agosto, Carnaval, Semana Santa)
- Temporada alta en enero y julio
- ~1000 registros sintéticos por ruta

**Serialización:**
```python
joblib.dump(model, 'app/models/demand_model.pkl')
```

---

### 5.4 Segmentación con K-Means

**Features:**
- `frecuencia_mensual` — viajes por mes
- `gasto_promedio` — en BOB
- `variedad_rutas` — número de rutas distintas usadas
- `dia_preferido` — día de la semana más frecuente (0-6)

**Número de clusters:** 3 (viajero frecuente, ocasional, comerciante)

Los datos se obtienen consultando MS-Core via HTTP antes de entrenar.

---

### 5.5 Detección de anomalías con Isolation Forest

**Features por vendedor (últimos 30 días):**
- `tasa_cancelaciones` — cancelaciones / total ventas
- `ventas_fuera_horario` — ventas después de las 22:00
- `ticket_promedio` — precio promedio cobrado
- `variacion_precio` — desviación estándar de precios cobrados

**Contaminación:** 0.05 (asume 5% de datos anómalos)

---

### 5.6 Reentrenamiento de modelos

**Manual via endpoint:**
```
POST /modelos/reentrenar
Body: { "modelo": "demand" | "kmeans" | "isolation_forest" | "all" }
```

**Automático con APScheduler:**
- XGBoost: reentrenar cada lunes a las 3:00 AM
- K-Means: reentrenar cada primer día del mes
- Isolation Forest: reentrenar cada semana

Al reentrenar:
1. Consultar datos frescos de MS-Core
2. Entrenar el modelo
3. Guardar nuevo `.pkl` sobrescribiendo el anterior
4. Loguear la versión y métricas del nuevo modelo

---

### 5.7 Estado de verificación del viaje

MS-IA guarda en DynamoDB el estado de verificación de cada viaje. La app móvil consulta este estado al cargar la pantalla de inicio de viaje para saber qué checklist ya está completado.

**Lógica:**
- Si existe inferencia `FACIAL` exitosa para el `viaje_id` → chofer verificado
- Si existe inferencia `BUS_PLACA` exitosa para el `viaje_id` → bus verificado
- Ambos en verde → `puede_iniciar = true`

---

## 6. Configuración de APIs Externas

### AWS Rekognition

Usar el método `CompareFaces` para identidad y `DetectFaces` para estado:

- `CompareFaces`: compara dos imágenes, retorna `FaceMatches` con `Similarity` (0-100)
- `DetectFaces`: analiza una imagen, retorna `FaceDetails` con `EyesOpen`, `Emotions`

Umbral de identidad: `Similarity >= 90`
Umbral somnolencia: `EyesOpen.Confidence < 70`

Las imágenes se pasan como referencia a S3 (no en base64 directamente) para mejor rendimiento:
```python
rekognition.compare_faces(
    SourceImage={'S3Object': {'Bucket': bucket, 'Name': key_foto_registrada}},
    TargetImage={'S3Object': {'Bucket': bucket, 'Name': key_selfie}},
    SimilarityThreshold=90
)
```

---

### Roboflow

Usar `inference-sdk` de Roboflow:

```python
from inference_sdk import InferenceHTTPClient

client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=ROBOFLOW_API_KEY
)

# Detección de placa
result = client.infer(imagen_base64, model_id="license-plate-detection/1")

# Detección de daños
result = client.infer(imagen_base64, model_id="vehicle-damage-detection/1")
```

> Los `model_id` exactos se obtienen desde la cuenta de Roboflow al seleccionar los modelos del universo público.

---

### Google Vision API

Usar `google-cloud-vision` para OCR del recorte de la placa:

```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()
image = vision.Image(content=imagen_bytes_recortada)
response = client.text_detection(image=image)
texto = response.text_annotations[0].description  # "3421-ABC"
```

Autenticación via variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` apuntando al archivo JSON de la service account.

---

## 7. Variables de Entorno

```env
# App
PORT=8002
ENVIRONMENT=development
FLASK_DEBUG=true

# JWT (misma secret que MS-Core)
JWT_SECRET=

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_EVIDENCIAS=bustrack-evidencias
S3_BUCKET_LICENCIAS=bustrack-licencias

# DynamoDB
DYNAMODB_ENDPOINT=http://localhost:4566   # LocalStack en desarrollo
DYNAMODB_TABLE_INFERENCIAS=inferencias_ia
DYNAMODB_TABLE_PREDICCIONES=predicciones_ml

# Roboflow
ROBOFLOW_API_KEY=
ROBOFLOW_MODEL_PLACA=license-plate-detection/1
ROBOFLOW_MODEL_DANOS=vehicle-damage-detection/1

# Google Vision
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-vision.json

# MS-Core
MS_CORE_URL=http://localhost:3000

# MS-Operaciones
MS_OPERACIONES_URL=http://localhost:8001

# Notificaciones Push (mock en desarrollo)
MOCK_PUSH_NOTIFICATIONS=true
EXPO_ACCESS_TOKEN=

# Modelos ML
MODELS_PATH=app/models/
REENTRENAR_AUTO=true

# Umbrales IA
UMBRAL_IDENTIDAD_FACIAL=90.0
UMBRAL_SOMNOLENCIA=70.0
UMBRAL_CONFIANZA_PLACA=80.0
UMBRAL_CONFIANZA_DANO=75.0
```

---

## 8. Docker

### docker-compose.yml (desarrollo local)

Solo levanta LocalStack para DynamoDB (mismo que MS-Operaciones, mismo puerto 4566):

```yaml
services:
  localstack:
    image: localstack/localstack:3.0
    ports:
      - "4566:4566"
    environment:
      - SERVICES=dynamodb
      - DEFAULT_REGION=us-east-1
    volumes:
      - localstack_data:/var/lib/localstack

volumes:
  localstack_data:
```

> Si MS-Operaciones ya está corriendo con LocalStack en el puerto 4566, MS-IA puede usar el mismo contenedor. No es necesario levantar dos instancias de LocalStack.

### Dockerfile

Multi-stage:
- **Stage 1 (build):** `python:3.11-slim`, instalar dependencias
- **Stage 2 (production):** copiar app y modelos `.pkl`, correr con Gunicorn

---

## 9. Orden de Implementación

1. **Setup inicial** — proyecto Flask, estructura de carpetas, health check, variables de entorno, PEP 8 con Black
2. **Docker** — LocalStack para DynamoDB (reusar el de MS-Operaciones si está corriendo)
3. **Script create_dynamo_tables.py** — crear `inferencias_ia` y `predicciones_ml`
4. **Schemas Pydantic** — todos los modelos de request y response
5. **S3Service** — subir y leer imágenes desde S3 (mock con carpeta local si `MOCK_S3=true`)
6. **DynamoService** — guardar y consultar inferencias y predicciones
7. **MSCoreService** — consultar chofer, bus y datos históricos via HTTP
8. **RekognitionService** — comparar caras y analizar estado (mock si `MOCK_REKOGNITION=true`)
9. **RoboflowService** — detectar placa y daños (mock si `MOCK_ROBOFLOW=true`)
10. **VisionService** — OCR de texto con Google Vision (mock si `MOCK_VISION=true`)
11. **Router verificacion** — endpoints de chofer y bus usando los servicios anteriores
12. **Scripts de entrenamiento** — generar datos sintéticos y entrenar XGBoost, K-Means, Isolation Forest
13. **PrediccionService** — XGBoost con cache en DynamoDB
14. **SegmentacionService** — K-Means consultando datos de MS-Core
15. **AnomaliaService** — Isolation Forest sobre datos de ventas
16. **Routers prediccion, segmentacion, anomalias**
17. **APScheduler** — reentrenamiento automático
18. **NotificacionService** — mock primero, Expo real después
19. **Dockerfile** — multi-stage para Azure Container Apps
20. **Pruebas** — probar todos los endpoints con Thunder Client

---

## 10. Mocks para Desarrollo

Cada servicio externo tiene un flag de mock en las variables de entorno:

| Variable | Servicio | Mock behavior |
|---|---|---|
| `MOCK_REKOGNITION=true` | AWS Rekognition | Retorna siempre identidad correcta, sin somnolencia |
| `MOCK_ROBOFLOW=true` | Roboflow API | Retorna placa detectada con bounding box fijo |
| `MOCK_VISION=true` | Google Vision | Retorna el texto "3421-ABC" directamente |
| `MOCK_S3=true` | AWS S3 | Guarda en carpeta local `tmp/ia-uploads/` |
| `MOCK_PUSH_NOTIFICATIONS=true` | Expo Push | Solo loguea la notificación |

Esto permite desarrollar y probar el flujo completo sin necesitar credenciales reales de ningún servicio.

---

## 11. Cambios en MS-Core

Antes de implementar MS-IA, agregar estos cambios en MS-Core:

**1. Endpoint para que MS-IA apruebe un precio sugerido:**
```
POST /tarifas/aprobar-sugerencia
Body: { rutaId, fecha, precioAprobado }
Roles: ADMIN
```
Crea una tarifa `TEMPORADA_ALTA` para esa fecha con el precio aprobado.

**2. Endpoint para consultar datos históricos de ventas (para entrenar modelos):**
```
GET /reportes/datos-entrenamiento?tipo=demanda|clientes|ventas
Roles: ADMIN (interno, solo MS-IA)
```
Retorna los datos en formato CSV o JSON para entrenar los modelos.

---

## 12. Cambios en el Frontend Angular

### 12.1 Dashboard — Predicción de demanda

En el módulo de Tarifas o Dashboard, agregar sección **"Predicciones de demanda"**:

- Selector de ruta y fecha
- Card con: ocupación predicha (%), precio actual, precio sugerido, botón "Aprobar precio"
- Al aprobar → llama a `POST /prediccion/aprobar` en MS-IA

```typescript
// environment.ts — agregar
iaUrl: 'http://localhost:8002'
```

### 12.2 Reportes — Segmentación de clientes

En el módulo de Reportes, agregar tab **"Clientes"**:

- Gráfica de torta ECharts con los 3 segmentos
- Cards con características de cada segmento
- Query: `GET {iaUrl}/segmentacion/clientes`

### 12.3 Reportes — Anomalías

En el módulo de Reportes, agregar tab **"Anomalías"**:

- Tabla de anomalías detectadas con nivel de alerta (badge rojo/amarillo)
- Detalle por vendedor
- Query: `GET {iaUrl}/anomalias/ventas`

### 12.4 Choferes — Historial de verificaciones

En el detalle del chofer, agregar sección **"Historial de verificaciones"**:

- Tabla con: fecha, viaje, resultado identidad, resultado estado, confianza
- Query: `GET {iaUrl}/verificacion/historial/chofer/{choferId}`

> Agregar este endpoint a MS-IA en el router de verificación.

---

## 13. Consideraciones Finales para el Agente

- **PEP 8 obligatorio.** Usar Black para formateo automático. Todos los archivos deben pasar `flake8` sin errores. Type hints en todas las funciones.
- **Lazy loading para modelos ML.** Los modelos `.pkl` se cargan en memoria solo cuando se necesitan por primera vez, no al arrancar el servicio.
- **Las imágenes llegan en base64** desde la app móvil. Siempre convertir a bytes antes de procesar: `image_bytes = base64.b64decode(imagen_base64)`.
- **Guardar siempre en S3 primero** antes de pasar la imagen a Rekognition o Roboflow. Rekognition trabaja mejor con referencias S3 que con base64 directo.
- **Timeout en APIs externas.** Configurar timeout de 10 segundos en todas las llamadas a Rekognition, Roboflow y Google Vision. Si timeout → retornar error claro, no colgar el request.
- **Puerto 8002** para no conflictuar con MS-Core (3000), MS-Blockchain (3001) y MS-Operaciones (8001).
- **Los modelos `.pkl` van en el repositorio** para el MVP. En producción real irían en S3 y se descargarían al arrancar el contenedor.
- **CORS.** Configurar Flask para aceptar requests desde `http://localhost:4200` (Angular) y la URL de producción de Vercel.
- **Google Vision credentials.** El archivo JSON de la service account debe estar en `.gitignore`. Pasarlo al contenedor como variable de entorno o montando el archivo.
