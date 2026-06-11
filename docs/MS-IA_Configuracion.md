# MS-IA — Guía de Configuración de Servicios Externos

> Este documento describe paso a paso cómo configurar cada servicio externo que usa MS-IA. Todos los servicios tienen un modo mock (`MOCK_*=true`) para desarrollo local. Las credenciales reales se configuran cuando se necesite probar la integración real.

---

## Estado de configuración

| Servicio | Mock disponible | Cuándo configurar real |
|---|---|---|
| AWS Rekognition | ✅ `MOCK_REKOGNITION=true` | Antes de probar verificación facial |
| AWS S3 | ✅ `MOCK_S3=true` | Antes de despliegue en producción |
| Roboflow | ✅ `MOCK_ROBOFLOW=true` | Antes de probar OCR y detección de daños |
| Google Vision API | ✅ `MOCK_VISION=true` | Antes de probar lectura de placa |
| Expo Push Notifications | ✅ `MOCK_PUSH_NOTIFICATIONS=true` | Cuando app móvil esté implementada |

---

## 1. AWS Rekognition + S3

### Requisito previo
MS-Core ya usa AWS (S3 + RDS). Las mismas credenciales sirven para MS-IA. Solo hay que verificar que el usuario IAM tenga los permisos necesarios.

### Paso 1 — Verificar permisos IAM

1. Ir a [console.aws.amazon.com](https://console.aws.amazon.com)
2. Navegar a **IAM → Usuarios**
3. Seleccionar el usuario que usa MS-Core
4. Clic en **Agregar permisos → Adjuntar políticas directamente**
5. Buscar y agregar:
   - `AmazonRekognitionFullAccess`
   - `AmazonS3FullAccess` (si no está ya)
6. Guardar cambios

### Paso 2 — Crear bucket S3 para evidencias

1. Ir a **S3 → Crear bucket**
2. Nombre: `bustrack-evidencias`
3. Región: `us-east-1` (misma que los demás buckets)
4. Configuración de acceso: **Bloquear todo acceso público** ✅
5. Crear bucket

> El bucket `bustrack-licencias` ya debería existir de MS-Core. Si no existe, crearlo con el mismo proceso.

### Variables de entorno

```env
# Mismas credenciales que MS-Core
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY

# Buckets S3
S3_BUCKET_EVIDENCIAS=bustrack-evidencias
S3_BUCKET_LICENCIAS=bustrack-licencias

# Mock
MOCK_REKOGNITION=false   # cambiar cuando tengas credenciales reales
MOCK_S3=false            # cambiar cuando tengas credenciales reales
```

### Verificar que funciona

Con las credenciales configuradas, probar desde Python:

```python
import boto3

# Verificar S3
s3 = boto3.client('s3', region_name='us-east-1')
buckets = s3.list_buckets()
print([b['Name'] for b in buckets['Buckets']])
# Debe aparecer: bustrack-evidencias, bustrack-licencias

# Verificar Rekognition
rekognition = boto3.client('rekognition', region_name='us-east-1')
print(rekognition.list_collections())
# Debe responder sin error de permisos
```

---

## 2. Roboflow

### Paso 1 — Crear cuenta

1. Ir a [roboflow.com](https://roboflow.com)
2. Clic en **Sign Up** → registrarse con email o Google
3. Elegir plan **Free** (1,000 inferencias/mes)

### Paso 2 — Obtener API Key

1. Una vez logueado, ir a **Settings → API Keys**
2. Copiar la **Private API Key**

### Paso 3 — Buscar modelo de detección de placas

1. Ir a [universe.roboflow.com](https://universe.roboflow.com)
2. Buscar: `license plate detection`
3. Filtrar por: **Object Detection**, ordenar por **Most Downloads**
4. Elegir un modelo con buenas métricas (mAP > 70%)
5. Recomendado buscar modelos con placas latinoamericanas: `latin america license plate`
6. Clic en el modelo → **Deploy** → copiar el `model_id`
   - Formato: `nombre-del-modelo/version` (ej: `license-plate-recognition-rxg4e/3`)

### Paso 4 — Buscar modelo de detección de daños

1. En [universe.roboflow.com](https://universe.roboflow.com)
2. Buscar: `vehicle damage detection`
3. Elegir un modelo con mAP > 60%
4. Clic en el modelo → **Deploy** → copiar el `model_id`

### Paso 5 — Probar los modelos

Desde la página del modelo en Roboflow hay un playground donde podés subir una foto y ver si detecta correctamente. Probarlo antes de configurarlo en MS-IA.

### Variables de entorno

```env
ROBOFLOW_API_KEY=TU_API_KEY
ROBOFLOW_MODEL_PLACA=license-plate-recognition-rxg4e/3   # reemplazar con tu model_id
ROBOFLOW_MODEL_DANOS=vehicle-damage-detection/1           # reemplazar con tu model_id

# Mock
MOCK_ROBOFLOW=false   # cambiar cuando tengas credenciales reales
```

### Nota importante

Los `model_id` exactos dependen de qué modelos elegiste en Roboflow Universe. El formato siempre es `nombre-del-modelo/numero-de-version`. Verificar el `model_id` en la página del modelo bajo la sección **Deploy → Hosted API**.

---

## 3. Google Vision API

### Paso 1 — Crear proyecto en Google Cloud

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Clic en el selector de proyectos (arriba) → **Nuevo proyecto**
3. Nombre del proyecto: `bustrack-ia`
4. Clic en **Crear**

### Paso 2 — Habilitar Cloud Vision API

1. Con el proyecto `bustrack-ia` seleccionado
2. Ir a **APIs y servicios → Biblioteca**
3. Buscar: `Cloud Vision API`
4. Clic en el resultado → **Habilitar**

### Paso 3 — Crear cuenta de servicio

1. Ir a **IAM y administración → Cuentas de servicio**
2. Clic en **Crear cuenta de servicio**
3. Nombre: `ms-ia-vision`
4. Descripción: `Cuenta de servicio para MS-IA BusTrack`
5. Clic en **Crear y continuar**
6. En **Otorgar acceso**, seleccionar rol: `Cloud Vision AI Service Agent`
7. Clic en **Continuar → Listo**

### Paso 4 — Descargar credenciales JSON

1. En la lista de cuentas de servicio, clic en `ms-ia-vision`
2. Ir a la tab **Claves**
3. Clic en **Agregar clave → Crear clave nueva**
4. Seleccionar formato **JSON**
5. Clic en **Crear** → se descarga automáticamente un archivo JSON
6. Renombrar el archivo a `google-vision.json`
7. Moverlo a la carpeta `ms-ia/credentials/google-vision.json`
8. **Verificar que `credentials/` está en el `.gitignore`** — nunca subir este archivo al repositorio

### Paso 5 — Verificar límites del free tier

Google Vision API ofrece **1,000 unidades gratuitas por mes**. Una unidad = una llamada a la API. Para el examen es más que suficiente.

Para ver el uso: **APIs y servicios → Panel → Cloud Vision API → Ver métricas**

### Variables de entorno

```env
GOOGLE_APPLICATION_CREDENTIALS=/ruta/absoluta/a/ms-ia/credentials/google-vision.json

# En Windows usar barras invertidas o dobles:
# GOOGLE_APPLICATION_CREDENTIALS=C:\proyectos\ms-ia\credentials\google-vision.json

# Mock
MOCK_VISION=false   # cambiar cuando tengas el JSON configurado
```

### Verificar que funciona

```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()
print("Google Vision API configurada correctamente")
# Si no lanza error, las credenciales están bien
```

---

## 4. Expo Push Notifications

> **Nota:** Este servicio depende de que la app móvil esté implementada. Dejarlo con `MOCK_PUSH_NOTIFICATIONS=true` hasta ese momento.

### Contexto — Dos tokens distintos

| Token | Quién lo genera | Dónde se guarda | Para qué |
|---|---|---|---|
| `ExponentPushToken[xxx]` | Expo SDK en la app móvil | DB de MS-Core (`usuarios.push_token`) | Identificar el dispositivo destino |
| `EXPO_ACCESS_TOKEN` | Tu cuenta de Expo | `.env` de MS-IA | Autenticarse en el servidor de Expo al enviar notificaciones |

### Paso 1 — Crear cuenta en Expo (cuando app móvil esté lista)

1. Ir a [expo.dev](https://expo.dev)
2. Clic en **Sign Up** → registrarse
3. Crear una organización o usar cuenta personal

### Paso 2 — Obtener Access Token

1. Ir a [expo.dev/accounts/TU_USUARIO/settings/access-tokens](https://expo.dev/accounts/TU_USUARIO/settings/access-tokens)
2. Clic en **Create Token**
3. Nombre: `ms-ia-notifications`
4. Copiar el token generado

### Paso 3 — Registrar push token en MS-Core (en la app móvil)

Cuando la app móvil esté implementada, al hacer login debe:
1. Pedir permiso de notificaciones al usuario
2. Obtener el `ExponentPushToken` del dispositivo con `expo-notifications`
3. Enviarlo a MS-Core: `PATCH /usuarios/push-token` con `{ push_token: "ExponentPushToken[xxx]" }`
4. MS-Core lo guarda en `usuarios.push_token`

### Paso 4 — Verificar que MS-IA puede enviar notificaciones

Con ambos tokens configurados, MS-IA puede enviar notificaciones así:

```
MS-IA detecta somnolencia del chofer
    ↓
Consulta MS-Core → GET /usuarios?rol=SUPERVISOR&terminal_id=xxx
    ↓
Obtiene push_token del supervisor
    ↓
POST https://exp.host/--/api/v2/push/send
Headers: Authorization: Bearer EXPO_ACCESS_TOKEN
Body: {
  "to": "ExponentPushToken[xxx]",
  "title": "⚠️ Alerta de conducción",
  "body": "Somnolencia detectada en chofer Pedro Mamani — Viaje CBBA→SCZ"
}
```

### Variables de entorno

```env
EXPO_ACCESS_TOKEN=TU_EXPO_ACCESS_TOKEN

# Mock
MOCK_PUSH_NOTIFICATIONS=true   # cambiar a false cuando app móvil esté lista
```

---

## 5. Resumen del archivo .env completo

```env
# ── App ──────────────────────────────────────────
PORT=8002
ENVIRONMENT=development
FLASK_DEBUG=true

# ── JWT (misma secret que MS-Core) ───────────────
JWT_SECRET=dev-jwt-secret-change-in-production

# ── AWS ──────────────────────────────────────────
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_EVIDENCIAS=bustrack-evidencias
S3_BUCKET_LICENCIAS=bustrack-licencias

# ── DynamoDB (LocalStack en desarrollo) ──────────
DYNAMODB_ENDPOINT=http://localhost:4566
DYNAMODB_TABLE_INFERENCIAS=inferencias_ia
DYNAMODB_TABLE_PREDICCIONES=predicciones_ml

# ── Roboflow ─────────────────────────────────────
ROBOFLOW_API_KEY=
ROBOFLOW_MODEL_PLACA=
ROBOFLOW_MODEL_DANOS=

# ── Google Vision ─────────────────────────────────
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-vision.json

# ── MS-Core ───────────────────────────────────────
MS_CORE_URL=http://localhost:3000

# ── MS-Operaciones ────────────────────────────────
MS_OPERACIONES_URL=http://localhost:8001

# ── Expo Push Notifications ───────────────────────
EXPO_ACCESS_TOKEN=

# ── Mocks (true en desarrollo, false en producción) ──
MOCK_REKOGNITION=true
MOCK_ROBOFLOW=true
MOCK_VISION=true
MOCK_S3=true
MOCK_PUSH_NOTIFICATIONS=true

# ── Modelos ML ────────────────────────────────────
MODELS_PATH=app/models/
REENTRENAR_AUTO=true

# ── Umbrales IA ───────────────────────────────────
UMBRAL_IDENTIDAD_FACIAL=90.0
UMBRAL_SOMNOLENCIA=70.0
UMBRAL_CONFIANZA_PLACA=80.0
UMBRAL_CONFIANZA_DANO=75.0
```

---

## 6. Orden de configuración recomendado

```
1. AWS (Rekognition + S3)
   → Ya tenés las credenciales de MS-Core
   → Solo agregar permiso AmazonRekognitionFullAccess al usuario IAM
   → Crear bucket bustrack-evidencias

2. Roboflow
   → Crear cuenta (5 minutos)
   → Buscar y seleccionar modelos en Universe
   → Copiar API Key y model_ids

3. Google Vision API
   → Crear proyecto en Google Cloud (10 minutos)
   → Habilitar API + crear service account + descargar JSON

4. Expo Push Notifications
   → Dejar para cuando app móvil esté implementada
   → Mantener MOCK_PUSH_NOTIFICATIONS=true hasta entonces
```
