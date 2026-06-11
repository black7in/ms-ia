from app.config import Config

DB_SCHEMA = """
Tablas disponibles en PostgreSQL:

asientos_viaje (
    id VARCHAR NOT NULL,
    viaje_id VARCHAR NOT NULL REFERENCES viajes(id),
    numero_asiento INTEGER NOT NULL,
    estado VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

boletos (
    id VARCHAR NOT NULL,
    viaje_id VARCHAR NOT NULL REFERENCES viajes(id),
    asiento_id VARCHAR NOT NULL REFERENCES asientos_viaje(id),
    cliente_id VARCHAR NOT NULL REFERENCES clientes(id),
    vendedor_id VARCHAR NOT NULL REFERENCES usuarios(id),
    precio_pagado NUMERIC NOT NULL,
    fecha_venta TIMESTAMP NOT NULL,
    estado VARCHAR NOT NULL,
    qr_code VARCHAR NOT NULL,
    pdf_s3_key VARCHAR NULL,
    recordatorio_enviado BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

buses (
    id VARCHAR NOT NULL,
    placa VARCHAR(15) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    anio INTEGER NOT NULL,
    capacidad INTEGER NOT NULL,
    numero_carriles INTEGER NOT NULL,
    estado_mecanico VARCHAR NOT NULL,
    foto_s3_key VARCHAR NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

choferes (
    id VARCHAR NOT NULL,
    ci VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    licencia_numero VARCHAR(30) NOT NULL,
    licencia_categoria VARCHAR(10) NOT NULL,
    licencia_vence VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    telefono VARCHAR(20) NULL,
    foto_perfil_s3_key VARCHAR NULL,
    foto_facial_s3_key VARCHAR NULL,
    usuario_id VARCHAR NULL REFERENCES usuarios(id),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

clientes (
    id VARCHAR NOT NULL,
    ci VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NULL,
    telefono VARCHAR(20) NULL,
    fecha_registro TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

facturas (
    id VARCHAR NOT NULL,
    boleto_id VARCHAR NOT NULL REFERENCES boletos(id),
    numero_factura VARCHAR(20) NOT NULL,
    nombre_cliente VARCHAR(100) NOT NULL,
    nit VARCHAR(20) NULL,
    razon_social VARCHAR(150) NULL,
    monto NUMERIC NOT NULL,
    fecha TIMESTAMP NOT NULL,
    estado VARCHAR NOT NULL,
    hash_sha256 VARCHAR(64) NULL,
    pdf_s3_key VARCHAR NULL,
    blockchain_estado VARCHAR NOT NULL,
    blockchain_tx_hash VARCHAR NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

horarios (
    id VARCHAR NOT NULL,
    ruta_id VARCHAR NOT NULL REFERENCES rutas(id),
    hora_salida VARCHAR NOT NULL,
    dias_semana ARRAY NOT NULL,
    activo BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

rutas (
    id VARCHAR NOT NULL,
    terminal_origen_id VARCHAR NOT NULL REFERENCES terminales(id),
    terminal_destino_id VARCHAR NOT NULL REFERENCES terminales(id),
    distancia_km NUMERIC NULL,
    duracion_estimada_min INTEGER NULL,
    activa BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

tarifas (
    id VARCHAR NOT NULL,
    ruta_id VARCHAR NOT NULL REFERENCES rutas(id),
    tipo_dia VARCHAR NOT NULL,
    precio_base NUMERIC NOT NULL,
    vigente_desde VARCHAR NOT NULL,
    vigente_hasta VARCHAR NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

terminales (
    id VARCHAR NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    direccion VARCHAR(200) NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

usuarios (
    id VARCHAR NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR NOT NULL,
    rol VARCHAR NOT NULL,
    activo BOOLEAN NOT NULL,
    terminal_id VARCHAR NULL REFERENCES terminales(id),
    push_token VARCHAR NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)

viajes (
    id VARCHAR NOT NULL,
    horario_id VARCHAR NOT NULL REFERENCES horarios(id),
    bus_id VARCHAR NULL REFERENCES buses(id),
    chofer_titular_id VARCHAR NULL REFERENCES choferes(id),
    chofer_auxiliar_id VARCHAR NULL REFERENCES choferes(id),
    fecha VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    carril_asignado VARCHAR(10) NULL,
    hora_salida_real TIMESTAMP NULL,
    hora_llegada_real TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
"""

SQL_SYSTEM_PROMPT = (
    "Eres un asistente que genera consultas SQL para PostgreSQL "
    "a partir de preguntas en lenguaje natural.\n\n"
    "Reglas:\n"
    "1. Solo genera SELECT. Nunca INSERT, UPDATE, DELETE, DROP ni CREATE.\n"
    "2. Usa solo las tablas y columnas que existen en el esquema.\n"
    "3. Retorna unicamente la consulta SQL, sin explicaciones ni markdown.\n"
    "4. Usa LIMIT 100 cuando la pregunta no especifique limite.\n"
    "5. Para fechas relativas como 'esta semana', usa CURRENT_DATE.\n"
    "6. Para agregaciones usa alias descriptivos con AS.\n"
    "7. Usa los JOIN correctos segun las foreign keys del esquema.\n"
    "8. Si la pregunta no es sobre datos del negocio (ventas, viajes, "
    "clientes, boletos, rutas, buses, choferes, tarifas, facturas, "
    "terminales, horarios, usuarios) responde con: NO_SQL"
)

EXPLAIN_SYSTEM_PROMPT = (
    "Eres un asistente que genera respuestas en lenguaje natural "
    "a partir de resultados de consultas SQL.\n\n"
    "Reglas:\n"
    "1. Responde en una sola oracion clara y concisa en espanol.\n"
    "2. Incluye numeros y datos concretos de los resultados.\n"
    "3. Si no hay resultados, indica que no se encontraron datos.\n"
    "4. NO uses markdown, solo texto plano.\n"
    "5. NO repitas la pregunta textualmente."
)


class AgenteService:
    def __init__(self) -> None:
        self.openai_api_key = Config.OPENAI_API_KEY

    def _llm_disponible(self) -> bool:
        return bool(self.openai_api_key)

    def generar_sql(self, pregunta: str) -> str:
        if not self._llm_disponible():
            return self._sql_fallback(pregunta)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=self.openai_api_key,
            max_tokens=500,
        )

        messages = [
            SystemMessage(content=SQL_SYSTEM_PROMPT + "\n\n" + DB_SCHEMA),
            HumanMessage(content=pregunta),
        ]

        response = llm.invoke(messages)
        sql = str(response.content).strip()

        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()

        if sql.upper().startswith("NO_SQL"):
            return ""

        return sql

    def generar_explicacion(
        self, pregunta: str, sql: str, columnas: list[str], filas: list[list]
    ) -> str:
        if not filas:
            return "No se encontraron datos para esa consulta."

        if not self._llm_disponible():
            return self._explain_fallback(pregunta, columnas, filas)

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        contexto = (
            f"Pregunta original: {pregunta}\n"
            f"SQL ejecutado: {sql}\n"
            f"Columnas: {columnas}\n"
            f"Total de filas obtenidas: {len(filas)}\n"
            f"Primeras filas: {filas[:3]}\n"
        )

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=self.openai_api_key,
            max_tokens=200,
        )

        messages = [
            SystemMessage(content=EXPLAIN_SYSTEM_PROMPT),
            HumanMessage(content=contexto),
        ]

        response = llm.invoke(messages)
        return str(response.content).strip()

    def _explain_fallback(
        self, pregunta: str, columnas: list[str], filas: list[list]
    ) -> str:
        if not filas:
            return "No se encontraron datos."

        total_filas = len(filas)
        primera = filas[0]
        partes = []
        for i, col in enumerate(columnas):
            if i < len(primera):
                partes.append(f"{col}={primera[i]}")
        detalle = ", ".join(partes)
        return f"Se encontraron {total_filas} resultados. {detalle}."

    def _sql_fallback(self, pregunta: str) -> str:
        p = pregunta.lower()

        if "boleto" in p and ("semana" in p or "vendieron" in p or "vendidos" in p):
            return (
                "SELECT COUNT(*) AS total, COALESCE(SUM(precio_pagado), 0) AS ingresos "
                "FROM boletos "
                "WHERE fecha_venta >= CURRENT_DATE - INTERVAL '7 days'"
            )
        if "boleto" in p:
            return (
                "SELECT COUNT(*) AS total, COALESCE(SUM(precio_pagado), 0) AS ingresos "
                "FROM boletos"
            )
        if "viaje" in p and ("activo" in p or "ruta" in p or "curso" in p):
            return (
                "SELECT COUNT(*) AS viajes_activos FROM viajes WHERE estado = 'EN_RUTA'"
            )
        if "viaje" in p:
            return "SELECT estado, COUNT(*) AS total " "FROM viajes GROUP BY estado"
        if "cliente" in p:
            return "SELECT COUNT(*) AS total FROM clientes"
        if "vendedor" in p:
            return (
                "SELECT u.nombre, COUNT(b.id) AS ventas, "
                "COALESCE(SUM(b.precio_pagado), 0) AS ingresos "
                "FROM usuarios u JOIN boletos b ON u.id = b.vendedor_id "
                "GROUP BY u.nombre ORDER BY ventas DESC LIMIT 10"
            )
        if "ruta" in p and ("popular" in p or "frecuente" in p or "mas" in p):
            return (
                "SELECT r.id, COUNT(b.id) AS total_boletos "
                "FROM rutas r "
                "JOIN horarios h ON h.ruta_id = r.id "
                "JOIN viajes v ON v.horario_id = h.id "
                "JOIN boletos b ON b.viaje_id = v.id "
                "GROUP BY r.id ORDER BY total_boletos DESC LIMIT 5"
            )
        if "cancel" in p:
            return "SELECT COUNT(*) AS total FROM boletos " "WHERE estado = 'CANCELADO'"
        if "ingreso" in p or "recaud" in p or "ganancia" in p:
            return (
                "SELECT COALESCE(SUM(precio_pagado), 0) AS ingresos_totales "
                "FROM boletos WHERE estado IN ('ACTIVO', 'USADO')"
            )
        if "bus" in p or "flota" in p:
            return (
                "SELECT estado_mecanico, COUNT(*) AS total "
                "FROM buses GROUP BY estado_mecanico"
            )

        return ""


agente_service = AgenteService()
