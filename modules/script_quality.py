"""
Script Quality Checker
Validates and scores scripts before video creation.
Ensures hooks are strong, length is right, and content is engaging.
"""

import re
from typing import Tuple
from modules.ai_engine import ask_ollama
from utils import get_logger

log = get_logger("quality")

# Ideal ranges
MIN_WORDS = 90
MAX_WORDS = 140
MIN_SENTENCES = 3
MAX_SENTENCES = 12
IDEAL_HOOK_MAX_WORDS = 8


def check_word_count(script: str) -> Tuple[bool, str]:
    """Check if script word count is in the ideal range."""
    words = len(script.split())
    if words < MIN_WORDS:
        return False, f"Too short ({words} words, need {MIN_WORDS}+)"
    if words > MAX_WORDS:
        return False, f"Too long ({words} words, max {MAX_WORDS})"
    return True, f"Word count OK ({words})"


def check_hook_strength(script: str) -> Tuple[bool, str]:
    """Check if the opening hook is strong."""
    first_sentence = script.split(".")[0].strip() if "." in script else script[:60]
    word_count = len(first_sentence.split())

    if word_count > IDEAL_HOOK_MAX_WORDS:
        return False, f"Hook too long ({word_count} words, max {IDEAL_HOOK_MAX_WORDS})"

    # Check for weak openings
    weak_starts = ["hi", "hello", "welcome", "today", "in this video", "so", "well",
                   "let me", "i want to", "have you ever"]
    first_lower = first_sentence.lower()
    for weak in weak_starts:
        if first_lower.startswith(weak):
            return False, f"Weak hook start: '{weak}...'"

    return True, f"Hook looks strong ({word_count} words)"


def check_has_question(script: str) -> Tuple[bool, str]:
    """Check if script ends with a polarized engagement question (Yes/No style).
    Polarized questions (e.g. 'Would you enter? Yes or No?') drive 3-5x more comments
    than open-ended questions because they require zero creative effort to answer.
    """
    has_question = "?" in script[-120:]  # Check last 120 chars
    if not has_question:
        return False, "Missing engagement question at the end"

    # Check if it's a POLARIZED (binary-choice) question — the high-engagement kind
    last_120 = script[-120:].lower()
    polarized_signals = [
        "yes or no", "agree or disagree", "would you", "could you",
        "genius or", "scam or", "right or wrong", "true or false",
        "real or fake", "believe it or not", "dare to", "worth it or not",
    ]
    is_polarized = any(p in last_120 for p in polarized_signals)

    if is_polarized:
        return True, "Strong polarized CTA ✓ (forces binary comment)"
    return True, "Has question but not polarized — upgrade to Yes/No format for more comments"


def check_no_filler(script: str) -> Tuple[bool, str]:
    """Check for filler words that hurt retention."""
    filler_words = ["basically", "actually", "literally", "kind of", "sort of",
                    "you know", "like", "um", "uh", "so yeah"]
    found = []
    lower = script.lower()
    for filler in filler_words:
        if filler in lower:
            found.append(filler)

    if found:
        return False, f"Filler words found: {', '.join(found)}"
    return True, "No filler words"


def check_hook_variety(title: str, recent_titles: list) -> Tuple[bool, str]:
    """
    Check if the hook pattern is too similar to recently used ones.
    Fails if the same leading word/pattern appears in 3+ of the last 10 titles.
    This prevents the channel from producing repetitive "😱 ... Revealed" spam.
    """
    if not recent_titles or not title:
        return True, "No recent titles to compare"

    recent_sample = recent_titles[:10]
    title_first_word = title.lower().split()[0].strip("!❤😱🤯😞🚨🚀") if title.split() else ""

    matching = 0
    for rt in recent_sample:
        rt_first = rt.lower().split()[0].strip("!❤😱🤯😞🚨🚀") if rt.split() else ""
        if rt_first == title_first_word and title_first_word:
            matching += 1

    if matching >= 3:
        return False, f"Hook pattern '{title_first_word}' repeated in {matching}/10 recent videos"
    return True, f"Hook is fresh ('{title_first_word}' used {matching} times recently)"


def check_retention_loop(script: str) -> Tuple[bool, str]:
    """
    Check if the script's ending echoes its beginning (creates a seamless replay loop).
    When the last sentence references the first, YouTube counts replays as continued
    watch time, which boosts the algorithm ranking significantly.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]', script) if s.strip() and len(s.strip()) > 5]
    if len(sentences) < 3:
        return False, "Too few sentences to evaluate retention loop"

    # Get key words from the first sentence (exclude stop words)
    stop_words = {"the", "a", "an", "is", "in", "and", "this", "that", "it",
                  "to", "of", "for", "on", "are", "was", "with", "you", "your"}
    first_words = set(sentences[0].lower().split()) - stop_words
    last_words = set(sentences[-1].lower().split()) - stop_words

    overlap = first_words & last_words
    if len(overlap) >= 2:
        return True, f"Retention loop detected ✓ (shared: {', '.join(list(overlap)[:3])})"
    elif len(overlap) == 1:
        return True, f"Weak retention loop (only 1 shared word: {list(overlap)[0]}) — add more echo"
    return False, "No retention loop — last sentence doesn't echo the hook (missed watch time boost)"


def check_specificity(script: str) -> Tuple[bool, str]:
    """
    Check if the script contains at least one specific element:
    a proper noun (capitalized word), a number, or a named place.
    Specific scripts have proven higher CTR than vague ones.
    """
    # Check for numbers (including $ amounts, percentages)
    has_number = bool(re.search(r'\b\d+[%kKmMbB]?\b|\$\d+', script))

    # Check for capitalized proper nouns (words not at start of sentence that are capitalized)
    words = script.split()
    proper_nouns = []
    for i, word in enumerate(words):
        clean = re.sub(r'[^a-zA-Z]', '', word)
        if i > 0 and clean and clean[0].isupper() and len(clean) > 2:
            proper_nouns.append(clean)

    has_proper_noun = len(proper_nouns) > 0

    if has_number or has_proper_noun:
        detail = f"numbers: {has_number}, proper nouns: {proper_nouns[:3]}"
        return True, f"Script is specific ({detail})"

    return False, "Script lacks specifics (no numbers or proper nouns) — add names/numbers"


def validate_script(script: str, title: str = "", recent_titles: list = None) -> dict:
    """
    Run all quality checks on a script.
    Returns dict with overall score and details.

    Args:
        script: The spoken script text.
        title: The video title (used for hook variety check).
        recent_titles: Last N uploaded titles (used for variety check).
    """
    checks = {
        "word_count": check_word_count(script),
        "hook_strength": check_hook_strength(script),
        "engagement_question": check_has_question(script),
        "no_filler": check_no_filler(script),
        "specificity": check_specificity(script),
        "retention_loop": check_retention_loop(script),  # Phase 4: new check
    }

    # Hook variety is a warning-only check (doesn't reduce score)
    if title and recent_titles:
        variety_ok, variety_msg = check_hook_variety(title, recent_titles)
        checks["hook_variety"] = (variety_ok, variety_msg)

    passed = sum(1 for ok, _ in checks.values() if ok)
    total = len(checks)
    score = round((passed / total) * 100)

    result = {
        "score": score,
        "passed": passed,
        "total": total,
        "checks": {name: {"pass": ok, "message": msg} for name, (ok, msg) in checks.items()},
        "approved": score >= 50,  # At least half must pass
    }

    log.info(f"Script quality: {score}% ({passed}/{total} checks passed)")
    for name, (ok, msg) in checks.items():
        icon = "✓" if ok else "✗"
        log.debug(f"  {icon} {name}: {msg}")

    return result


def ai_quality_score(script: str) -> int:
    """Use AI to score the script 1-10."""
    prompt = f"""Rate this YouTube Shorts script from 1-10 for viral potential.

SCRIPT: {script}

Consider:
- Hook strength (does it stop the scroll?)
- Curiosity (does it create an open loop?)
- Pacing (short punchy sentences?)
- Twist (is there a surprising element?)
- Engagement (does it encourage comments/shares?)

Return ONLY a single number from 1 to 10. Nothing else:"""

    response = ask_ollama(prompt)
    try:
        # Extract number from response
        numbers = re.findall(r'\d+', response)
        if numbers:
            score = int(numbers[0])
            return min(max(score, 1), 10)
    except Exception:
        pass
    return 5  # Default middle score


def improve_script(script: str, issues: list) -> str:
    """Ask AI to fix specific issues in the script."""
    issues_text = "\n".join([f"- {issue}" for issue in issues])

    prompt = f"""Rewrite this YouTube Shorts script fixing these issues:

ISSUES:
{issues_text}

CURRENT SCRIPT:
{script}

Rules:
- Keep it 90-120 words
- Strong hook under 10 words
- End with an engagement question
- No filler words
- Short punchy sentences

Return ONLY the rewritten script, nothing else:"""

    improved = ask_ollama(prompt)
    if improved and len(improved) > 20:
        return improved
    return script  # Return original if improvement fails


if __name__ == "__main__":
    test_script = (
        "This AI just replaced 1000 employees overnight. "
        "A major tech company quietly deployed an AI system that handles "
        "all customer support. The crazy part? Customer satisfaction actually "
        "went up by 30 percent. Nobody noticed the difference. "
        "What job do you think AI will replace next?"
    )

    print("Validating script...")
    result = validate_script(test_script)
    print(f"\nScore: {result['score']}%")
    for name, check in result["checks"].items():
        icon = "✓" if check["pass"] else "✗"
        print(f"  {icon} {name}: {check['message']}")
