"""Frame-time reveal and pen placement for planned sweety assets.

Vendored from threerocks/sweety-handdraw-video @ 5206ec0d17f9b353e400b64b9c51ad69e721e02a
(MIT, Copyright (c) 2026 threerocks; see LICENSE):
  * ease, point_on_asset            <- scripts/video_renderer.py (verbatim apart from taking segments)
  * reveal_alpha                    <- scripts/video_renderer.py Renderer.layer (array form)
  * pen_position                    <- scripts/video_renderer.py Renderer.pen, CHANGED: between groups the
                                       pen glides on an arc to the next stroke instead of leaving the frame,
                                       it eases in before the first and out after the last group, and the
                                       nib is clamped to the canvas
  * validate_strokes                <- scripts/drawing_contract.py (verbatim)
  * match_reveal_to_tip             <- scripts/video_verifier.py (verbatim)
"""
import math

import numpy as np


def ease(fraction):
    fraction=float(np.clip(fraction,0,1))
    return fraction*fraction*(3-2*fraction)


def point_on_asset(segments,progress):
    previous = None
    for segment in segments:
        if progress < segment['start']:
            if previous:
                fraction = ease((progress-previous['end'])/max(1e-7,segment['start']-previous['end']))
                origin=np.array(previous['points'][-1]); destination=np.array(segment['points'][0])
                return origin+fraction*(destination-origin)+[0,-10*math.sin(math.pi*fraction)]
            return np.array(segment['points'][0])
        if segment['start']<=progress<=segment['end']:
            fraction=(progress-segment['start'])/max(1e-7,segment['end']-segment['start'])
            points=np.array(segment['points'])
            if segment['kind']=='travel':
                return points[0]+ease(fraction)*(points[-1]-points[0])+[0,-10*math.sin(math.pi*fraction)]
            distances=np.array(segment['lengths'])
            target=fraction*distances[-1]
            return np.array([np.interp(target,distances,points[:,0]),np.interp(target,distances,points[:,1])])
        previous=segment
    if progress<segments[0]['start']:
        return np.array(segments[0]['points'][0])
    return np.array(segments[-1]['points'][-1])


def reveal_alpha(alpha, maps, progress):
    """Alpha channel of an asset revealed to `progress` in [0, 1] (two-channel ink/colour for art)."""
    if progress >= 1:
        return alpha
    if 'ink' in maps:
        ink_fraction=np.clip((progress-maps['ink'])*250,0,1)
        color_fraction=np.clip((progress-maps['color'])*250,0,1)
        fraction=maps['ink_weight']*ink_fraction+(1-maps['ink_weight'])*color_fraction
    else:
        fraction=np.clip((progress-maps['reveal'])*250,0,1)
    return np.rint(alpha*fraction).astype(np.uint8)


def pen_position(events, tip, time, canvas, lead=.35, tail=.45, away=(.10, .13)):
    """events: [{'start','end',...}] sorted; tip(event, progress) -> canvas xy. Returns xy or None."""
    if not events:
        return None
    width, height = canvas
    offset = np.array([away[0] * width, away[1] * height])
    point = None
    for index, event in enumerate(events):
        if event['start'] <= time <= event['end']:
            point = tip(event, (time - event['start']) / max(1e-7, event['end'] - event['start']))
            break
        if time < event['start']:
            following = tip(event, 0.)
            if index:
                previous = events[index - 1]
                origin = tip(previous, 1.)
                progress = ease((time - previous['end']) / max(1e-7, event['start'] - previous['end']))
                lift = min(60., .25 * float(np.linalg.norm(following - origin)) + 12)
                point = origin + progress * (following - origin) + [0, -lift * math.sin(math.pi * progress)]
            elif event['start'] - time < lead:
                point = following + (1 - ease(1 - (event['start'] - time) / lead)) * offset
            break
    else:
        last = events[-1]
        if time < last['end'] + tail:
            point = tip(last, 1.) + ease((time - last['end']) / tail) * offset
    if point is None:
        return None
    return np.array([np.clip(point[0], 0, width - 1), np.clip(point[1], 0, height - 1)])


def validate_strokes(metadata):
    segments = metadata['segments']
    previous_ink = None
    for segment in segments:
        if segment['end'] <= segment['start']:
            raise ValueError('Every stroke and pen lift needs a positive duration')
        if segment['kind'] != 'ink':
            continue
        points = np.asarray(segment['points'], dtype=float)
        if len(points) < 2 or not np.isfinite(points).all() or (np.linalg.norm(np.diff(points, axis=0), axis=1) > 1.5).any():
            raise ValueError('A pen stroke bridges disconnected outline points; split and lift the pen')
        if previous_ink is not None and segment['start'] <= previous_ink['end'] + 1e-10:
            raise ValueError('Separate strokes require a pen-up interval, even at a shared endpoint')
        previous_ink = segment
    return True


def match_reveal_to_tip(metadata, reveal, mask, kinds):
    ys, xs = np.where(mask)
    timestamps = reveal[ys, xs].astype(float)
    distances = np.full(len(timestamps), np.inf)
    radii = np.zeros(len(timestamps))
    for segment in metadata['segments']:
        if segment['kind'] not in kinds:
            continue
        selected = (timestamps >= segment['start'] - 2e-7) & (timestamps <= segment['end'] + 2e-7)
        if not selected.any():
            continue
        points = np.array(segment['points'])
        lengths = np.array(segment['lengths'])
        along = np.clip((timestamps[selected] - segment['start']) / max(1e-8, segment['end'] - segment['start']), 0, 1) * lengths[-1]
        separation = np.hypot(xs[selected] - np.interp(along, lengths, points[:, 0]), ys[selected] - np.interp(along, lengths, points[:, 1]))
        distances[selected] = np.minimum(distances[selected], separation)
        radii[selected] = np.maximum(radii[selected], segment.get('radius', 0))
    return distances, radii
