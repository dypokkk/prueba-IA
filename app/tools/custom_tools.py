from typing import Dict, Any

def calculate_course_quote(
    program_type: str = "standard_group",
    has_early_bird: bool = False,
    has_sibling: bool = False,
    annual_bundle: bool = False
) -> Dict[str, Any]:
    """
    Computes accurate tuition quotes, discounts, and installment plans.
    """
    base_prices_cop = {
        "standard_group": 1250000,
        "intensive_group": 1450000,
        "saturday_intensive": 1350000,
        "kids_teens": 1150000,
        "private_10h": 850000,
        "private_25h": 1950000,
        "private_50h": 3600000,
    }

    base_price = base_prices_cop.get(program_type.lower(), 1250000)

    # Calculate discount percentages
    discount_pct = 0.0
    discount_names = []

    if annual_bundle:
        discount_pct = 0.25
        discount_names.append("Annual Bundle (25%)")
    else:
        if has_early_bird:
            discount_pct += 0.15
            discount_names.append("Early Bird (15%)")
        if has_sibling:
            discount_pct += 0.10
            discount_names.append("Family & Sibling (10%)")

    # Cap discount at 30%
    discount_pct = min(discount_pct, 0.30)
    discount_amount = int(base_price * discount_pct)
    final_price_cop = base_price - discount_amount

    # Approximate USD (at 3900 COP / USD)
    usd_rate = 3900.0
    final_price_usd = round(final_price_cop / usd_rate, 2)

    # 3-Month installments
    installment_3m = round(final_price_cop / 3)

    return {
        "program_type": program_type,
        "base_price_cop": f"${base_price:,.0f} COP",
        "discount_applied": f"{int(discount_pct * 100)}%",
        "discounts_used": discount_names if discount_names else ["None"],
        "discount_savings_cop": f"${discount_amount:,.0f} COP",
        "final_price_cop": f"${final_price_cop:,.0f} COP",
        "approx_price_usd": f"~${final_price_usd} USD",
        "installment_plan_3_months": f"3 payments of ${installment_3m:,.0f} COP (0% interest)"
    }


def check_level_placement(score_percentage: float) -> Dict[str, Any]:
    """
    Maps diagnostic placement test score percentage (0-100%) to CEFR Level and recommended course module.
    """
    score = max(0.0, min(100.0, float(score_percentage)))

    if score < 30.0:
        cefr = "A1 (Breakthrough / Beginner)"
        recommended_module = "Module A1.1 (Foundations)"
        description = "Focus on basic greetings, survival vocabulary, and essential sentence structures."
    elif score < 50.0:
        cefr = "A2 (Waystage / Elementary)"
        recommended_module = "Module A2.1 (Elementary Fluency)"
        description = "Focus on everyday communication, past tense narratives, and routine interactions."
    elif score < 70.0:
        cefr = "B1 (Threshold / Intermediate)"
        recommended_module = "Module B1.1 (Intermediate Practical)"
        description = "Focus on opinions, work travel, and spontaneous conversational flow."
    elif score < 85.0:
        cefr = "B2 (Vantage / Upper-Intermediate)"
        recommended_module = "Module B2.1 (Professional Upper)"
        description = "Focus on technical topics, debates, and complex linguistic structures."
    elif score < 95.0:
        cefr = "C1 (Effective Operational Proficiency)"
        recommended_module = "Module C1.1 (Advanced Executive)"
        description = "Focus on academic discussions, idiomatic precision, and executive presentations."
    else:
        cefr = "C2 (Mastery / Native-Level)"
        recommended_module = "Module C2 (Mastery & Exam Certification)"
        description = "Full native-like precision and subtle nuance mastery."

    return {
        "score_percentage": f"{score}%",
        "cefr_level": cefr,
        "recommended_module": recommended_module,
        "description": description,
        "official_prep_eligible": score >= 70.0
    }
