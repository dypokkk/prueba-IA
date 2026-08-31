import re
from typing import Optional, Dict, Any, List

class DeterministicService:
    """
    Tier 1 Deterministic Engine:
    Instantly matches canonical customer questions with concise, bite-sized, verified factual answers.
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
                "sources": ["01_courses_and_pricing.md#1-institutional-overview-and-cefr-alignment"],
                "answer": (
                    "¡Hola! 👋 Bienvenido a **Global Language Academy**.\n\n"
                    "Puedo orientarte con **precios**, **horarios**, **sedes** en Bogotá y Medellín o nuestra **prueba diagnóstica gratuita**.\n\n"
                    "¿En qué idioma estás interesado hoy?"
                )
            },

            # 1. Group Courses Dynamics
            {
                "category": "group_courses_details",
                "patterns": [
                    r"\b(cursos? grupales?|qu[eé] son los cursos grupales|c[oó]mo funcionan los cursos grupales|armar (el|un) grupo|debo llevar|por persona|individual|cu[aá]ntos alumnos por grupo)\b"
                ],
                "sources": ["01_courses_and_pricing.md#3-group-courses-vs-private-1-on-1-mentorship-operating-dynamics"],
                "answer": (
                    "**Cursos Grupales en Global Language Academy:**\n\n"
                    "• **Inscripción individual**: No necesitas armar grupo; la academia conforma las cohortes por nivel (máx. 8 alumnos por aula).\n"
                    "• **Tarifas**: **$1,250,000 COP** (Trimestral 10 sem) o **$1,450,000 COP** (Intensivo mensual 4 sem).\n"
                    "• **Incluye**: 60h de clase, libros digitales Cambridge/Oxford y clubes de conversación.\n\n"
                    "¿Prefieres estudiar entre semana o los sábados?"
                )
            },

            # 2. Private 1-on-1 Personalized Mentorship
            {
                "category": "private_courses_details",
                "patterns": [
                    r"\b(clases particulares|cursos? personalizados?|clases privadas|clases uno a uno|tutor[ií]as? privadas?|one-on-one|private)\b"
                ],
                "sources": ["01_courses_and_pricing.md#4-1-on-1-private-tutoring-packages-custom-individual-mentorship"],
                "answer": (
                    "**Clases Particulares 1 a 1:**\n\n"
                    "• **Starter Pack (10h)**: $850,000 COP ($85,000/h).\n"
                    "• **Fluency Booster (25h)**: $1,950,000 COP ($78,000/h).\n"
                    "• **Mastery Pack (50h)**: $3,600,000 COP ($72,000/h).\n"
                    "• Horarios 100% flexibles con reprogramación con 12h de aviso previo.\n\n"
                    "¿Para qué idioma buscas clases particulares?"
                )
            },

            # 3. Missed Classes & Attendance Policies
            {
                "category": "missed_classes_policy",
                "patterns": [
                    r"\b(falto|falta|faltar|inasistencia|asistencia|recuperar clase|recuperaci[oó]n|reponer|graban|grabaciones?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#4-attendance-missed-classes-and-makeup-policies"],
                "answer": (
                    "**Asistencia y Reposición de Clases:**\n\n"
                    "• **Grabaciones en HD**: Disponibles en el portal virtual en menos de 2 horas.\n"
                    "• **Tutorías gratuitas**: Tienes hasta **2 sesiones 1 a 1 de reposición** por módulo con un docente tutor.\n"
                    "• Se requiere un 80% de asistencia para certificar nivel.\n\n"
                    "¿Tienes alguna duda sobre los horarios de las clases?"
                )
            },

            # 4. Teachers, Methodology & Native Instructors
            {
                "category": "methodology_and_teachers",
                "patterns": [
                    r"\b(profesores? nativos?|metodolog[ií]a|m[eé]todo|c[oó]mo ense[ñn]an|docentes? certificados?|profesores? certificados?)\b"
                ],
                "sources": ["04_student_faq_and_academic_policies.md#1-academic-methodology-and-teaching-philosophy"],
                "answer": (
                    "**Metodología y Docentes:**\n\n"
                    "• **80% Producción Oral**: Enfoque comunicativo directo, debates y casos reales en grupos de máx. 8 estudiantes.\n"
                    "• **Docentes Certificados**: Profesores nativos y bilingües C2 con credenciales Cambridge CELTA/DELTA.\n\n"
                    "¿Te gustaría conocer las opciones de horarios disponibles?"
                )
            },

            # 5. Payment Methods & Financing
            {
                "category": "payment_methods",
                "patterns": [
                    r"\b(payment methods?|m[eé]todos? de pago|formas? de pago|how (can|do) i pay|c[oó]mo puedo pagar|pago con pse|pagar con tarjeta|cuotas sin inter[eé]s|financiaci[oó]n|pse|bancolombia|tarjeta de cr[eé]dito)\b"
                ],
                "sources": ["01_courses_and_pricing.md#6-payment-methods-and-financing-options"],
                "answer": (
                    "**Medios de Pago y Financiación:**\n\n"
                    "• **PSE y Tarjetas**: Visa, MasterCard, Amex y transferencias Bancolombia.\n"
                    "• **0% Interés**: Difiere en hasta **3 cuotas mensuales sin interés** con tarjeta o crédito directo.\n"
                    "• **Pronto Pago**: 15% de descuento cancelando 10 días antes del inicio.\n\n"
                    "¿Deseas que te ayudemos a gestionar tu inscripción?"
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
                    "**Nuestras Sedes Principales:**\n\n"
                    "• **Bogotá**: Calle 63 # 9-45, Chapinero Central (Lun–Vie 6am–9pm | Sáb 7:30am–2:30pm).\n"
                    "• **Medellín**: Carrera 43A # 7-50, El Poblado (Lun–Vie 6:30am–8:30pm | Sáb 8am–2pm).\n"
                    "• **100% Live Online**: Clases en vivo vía Zoom Education.\n\n"
                    "¿En cuál sede o modalidad te gustaría estudiar?"
                )
            },

            # 7. Saturday Intensive Schedules
            {
                "category": "saturday_schedules",
                "patterns": [
                    r"\b(saturday intensives?|s[aá]bados? intensivos?|horarios? de los s[aá]bados?|saturday schedule|fin de semana intensivo|s[aá]bados?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-comprehensive-class-schedules-and-timetables"],
                "answer": (
                    "**Curso Intensivo de Sábados:**\n\n"
                    "• **Horario**: 8:00 AM a 1:00 PM (5 horas continuas con receso).\n"
                    "• **Duración**: 12 sábados (60 horas académicas por nivel).\n"
                    "• **Inversión**: **$1,350,000 COP** (~$345 USD) con libros digitales incluidos.\n\n"
                    "¿Prefieres modalidad presencial en sede o virtual en vivo?"
                )
            },

            # 8. Weekday & Evening Schedules
            {
                "category": "weekday_schedules",
                "patterns": [
                    r"\b(evening track|nocturno|horario de noche|madrugadores?|morning schedule|qu[eé] horarios tienen|what are the class schedules|horarios?)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-comprehensive-class-schedules-and-timetables"],
                "answer": (
                    "**Horarios Entre Semana (Lunes a Jueves):**\n\n"
                    "• **Madrugadores**: 6:30 AM – 8:30 AM.\n"
                    "• **Mañana / Tarde**: 9:00 AM – 11:00 AM y 4:00 PM – 6:00 PM.\n"
                    "• **Nocturno Ejecutivo**: 6:30 PM – 8:30 PM.\n"
                    "• **Sábados**: 8:00 AM – 1:00 PM.\n\n"
                    "¿Qué horario se acomoda mejor a tu rutina?"
                )
            },

            # 9. Free Placement Diagnostic Test & Prior Knowledge Assessment
            {
                "category": "placement_test",
                "patterns": [
                    r"\b(s[eé] algo|no s[eé] (en )?qu[eé] nivel|no s[eé] mi nivel|qu[eé] nivel (soy|tengo)|d[oó]nde (puedo )?(comenzar|empezar)|por d[oó]nde empezar|en qu[eé] curso empezar|examen de clasificaci[oó]n|prueba de clasificaci[oó]n|placement|nivelaci[oó]n|diagn[oó]stico|evaluar mi nivel|saber mi nivel|hacer un examen|prueba de nivel|test de nivel|evaluaci[oó]n de nivel)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#2-free-placement-diagnostic-test--prior-knowledge-assessment-prueba-de-nivelacion-y-clasificacion"],
                "answer": (
                    "**Prueba de Nivelación Gratuita ($0 COP):**\n\n"
                    "Si ya tienes conocimientos previos, **no necesitas empezar desde cero**:\n\n"
                    "• **Formato**: 35 min online adaptativo + 10 min entrevista oral con un docente.\n"
                    "• **Resultados en 2 horas**: Informe oficial MCER (A1 a C2) con tu módulo exacto de inicio.\n\n"
                    "¿Te gustaría solicitar el enlace para presentar tu prueba hoy?"
                )
            },

            # 10. Languages Offered
            {
                "category": "languages_offered",
                "patterns": [
                    r"\b(languages? offered|qu[eé] idiomas ofrecen|what languages do you teach|qu[eé] cursos tienen|programas de idiomas|idiomas)\b"
                ],
                "sources": ["01_courses_and_pricing.md#2-detailed-language-programs-and-specializations"],
                "answer": (
                    "**Idiomas Disponibles en Global Language Academy:**\n\n"
                    "• **Inglés** (General, Negocios y Certificaciones IELTS/TOEFL).\n"
                    "• **Francés (DELF) & Alemán (Goethe)**.\n"
                    "• **Italiano, Portugués & Español para Extranjeros**.\n\n"
                    "¿Cuál de estos idiomas deseas aprender?"
                )
            },

            # 11. Official Exam Preparation (IELTS, TOEFL, Cambridge)
            {
                "category": "certifications",
                "patterns": [
                    r"\b(ielts|toefl|cambridge|fce|cae|delf|dalf|dele|siele|certificaciones?)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#3-official-international-certification-preparation-programs"],
                "answer": (
                    "**Preparación de Certificaciones Oficiales:**\n\n"
                    "• **IELTS & TOEFL iBT**: 40 horas de estrategia + 4 simulacros completos.\n"
                    "• **Cambridge**: B2 First (FCE) y C1 Advanced (CAE).\n"
                    "• **DELF/DALF** (Francés) y **DELE** (Español).\n\n"
                    "¿Qué examen internacional te interesa certificar?"
                )
            },

            # 12. Standard Discounts and Special Promotions
            {
                "category": "discounts",
                "patterns": [
                    r"\b(early bird discount|family discount|descuento por pronto pago|descuento de hermanos|convenios corporativos|tienen descuentos|hay promociones|descuentos?|promociones?)\b"
                ],
                "sources": ["01_courses_and_pricing.md#5-discounts-promotions-and-special-academic-bundles"],
                "answer": (
                    "**Descuentos y Beneficios Especiales:**\n\n"
                    "• **15% OFF**: Por Pronto Pago (10 días antes del inicio).\n"
                    "• **10% OFF**: Descuento familiar (2 o más matriculados).\n"
                    "• **25% OFF**: Paquete anual de 4 niveles consecutivos.\n"
                    "• Hasta **3 cuotas 0% interés** con tarjeta de crédito.\n\n"
                    "¿Deseas calcular tu tarifa final con descuento?"
                )
            },

            # 13. Immediate Schedule Change Follow-up
            {
                "category": "schedule_immediate_change",
                "patterns": [
                    r"^(\s*(de inmediato|inmediato|ya|lo antes posible|desde ya|inmediatamente)\s*)+[\.!\?]?$"
                ],
                "sources": ["02_schedules_and_modalities.md#4-schedule-changes-and-transfers"],
                "answer": (
                    "¡Entendido! Para realizar tu cambio de horario de inmediato, debemos verificar la disponibilidad de cupos en el grupo.\n\n"
                    "• **Disponibilidad**: Sujeto a espacios libres en el grupo actual.\n"
                    "• **Asesoría**: Un asesor confirmará tu traspaso hoy mismo.\n\n"
                    "¿Prefieres que te contactemos por llamada telefónica o por correo electrónico?"
                )
            },

            # 14. Email Contact Preference
            {
                "category": "email_contact_preference",
                "patterns": [
                    r"^(\s*(correo|por correo|email|por email|correo electr[oó]nico|por correo electr[oó]nico)\s*)+[\.!\?]?$"
                ],
                "sources": ["02_schedules_and_modalities.md#4-schedule-changes-and-transfers"],
                "answer": (
                    "¡Perfecto! Hemos registrado tu preferencia de contacto por correo electrónico.\n\n"
                    "• **Confirmación**: Un asesor revisará el cupo disponible y te escribirá hoy mismo.\n"
                    "• **Proceso**: Te enviaremos los detalles de tu nuevo horario.\n\n"
                    "Por favor compárteme tu correo electrónico actual para enviarte la confirmación:"
                )
            },

            # 15. Missing Email Alert & Clarification
            {
                "category": "missing_email_clarification",
                "patterns": [
                    r"\b(no te he dado mi correo|no te di mi correo|no te he pasado mi correo|no tienes mi correo|cu[aá]l correo si no te lo he dado|no tengo correo)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#4-schedule-changes-and-transfers"],
                "answer": (
                    "¡Tienes toda la razón, disculpa el olvido! Por favor, compárteme tu correo electrónico actual para asociarlo a tu solicitud de cambio de horario.\n\n"
                    "• **Gestión**: Así el asesor podrá escribirte directamente y confirmar tu cupo a través de Resend.\n\n"
                    "¿Cuál es tu dirección de correo electrónico?"
                )
            },

            # 16. Payment Troubleshooting
            {
                "category": "payment_troubleshooting",
                "patterns": [
                    r"\b(problemas? con el pago|fall[oó] el pago|no me deja pagar|error en el pago|pago pendiente|no pasa la tarjeta|rechaz[oó] el pago)\b"
                ],
                "sources": ["04_student_faq_and_academic_policies.md#3-payment-troubleshooting-and-financial-faq"],
                "answer": (
                    "¡Hola! Lamento el inconveniente con tu pago. Revisemos las causas más frecuentes:\n\n"
                    "• **PSE / Bancos**: Si el dinero fue debitado, la confirmación bancaria (CUS) suele tardar entre **15 y 30 minutos**.\n"
                    "• **Tarjetas de Crédito**: Revisa si tu banco requiere autorización de compras digitales o superaste el cupo diario.\n"
                    "• **Alternativas**: Puedes pagar vía transferencia directa Bancolombia, Addi (sin tarjeta) o en sedes Bogotá/Medellín.\n\n"
                    "¿Qué método utilizaste (PSE o Tarjeta) o qué mensaje de error te apareció?"
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
