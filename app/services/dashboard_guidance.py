"""Source-linked dashboard education selected from real onboarding context.

This catalogue is authored patient education, not an approved Stage 5 release
or generated RAG output. Its provenance travels with every displayed section.
It does not import evaluation fixtures or call a model.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.schemas.retrieval import JourneyPosition
from app.services.dashboard_overview import static_overview


CATALOGUE = json.loads((Path(__file__).resolve().parents[2] / "data/dashboard/reference_catalogue.json").read_text(encoding="utf-8"))

# All examples are single ingredients/food groups. No recipe is declared
# allergen-free: packaging, preparation and cross-contact still matter.
ALIASES = {
    "peanut": ("peanut", "peanuts", "groundnut", "groundnuts", "moongphali"),
    "dairy": ("dairy", "milk", "lactose", "paneer", "curd", "yogurt", "yoghurt", "whey", "casein", "ghee", "butter"),
    "soy": ("soy", "soya", "soybean", "soybeans", "tofu"),
    "gluten": ("gluten", "wheat", "barley", "rye", "atta", "maida", "semolina", "suji", "celiac", "coeliac"),
    "egg": ("egg", "eggs"),
    "nuts": ("nut", "nuts", "almond", "almonds", "cashew", "cashews", "walnut", "walnuts", "pistachio"),
    "sesame": ("sesame", "til"),
    "lentil": ("lentil", "lentils", "dal", "daal", "moong", "masoor"),
    "chickpea": ("chickpea", "chickpeas", "chana", "besan"),
    "bean": ("bean", "beans", "rajma", "kidney bean"),
    "legume": ("legume", "legumes", "pulse", "pulses"),
    "chicken": ("chicken", "poultry"),
    "fish": ("fish", "seafood", "shellfish", "prawn", "prawns"),
    "greens": ("greens", "leafy greens"),
    "spinach": ("spinach", "palak"),
    "broccoli": ("broccoli",),
    "rice": ("rice",),
    "oats": ("oat", "oats"),
}


def _contains(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text, re.I) for word in words)


def food_constraints(diets: list[str], allergies: list[str]) -> dict:
    diet = " ".join(diets).casefold()
    excluded: set[str] = set()
    unmatched = []
    for value in allergies:
        # Split multi-allergen free text so a recognised first ingredient does
        # not hide an unrecognised second ingredient.
        parts = re.split(r"[,;/]|\band\b|\b&\b", value, flags=re.I)
        for part in parts:
            normalized = re.sub(r"\b(i am|i'm|allergic to|allergy to|allergy|allergies|avoid|intolerant to)\b", "", part, flags=re.I).strip(" .:-")
            if not normalized:
                continue
            matched = {key for key, aliases in ALIASES.items() if _contains(normalized, aliases)}
            if not matched:
                unmatched.append(normalized)
            excluded.update(matched)
    vegan = _contains(diet, ("vegan", "plant-based"))
    vegetarian = any(value.strip().casefold() == "vegetarian" for value in diets)
    egg_friendly = _contains(diet, ("egg-friendly", "eggs"))
    if vegan:
        excluded.add("animal")
    elif vegetarian:
        excluded.add("meat")
        if not egg_friendly:
            excluded.add("egg")
    if _contains(diet, ("dairy-free", "dairy free")):
        excluded.add("dairy")
    if _contains(diet, ("gluten-free", "gluten free")):
        excluded.add("gluten")
    return {"excluded_tags": excluded, "unmatched": unmatched, "vegan": vegan,
            "plant_based": vegan or vegetarian}


def _source_links(ids: list[str]) -> list[dict]:
    return [{"id": key, **CATALOGUE["sources"][key]} for key in dict.fromkeys(ids)]


def _section(key: str, title: str, summary: str, sources: list[str], *,
             bullets: list[str] | None = None, reference: str | None = None,
             basis: str | None = None, options: list[dict] | None = None,
             tone: str = "normal") -> dict:
    return {"id": key, "title": title, "summary": summary, "bullets": bullets or [],
            "reference": reference, "basis": basis, "food_options": options or [],
            "source_links": _source_links(sources), "tone": tone}


def journey_overview(journey: JourneyPosition, label: str) -> dict:
    start = journey.exact if journey.exact is not None else journey.range_start
    end = journey.exact if journey.exact is not None else journey.range_end
    assert start is not None and end is not None
    if journey.stage == "postpartum":
        return {"label": label, "phase": "Early recovery" if end <= 6 else "Building back gradually",
                "progress_start": round(min(start / 12, 1) * 100, 1),
                "progress_end": round(min(end / 12, 1) * 100, 1),
                "range": start != end, "start": start, "end": end,
                "progress_label": "Position in the first 12 weeks; not a recovery score"}
    phases = ["First trimester" if value < 14 else "Second trimester" if value < 28 else "Third trimester" for value in (start, end)]
    return {"label": label, "phase": phases[0] if phases[0] == phases[1] else " / ".join(phases),
            "progress_start": round(min(start / 40, 1) * 100, 1),
            "progress_end": round(min(end / 40, 1) * 100, 1),
            "range": start != end, "start": start, "end": end,
            "progress_label": "Pregnancy timeline toward 40 weeks"}


def build_dashboard_guidance(journey: JourneyPosition, label: str, *, diets: list[str],
                             allergies: list[str], symptoms: list[str], restrictions: list[str] | None = None) -> dict:
    overview = journey_overview(journey, label)
    start, end = overview["start"], overview["end"]
    pregnant = journey.stage == "pregnancy"
    constraints = food_constraints(diets, allergies)
    eligible_foods = [food for food in CATALOGUE["foods"]
                      if not constraints["excluded_tags"].intersection(food["tags"])
                      and not (allergies and "packaged" in food["tags"])]
    if constraints["unmatched"]:
        eligible_foods = []

    nutrition = []
    if pregnant:
        for item in CATALOGUE["nutrients"]:
            options = [food for food in eligible_foods if item["id"] in food["nutrients"]]
            bullets = []
            if item["id"] == "iron" and constraints["plant_based"]:
                bullets.append("With a vegetarian or vegan diet, iron is absorbed less readily. Ask your care team about your individual food target and any prescribed iron; do not double a tablet dose.")
            nutrition.append(_section(item["id"], item["title"], item["summary"],
                item["source_ids"] + [key for food in options for key in food["source_ids"]],
                reference=item["reference"], basis=item["basis"], bullets=bullets,
                options=[{"id": food["id"], "label": food["label"], "tags": food["tags"]} for food in options]))
        nutrition.append(_section("supplements", "Your supplement routine", "Keep prescribed supplements on the schedule your clinician gave you. These food references do not calculate a supplement dose.", ["pregnancy_nutrients", "b12"], bullets=[
            "Vitamin D: the US pregnancy intake reference is 15 mcg (600 IU) daily; local supplement advice can differ.",
            "If you already use a prenatal supplement, check its contents with your clinician before adding another product.",
            *(["A vegan diet needs a reliable vitamin B12 source, such as suitable fortified foods or a clinician-advised supplement."] if constraints["vegan"] else []),
        ]))
        nutrition.append(_section("food-safety", "Food preparation & things to avoid", "Choose hygienically prepared food and check ingredient labels.", ["food_safety"], bullets=[
            "Wash produce; cook meat and eggs thoroughly; choose pasteurised dairy if it fits your diet.",
            "Avoid alcohol, raw seafood, liver and liver products, and supplements containing retinol (vitamin A).",
            "Keep caffeine at or below 200 mg a day from all sources.",
            "Avoid shark, swordfish and marlin. Follow local advice on other fish and mercury.",
        ]))
    else:
        nutrition.append(_section("recovery-meals", "Make regular meals easier", "Keep varied, balanced meals and fluids within reach while you recover.", ["postpartum", "diet"], options=[{"id": food["id"], "label": food["label"], "tags": food["tags"]} for food in eligible_foods if "protein" in food["nutrients"]], bullets=[
            "Ask someone to help with shopping, cooking or a prepared meal when you need it.",
            "Your breastfeeding status was not entered, so Maya has not assigned breastfeeding-specific intake targets.",
        ]))
        nutrition.append(_section("postpartum-iron", "Iron after birth", "Continue any prescribed iron as directed. Blood loss, test results and feeding status affect individual needs.", ["iron"], bullets=["Pregnancy's 27 mg reference is not automatically your postpartum target.", "If you have ongoing heavy bleeding or feel faint, seek medical help rather than treating this with food alone."]))
        nutrition.append(_section("postpartum-calcium", "Calcium & variety", "Include suitable calcium sources as part of a varied diet.", ["calcium"], reference="1,000 mg / day", basis="US adult reference, ages 19–50, including breastfeeding. Ages 14–18: 1,300 mg / day.", options=[{"id": food["id"], "label": food["label"], "tags": food["tags"]} for food in eligible_foods if "calcium" in food["nutrients"]]))

    symptom_text = " ".join(symptoms).casefold()
    back_pain = _contains(symptom_text, ("back ache", "backache", "back pain", "lower back", "pelvic pain"))
    heartburn = _contains(symptom_text, ("heartburn", "acid reflux", "acidity"))
    nausea = _contains(symptom_text, ("nausea", "nauseous", "vomiting", "morning sickness"))
    known_nonmovement = {"heartburn", "acid reflux", "acidity", "trouble sleeping", "low energy", "tired", "fatigue"}
    other_movement_concern = bool(symptoms) and not back_pain and any(
        value.casefold().strip() not in known_nonmovement for value in symptoms)
    if heartburn and pregnant:
        nutrition.insert(0, _section("heartburn-adjustment", "For the heartburn you reported", "Try smaller, more frequent meals and stay upright after eating.", ["heartburn"], bullets=["Avoid eating in the three hours before bed; notice and limit foods that trigger your symptoms.", "Get medical advice if symptoms persist or you have trouble swallowing."], tone="context"))
    if nausea and pregnant:
        nutrition.insert(0, _section("nausea-adjustment", "For the nausea you reported", "Small, frequent meals and small sips of fluid may be easier to tolerate.", ["nausea"], bullets=["Get medical advice if you cannot keep food or fluids down for 24 hours, or have dark urine or dizziness."], tone="context"))

    if back_pain:
        movement = [_section("back-adjustment", "For the back discomfort you reported", "Do not push through pain or add heavy lifting and twisting. Comfortable posture and support can help while you arrange advice.", ["back_pain"] if pregnant else ["postpartum"], bullets=[
            *( ["Because your timing includes the second or third trimester, contact your maternity team promptly about back pain; it can sometimes signal early labour."] if pregnant and end >= 14 else ["Talk to your care team if the pain is severe, persistent or limits movement."]),
            "Get urgent help for pain with bleeding, fever, urinary symptoms, or loss of feeling in your legs or pelvic area.",
        ], tone="context")]
    elif other_movement_concern:
        movement = [_section("symptom-adjustment", "Movement with your reported symptoms", "Your reported symptoms are kept in context. Avoid starting or increasing exercise while a new or unexplained symptom is affecting you.", ["exercise"] if pregnant else ["postpartum"], bullets=["Ask your care team which activities fit the symptom you entered. Nutrition and the rest of your dashboard remain available."], tone="context")]
    else:
        movement = []
    limited = back_pain or other_movement_concern or bool(restrictions)
    if restrictions:
        movement.insert(0, _section("restriction-context", "Your movement restrictions", "Keep the instructions you reported in place; a week-based card does not override them.", ["exercise"] if pregnant else ["postpartum"], bullets=list(restrictions), tone="context"))
    if pregnant:
        movement.append(_section("aerobic", "Walking & low-impact activity", "Choose an activity you can do comfortably while still being able to talk.", ["activity", "exercise"], reference="150 min / week" if not limited else None,
            basis="General moderate-activity goal for an uncomplicated pregnancy; build up gradually from your current level." if not limited else "General information, not an exercise prescription for your reported symptoms or restrictions.",
            bullets=["Walking, swimming or a suitable prenatal class can be options when comfortable.", "If you were inactive, begin gradually. An early pregnancy week is not a reason to start strenuous exercise."] if not limited else ["Discuss comfortable activity options with your care team before using an activity target."]))
        movement.append(_section("strength", "Strength, posture & pelvic floor", "Keep movement controlled and within a comfortable range.", ["exercise"], bullets=[
            "A qualified prenatal instructor can help adapt strengthening work; tell them your pregnancy stage.",
            "Pelvic floor exercises are part of pregnancy movement guidance; follow the linked instructions.",
        ] if not limited else ["A maternity physiotherapist can help choose exercises that suit your reported symptoms or restrictions. Do not treat this general page as clearance for a workout."]))
        movement.append(_section("position", "Position & comfort", "Adapt positions as your pregnancy progresses.", ["exercise"], bullets=[
            "Avoid long periods lying flat on your back, particularly after 16 weeks." if end >= 16 else "Use comfortable positions; from around 16 weeks, avoid long periods lying flat on your back.",
            "Warm up, cool down, drink water and avoid strenuous exercise in hot conditions.",
            "Avoid contact sports and scuba diving; take care with activities that risk a fall.",
        ]))
    else:
        movement.append(_section("postpartum-activity", "A gradual return to movement", "Recovery and birth experience matter as well as the week on your timeline.", ["postpartum"], bullets=[
            "After a straightforward birth, gentle walking, stretches and pelvic floor work can start when you feel ready." if end <= 6 else "Build activity gradually according to your recovery and postnatal advice.",
            "After a caesarean or complicated birth, ask your care team before strenuous activity.",
            "Discuss high-impact activity at your postnatal check before returning to running or aerobics.",
        ]))

    overview_content = static_overview(journey, movement_limited=limited)
    focus, focus_detail = overview_content['nutrition']['title'], overview_content['nutrition']['body']
    movement_focus = overview_content['movement']['title']
    # Stage-specific presentation surrounds pregnancy-wide references. Do not
    # invent a different daily nutrient requirement for every seven-day window.
    if pregnant:
        if end <= 13:
            stage_title, stage_body = 'Early pregnancy: make meals manageable', 'Focus on regular, varied meals and your advised folic-acid routine. If nausea affects you, smaller meals may be easier.'
            stage_sources = ['diet', 'pregnancy_nutrients', 'nausea']
        elif start >= 28:
            stage_title, stage_body = 'Later pregnancy: variety with comfort', 'Keep protein, iron and calcium foods in your routine. If fullness or heartburn affects you, try smaller meals rather than forcing large portions.'
            stage_sources = ['diet', 'iron', 'calcium', 'heartburn']
        elif start >= 14 and end <= 27:
            stage_title, stage_body = 'Middle pregnancy: build a varied routine', 'Include protein foods, calcium sources and iron-rich choices across your meals. Pair plant iron with vitamin C; maintain variety rather than relying on one food.'
            stage_sources = ['diet', 'iron', 'calcium']
        else:
            stage_title, stage_body = 'Across your week range', 'Your selected month spans a stage boundary. Keep a varied diet; the references below apply across pregnancy, not to one exact week.'
            stage_sources = ['diet', 'pregnancy_nutrients']
        nutrition.insert(0, _section('stage-nutrition', stage_title, stage_body, stage_sources,
            bullets=[f'This stage’s editorial highlights: {focus}. These do not mean other nutrients are less important.']))
        nutrition.append(_section('hydration', 'Water through the day', 'Spread drinks across the day. Follow any fluid restriction your care team has given you.', ['water'],
            bullets=['General pregnancy reference: 8–12 US cups of water daily (about 1.9–2.8 litres), not a target for someone with a prescribed fluid restriction.'] if not restrictions else ['Your reported restrictions take priority; confirm a fluid target with your care team.']))
    if allergies:
        nutrition.insert(0, _section('allergy-exclusions', 'Your ingredients to avoid', 'Your allergy entries filter the food options below. Check every ingredient and preparation method, including cross-contact.', ['food_safety'], bullets=[f'Avoid your reported allergen: {value}' for value in allergies], tone='context'))
    movement.insert(sum(section['tone'] == 'context' for section in movement), _section('stage-movement', movement_focus, overview_content['movement']['body'], ['exercise'] if pregnant else ['postpartum'],
        bullets=([('As your bump grows, adapt for balance and comfort; this is not a week-based fitness test.' if end >= 21 else 'Build from your existing activity level; an earlier week does not make strenuous exercise automatically suitable.')] if pregnant else ['Birth experience and recovery take priority over a calendar target.'])))
    movement.append(_section('stop-signs', 'When to pause and get help', 'Stop activity if you feel unwell. Seek urgent medical care for warning signs rather than continuing a workout.', ['warning_signs'], bullets=['Examples include chest pain, trouble breathing, fainting, severe persistent pain, bleeding or fluid leakage.', 'During pregnancy, reduced or changed baby movements need prompt maternity advice. This is not a complete list.']))

    symptom_sections = [_section('reported-symptoms', 'What you have shared' if symptoms else 'No symptoms added',
        'These are your onboarding entries, not a diagnosis.' if symptoms else 'You do not need a symptom to use Maya. Add or update details using Edit my details when something changes.',
        ['warning_signs'], bullets=list(symptoms), tone='context' if symptoms else 'normal')]
    for section in nutrition + movement:
        if section['id'] in {'heartburn-adjustment', 'nausea-adjustment', 'back-adjustment'}:
            symptom_sections.append(section)
    sleep_reported = _contains(symptom_text, ('trouble sleeping', 'sleep', 'insomnia', 'low energy', 'tired', 'fatigue'))
    if sleep_reported and pregnant:
        symptom_sections.append(_section('sleep-support', 'For the rest or sleep concern you shared', 'Make room for rest and ask for practical help. Speak to your maternity team if sleep problems persist or affect daily life.', ['sleep'], bullets=['A quiet wind-down and less caffeine in the evening may help.', *(['From 28 weeks, settle to sleep on your side; pillows can support your bump and knees.'] if end >= 28 else [])]))
    symptom_sections.append(_section('symptom-notes', 'Make a useful symptom note', 'For a new, persistent or worrying symptom, tell your care team what changed, when it began and what makes it better or worse. Maya cannot diagnose it.', ['warning_signs'], bullets=['Do not wait for a chatbot reply when you need urgent help.']))
    symptom_sections.append(_section('urgent-signs', 'Know when not to wait', 'Get urgent medical help for chest pain, trouble breathing, fainting, severe headache or pain, heavy bleeding, or thoughts of harming yourself or your baby.', ['warning_signs'], bullets=['During pregnancy, a change or reduction in baby movements needs prompt maternity advice.', 'Tell the clinician if you are pregnant or have given birth within the past year.']))
    wellbeing = [
        _section('self-care', 'Make a little room for yourself', 'Choose one small thing you enjoy today. Your week does not determine your mood, and there is no right way to feel.', ['mental_health'], bullets=['Speak with someone you trust about what you need.', 'A practical favour, a shared meal or company can be a useful form of support.']),
        _section('rest-routine', overview_content['energy']['title'], overview_content['energy']['body'], ['sleep'] if pregnant else ['postpartum'], bullets=([('From 28 weeks, settle to sleep on your side; turn back onto your side if you wake on your back.' if end >= 28 else 'Make space for a comfortable rest when you need one.')] if pregnant else ['Accept help with meals and household jobs so you can rest.'])),
        _section('emotional-support', 'Support is part of self-care', 'If worry, low mood or sleep difficulties are affecting you, speak to your maternity team or doctor. You do not have to manage this alone.', ['mental_health', 'warning_signs'], bullets=['Seek urgent help if you feel unsafe or have thoughts of harming yourself or your baby.']),
    ]
    if sleep_reported and pregnant:
        wellbeing.insert(0, _section('your-rest-context', 'Rest, with your needs in mind', 'You mentioned a rest or energy concern. Give yourself permission to ask for help; speak to your care team if it persists or affects daily life.', ['sleep', 'mental_health'], tone='context'))
    emotional_reports = [value for value in symptoms if _contains(value, ('anxious', 'anxiety', 'worried', 'worry', 'sad', 'low mood', 'stress', 'stressed'))]
    if emotional_reports:
        wellbeing.insert(0, _section('your-emotional-context', 'Space for what you shared', 'Talk with someone you trust and your maternity team about these concerns. Maya does not diagnose a condition from your entries.', ['mental_health'], bullets=emotional_reports, tone='context'))
    week_sections = [_section("week-nutrition", focus, focus_detail, ["pregnancy_nutrients", "diet"] if pregnant else ["postpartum"]),
        _section("week-movement", movement_focus, "See Movement for options and adjustments based on your timeline and reported symptoms.", ["exercise"] if pregnant else ["postpartum"])]
    if pregnant and end >= 24:
        week_sections.append(_section("baby-movement", "Know your baby's usual movement pattern", "If movements slow, stop or change from the usual pattern, contact your maternity team immediately; do not wait until tomorrow.", ["fetal_movement"]))
    return {
        "version": CATALOGUE["version"], "kind": CATALOGUE["kind"],
        "source_checked_on": CATALOGUE["source_checked_on"], "clinical_approval": None,
        "journey": overview, "overview_content": overview_content,
        "nutrition_focus": focus, "nutrition_focus_detail": focus_detail,
        "movement_focus": movement_focus, "movement_focus_detail": overview_content['movement']['body'],
        "nutrition": nutrition, "movement": movement, "this_week": week_sections,
        "symptoms": symptom_sections, "wellbeing": wellbeing,
        "applied_context": {"diets": diets, "allergies": allergies, "symptoms": symptoms},
        "unmatched_allergies": constraints["unmatched"],
        "food_note": "Check labels, ingredients and cross-contact for your stated allergies. Food examples are not a nutritionally complete meal plan.",
        "reference_note": "Daily figures are published US dietary references, not a personalised prescription or India-specific supplement schedule. Your clinician's advice takes priority. Many targets stay the same across pregnancy.",
        "trace": {"fixture_used": False, "model_called": False, "retrieval": "local_reference_catalogue", "excluded_food_tags": sorted(constraints["excluded_tags"])},
    }
