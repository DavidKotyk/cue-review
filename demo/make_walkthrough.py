"""Optional media assembly; needs Pillow, numpy, imageio-ffmpeg. No app dependency."""
from pathlib import Path
import textwrap
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 960, 6
def font(size, mono=False):
    candidates = (["/System/Library/Fonts/Menlo.ttc"] if mono else
                  ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"])
    for name in candidates:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)

def frame(title, subtitle, image=None, lines=None, crop=None):
    canvas = Image.new('RGB', (W,H), '#f3f1e9')
    draw = ImageDraw.Draw(canvas)
    draw.text((38,24), title, font=font(30), fill='#172e2a')
    draw.text((38,70), subtitle, font=font(19), fill='#435e50')
    if image:
        im = Image.open(ROOT / image).convert('RGB')
        if crop:
            im = im.crop(crop)
        im.thumbnail((W-60,H-185))
        canvas.paste(im,((W-im.width)//2,124))
    if lines:
        y = 150
        for line in lines:
            for piece in textwrap.wrap(line, width=87, replace_whitespace=False) or ['']:
                draw.text((50,y),piece,font=font(22,True),fill='#172e2a')
                y += 36
    draw.rectangle((0,H-44,W,H),fill='#172e2a')
    draw.text((30,H-32),'CUE REVIEW | Real browser screenshots, assembled walkthrough | Fictional captions | No narration',font=font(16),fill='#f3f1e9')
    return np.asarray(canvas)

scenes = [
    (frame('Cue Review — the last pass before delivery', 'A local SRT studio for freelance editors; no client or sales claims.', '03-approved.jpg',crop=(0,0,1280,1000)),8),
    (frame('01 / Ask for a tighter cut', 'Actual local phi3 inference. This is a pending draft; the original stays unchanged.', '09-final-draft.jpg'),10),
    (frame('02 / Make the call', 'Approved synthetic edit: 24.29 → 10.57 chars/s. Timestamps are unchanged.', '10-final-approved.jpg'),10),
    (frame('03 / A useful failure', '“Wait 10s” loses the opening instruction. The test operator rejected this draft.', '11-final-risk.jpg'),12),
    (frame('04 / A handoff you can inspect', 'Actual exported SRT: only cue 2 was replaced. Rejected cue 4 keeps its original.', lines=(ROOT/'reviewed.srt').read_text().splitlines()),12),
    (frame('05 / What was tested, and what remains', 'A narrow prototype with documented limitations.', lines=[
        '11 domain / real HTTP tests passed.',
        '4 actual local-model cases; 2 semantic concerns documented.',
        'Browser approval, rejection, persistence, import and export checked.',
        'Mobile checked at 390px; no horizontal overflow observed.',
        '',
        'No transcription or timing repair. English plain-text SRT only.',
        'No independent professional validation or paid users.',
        'Model drafts require comparison with the audio.',
        'Code and prompts are inspectable. No cloud inference calls.'
    ]),10),
]
writer = imageio_ffmpeg.write_frames(str(ROOT/'walkthrough.mp4'),(W,H),fps=FPS,codec='libx264',pix_fmt_out='yuv420p',output_params=['-movflags','+faststart','-crf','22'])
writer.send(None)
for pixels,duration in scenes:
    for _ in range(duration*FPS):
        writer.send(pixels.tobytes())
writer.close()
(ROOT/'video-metadata.json').write_text(json.dumps({'width':W,'height':H,'fps':FPS,'duration_seconds':sum(s[1] for s in scenes),'audio':False,'type':'Annotated real screenshots; not continuous screen recording','source_screenshots':['03-approved.jpg','09-final-draft.jpg','10-final-approved.jpg','11-final-risk.jpg']},indent=2)+'\n')
print('Created walkthrough.mp4')
