import re
from typing import Optional, Dict, Any, List

class DeterministicService:
    """
    Tier 1 Deterministic Engine:
    Instantly matches canonical customer questions with rich, comprehensive, verified factual answers.
    Zero latency (<2ms), zero AI token cost, and 100% grounded accuracy.
    """

    def __init__(self):
        # Patterns that indicate explicit human escalation or complaints
        self.escalation_patterns = [
            r"\b(refund|reembolso|devoluci[oó]n|money back)\b",
            r"\b(complaint|queja|reclamo|demand|demanda|dispute|disputa)\b",
            r"\b(director|directora|president|presidente|rector|rectora|gerente|personal (phone|contact|number)|celular personal)\b",
            r"\b(talk to (a )?human|hablar con un asesor|asesor humano|agente humano|atenci[oó]n humana)\b",
            r"\b(beca del \d+%|scholarship of \d+%|\b90%|\b80%|\b70% discount)\b"
        ]

        self.rules: List[Dict[str, Any]] = [
            # 0. Greetings
            {
                "category": "greetings",
                "patterns": [
                    r"^(\s*(hola|buenos d[ií]as|buenas tardes|buenas noches|hello|hi|hey|saludos|qu[eé] tal)\s*)+[\.!\?]?$"
                ],
                "sources": ["01_courses_and_pricing.md#1-course-offerings-overview"],
                "answer": (
                    "¡Hola! 👋 Bienvenido a **Global Language Academy**.\n\n"
                    "Soy tu asesor académico virtual. Con mucho gusto te puedo ayudar con información sobre:\n"
                    "- 👥 **Cursos Grupales y Personalizados** (Dinámica de grupos de máx. 8 alumnos, tarifas individuales y particulares).\n"
                    "- 💰 **Precios y Financiación** (PSE, tarjetas de crédito a 3 cuotas con 0% de interés).\n"
                    "- ⏰ **Horarios y Modalidades** (Mañanas, noches, sábados intensivos, virtual o presencial en Bogotá y Medellín).\n"
                    "- 🎯 **Prueba de Nivelación Gratuita** (Online, diagnóstica MCER A1-C2).\n"
                    "- 📜 **Certificaciones Internacionales** (IELTS, TOEFL, Cambridge, DELF, DELE).\n\n"
                    "¿En qué programa o idioma estás interesado hoy?"
                )
            },

            # 1. Group Courses Dynamics & Detailed Operation (Addresses user's specific scenario)
            {
                "category": "group_courses_details",
                "patterns": [
                    r"\b(cursos? grupales?|qu[eé] son los cursos grupales|c[oó]mo funcionan los cursos grupales|armar (el|un) grupo|debo llevar|por persona|individual|cu[aá]ntos alumnos por grupo)\b"
                ],
                "sources": ["01_courses_and_pricing.md#2-group-courses-vs-private-1-on-1-mentorship-how-it-works"],
                "answer": (
                    "**¿Cómo funcionan los Cursos Grupales en Global Language Academy?**\n\n"
                    "1. **Tú NO necesitas armar el grupo**: Te inscribes de forma individual y la academia te asigna a un grupo con estudiantes que tienen exactamente tu mismo nivel (determinado por la prueba de nivelación gratuita).\n"
                    "2. **Tarifas Individuales por Persona**: Todos los valores publicados son **por persona / por módulo completo de 60 horas**.\n"
                    "3. **Límite Estricto de Máximo 8 Estudiantes**: Los grupos tienen un mínimo de 4 y un máximo de 8 alumnos para asegurar que tengas constante práctica de conversación y retroalimentación personalizada.\n"
                    "4. **¿Qué incluye tu matrícula individual?**\n"
                    "   - 60 horas académicas de clase guiadas por profesores certificados.\n"
                    "   - Acceso 24/7 a nuestro Campus Virtual y libros digitales oficiales (Cambridge/Oxford).\n"
                    "   - Clubes de conversación semanales sin costo adicional.\n"
                    "   - Hasta 2 tutorías individuales de recuperación gratuitas si llegas a faltar a alguna sesión.\n\n"
                    "**Opciones de Cursos Grupales:**\n"
                    "• **Standard Group (Trimestral)**: 10 semanas (60 hrs) - **$1,250,000 COP** (~$320 USD).\n"
                    "• **Intensive Group (Mensual)**: 4 semanas (60 hrs) - **$1,450,000 COP** (~$370 USD).\n"
                    "• **Sábados Intensivo**: 12 sábados (60 hrs, 8am a 1pm) - **$1,350,000 COP** (~$345 USD)."
                )
            },

            # 2. Private 1-on-1 Personalized Mentorship
            {
                "category": "private_courses_details",
                "patterns": [
                    r"\b(clases particulares|cursos? personalizados?|clases privadas|clases uno a uno|tutor[ií]as? privadas?|one-on-one|private)\b"
                ],
                "sources": ["01_courses_and_pricing.md#3-1-on-1-private-tutoring-customized-individual-mentorship"],
                "answer": (
                    "**Clases Personalizadas 1-on-1 (Tutorías Privadas):**\n\n"
                    "Ideales si buscas flexibilidad horaria total, avanzar a tu propio ritmo o preparar una entrevista u objetivo puntual.\n\n"
                    "• **Starter Pack (10 Horas)**: $850,000 COP ($85,000/hora) | Validez: 60 días.\n"
                    "• **Fluency Booster (25 Horas)**: $1,950,000 COP ($78,000/hora) | Validez: 120 días.\n"
                    "• **Mastery Package (50 Horas)**: $3,600,000 COP ($72,000/hora) | Validez: 180 días.\n\n"
                    "**Beneficios**:\n"
                    "- Horarios 100% a tu elección (Lunes a Sábado de 6:00 AM a 9:00 PM).\n"
                    "- Puedes reprogramar clases con 12 horas de anticipación sin perder la sesión."
                )
            },

            # 3. Missed Classes & Attendance Policies
            {
                "category": "missed_classes_policy",
                "patterns": [
                    r"\b(falto|falta|faltar|inasistencia|asistencia|recuperar clase|recuperaci[oó]n|reponer|graban|grabaciones?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#4-attendance-and-makeup-class-policies"],
                "answer": (
                    "**Política de Asistencia y Recuperación de Clases:**\n\n"
                    "1. **Grabaciones en HD**: Si estás en modalidad online, todas las sesiones se suben al portal en menos de 2 horas para que las repases cuando quieras.\n"
                    "2. **Tutorías de Recuperación Gratuitas**: Tienes derecho a **hasta 2 sesiones individuales de 45 minutos** con un tutor académico por módulo para ponerte al día con los temas vistos si faltas por motivos laborales o de fuerza mayor.\n"
                    "3. **Asistencia Mínima**: Se requiere un 80% de asistencia para presentar el examen final de nivel."
                )
            },

            # 4. Teachers, Methodology & Native Instructors
            {
                "category": "methodology_and_teachers",
                "patterns": [
                    r"\b(profesores? nativos?|metodolog[ií]a|m[eé]todo|c[oó]mo ense[ñn]an|docentes? certificados?|profesores? certificados?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#2-learning-modalities"],
                "answer": (
                    "**Metodología y Cuerpo Docente:**\n\n"
                    "• **Enfoque Comunicativo Directo**: El 80% del tiempo de clase se dedica a producción oral activa, debates y resolución de situaciones de la vida real (no a memorización pasiva de reglas).\n"
                    "• **Profesores Certificados**: Todos nuestros docentes cuentan con certificación internacional (CELTA, DELTA, TESOL, DAEFLE o equivalentes) y combinamos docentes nativos y bilingües de alto nivel C2.\n"
                    "• **Acompañamiento Continuo**: Grupos reducidos (máx. 8 alumnos) para corregir pronunciación y fluidez en tiempo real."
                )
            },

            # 5. Payment Methods & Financing
            {
                "category": "payment_methods",
                "patterns": [
                    r"\b(payment methods?|m[eé]todos? de pago|formas? de pago|how (can|do) i pay|c[oó]mo puedo pagar|pago con pse|pagar con tarjeta|cuotas sin inter[eé]s|financiaci[oó]n|pse|bancolombia|tarjeta de cr[eé]dito)\b"
                ],
                "sources": ["01_courses_and_pricing.md#5-payment-methods-and-financing-options"],
                "answer": (
                    "**Formas de Pago y Financiación en Global Language Academy:**\n\n"
                    "• **PSE (Pagos Seguros en Línea)**: Débito bancario desde cualquier banco en Colombia (Bancolombia, Davivienda, Nequi, Daviplata, etc.).\n"
                    "• **Tarjetas de Crédito y Débito**: Visa, MasterCard, American Express y Diners Club.\n"
                    "• **Transferencia Bancaria**: Cuenta de Ahorros Bancolombia # 104-589231-88 (NIT 901.458.712-3).\n"
                    "• **Financiación Sin Intereses (0% Interés)**: Hasta 3 cuotas mensuales sin interés con tarjeta de crédito o mediante crédito directo con la academia (50% al matricularte, 25% en semana 4, 25% en semana 8)."
                )
            },

            # 6. Campus Locations & Facilities
            {
                "category": "locations",
                "patterns": [
                    r"\b(locations?|sedes?|direcci[oó]n|direcciones|addresses?|d[oó]nde est[aá]n|where are you located|d[oó]nde quedan|campus bogot[aá]|campus medell[ií]n|chapinero|el poblado)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#3-physical-campus-locations-and-facilities"],
                "answer": (
                    "**Nuestras Sedes Principales en Colombia:**\n\n"
                    "• **Sede Bogotá**: Calle 63 # 9-45, Chapinero Central (a 2 cuadras de la estación TransMilenio Calle 63). Horario: Lun–Vie 6:00 AM–9:00 PM, Sáb 7:30 AM–2:30 PM.\n"
                    "• **Sede Medellín**: Carrera 43A # 7-50, El Poblado (cerca al Parque del Poblado). Horario: Lun–Vie 6:30 AM–8:30 PM, Sáb 8:00 AM–2:00 PM.\n"
                    "• **100% Live Online**: Clases interactivas en vivo vía Zoom Education desde cualquier lugar del mundo."
                )
            },

            # 7. Saturday Intensive Schedules
            {
                "category": "saturday_schedules",
                "patterns": [
                    r"\b(saturday intensives?|s[aá]bados? intensivos?|horarios? de los s[aá]bados?|saturday schedule|fin de semana intensivo|s[aá]bados?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-class-schedules-and-timetables"],
                "answer": (
                    "**Programa Intensivo de Sábados:**\n\n"
                    "• **Horario**: 8:00 AM a 1:00 PM (5 horas continuas con receso de café de 20 minutos).\n"
                    "• **Estructura**: 60 horas académicas distribuidas en 12 sábados consecutivos.\n"
                    "• **Tarifa Individual**: $1,350,000 COP (~$345 USD) por módulo de 12 semanas.\n"
                    "• Disponible en modalidad presencial (Bogotá y Medellín) y 100% Virtual en vivo."
                )
            },

            # 8. Weekday & Evening Schedules
            {
                "category": "weekday_schedules",
                "patterns": [
                    r"\b(evening track|nocturno|horario de noche|madrugadores?|morning schedule|qu[eé] horarios tienen|what are the class schedules|horarios?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-class-schedules-and-timetables"],
                "answer": (
                    "**Horarios de Clases Entre Semana (Lunes a Jueves):**\n\n"
                    "• **Madrugadores**: 6:30 AM – 8:30 AM (8 hrs/semana).\n"
                    "• **Mañana Estándar**: 9:00 AM – 11:00 AM.\n"
                    "• **Tarde**: 4:00 PM – 6:00 PM.\n"
                    "• **Nocturno Ejecutivo**: 6:30 PM – 8:30 PM (ideal para quienes trabajan).\n"
                    "• **Sábados Intensivos**: 8:00 AM – 1:00 PM."
                )
            },

            # 9. Free Placement Diagnostic Test
            {
                "category": "placement_test",
                "patterns": [
                    r"\b(placement test|prueba de nivelaci[oó]n|examen de nivel|diagnostic test|test de nivel gratis|how do i know my level|c[oó]mo s[eé] mi nivel|saber mi nivel)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#2-free-placement-diagnostic-test-prueba-de-nivelacion"],
                "answer": (
                    "**Prueba de Nivelación Diagnóstica Gratuita:**\n\n"
                    "• **Costo**: 100% Gratuita ($0 COP), sin ningún compromiso de matrícula.\n"
                    "• **Formato**: 45 minutos online (lectura, gramática y escucha) + una breve entrevista oral de 10 minutos con un docente evaluador.\n"
                    "• **Resultados**: Te los entregamos en menos de 2 horas hábiles vía correo electrónico y WhatsApp, válidos por 90 días."
                )
            },

            # 10. Languages Offered
            {
                "category": "languages_offered",
                "patterns": [
                    r"\b(languages? offered|qu[eé] idiomas ofrecen|what languages do you teach|qu[eé] cursos tienen|programas de idiomas|idiomas)\b"
                ],
                "sources": ["01_courses_and_pricing.md#1-course-offerings-overview"],
                "answer": (
                    "**Idiomas Disponibles en Global Language Academy:**\n\n"
                    "• **Inglés General** (Niveles A1 a C1)\n"
                    "• **Inglés de Negocios y Profesional** (Niveles B1 a C2)\n"
                    "• **Francés (Français)** (Niveles A1 a C1 - Marco CIEP)\n"
                    "• **Alemán (Deutsch)** (Niveles A1 a B2 - Marco Goethe-Institut)\n"
                    "• **Italiano (Italiano)** (Niveles A1 a B2)\n"
                    "• **Portugués (Português)** (Niveles A1 a B2)\n"
                    "• **Español para Extranjeros** (Niveles A1 a C2)"
                )
            },

            # 11. Official Exam Preparation (IELTS, TOEFL, Cambridge)
            {
                "category": "certifications",
                "patterns": [
                    r"\b(ielts|toefl|cambridge|fce|cae|delf|dalf|dele|siele|certificaciones?)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#3-official-exam-preparation-and-international-certifications"],
                "answer": (
                    "**Cursos de Preparación para Exámenes Oficiales:**\n\n"
                    "• **IELTS Academic & General**: 40 horas de estrategia + 4 simulacros completos por computador con diagnóstico de banda.\n"
                    "• **TOEFL iBT**: 40 horas enfocadas en redacción académica y expresión oral integrada.\n"
                    "• **Cambridge**: B2 First (FCE) y C1 Advanced (CAE).\n"
                    "• **DELF / DALF** (Francés) y **DELE / SIELE** (Español).\n\n"
                    "Al finalizar cualquier nivel regular con 80/100 o más, recibes tu diploma digital oficial con código QR y certificación en blockchain."
                )
            },

            # 12. Standard Discounts and Special Promotions
            {
                "category": "discounts",
                "patterns": [
                    r"\b(early bird discount|family discount|descuento por pronto pago|descuento de hermanos|convenios corporativos|tienen descuentos|hay promociones|descuentos?|promociones?)\b"
                ],
                "sources": ["01_courses_and_pricing.md#4-discounts-promotions-and-special-offers"],
                "answer": (
                    "**Descuentos y Beneficios Especiales:**\n\n"
                    "• **Pronto Pago / Early Bird (15% OFF)**: Al matricularte al menos 10 días calendario antes de iniciar el curso.\n"
                    "• **Familiar y Hermanos (10% OFF)**: Cuando se matriculan 2 o más familiares juntos.\n"
                    "• **Paquete Anual (25% OFF)**: Al pagar 4 niveles por adelantado + kit diagnóstico Cambridge/IELTS sin costo.\n"
                    "• **Convenios Corporativos (12% OFF)**: Para colaboradores de empresas aliadas.\n"
                    "*(El descuento máximo acumulable es del 30%)*"
                )
            }
        ]

    def match(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates the user query against deterministic patterns.
        If an escalation or dispute pattern is present, returns None to allow Tier 2/3 handling.
        """
        clean_query = query.strip().lower()

        # If explicit escalation intent is present, let it fall through to RAG / Escalation
        for esc_pat in self.escalation_patterns:
            if re.search(esc_pat, clean_query, re.IGNORECASE):
                return None

        for rule in self.rules:
            for pattern in rule["patterns"]:
                if re.search(pattern, clean_query, re.IGNORECASE):
                    return {
                        "matched": True,
                        "tier": "deterministic",
                        "category": rule["category"],
                        "answer": rule["answer"],
                        "sources": rule["sources"],
                        "confidence": 1.0,
                        "escalate_to_human": False,
                        "escalation_reason": None
                    }

        return None

deterministic_service = DeterministicService()
