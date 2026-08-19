"""
Genera datos de ejemplo (semilla) para que el sistema tenga información
realista desde el primer arranque, incluyendo un historial de varios
meses de citas y consultas para que los módulos de Reportes y Machine
Learning tengan suficientes datos con los que trabajar.
"""
import os
import random
from datetime import datetime, timedelta

import pandas as pd

from utils import storage as st_db

random.seed(42)

NOMBRES = ["María", "José", "Luis", "Ana", "Carlos", "Laura", "Jorge", "Sofía",
           "Miguel", "Fernanda", "Diego", "Valeria", "Ricardo", "Paola", "Andrés",
           "Daniela", "Roberto", "Karla", "Eduardo", "Mónica", "Pedro", "Lucía",
           "Javier", "Renata", "Sergio", "Ximena", "Alberto", "Camila"]
APELLIDOS = ["García", "López", "Martínez", "Hernández", "González", "Pérez",
             "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
             "Díaz", "Cruz", "Morales", "Reyes", "Ortiz", "Vázquez"]

ESPECIALIDADES = [
    ("Medicina General", "Consulta y valoración general del paciente"),
    ("Pediatría", "Atención médica a niños y adolescentes"),
    ("Ginecología", "Salud del sistema reproductivo femenino"),
    ("Cardiología", "Enfermedades del corazón y sistema circulatorio"),
    ("Traumatología", "Lesiones óseas, musculares y articulares"),
    ("Dermatología", "Enfermedades de la piel"),
    ("Medicina Interna", "Diagnóstico y tratamiento integral en adultos"),
    ("Urgencias", "Atención inmediata de casos críticos"),
]

DIAGNOSTICOS = [
    ("J00", "Rinofaringitis aguda (resfriado común)", "Respiratorio"),
    ("J06.9", "Infección aguda de vías respiratorias altas", "Respiratorio"),
    ("A09", "Diarrea y gastroenteritis de presunto origen infeccioso", "Digestivo"),
    ("I10", "Hipertensión arterial esencial", "Cardiovascular"),
    ("E11", "Diabetes mellitus tipo 2", "Endocrino"),
    ("M54.5", "Lumbago no especificado", "Musculoesquelético"),
    ("J45", "Asma", "Respiratorio"),
    ("N39.0", "Infección de vías urinarias", "Genitourinario"),
    ("R51", "Cefalea", "Neurológico"),
    ("L20", "Dermatitis atópica", "Dermatológico"),
    ("K29.7", "Gastritis no especificada", "Digestivo"),
    ("F41.1", "Trastorno de ansiedad generalizada", "Salud mental"),
]

MEDICAMENTOS = [
    ("Paracetamol 500mg", "Tableta", 500, 1.5),
    ("Ibuprofeno 400mg", "Tableta", 400, 2.0),
    ("Amoxicilina 500mg", "Cápsula", 300, 3.2),
    ("Loratadina 10mg", "Tableta", 250, 1.8),
    ("Omeprazol 20mg", "Cápsula", 350, 2.5),
    ("Losartán 50mg", "Tableta", 300, 3.0),
    ("Metformina 850mg", "Tableta", 300, 2.2),
    ("Salbutamol Inhalador", "Inhalador", 120, 8.5),
    ("Diclofenaco 50mg", "Tableta", 260, 1.9),
    ("Azitromicina 500mg", "Tableta", 180, 4.5),
]

ESTADOS_CITA = ["Completada", "Completada", "Completada", "Confirmada",
                "Pendiente", "Cancelada", "No Asistió"]


def _rand_fecha_nacimiento(min_edad=0, max_edad=90):
    edad = random.randint(min_edad, max_edad)
    hoy = datetime.today()
    return (hoy - timedelta(days=edad * 365 + random.randint(0, 364))).strftime("%Y-%m-%d")


def initialize(force=False):
    """Crea datos de ejemplo solo si el sistema aún no tiene información."""
    st_db.ensure_data_dir()
    pacientes = st_db.load("pacientes")
    if not pacientes.empty and not force:
        return  # ya existen datos, no se vuelve a sembrar

    hoy = datetime.today()

    # --- Especialidades ---
    especialidades = pd.DataFrame([
        {"id_especialidad": i + 1, "nombre": n, "descripcion": d}
        for i, (n, d) in enumerate(ESPECIALIDADES)
    ])
    st_db.save("especialidades", especialidades)

    # --- Consultorios ---
    consultorios = pd.DataFrame([
        {"id_consultorio": i + 1, "nombre": f"Consultorio {i + 1}",
         "ubicacion": f"Piso {1 + i // 3}", "id_especialidad": (i % len(especialidades)) + 1}
        for i in range(10)
    ])
    st_db.save("consultorios", consultorios)

    # --- Médicos ---
    medicos_rows = []
    for i in range(16):
        medicos_rows.append({
            "id_medico": i + 1,
            "nombre": random.choice(NOMBRES),
            "apellido": random.choice(APELLIDOS),
            "id_especialidad": (i % len(especialidades)) + 1,
            "cedula": f"CED-{10000 + i}",
            "telefono": f"55{random.randint(10000000, 99999999)}",
            "email": f"medico{i + 1}@sighospital.com",
            "fecha_ingreso": (hoy - timedelta(days=random.randint(200, 3000))).strftime("%Y-%m-%d"),
        })
    medicos = pd.DataFrame(medicos_rows)
    st_db.save("medicos", medicos)

    # --- Pacientes ---
    pacientes_rows = []
    n_pacientes = 120
    for i in range(n_pacientes):
        pacientes_rows.append({
            "id_paciente": i + 1,
            "nombre": random.choice(NOMBRES),
            "apellido": random.choice(APELLIDOS),
            "fecha_nacimiento": _rand_fecha_nacimiento(),
            "sexo": random.choice(["F", "M"]),
            "telefono": f"55{random.randint(10000000, 99999999)}",
            "email": f"paciente{i + 1}@correo.com",
            "direccion": f"Calle {random.randint(1, 200)}, Col. Centro",
            "tipo_sangre": random.choice(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]),
            "fecha_registro": (hoy - timedelta(days=random.randint(30, 1200))).strftime("%Y-%m-%d"),
        })
    pacientes = pd.DataFrame(pacientes_rows)
    st_db.save("pacientes", pacientes)

    # --- Catálogo de diagnósticos ---
    diagnosticos_cat = pd.DataFrame([
        {"id_diagnostico": i + 1, "codigo": c, "nombre": n, "categoria": cat}
        for i, (c, n, cat) in enumerate(DIAGNOSTICOS)
    ])
    st_db.save("diagnosticos_catalogo", diagnosticos_cat)

    # --- Medicamentos ---
    medicamentos = pd.DataFrame([
        {"id_medicamento": i + 1, "nombre": n, "presentacion": p, "stock": s, "precio_unitario": pr}
        for i, (n, p, s, pr) in enumerate(MEDICAMENTOS)
    ])
    st_db.save("medicamentos", medicamentos)

    # --- Camas ---
    camas = pd.DataFrame([
        {"id_cama": i + 1, "numero": f"C-{i + 1:03d}",
         "area": random.choice(["Medicina Interna", "Cirugía", "Pediatría", "Urgencias", "UCI"]),
         "estado": "Disponible"}
        for i in range(25)
    ])
    st_db.save("camas", camas)

    # --- Historial de citas y consultas (180 días) ---
    citas_rows, consultas_rows, tratamientos_rows, pagos_rows = [], [], [], []
    id_cita = 1
    id_consulta = 1
    id_tratamiento = 1
    id_pago = 1

    dias_hist = 180
    for d in range(dias_hist, 0, -1):
        fecha = hoy - timedelta(days=d)
        # más carga en días entre semana
        n_citas_dia = random.randint(3, 10) if fecha.weekday() < 5 else random.randint(0, 4)
        for _ in range(n_citas_dia):
            id_paciente = random.randint(1, n_pacientes)
            id_medico = random.randint(1, len(medicos))
            id_especialidad = int(medicos.loc[medicos.id_medico == id_medico, "id_especialidad"].iloc[0])
            consultorios_validos = consultorios[consultorios.id_especialidad == id_especialidad]
            id_consultorio = int(consultorios_validos.sample(1).id_consultorio.iloc[0]) \
                if not consultorios_validos.empty else int(consultorios.sample(1).id_consultorio.iloc[0])
            hora = f"{random.randint(8, 18):02d}:{random.choice(['00', '15', '30', '45'])}"
            estado = random.choices(ESTADOS_CITA, weights=[30, 20, 15, 5, 5, 15, 10])[0]

            citas_rows.append({
                "id_cita": id_cita,
                "id_paciente": id_paciente,
                "id_medico": id_medico,
                "id_consultorio": id_consultorio,
                "fecha": fecha.strftime("%Y-%m-%d"),
                "hora": hora,
                "motivo": random.choice(["Consulta general", "Seguimiento", "Dolor", "Chequeo", "Control"]),
                "estado": estado,
                "fecha_registro": (fecha - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d"),
            })

            if estado == "Completada":
                diag = random.choice(diagnosticos_cat.to_dict("records"))
                consultas_rows.append({
                    "id_consulta": id_consulta,
                    "id_cita": id_cita,
                    "id_paciente": id_paciente,
                    "id_medico": id_medico,
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "peso": round(random.uniform(4, 110), 1),
                    "talla": round(random.uniform(0.5, 1.9), 2),
                    "presion": f"{random.randint(100, 140)}/{random.randint(60, 90)}",
                    "temperatura": round(random.uniform(36.0, 38.5), 1),
                    "motivo_consulta": random.choice(["Dolor", "Malestar general", "Control", "Fiebre", "Chequeo"]),
                    "observaciones": "Paciente estable, se indica tratamiento.",
                    "id_diagnostico": diag["id_diagnostico"],
                })

                if random.random() < 0.75:
                    # Combinaciones frecuentes de medicamentos (para que el
                    # módulo de reglas de asociación tenga patrones reales
                    # que descubrir), además de recetas de un solo fármaco.
                    combos_frecuentes = [
                        ["Paracetamol 500mg", "Ibuprofeno 400mg"],
                        ["Amoxicilina 500mg", "Paracetamol 500mg"],
                        ["Loratadina 10mg", "Salbutamol Inhalador"],
                        ["Omeprazol 20mg", "Diclofenaco 50mg"],
                        ["Losartán 50mg", "Metformina 850mg"],
                        ["Azitromicina 500mg", "Paracetamol 500mg"],
                    ]
                    nombres_meds = [m["nombre"] for m in medicamentos.to_dict("records")]
                    if random.random() < 0.45:
                        combo = random.choice(combos_frecuentes)
                        seleccionados = [m for m in medicamentos.to_dict("records") if m["nombre"] in combo]
                    else:
                        seleccionados = [random.choice(medicamentos.to_dict("records"))]

                    for med in seleccionados:
                        tratamientos_rows.append({
                            "id_tratamiento": id_tratamiento,
                            "id_consulta": id_consulta,
                            "id_paciente": id_paciente,
                            "id_medicamento": med["id_medicamento"],
                            "dosis": random.choice(["1 tableta", "2 tabletas", "5 ml", "1 cápsula"]),
                            "frecuencia": random.choice(["Cada 8 horas", "Cada 12 horas", "Cada 24 horas"]),
                            "duracion_dias": random.choice([3, 5, 7, 10, 14]),
                            "indicaciones": "Tomar con alimentos.",
                            "fecha": fecha.strftime("%Y-%m-%d"),
                        })
                        id_tratamiento += 1

                monto = round(random.uniform(300, 1500), 2)
                pagos_rows.append({
                    "id_pago": id_pago,
                    "id_paciente": id_paciente,
                    "concepto": "Consulta médica",
                    "referencia": f"CITA-{id_cita}",
                    "monto": monto,
                    "fecha_pago": fecha.strftime("%Y-%m-%d"),
                    "metodo_pago": random.choice(["Efectivo", "Tarjeta", "Transferencia"]),
                    "estado": "Pagado",
                })
                id_pago += 1
                id_consulta += 1

            id_cita += 1

    st_db.save("citas", pd.DataFrame(citas_rows))
    st_db.save("consultas", pd.DataFrame(consultas_rows))
    st_db.save("tratamientos", pd.DataFrame(tratamientos_rows))
    st_db.save("pagos", pd.DataFrame(pagos_rows))

    # --- Hospitalizaciones (algunas activas, algunas de alta) ---
    hosp_rows = []
    camas_df = st_db.load("camas")
    for i in range(18):
        id_paciente = random.randint(1, n_pacientes)
        id_medico = random.randint(1, len(medicos))
        id_cama = int(camas_df.sample(1).id_cama.iloc[0])
        fecha_ingreso = hoy - timedelta(days=random.randint(1, 60))
        activa = random.random() < 0.3
        diag = random.choice(diagnosticos_cat.to_dict("records"))
        fecha_alta = "" if activa else (fecha_ingreso + timedelta(days=random.randint(1, 12))).strftime("%Y-%m-%d")
        hosp_rows.append({
            "id_hospitalizacion": i + 1,
            "id_paciente": id_paciente,
            "id_medico": id_medico,
            "id_cama": id_cama,
            "fecha_ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
            "motivo_ingreso": random.choice(["Cirugía programada", "Observación", "Urgencia", "Parto", "Fractura"]),
            "diagnostico_ingreso": diag["nombre"],
            "costo_diario": round(random.uniform(800, 3500), 2),
            "fecha_alta": fecha_alta,
            "estado": "Hospitalizado" if activa else "Alta",
        })
        if activa:
            camas_df.loc[camas_df.id_cama == id_cama, "estado"] = "Ocupada"
    st_db.save("hospitalizaciones", pd.DataFrame(hosp_rows))
    st_db.save("camas", camas_df)
