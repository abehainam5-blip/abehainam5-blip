"""
build.py
Assembles the final dark.svg / light.svg banner from timeline.json:
terminal-style frame, traffic-light dots, particle stage (clipped,
scaled into the frame), glow layer, and the right-hand info panel.
"""
import json
import os
import random
import sys
from xml.sax.saxutils import escape as xml_escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import premium as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(HERE, "_cache")

NAME = xml_escape("Abeha Inam")
TITLE = xml_escape("AI & Software Developer")
SKILL_LINE_1 = xml_escape("AI  •  React.js  •  Python")
SKILL_LINE_2 = xml_escape("Software Development  •  Databases")
ARIA_LABEL = xml_escape("Abeha Inam — AI & Software Developer")
TOPBAR_LABEL = xml_escape("abeha@github ~ profile.svg")
FOOTER_LABEL = xml_escape("github.com/abehainam5-blip")

# Scene color keyed by the exact keyTime it appears at in timeline.json
# (see anim.py SCENE_KEYFRAME_T). Colors cycle green/cyan across the tech
# logos, purple for the portrait, matching the requested palette.
SCENE_COLOR_BY_T = {
    0.0: "cyan",
    1.8: "cyan",
    3.6: "green",     # python
    4.4: "green",
    6.0: "cyan",      # react
    6.7: "cyan",
    8.3: "green",     # javascript
    9.0: "green",
    10.6: "cyan",     # github
    11.3: "cyan",
    15.3: "portrait",  # final portrait
    18.3: "portrait",
    19.5: "cyan",
}


def _fmt(n):
    if isinstance(n, int):
        return str(n)
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _nearest_scene_key(t, keys):
    # values inserted per-particle (t=0 exact, appear_t variable) need to
    # map to the closest defined scene time for color lookup.
    best = min(keys, key=lambda k: abs(k - t))
    return best


def build_particle_markup(timeline, theme):
    colors = P.THEMES[theme]
    color_map = {"cyan": colors["cyan"], "green": colors["green"], "portrait": colors["portrait"]}
    scene_ts = sorted(SCENE_COLOR_BY_T.keys())

    rnd = random.Random(55)
    out = []
    for particle in timeline["particles"]:
        pid = particle["id"]
        frames = particle["frames"]

        key_times = [f[0] for f in frames]
        total = timeline["total_dur"]
        key_times_norm = [round(t / total, 4) for t in key_times]
        # guard monotonic strictly increasing (SMIL requirement) & final==1
        for i in range(1, len(key_times_norm)):
            if key_times_norm[i] <= key_times_norm[i - 1]:
                key_times_norm[i] = round(key_times_norm[i - 1] + 0.0001, 4)
        key_times_norm[-1] = 1.0

        xs = ";".join(_fmt(f[1]) for f in frames)
        ys = ";".join(_fmt(f[2]) for f in frames)
        ops = ";".join(_fmt(f[4]) for f in frames)
        kt = ";".join(_fmt(t) for t in key_times_norm)

        fills = []
        for f in frames:
            skey = _nearest_scene_key(f[0], scene_ts)
            fills.append(color_map[SCENE_COLOR_BY_T[skey]])
        fill_vals = ";".join(fills)

        r = frames[3][3] if len(frames) > 3 else 1.2
        # radius stays constant (based on the portrait/logo-assigned size
        # at its most detailed usage) -- pick the max r seen for a touch
        # more presence, small jitter kept from generation.
        r = round(max(f[3] for f in frames), 2)

        # subtle organic idle drift + gentle scale pulse, independent
        # per-particle timing so particles don't move identically.
        wig_dur = round(rnd.uniform(3.2, 6.5), 2)
        wig_delay = round(rnd.uniform(0, wig_dur), 2)
        dx = round(rnd.uniform(1.2, 3.2) * rnd.choice([-1, 1]), 2)
        dy = round(rnd.uniform(1.2, 3.2) * rnd.choice([-1, 1]), 2)
        scale_dur = round(rnd.uniform(2.6, 5.0), 2)
        scale_delay = round(rnd.uniform(0, scale_dur), 2)
        scale_amt = round(rnd.uniform(1.12, 1.3), 2)

        glow_class = ' class="glowp"' if pid % 9 == 0 else ""

        g = (
            f'<g transform="translate(0,0)">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0;{dx},{dy};0,0" dur="{wig_dur}s" begin="-{wig_delay}s" '
            f'repeatCount="indefinite" additive="sum"/>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'values="1;{scale_amt};1" dur="{scale_dur}s" begin="-{scale_delay}s" '
            f'repeatCount="indefinite" additive="sum"/>'
            f'<circle{glow_class} cx="{_fmt(frames[0][1])}" cy="{_fmt(frames[0][2])}" '
            f'r="{_fmt(r)}" fill="{fills[0]}" opacity="{_fmt(frames[0][4])}">'
            f'<animate attributeName="cx" values="{xs}" keyTimes="{kt}" '
            f'dur="{total}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{ys}" keyTimes="{kt}" '
            f'dur="{total}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{ops}" keyTimes="{kt}" '
            f'dur="{total}s" repeatCount="indefinite"/>'
            f'<animate attributeName="fill" values="{fill_vals}" keyTimes="{kt}" '
            f'dur="{total}s" repeatCount="indefinite"/>'
            f'</circle></g>'
        )
        out.append(g)
    return "".join(out)


def build_svg(theme):
    with open(os.path.join(CACHE, "timeline.json")) as f:
        timeline = json.load(f)

    colors = P.THEMES[theme]
    particles_markup = build_particle_markup(timeline, theme)

    stage_tx = P.STAGE_X
    stage_ty = P.STAGE_Y
    scale = P.STAGE_SCALE

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {P.BANNER_W} {P.BANNER_H}" width="{P.BANNER_W}" height="{P.BANNER_H}" role="img" aria-label="{ARIA_LABEL}">
<defs>
  <clipPath id="frameClip-{theme}">
    <rect x="{P.FRAME_MARGIN}" y="{P.FRAME_MARGIN}" width="{P.BANNER_W - P.FRAME_MARGIN*2}" height="{P.BANNER_H - P.FRAME_MARGIN*2}" rx="{P.FRAME_RADIUS}"/>
  </clipPath>
  <clipPath id="stageClip-{theme}">
    <rect x="{stage_tx}" y="{stage_ty}" width="{P.STAGE_SIZE}" height="{P.STAGE_SIZE}" rx="16"/>
  </clipPath>
  <linearGradient id="bgGrad-{theme}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{colors['frame_bg']}"/>
    <stop offset="100%" stop-color="{colors['bg']}"/>
  </linearGradient>
  <linearGradient id="panelFade-{theme}" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{colors['frame_bg']}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{colors['frame_bg']}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glowBlur-{theme}" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="3.2"/>
  </filter>
  <filter id="softGlow-{theme}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.1"/>
  </filter>
</defs>

<rect x="0" y="0" width="{P.BANNER_W}" height="{P.BANNER_H}" fill="{colors['bg']}"/>

<g clip-path="url(#frameClip-{theme})">
  <rect x="{P.FRAME_MARGIN}" y="{P.FRAME_MARGIN}" width="{P.BANNER_W - P.FRAME_MARGIN*2}" height="{P.BANNER_H - P.FRAME_MARGIN*2}" fill="url(#bgGrad-{theme})"/>
  <rect x="{P.FRAME_MARGIN}" y="{P.FRAME_MARGIN}" width="{P.BANNER_W - P.FRAME_MARGIN*2}" height="{P.TOPBAR_H}" fill="{colors['topbar_bg']}"/>

  <circle cx="{P.FRAME_MARGIN + 22}" cy="{P.FRAME_MARGIN + P.TOPBAR_H/2}" r="6" fill="{colors['dot_red']}"/>
  <circle cx="{P.FRAME_MARGIN + 44}" cy="{P.FRAME_MARGIN + P.TOPBAR_H/2}" r="6" fill="{colors['dot_yellow']}"/>
  <circle cx="{P.FRAME_MARGIN + 66}" cy="{P.FRAME_MARGIN + P.TOPBAR_H/2}" r="6" fill="{colors['dot_green']}"/>
  <text x="{P.BANNER_W/2}" y="{P.FRAME_MARGIN + P.TOPBAR_H/2 + 4}" text-anchor="middle" font-family="{P.MONO_STACK}" font-size="12" fill="{colors['text_dim']}">{TOPBAR_LABEL}</text>

  <rect x="{P.FRAME_MARGIN + 0.5}" y="{P.FRAME_MARGIN + 0.5}" width="{P.BANNER_W - P.FRAME_MARGIN*2 - 1}" height="{P.BANNER_H - P.FRAME_MARGIN*2 - 1}" rx="{P.FRAME_RADIUS}" fill="none" stroke="{colors['frame_border']}" stroke-width="1.5"/>

  <rect x="{stage_tx - 6}" y="{stage_ty - 6}" width="{P.STAGE_SIZE + 12}" height="{P.STAGE_SIZE + 12}" rx="18" fill="none" stroke="{colors['frame_border']}" stroke-width="1"/>

  <g clip-path="url(#stageClip-{theme})">
    <rect x="{stage_tx}" y="{stage_ty}" width="{P.STAGE_SIZE}" height="{P.STAGE_SIZE}" fill="{colors['frame_bg']}"/>
    <g transform="translate({stage_tx},{stage_ty}) scale({scale})">
      <g filter="url(#glowBlur-{theme})" opacity="{colors['glow_opacity']}">
        <use href="#particlesCore-{theme}"/>
      </g>
      <g id="particlesCore-{theme}">
        {particles_markup}
      </g>
    </g>
  </g>

  <line x1="{P.PANEL_X - 32}" y1="{P.FRAME_MARGIN + P.TOPBAR_H + 18}" x2="{P.PANEL_X - 32}" y2="{P.BANNER_H - P.FRAME_MARGIN - 18}" stroke="{colors['frame_border']}" stroke-width="1"/>

  <text x="{P.PANEL_X}" y="128" font-family="{P.FONT_STACK}" font-size="40" font-weight="700" fill="{colors['name']}">{NAME}</text>
  <text x="{P.PANEL_X}" y="164" font-family="{P.FONT_STACK}" font-size="19" font-weight="500" fill="{colors['cyan']}">{TITLE}</text>

  <rect x="{P.PANEL_X}" y="184" width="46" height="3" rx="1.5" fill="{colors['green']}"/>

  <text x="{P.PANEL_X}" y="220" font-family="{P.FONT_STACK}" font-size="16" fill="{colors['text']}">{SKILL_LINE_1}</text>
  <text x="{P.PANEL_X}" y="246" font-family="{P.FONT_STACK}" font-size="16" fill="{colors['text']}">{SKILL_LINE_2}</text>

  <text x="{P.PANEL_X}" y="276" font-family="{P.MONO_STACK}" font-size="12.5" fill="{colors['text_dim']}">{FOOTER_LABEL}</text>
</g>
</svg>'''
    return svg


def main():
    out_dark = build_svg("dark")
    out_light = build_svg("light")

    dark_path = os.path.join(ROOT, "dark.svg")
    light_path = os.path.join(ROOT, "light.svg")
    with open(dark_path, "w") as f:
        f.write(out_dark)
    with open(light_path, "w") as f:
        f.write(out_light)

    print(f"Wrote {dark_path} ({os.path.getsize(dark_path)/1024:.1f} KB)")
    print(f"Wrote {light_path} ({os.path.getsize(light_path)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
