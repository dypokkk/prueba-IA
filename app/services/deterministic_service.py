import re
from typing import Optional, Dict, Any, List

class DeterministicService:
    """
    Tier 1 Deterministic Engine:
    Instantly matches frequent canonical questions with verified factual answers.
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
                    "- 💰 **Precios y formas de pago** (PSE, tarjetas de crédito sin interés).\n"
                    "- ⏰ **Horarios y modalidades** (Mañanas, noches, sábados intensivos, virtual o presencial en Bogotá y Medellín).\n"
                    "- 🎯 **Prueba de nivelación gratuita** (Online, diagnóstica MCER A1-C2).\n"
                    "- 📜 **Certificaciones y exámenes oficiales** (IELTS, TOEFL, Cambridge, DELF, DELE).\n\n"
                    "¿En qué programa o idioma estás interesado hoy?"
                )
            },

            # 1. Payment Methods & Financing
            {
                "category": "payment_methods",
                "patterns": [
                    r"\b(payment methods?|m[eé]todos? de pago|formas? de pago|how (can|do) i pay|c[oó]mo puedo pagar|pago con pse|pagar con tarjeta|cuotas sin inter[eé]s)\b",
                    r"\b(pse|bancolombia transfer|tarjeta de cr[eé]dito)\b"
                ],
                "sources": ["01_courses_and_pricing.md#4-payment-methods-and-financing-options"],
                "answer": (
                    "**Payment Methods & Financing at Global Language Academy:**\n\n"
                    "- **PSE (Pagos Seguros en Línea)**: Direct bank debit from any Colombian bank (Bancolombia, Davivienda, Nequi, Daviplata, etc.).\n"
                    "- **Credit & Debit Cards**: Visa, MasterCard, American Express, and Diners Club.\n"
                    "- **Direct Bank Transfer**: Bancolombia Savings Account # 104-589231-88 (NIT 901.458.712-3).\n"
                    "- **0% Interest Installment Plans**: Up to 3 monthly installments at 0% interest via credit cards, or direct academy financing (50% upfront, 25% week 4, 25% week 8)."
                )
            },

            # 2. Campus Locations & Facilities
            {
                "category": "locations",
                "patterns": [
                    r"\b(locations?|sedes?|direcci[oó]n|addresses?|d[oó]nde est[aá]n|where are you located|d[oó]nde quedan|campus bogot[aá]|campus medell[ií]n|chapinero|el poblado)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#3-physical-campus-locations-and-facilities"],
                "answer": (
                    "**Our Flagship Campus Locations in Colombia:**\n\n"
                    "- **Bogotá Campus**: Calle 63 # 9-45, Chapinero Central (2 blocks from Calle 63 TransMilenio Station). Open Mon–Fri 6:00 AM–9:00 PM, Sat 7:30 AM–2:30 PM.\n"
                    "- **Medellín Campus**: Carrera 43A # 7-50, El Poblado (near Parque del Poblado). Open Mon–Fri 6:30 AM–8:30 PM, Sat 8:00 AM–2:00 PM.\n"
                    "- **100% Live Online**: Available worldwide via Zoom Education and Virtual Campus."
                )
            },

            # 3. Saturday Intensive Schedules
            {
                "category": "saturday_schedules",
                "patterns": [
                    r"\b(saturday intensives?|s[aá]bados? intensivos?|horarios? de los s[aá]bados?|saturday schedule|fin de semana intensivo)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-class-schedules-and-timetables"],
                "answer": (
                    "**Saturday Intensive Schedule:**\n\n"
                    "- **Time**: 8:00 AM to 1:00 PM (5 continuous hours with a 20-minute coffee break).\n"
                    "- **Structure**: 60 class hours completed in 12 consecutive Saturdays.\n"
                    "- **Tuition**: $1,350,000 COP (~$345 USD) per 12-week module.\n"
                    "- Available on-campus (Bogotá / Medellín) and 100% Live Online."
                )
            },

            # 4. Weekday & Evening Schedules
            {
                "category": "weekday_schedules",
                "patterns": [
                    r"\b(evening track|nocturno|horario de noche|madrugadores?|morning schedule|qu[eé] horarios tienen|what are the class schedules)\b"
                ],
                "sources": ["02_schedules_and_modalities.md#1-class-schedules-and-timetables"],
                "answer": (
                    "**Weekday Class Schedules (Monday to Thursday):**\n\n"
                    "- **Early Morning Track**: 6:30 AM – 8:30 AM (8 hrs/week).\n"
                    "- **Morning Standard Track**: 9:00 AM – 11:00 AM.\n"
                    "- **Afternoon Track**: 4:00 PM – 6:00 PM.\n"
                    "- **Evening Executive Track**: 6:30 PM – 8:30 PM (ideal for working professionals).\n"
                    "- **Saturday Intensives**: 8:00 AM – 1:00 PM."
                )
            },

            # 5. Free Placement Diagnostic Test
            {
                "category": "placement_test",
                "patterns": [
                    r"\b(placement test|prueba de nivelaci[oó]n|examen de nivel|diagnostic test|test de nivel gratis|how do i know my level|c[oó]mo s[eé] mi nivel)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#2-free-placement-diagnostic-test-prueba-de-nivelacion"],
                "answer": (
                    "**Free Online Placement Diagnostic Test:**\n\n"
                    "- **Cost**: 100% Free ($0 COP) with zero enrollment commitment.\n"
                    "- **Duration & Format**: 45-minute adaptive online test (Reading, Grammar, Listening) + a brief 10-minute speaking interview.\n"
                    "- **Results**: Delivered within 2 business hours via email and WhatsApp, valid for 90 days."
                )
            },

            # 6. Languages Offered
            {
                "category": "languages_offered",
                "patterns": [
                    r"\b(languages? offered|qu[eé] idiomas ofrecen|what languages do you teach|qu[eé] cursos tienen|programas de idiomas)\b"
                ],
                "sources": ["01_courses_and_pricing.md#1-course-offerings-overview"],
                "answer": (
                    "**Language Programs Offered at Global Language Academy:**\n\n"
                    "- **General English** (Levels A1 to C1)\n"
                    "- **Business & Executive English** (Levels B1 to C2)\n"
                    "- **French (Français)** (Levels A1 to C1)\n"
                    "- **German (Deutsch)** (Levels A1 to B2)\n"
                    "- **Italian (Italiano)** (Levels A1 to B2)\n"
                    "- **Portuguese (Português)** (Levels A1 to B2)\n"
                    "- **Spanish for Foreigners** (Levels A1 to C2)"
                )
            },

            # 7. Official Exam Preparation (IELTS, TOEFL, Cambridge)
            {
                "category": "certifications",
                "patterns": [
                    r"\b(ielts|toefl|cambridge|fce|cae|delf|dalf|dele|siele)\b"
                ],
                "sources": ["03_enrollment_and_certifications.md#3-official-exam-preparation-and-international-certifications"],
                "answer": (
                    "**Official Exam Preparation Programs:**\n\n"
                    "- **IELTS Academic & General**: 40-hour strategy course + 4 computer-delivered mock tests with band score diagnostic.\n"
                    "- **TOEFL iBT**: 40 hours focused on academic writing and integrated speaking.\n"
                    "- **Cambridge Qualifications**: B2 First (FCE) and C1 Advanced (CAE).\n"
                    "- **DELF / DALF** (French) and **DELE / SIELE** (Spanish).\n"
                    "- All regular course graduates receive a verifiable digital diploma with blockchain certification."
                )
            },

            # 8. Standard Discounts and Special Promotions
            {
                "category": "discounts",
                "patterns": [
                    r"\b(early bird discount|family discount|descuento por pronto pago|descuento de hermanos|convenios corporativos|tienen descuentos|hay promociones)\b"
                ],
                "sources": ["01_courses_and_pricing.md#3-discounts-promotions-and-special-offers"],
                "answer": (
                    "**Standard Discounts & Special Offers:**\n\n"
                    "- **Early Bird (15% OFF)**: Register at least 10 calendar days before course start.\n"
                    "- **Family & Sibling (10% OFF)**: When 2+ family members enroll together.\n"
                    "- **Annual Academic Bundle (25% OFF)**: Pay 4 levels upfront + free diagnostic kit.\n"
                    "- **Corporate Agreements (12% OFF)**: For employees of affiliated partner organizations.\n"
                    "*(Maximum cumulative discount is 30%)*"
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
