"""SNAZZY V9 Hello World Router - The Ultimate Greeting Experience."""

import random
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/hello", tags=["hello"])

# SNAZZY ASCII art collection
ASCII_ARTS = [
    """
    ╔═══════════════════════════════════════╗
    ║  🌟 HELLO WORLD V9 - ULTRA SNAZZY! 🌟  ║
    ╚═══════════════════════════════════════╝
    """,
    r"""
     _   _      _ _        __        __         _     _
    | | | | ___| | | ___   \ \      / /__  _ __| | __| |
    | |_| |/ _ \ | |/ _ \   \ \ /\ / / _ \| '__| |/ _` |
    |  _  |  __/ | | (_) |   \ V  V / (_) | |  | | (_| |
    |_| |_|\___|_|_|\___/     \_/\_/ \___/|_|  |_|\__,_|
                         V9 SNAZZY EDITION
    """,
    """
    ██╗  ██╗███████╗██╗     ██╗      ██████╗     ██╗    ██╗ ██████╗ ██████╗ ██╗     ██████╗
    ██║  ██║██╔════╝██║     ██║     ██╔═══██╗    ██║    ██║██╔═══██╗██╔══██╗██║     ██╔══██╗
    ███████║█████╗  ██║     ██║     ██║   ██║    ██║ █╗ ██║██║   ██║██████╔╝██║     ██║  ██║
    ██╔══██║██╔══╝  ██║     ██║     ██║   ██║    ██║███╗██║██║   ██║██╔══██╗██║     ██║  ██║
    ██║  ██║███████╗███████╗███████╗╚██████╔╝    ╚███╔███╔╝╚██████╔╝██║  ██║███████╗██████╔╝
    ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝      ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═════╝
    """,
]

# SNAZZY greetings in multiple languages
GREETINGS = {
    "en": "Hello World",
    "es": "Hola Mundo",
    "fr": "Bonjour le Monde",
    "de": "Hallo Welt",
    "it": "Ciao Mondo",
    "pt": "Olá Mundo",
    "ja": "こんにちは世界",
    "ko": "안녕하세요 세계",
    "zh": "你好世界",
    "ru": "Привет мир",
    "ar": "مرحبا بالعالم",
    "hi": "नमस्ते दुनिया",
    "sw": "Hujambo Dunia",
    "emoji": "👋🌍",
}

# SNAZZY emoji collections
EMOJI_THEMES = {
    "space": ["🚀", "🌟", "✨", "🌙", "☄️", "🪐", "🌌", "👽"],
    "party": ["🎉", "🎊", "🎈", "🎆", "🎇", "🥳", "🎪", "🎭"],
    "nature": ["🌸", "🌺", "🌻", "🌷", "🌹", "🌿", "🌳", "🦋"],
    "tech": ["💻", "🖥️", "⌨️", "🖱️", "💾", "💿", "📱", "🤖"],
    "food": ["🍕", "🍔", "🌮", "🍜", "🍣", "🍰", "🍩", "🍪"],
}

# SNAZZY colors for the web interface
COLORS = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#F8B500",
    "#00D9FF",
    "#FF006E",
    "#8338EC",
    "#3A86FF",
    "#06FFA5",
    "#FFB700",
]


@router.get("/", response_class=JSONResponse)
async def hello_world_json() -> Dict:
    """Get a SNAZZY JSON hello world response."""
    theme = random.choice(list(EMOJI_THEMES.keys()))
    emojis = random.sample(EMOJI_THEMES[theme], 3)
    greeting = random.choice(list(GREETINGS.values()))

    return {
        "message": f"{emojis[0]} {greeting} V9 - ULTRA SNAZZY EDITION! {emojis[1]}",
        "version": "9.0.0-SNAZZY",
        "timestamp": datetime.now().isoformat(),
        "theme": theme,
        "greeting_language": next(k for k, v in GREETINGS.items() if v == greeting),
        "ascii_art": random.choice(ASCII_ARTS),
        "fun_fact": get_random_fun_fact(),
        "snazziness_level": random.randint(9000, 10000),
        "emojis": emojis,
    }


@router.get("/web", response_class=HTMLResponse)
async def hello_world_web(request: Request) -> HTMLResponse:
    """Get an ULTRA SNAZZY animated HTML hello world page."""
    greeting = random.choice(list(GREETINGS.values()))
    theme = random.choice(list(EMOJI_THEMES.keys()))
    emojis = EMOJI_THEMES[theme]
    color_scheme = random.sample(COLORS, 5)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HELLO WORLD V9 - ULTRA SNAZZY!</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, {color_scheme[0]}, {color_scheme[1]}, {color_scheme[2]});
                background-size: 600% 600%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
                position: relative;
            }}

            @keyframes gradientShift {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}

            .container {{
                text-align: center;
                z-index: 10;
                position: relative;
            }}

            .main-title {{
                font-size: 5rem;
                font-weight: bold;
                color: white;
                text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
                animation: bounce 2s ease-in-out infinite;
                margin-bottom: 2rem;
            }}

            @keyframes bounce {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-20px); }}
            }}

            .greeting {{
                font-size: 3rem;
                color: white;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                animation: pulse 2s ease-in-out infinite;
                margin-bottom: 2rem;
            }}

            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
                100% {{ transform: scale(1); }}
            }}

            .ascii-art {{
                font-family: monospace;
                font-size: 0.8rem;
                color: rgba(255,255,255,0.9);
                white-space: pre;
                background: rgba(0,0,0,0.2);
                padding: 1rem;
                border-radius: 10px;
                margin: 2rem auto;
                display: inline-block;
                animation: glow 2s ease-in-out infinite;
            }}

            @keyframes glow {{
                0%, 100% {{ box-shadow: 0 0 20px rgba(255,255,255,0.5); }}
                50% {{ box-shadow: 0 0 40px rgba(255,255,255,0.8); }}
            }}

            .emoji-rain {{
                position: absolute;
                top: -50px;
                font-size: 2rem;
                animation: fall linear infinite;
            }}

            @keyframes fall {{
                to {{
                    transform: translateY(calc(100vh + 50px)) rotate(360deg);
                }}
            }}

            .features {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-top: 3rem;
                flex-wrap: wrap;
            }}

            .feature-card {{
                background: rgba(255,255,255,0.2);
                padding: 1.5rem;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                color: white;
                min-width: 200px;
                animation: float 3s ease-in-out infinite;
                animation-delay: var(--delay);
            }}

            @keyframes float {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-10px); }}
            }}

            .snazzy-meter {{
                margin-top: 2rem;
                background: rgba(255,255,255,0.2);
                padding: 1rem;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}

            .meter-bar {{
                height: 30px;
                background: linear-gradient(90deg, #00ff00, #ffff00, #ff0000);
                border-radius: 15px;
                overflow: hidden;
                position: relative;
            }}

            .meter-fill {{
                height: 100%;
                background: rgba(255,255,255,0.3);
                animation: fillMeter 2s ease-out forwards;
            }}

            @keyframes fillMeter {{
                from {{ width: 0; }}
                to {{ width: {random.randint(90, 100)}%; }}
            }}

            .fun-fact {{
                margin-top: 2rem;
                font-size: 1.2rem;
                color: white;
                font-style: italic;
                opacity: 0;
                animation: fadeIn 1s ease-out 2s forwards;
            }}

            @keyframes fadeIn {{
                to {{ opacity: 1; }}
            }}

            .version-badge {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: {color_scheme[3]};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                font-weight: bold;
                animation: spin 10s linear infinite;
            }}

            @keyframes spin {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="version-badge">V9 SNAZZY</div>

        <div class="container">
            <h1 class="main-title">{''.join(random.sample(emojis, 3))}</h1>
            <h2 class="greeting">{greeting}</h2>

            <pre class="ascii-art">{random.choice(ASCII_ARTS)}</pre>

            <div class="features">
                <div class="feature-card" style="--delay: 0s;">
                    <h3>🚀 Blazing Fast</h3>
                    <p>V9 delivers greetings at the speed of light!</p>
                </div>
                <div class="feature-card" style="--delay: 0.5s;">
                    <h3>🌈 Ultra Colorful</h3>
                    <p>Experience the rainbow of possibilities!</p>
                </div>
                <div class="feature-card" style="--delay: 1s;">
                    <h3>✨ Maximum Snazzy</h3>
                    <p>Snazziness level over 9000!</p>
                </div>
            </div>

            <div class="snazzy-meter">
                <h3 style="color: white; margin-bottom: 0.5rem;">Snazziness Meter</h3>
                <div class="meter-bar">
                    <div class="meter-fill"></div>
                </div>
            </div>

            <div class="fun-fact">
                💡 Fun Fact: {get_random_fun_fact()}
            </div>
        </div>

        <!-- Emoji rain effect -->
        {
            "".join(
                f'<div class="emoji-rain" style="left: {random.randint(0, 100)}%; '
                f'animation-duration: {random.randint(3, 8)}s; '
                f'animation-delay: {random.uniform(0, 3)}s;">'
                f'{random.choice(emojis)}</div>'
                for _ in range(20)
            )
        }

        <script>
            // Add some interactive snazziness
            document.addEventListener('click', function(e) {{
                const emoji = document.createElement('div');
                emoji.innerHTML = '{random.choice(emojis)}';
                emoji.style.position = 'absolute';
                emoji.style.left = e.clientX + 'px';
                emoji.style.top = e.clientY + 'px';
                emoji.style.fontSize = '2rem';
                emoji.style.animation = 'explode 1s ease-out forwards';
                emoji.style.pointerEvents = 'none';
                document.body.appendChild(emoji);

                setTimeout(() => emoji.remove(), 1000);
            }});

            // Add explode animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes explode {{
                    0% {{ transform: scale(0) rotate(0deg); opacity: 1; }}
                    100% {{ transform: scale(3) rotate(720deg); opacity: 0; }}
                }}
            `;
            document.head.appendChild(style);

            // Log snazziness to console
            console.log(
                '%c🌟 HELLO WORLD V9 - ULTRA SNAZZY! 🌟',
                'font-size: 24px; font-weight: bold; color: {color_scheme[0]}; '
                + 'text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'
            );
            console.log(
                '%cSnazziness Level: OVER 9000!',
                'font-size: 16px; color: {color_scheme[1]};'
            );
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/languages", response_class=JSONResponse)
async def get_all_languages() -> Dict:
    """Get hello world in all available languages."""
    return {
        "languages": GREETINGS,
        "total": len(GREETINGS),
        "snazzy_factor": "MAXIMUM",
    }


@router.get("/themes", response_class=JSONResponse)
async def get_emoji_themes() -> Dict:
    """Get all available emoji themes."""
    return {
        "themes": EMOJI_THEMES,
        "total": len(EMOJI_THEMES),
        "current_vibe": random.choice(["cosmic", "festive", "natural", "digital", "delicious"]),
    }


@router.get("/{language}", response_class=JSONResponse)
async def hello_world_language(language: str) -> Dict:
    """Get hello world in a specific language."""
    greeting = GREETINGS.get(language, GREETINGS["en"])
    theme = random.choice(list(EMOJI_THEMES.keys()))
    emojis = random.sample(EMOJI_THEMES[theme], 2)

    return {
        "message": f"{emojis[0]} {greeting} {emojis[1]}",
        "language": language,
        "version": "9.0.0-SNAZZY",
        "ascii_art": random.choice(ASCII_ARTS),
    }


def get_random_fun_fact() -> str:
    """Get a random fun fact about Hello World."""
    facts = [
        "The first 'Hello, World!' program was written in 1972 by Brian Kernighan!",
        "Hello World has been written in over 600 programming languages!",
        "V9 is 9x more snazzy than V8, scientifically proven!",
        "This endpoint generates over 1 million possible greeting combinations!",
        "The ASCII art took 0.001 seconds to render - that's FAST!",
        "Each request uses quantum-grade randomness for maximum snazziness!",
        "This hello world is carbon-neutral and saves digital trees!",
        "The emojis are hand-picked by our AI for optimal joy delivery!",
        "V9 features 200% more sparkles than industry standard!",
        "This greeting is visible from space (if you have really good eyes)!",
    ]
    return random.choice(facts)
