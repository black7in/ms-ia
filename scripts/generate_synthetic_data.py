import csv
import os
import random
from datetime import date, timedelta

FERIADOS_BOLIVIA = {
    date(2025, 1, 1),
    date(2025, 2, 17),
    date(2025, 2, 18),
    date(2025, 4, 17),
    date(2025, 4, 18),
    date(2025, 5, 1),
    date(2025, 6, 19),
    date(2025, 8, 6),
    date(2025, 11, 2),
    date(2025, 12, 25),
    date(2026, 1, 1),
    date(2026, 2, 9),
    date(2026, 2, 10),
    date(2026, 4, 2),
    date(2026, 4, 3),
    date(2026, 5, 1),
    date(2026, 6, 19),
    date(2026, 8, 6),
    date(2026, 11, 2),
    date(2026, 12, 25),
}


def es_temporada_alta(mes: int) -> int:
    return 1 if mes in (1, 7) else 0


def generar_demand_data(output_path: str, num_rutas: int = 3, dias: int = 365) -> None:
    ruta_ids = [f"ruta-{i}" for i in range(1, num_rutas + 1)]
    start_date = date(2025, 5, 1)
    rows = []
    historico = {}

    for ruta_id in ruta_ids:
        for d in range(dias):
            fecha = start_date + timedelta(days=d)
            dia_semana = fecha.weekday()
            es_feriado_flag = 1 if fecha in FERIADOS_BOLIVIA else 0
            mes = fecha.month
            semana = fecha.isocalendar()[1]
            temporada = es_temporada_alta(mes)

            base = 0.55
            if dia_semana in (4, 5):
                base += random.uniform(0.15, 0.30)
            if dia_semana == 6:
                base += random.uniform(0.05, 0.15)
            if es_feriado_flag:
                base += random.uniform(0.20, 0.35)
            if temporada:
                base += random.uniform(0.10, 0.20)

            ruido = random.gauss(0, 0.05)
            ocupacion = min(max(base + ruido, 0.1), 1.0)

            key_ant = (ruta_id, fecha - timedelta(days=7))
            key_misma = (ruta_id, fecha - timedelta(days=7))
            ocupacion_semana_anterior = historico.get(key_ant, 0.55)
            ocupacion_mismo_dia = historico.get(key_misma, 0.55)

            rows.append(
                {
                    "ruta_id": ruta_id,
                    "fecha": fecha.isoformat(),
                    "dia_semana": dia_semana,
                    "es_feriado": es_feriado_flag,
                    "mes": mes,
                    "semana_del_anio": semana,
                    "es_temporada_alta": temporada,
                    "ocupacion_semana_anterior": round(ocupacion_semana_anterior, 4),
                    "ocupacion_mismo_dia_semana_pasada": round(ocupacion_mismo_dia, 4),
                    "ocupacion": round(ocupacion, 4),
                }
            )
            historico[(ruta_id, fecha)] = ocupacion

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Demanda: {len(rows)} registros -> {output_path}")


def generar_clientes_data(output_path: str, num_clientes: int = 250) -> None:
    random.seed(42)
    rows = []
    for i in range(1, num_clientes + 1):
        segmento = random.choices([0, 1, 2], weights=[0.18, 0.50, 0.32])[0]
        if segmento == 0:
            frecuencia = random.uniform(3, 8)
            gasto = random.uniform(200, 500)
            variedad = random.randint(2, 5)
        elif segmento == 1:
            frecuencia = random.uniform(1, 2)
            gasto = random.uniform(50, 150)
            variedad = random.randint(1, 2)
        else:
            frecuencia = random.uniform(2, 5)
            gasto = random.uniform(100, 300)
            variedad = random.randint(1, 3)

        rows.append(
            {
                "cliente_id": f"cli-{i}",
                "frecuencia_mensual": round(frecuencia, 2),
                "gasto_promedio": round(gasto, 2),
                "variedad_rutas": variedad,
                "dia_preferido": random.randint(0, 6),
            }
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Clientes: {len(rows)} registros -> {output_path}")


def generar_ventas_data(output_path: str, num_vendedores: int = 30) -> None:
    random.seed(42)
    rows = []
    for i in range(1, num_vendedores + 1):
        if i <= 2:
            tasa_cancel = random.uniform(0.15, 0.30)
            fuera_horario = random.randint(5, 15)
            ticket_prom = random.uniform(200, 500)
            variacion = random.uniform(100, 200)
        else:
            tasa_cancel = random.uniform(0.01, 0.06)
            fuera_horario = random.randint(0, 2)
            ticket_prom = random.uniform(50, 150)
            variacion = random.uniform(10, 40)

        rows.append(
            {
                "vendedor_id": f"ven-{i}",
                "vendedor_nombre": f"Vendedor {i}",
                "tasa_cancelaciones": round(tasa_cancel, 4),
                "ventas_fuera_horario": fuera_horario,
                "ticket_promedio": round(ticket_prom, 2),
                "variacion_precio": round(variacion, 2),
            }
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Ventas: {len(rows)} registros -> {output_path}")


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..", "tmp", "training_data")
    generar_demand_data(os.path.join(base_dir, "demand_data.csv"))
    generar_clientes_data(os.path.join(base_dir, "clientes_data.csv"))
    generar_ventas_data(os.path.join(base_dir, "ventas_data.csv"))
