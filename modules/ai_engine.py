"""
AI Engine - Local Ollama Integration
Handles all AI generation: ideas, scripts, SEO, hook optimization.
100% FREE - runs on your computer via Ollama.

STRATEGY: English scripts + Hindi voice = best quality + maximum reach
"""

import requests
import json
import re
from typing import Optional
from config.settings import OLLAMA_URL, OLLAMA_MODEL, CONTENT_LANGUAGE
from utils import get_logger

log = get_logger("ai_engine")


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


def generate_viral_idea(trending_topics: list, niche: dict) -> str:
    """Generate a viral YouTube Shorts idea from trending topics."""

    topics_text = "\n".join([f"- {t['title']}" for t in trending_topics[:10]])
    niche_name = niche.get("name", "Technology")
    keywords = ", ".join(niche.get("keywords", []))

    prompt = f"""You are a viral YouTube Shorts content strategist.

TRENDING TOPICS RIGHT NOW:
{topics_text}

YOUR NICHE: {niche_name}
KEYWORDS: {keywords}

Generate ONE viral YouTube Shorts video idea in ENGLISH.

Rules:
- Must be SHOCKING, curious, or reveal a HIDDEN SECRET
- Target "Relatable Everyday" mysteries (Consumer secrets, hidden tech features, grocery store tricks)
- Target the "curiosity gap" (make them wonder what's hidden)
- Must target young audience (18-35 age)
- Under 12 words
- Write in ENGLISH only

Good examples:
- "😱 The Hidden Grocery Store Secret They Don't Want You to Know"
- "🤯 Why Your Phone Is Quietly Listening To You Right Now"
- "😱 The Forbidden Truth About How Much CEOs Actually Make"
- "🤯 Secret IKEA Hack That Will Save You Thousands"
- "😱 Why You Should Never Trust A 'Free' Trial Again"

Return ONLY the video idea title (one line, English). Nothing else:"""

    idea = ask_ollama(prompt)
    idea = idea.strip().strip('"').strip("'").strip("*").strip("#")
    lines = idea.split("\n")
    idea = lines[0].strip() if lines else idea
    # Remove any numbering
    idea = re.sub(r'^\d+[\.\)]\s*', '', idea)

    log.info(f"Generated idea: {idea}")
    return idea


def generate_script(idea: str) -> str:
    """Generate a 45-55 second YouTube Shorts script in English."""

    prompt = f"""You are an expert YouTube Shorts scriptwriter. Write scripts that get MILLIONS of views by revealing SECRETS.

VIDEO IDEA: {idea}

Write a YouTube Shorts script. Target duration: 45-55 seconds when spoken.
That means exactly 120-150 words.

VIRAL SCRIPT STRUCTURE:

HOOK (0-3 sec): One shocking sentence that stops the scroll. UNDER 8 WORDS. Must scream "REVEALED" or "SECRET".

CURIOSITY (4-10 sec): Create an intense open loop. Tease the "Hidden" aspect. Use words like "Nobody knows", "They hid this for years".

BODY (11-35 sec): Deliver the main content in SHORT punchy sentences.
- Each sentence 5-10 words MAX
- Use specific numbers, locations, and names
- Create mini-cliffhangers between sentences
- Build tension gradually toward the big reveal

THE REVEAL/TWIST (36-48 sec): Reveal the core secret. The "wait, WHAT?" moment. This is what they stayed for.

RETAINER/CTA (49-55 sec): End with a high-intensity "Interaction Poll" question that forced people to comment. Must be polarized (Yes/No, Agree/Disagree).
Example: "Would you take this risk for a million dollars? Yes or No?" or "Is this a secret or a scam? Tell me in the comments!"

STRICT RULES:
- Write ONLY the spoken words
- NO labels (no "HOOK:", "BODY:", etc.)
- NO stage directions
- NO asterisks or formatting
- Short punchy sentences ONLY
- Use dramatic pauses (new sentence = pause)
- Total: 120-150 words exactly
- Language: ENGLISH only
- Sound like a confident, dramatic narrator
- Make the listener feel like they're being told something ILLEGAL or HIDDEN
- MANDATORY: End with a question that FORCES a comment.

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
- Must create INSTANT curiosity
- Must start with words like "Nobody", "Stop", "This", "Why"
- Must feel like a forbidden secret is being revealed
- Use power words: "shocking", "revealed", "forbidden", "hidden", "nobody knows", "illegal"
- Language: ENGLISH only

Best performing hook patterns:
- "😱 Japan's secret underground just revealed"
- "This CEO's secret paycheck just leaked"
- "Why nobody is allowed inside this location"
- "The forbidden reason this company is failing"
- "Stop believing this success lie right now"
- "They kept this hidden for 50 years"

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

    prompt = f"""You are a YouTube SEO expert who creates viral "Reveal" style titles.

VIDEO IDEA: {idea}
SCRIPT PREVIEW: {script[:250]}

Generate SEO metadata in ENGLISH for this YouTube Shorts video.

Return in this EXACT format:
TITLE: [shocking English title, under 55 chars, start with 😱 or 🤯, must use words like SECRET, REVEALED, or HIDDEN, end with #Shorts]
DESCRIPTION: [3 English sentences teasing the big secret, end with hashtags]
TAGS: [20 comma-separated English tags focusing on the mystery]
HASHTAGS: #Shorts #Secret #Revealed #Mystery #Hidden #SuccessShorts #Shocking

Examples of PERFECT titles:
TITLE: 😱 Japan's Secret Underground Revealed! #Shorts
TITLE: 🤯 The Forbidden Truth About CEO Paychecks #Shorts
TITLE: 😱 Why Nobody Is Allowed In This City #Shorts
TITLE: 🤯 Apple's Dark Secret Finally Exposed #Shorts

Return ONLY the metadata:"""

    response = ask_ollama(prompt)

    seo = {
        "title": f"😱 {idea} #Shorts",
        "description": f"{idea}. Watch this incredible short! #Shorts #Viral #Facts",
        "tags": ["shorts", "viral", "facts", "trending", "amazing", "mind blown",
                 "education", "science", "technology", "motivation"],
        "hashtags": ["#Shorts", "#Viral", "#Facts", "#Trending", "#Amazing"],
    }

    for line in response.split("\n"):
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            title = line.split(":", 1)[1].strip()[:100]
            # Strip any Devanagari characters
            clean = "".join(c for c in title if not ('\u0900' <= c <= '\u097F'))
            if clean.strip():
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