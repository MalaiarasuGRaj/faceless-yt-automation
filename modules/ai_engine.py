"""
AI Engine - Local Ollama Integration
Handles all AI generation: ideas, scripts, SEO, hook optimization.
100% FREE - runs on your computer via Ollama.

STRATEGY: English scripts + Hindi voice = best quality + maximum reach
"""

import requests
import json
import re
import random
import os
from typing import Optional
from config.settings import OLLAMA_URL, OLLAMA_MODEL, CONTENT_LANGUAGE, HOOK_TYPE_WEIGHTS
from utils import get_logger

log = get_logger("ai_engine")

# Lazy import to avoid circular dependency (analytics_engine imports ai_engine)
def _get_performance_context() -> str:
    """Lazy-load performance context to avoid circular imports."""
    try:
        from modules.analytics_engine import get_performance_context
        return get_performance_context()
    except Exception:
        return ""

# Curated fallback title templates (used when Ollama fails)
# Based on real channel top performers — avoids the spammy default
SEO_FALLBACK_TEMPLATES = [
    "{idea} — You Won't Believe This #Shorts",
    "Stop doing this until you watch this #Shorts",
    "The hidden truth about {idea} #Shorts",
    "What's really hiding beneath {idea}? #Shorts",
    "99% of people don't know this about {idea} #Shorts",
    "They've been hiding {idea} from you #Shorts",
    "The shocking secret behind {idea} #Shorts",
    "Why {idea} changes everything you know #Shorts",
    "{idea}: The truth nobody talks about #Shorts",
    "What {idea} doesn't want you to know #Shorts",
]


def ask_ollama(prompt: str, max_retries: int = 3) -> str:
    """Send a prompt to Ollama and get response."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 1500,
                    },
                },
                timeout=180,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                log.warning(f"Ollama returned status {resp.status_code}")
        except requests.exceptions.ConnectionError:
            log.error("Cannot connect to Ollama. Make sure it's running: ollama serve")
            break
        except Exception as e:
            log.warning(f"Ollama attempt {attempt+1} failed: {e}")

    return ""


def generate_viral_idea(trending_topics: list, niche: dict, recent_titles: list = None) -> str:
    """Generate a viral YouTube Shorts idea from trending topics.
    
    Args:
        trending_topics: List of trending topic dicts from trend_scraper.
        niche: Content niche config dict.
        recent_titles: Last N uploaded video titles for novelty checking.
                       AI is told to avoid repeating the same patterns.
    """
    # --- Select a hook type by weight (prevents formula fatigue) ---
    hook_types = list(HOOK_TYPE_WEIGHTS.keys())
    hook_weights = list(HOOK_TYPE_WEIGHTS.values())
    chosen_hook = random.choices(hook_types, weights=hook_weights, k=1)[0]
    log.info(f"Selected hook type: {chosen_hook}")

    # --- Build hook-type-specific instructions ---
    hook_instructions = {
        "negative": (
            'Use a NEGATIVE hook: Start with "Stop...", "Don\'t...", or "Never..." followed by a specific action. '
            'Example: "Stop buying X until you see this hidden truth"'
        ),
        "statistical": (
            "Use a STATISTICAL hook: Lead with a surprising specific number or percentage. "
            'Example: "99% of people are missing this $500/month trick" or "Only 1 in 100 people know this"'
        ),
        "curiosity_gap": (
            "Use a CURIOSITY GAP hook: Tease hidden knowledge without revealing it. "
            'Example: "What\'s really hiding beneath your city?" or "The secret they\'ve kept from you for decades"'
        ),
        "real_news": (
            "Use a REAL NEWS hook: Reference a real company, person, or recent event with a shocking angle. "
            'Example: "The real reason [Company] just fired 10,000 people" or "What [CEO] does at 4AM every day"'
        ),
        "geographic": (
            "Use a GEOGRAPHIC MYSTERY hook: Name a specific real place with something hidden or shocking about it. "
            'Example: "Japan\'s secret underground city they don\'t want you to know" or "What\'s 2 miles beneath Tokyo"'
        ),
    }

    hook_instruction = hook_instructions.get(chosen_hook, hook_instructions["curiosity_gap"])

    # --- Niche-specific tone instructions (boosts specificity for top niches) ---
    niche_tone_map = {
        "Hidden Places & Mysteries": (
            "You are writing for a MYSTERY DISCOVERY channel. "
            "Focus on a SPECIFIC real location — name the country, city, depth, or distance. "
            "The more precise the detail, the more credible and viral it becomes. "
            "Use language that implies FORBIDDEN or HIDDEN knowledge. "
            "Examples of the exact style needed: "
            "'What\'s buried 18 meters beneath Istanbul\'s oldest district?', "
            "'The cave sealed for 5,000 years just opened in Peru', "
            "'Why China banned entry to this underground city in 2019'"
        ),
        "Billionaire Money Mindset": (
            "Name one specific real billionaire. Use one specific dollar amount or statistic. "
            "Reveal a single counterintuitive habit, decision, or secret — not generic advice. "
            "Example: 'The $47M mistake Warren Buffett admits he still regrets'"
        ),
        "AI Power Hacks": (
            "Name a specific AI tool (not just 'AI'). Give a specific use case with a measurable outcome. "
            "Example: 'ChatGPT prompt that writes 30 days of posts in 11 minutes'"
        ),
    }
    niche_tone = niche_tone_map.get(niche_name, "Be SPECIFIC: use real names, real numbers, real places.")

    # --- Build novelty constraint from recent titles ---
    novelty_block = ""
    if recent_titles:
        recent_sample = recent_titles[:10]
        titles_list = "\n".join([f"  - {t}" for t in recent_sample])
        novelty_block = f"""
AVOID THESE PATTERNS (already used recently):
{titles_list}
Do NOT repeat similar topics, phrasings, or the same leading word as any title above.
"""

    topics_text = "\n".join([f"- {t['title']}" for t in trending_topics[:10]])
    niche_name = niche.get("name", "Technology")
    keywords = ", ".join(niche.get("keywords", []))

    # --- Load real channel performance context (self-improving loop) ---
    perf_context = _get_performance_context()
    perf_block = f"\n{perf_context}\n" if perf_context else ""

    prompt = f"""You are a viral YouTube Shorts content strategist specializing in the '{niche_name}' niche.

NICHE TONE GUIDE:
{niche_tone}
{perf_block}
TRENDING TOPICS RIGHT NOW:
{topics_text}

YOUR NICHE: {niche_name}
KEYWORDS: {keywords}
{novelty_block}
YOUR ASSIGNED HOOK STRATEGY: {hook_instruction}

Generate ONE viral YouTube Shorts video idea in ENGLISH.

Rules:
- Under 12 words
- MUST follow the assigned hook strategy above
- MUST follow the Niche Tone Guide above — be extremely specific
- NO emojis in the idea itself
- Write in ENGLISH only

Return ONLY the video idea title (one line). Nothing else:"""

    idea = ask_ollama(prompt)
    idea = idea.strip().strip('"').strip("'").strip("*").strip("#")
    lines = idea.split("\n")
    idea = lines[0].strip() if lines else idea
    idea = re.sub(r'^\d+[\.\)]\s*', '', idea)

    log.info(f"Generated idea [{chosen_hook}]: {idea}")
    return idea


def generate_script(idea: str) -> str:
    """Generate a 45-55 second YouTube Shorts script in English."""

    prompt = f"""You are an expert YouTube Shorts scriptwriter. Write scripts that get MILLIONS of views by revealing SECRETS.

VIDEO IDEA: {idea}

Write a YouTube Shorts script. Target duration: 45-55 seconds when spoken.
That means exactly 120-150 words.

VIRAL SCRIPT STRUCTURE:

HOOK (0-3 sec): One shocking sentence that stops the scroll. UNDER 8 WORDS.
Strategy: Use a 'Pattern Interrupt' (e.g., "Stop doing this", "99% of people miss this", "This changes everything"). DO NOT just use "REVEALED".

CURIOSITY (4-10 sec): Create an intense open loop. Tease the "Hidden" aspect. Use words like "Nobody knows", "They hid this for years", "Governments erased this".

BODY (11-35 sec): Deliver the main content in SHORT punchy sentences.
- Each sentence 5-10 words MAX
- Use specific numbers, locations, real names, and dates
- Create mini-cliffhangers between sentences
- Build tension gradually toward the big reveal

THE REVEAL/TWIST (36-48 sec): Reveal the core secret. The "wait, WHAT?" moment. This is what they stayed for.

RETENTION LOOP (last sentence): CRITICAL — the final sentence MUST echo the exact words or theme of the HOOK (first sentence).
This creates a seamless replay loop, boosting your watch time score.
Example — Hook: "This underground city changes everything."
Example — Last line: "...and that is exactly why this underground city... changes everything."

CTA (final): Before the loop sentence, ask one POLARIZED engagement question.
Must force a binary choice: Yes or No, Agree or Disagree, Genius or Scam.
Example: "Would you dare to enter this city? Yes or No?"

STRICT RULES:
- Write ONLY the spoken words
- NO labels (no "HOOK:", "BODY:", etc.)
- NO stage directions, NO asterisks, NO formatting
- Short punchy sentences ONLY (5-10 words each)
- Use dramatic pauses (new sentence = pause)
- Total: 120-150 words exactly
- Language: ENGLISH only
- Sound like a confident, dramatic documentary narrator
- MANDATORY: End with the RETENTION LOOP sentence that echoes the hook

Write the script now:"""

    script = ask_ollama(prompt)

    # Clean script thoroughly
    lines = script.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove ALL labels and formatting
        skip_patterns = ["HOOK:", "CURIOSITY:", "BODY:", "TWIST:", "CTA:",
                         "Hook:", "Curiosity:", "Body:", "Twist:", "Cta:",
                         "EXPLANATION:", "LOOP:", "OPENING:", "CLOSING:",
                         "**", "##", "---", "```", "Scene", "SCENE",
                         "[", "(Note", "(note", "Word count"]
        should_skip = False
        for pattern in skip_patterns:
            if line.startswith(pattern):
                line = line.replace(pattern, "")
                if not line.strip():
                    should_skip = True
        if should_skip:
            continue

        line = line.strip().strip("*").strip("#").strip("-").strip('"').strip()
        # Remove numbering like "1.", "2)", etc
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        # Remove brackets content like [pause], (dramatic)
        line = re.sub(r'\[.*?\]', '', line)
        line = re.sub(r'\(.*?\)', '', line)
        line = line.strip()

        if line and len(line) > 3:
            clean_lines.append(line)

    script = " ".join(clean_lines)

    # Ensure minimum length
    word_count = len(script.split())
    log.info(f"Generated script ({word_count} words): {script[:120]}...")

    return script


def optimize_hook(script: str) -> str:
    """Rewrite the hook (first sentence) to maximize retention."""

    # Get first sentence
    sentences = re.split(r'[.!?]', script)
    first_sentence = sentences[0].strip() if sentences else script[:60]

    prompt = f"""You are the world's best YouTube Shorts hook writer.

CURRENT HOOK: "{first_sentence}"

Rewrite this hook to be IMPOSSIBLY viral. It must stop someone mid-scroll using "The Reveal" strategy.

Rules:
- Maximum 6-8 words
- Must stop the scroll with a "Pattern Interrupt".
- Strategies: 
  1. Negative ("Stop...", "Don't...", "You're failing...")
  2. Statistical ("90% missed...", "1 in 100 know...")
  3. Relatable Mystery ("Why your X does Y...")
- Avoid overusing "😱" or "Revealed".
- Language: ENGLISH only

Best performing hook patterns:
- "Stop buying coffee until you see this"
- "99% of people use this wrong"
- "Why your phone is actually listening"
- "The hidden reason you aren't successful"
- "This CEO's secret just leaked"
- "1 simple trick to save thousands"

Return ONLY the new hook. One sentence. Nothing else:"""

    new_hook = ask_ollama(prompt)
    new_hook = new_hook.strip().strip('"').strip("'").split("\n")[0]
    new_hook = re.sub(r'^\d+[\.\)]\s*', '', new_hook).strip()

    if new_hook and len(new_hook) > 5 and len(new_hook.split()) <= 15:
        # Replace first sentence with new hook
        rest_parts = re.split(r'[.!?]', script, 1)
        rest = rest_parts[1].strip() if len(rest_parts) > 1 else ""
        if rest:
            script = f"{new_hook}. {rest}"
        else:
            script = f"{new_hook}. {script}"

    log.info(f"Optimized hook: {new_hook}")
    return script


def generate_seo(idea: str, script: str) -> dict:
    """Generate SEO metadata. ALWAYS IN ENGLISH."""

    prompt = f"""You are a YouTube SEO expert who creates viral titles that stop the scroll.

VIDEO IDEA: {idea}
SCRIPT PREVIEW: {script[:250]}

Generate SEO metadata in ENGLISH for this YouTube Shorts video.

Title rules:
- Under 55 chars, max 1 emoji, must end with #Shorts
- Use ONE of these proven patterns:
  * Negative: "Stop [doing X] until you see this [result]"
  * Statistical: "[X%] of people are [doing Y wrong]"
  * Curiosity: "What's really hiding [specific place/thing]?"
  * Real news: "[Real entity] just [shocking action]"
  * Geographic: "[Real place]\'s secret [thing] revealed"
- NO generic title — be SPECIFIC with names/numbers/places

Return in this EXACT format:
TITLE: [clean English title, under 55 chars, max 1 emoji, end with #Shorts]
DESCRIPTION: [3 English sentences teasing the benefit/secret, end with hashtags]
TAGS: [20 comma-separated English tags]
HASHTAGS: #Shorts #SuccessTips #GrowthMindset #Efficiency #LifeHacks #Shorts

Return ONLY the metadata:"""

    response = ask_ollama(prompt)

    # --- Curated fallback: never use the spammy "😱 {idea} #Shorts" default ---
    fallback_template = random.choice(SEO_FALLBACK_TEMPLATES)
    fallback_title = fallback_template.format(idea=idea[:30])[:100]

    seo = {
        "title": fallback_title,
        "description": f"{idea}. Watch this to find out what they don't want you to know! #Shorts #Viral #Facts",
        "tags": ["shorts", "viral", "facts", "trending", "amazing", "mind blown",
                 "education", "science", "technology", "motivation"],
        "hashtags": ["#Shorts", "#Viral", "#Facts", "#Trending", "#Amazing"],
    }

    for line in response.split("\n"):
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            title = line.split(":", 1)[1].strip()[:90]  # 90 chars max to prevent truncated titles
            # Strip any Devanagari characters
            clean = "".join(c for c in title if not ('\u0900' <= c <= '\u097F'))
            if clean.strip() and len(clean.strip()) > 10:
                seo["title"] = clean.strip()
        elif line.upper().startswith("DESCRIPTION:"):
            desc = line.split(":", 1)[1].strip()
            clean = "".join(c for c in desc if not ('\u0900' <= c <= '\u097F'))
            if clean.strip():
                seo["description"] = clean.strip()
        elif line.upper().startswith("TAGS:"):
            tags_str = line.split(":", 1)[1].strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            if tags:
                seo["tags"] = tags
        elif line.upper().startswith("HASHTAG"):
            ht_str = line.split(":", 1)[1].strip()
            hts = [h.strip() for h in ht_str.split() if h.startswith("#")]
            if hts:
                seo["hashtags"] = hts

    # Ensure #Shorts is always present
    if "#Shorts" not in seo["hashtags"]:
        seo["hashtags"].insert(0, "#Shorts")
    if "#Shorts" not in seo["title"]:
        seo["title"] = seo["title"].rstrip() + " #Shorts"

    log.info(f"Generated SEO - Title: {seo['title']}")
    return seo


def generate_search_keywords(script: str) -> list:
    """Generate search keywords for finding stock footage."""

    prompt = f"""You need to find stock video clips for a YouTube Short.

SCRIPT: {script[:300]}

Return exactly 5 search keywords for Pexels stock video website.
Each keyword must be a VISUAL thing that can be filmed.

Rules:
- 2-4 words each
- Must be something you can SEE in a video
- MUST include aesthetic modifiers for each keyword (e.g., "cinematic", "dark", "atmospheric", "low light", "ominous", "handheld", "dramatic")
- Good: "dark cinematic cave", "empty atmospheric office", "abandoned city low light", "shady businessman silhouette", "mysterious vault door"
- Bad: "innovation", "concept", "idea", "future"
- Each keyword on its own line

Return ONLY 5 keywords:"""

    response = ask_ollama(prompt)
    keywords = []
    for line in response.split("\n"):
        kw = line.strip().strip("-").strip("*").strip("0123456789.").strip()
        kw = re.sub(r'^\d+[\.\)]\s*', '', kw).strip()
        # Remove quotes
        kw = kw.strip('"').strip("'")
        if kw and len(kw) > 1 and len(kw) < 30 and not kw.startswith("("):
            keywords.append(kw)

    if not keywords:
        keywords = ["technology", "future city", "robot", "digital screen", "person thinking"]

    log.info(f"Search keywords: {keywords[:5]}")
    return keywords[:5]


if __name__ == "__main__":
    print("Testing Ollama connection...")
    result = ask_ollama("Say 'AI Engine is working!' in one line.")
    print(f"Response: {result}")