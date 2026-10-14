"""Stroke planning for handwritten text and semantic-part illustrations.

Vendored from threerocks/sweety-handdraw-video @ 5206ec0d17f9b353e400b64b9c51ad69e721e02a
skills/sweety-handdraw-video/scripts/stroke_assets.py (MIT, Copyright (c) 2026 threerocks; see LICENSE).

Kept verbatim: lengths, ordered_paths, time_paths, measure_text, and the planning core of
build_text / build_illustration (outline strokes in part order, then paint passes in part order).
Changed (see SOURCE.md):
  * no global asset directory and no file writes: builders take a PIL image / font path and
    return arrays + metadata (the caller caches them);
  * build_brush (marker highlights) dropped;
  * build_illustration: empty parts are skipped and parts without outline pixels are painted only
    (upstream raised); visible pixels outside every polygon go to an implicit trailing "rest" part
    (upstream raised); fill pixels are re-owned per colour component by majority part, so a large
    fill region crossing a part boundary is painted in one piece instead of showing straight seams.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from . import stroke_paths as stroke_utils
from .paint_motion import build_painting


def lengths(points):
    return stroke_utils.calculate_lengths(points)


def ordered_paths(mask):
    skeleton = stroke_utils.thin_ink(mask)
    paths = [np.array(path) for path in stroke_utils.trace_strokes(skeleton)]
    covered = np.zeros(skeleton.shape, dtype=bool)
    for path in paths:
        coordinates = np.rint(path).astype(int)
        covered[coordinates[:, 1], coordinates[:, 0]] = True
    # Follow only adjacent leftover pixels. A branch starts a new physical stroke.
    pending = set(zip(*np.where(skeleton & ~covered)))
    while pending:
        point = min(pending)
        chain = []
        while point in pending:
            pending.remove(point)
            y, x = point
            chain.append([x, y])
            neighbors = sorted((y+dy, x+dx) for dy in (-1,0,1) for dx in (-1,0,1)
                               if (dy or dx) and (y+dy, x+dx) in pending)
            if not neighbors:
                break
            point = neighbors[0]
        if len(chain) == 1:
            chain.append([chain[0][0]+.01, chain[0][1]])
        paths.append(np.array(chain, dtype=float))
    if not paths:
        ys, xs = np.where(mask)
        if not len(xs):
            return []
        paths = [np.array([[xs[0],ys[0]],[xs[0]+.01,ys[0]]],dtype=float)]
    covered[:] = False
    for path in paths:
        coordinates = np.rint(path).astype(int)
        covered[coordinates[:,1],coordinates[:,0]] = True
    # Keep broad stroke tips within nib distance without connecting across blank paper.
    while True:
        distance, nearest = ndimage.distance_transform_edt(~covered, return_indices=True)
        distance[~mask] = 0
        y, x = np.unravel_index(np.argmax(distance), mask.shape)
        if distance[y,x] <= 7:
            break
        anchor = np.array([nearest[1,y,x],nearest[0,y,x]],dtype=float)
        extension = np.linspace(anchor,[x,y],max(2,math.ceil(distance[y,x])+1))
        coordinates = np.rint(extension).astype(int)
        if not mask[coordinates[:,1],coordinates[:,0]].all():
            extension = np.array([[x,y],[x+.01,y]],dtype=float)
            coordinates = np.rint(extension).astype(int)
        paths.append(extension)
        covered[coordinates[:,1],coordinates[:,0]] = True
    oriented = [path if tuple(path[0][::-1]) <= tuple(path[-1][::-1]) else path[::-1] for path in paths]
    return sorted(oriented,key=lambda path:(round(path[:,1].min()/16),path[:,0].min()))


def time_paths(paths, shape, start=0., duration=1.):
    reveal = np.full(shape, np.inf, dtype=np.float32)
    segments = []
    weights = [max(1., lengths(path)[-1]) for path in paths]
    travel_weights = [max(3., np.linalg.norm(paths[i + 1][0] - paths[i][-1]) * .22) for i in range(len(paths) - 1)]
    total = sum(weights) + sum(travel_weights)
    cursor = start
    for index, (path, weight) in enumerate(zip(paths, weights)):
        path_length = lengths(path)
        interval = duration * weight / max(1, total)
        for point, distance in zip(path, path_length):
            x, y = np.rint(point).astype(int)
            if 0 <= y < shape[0] and 0 <= x < shape[1]:
                reveal[y, x] = min(reveal[y, x], cursor + interval * distance / max(.001, path_length[-1]))
        segments.append({'kind':'ink','start':cursor,'end':cursor + interval,'points':path.tolist(),'lengths':path_length.tolist()})
        cursor += interval
        if index + 1 < len(paths):
            transit = duration * travel_weights[index] / max(1, total)
            segments.append({'kind':'travel','start':cursor,'end':cursor + transit,'points':[path[-1].tolist(),paths[index + 1][0].tolist()]})
            cursor += transit
    if np.isfinite(reveal).any():
        _, nearest = ndimage.distance_transform_edt(~np.isfinite(reveal), return_indices=True)
        reveal = reveal[nearest[0], nearest[1]]
    return reveal, segments


def measure_text(text, font, margin=5):
    """Reserve actual glyph bearings and descenders, not the nominal font size."""
    placements, cursor = [], 0.
    for character in text:
        placements.append((character, round(cursor), font.getbbox(character)))
        cursor += font.getlength(character)
    left = min([0] + [x + bounds[0] for _, x, bounds in placements])
    top = min([0] + [bounds[1] for _, _, bounds in placements])
    right = max([math.ceil(cursor)] + [x + bounds[2] for _, x, bounds in placements])
    bottom = max([0] + [bounds[3] for _, _, bounds in placements])
    return {'width': right-left+2*margin, 'height': bottom-top+2*margin,
            'origin': [margin-left, margin-top], 'placements': placements}


def build_text(text, size, color, font_path, font_index=0):
    """Returns (rgba uint8 array, {'reveal','owners'} maps, metadata)."""
    font = ImageFont.truetype(str(font_path), size, index=font_index)
    layout = measure_text(text, font)
    width, height = layout['width'], layout['height']
    layer = Image.new('RGBA',(width,height))
    glyphs = []
    for character, offset, bounds in layout['placements']:
        glyph = Image.new('L',(max(1,bounds[2]-bounds[0]),max(1,bounds[3]-bounds[1])))
        glyph_draw = ImageDraw.Draw(glyph)
        glyph_draw.text((-bounds[0],-bounds[1]),character,font=font,fill=255)
        mask = np.array(glyph) > 30
        paths = ordered_paths(mask)
        left = layout['origin'][0]+offset+bounds[0]
        top = layout['origin'][1]+bounds[1]
        glyphs.append((character, left, top, np.array(glyph), paths))
        ink = Image.new('RGBA',glyph.size,color)
        ink.putalpha(glyph)
        layer.alpha_composite(ink,(left,top))
    pixels = np.array(layer)
    reveal = np.full((height, width), np.inf, dtype=np.float32)
    owners = np.full((height, width), -1, dtype=np.int16)
    segments, character_intervals = [], []
    weights = [max(4., sum(lengths(path)[-1] for path in paths)) for _, _, _, _, paths in glyphs]
    cursor = 0.
    for index, ((character, left, top, glyph, paths), weight) in enumerate(zip(glyphs, weights)):
        interval = weight / sum(weights)
        if paths:
            local, strokes = time_paths(paths, glyph.shape, cursor, interval * .94)
            glyph_height, glyph_width = glyph.shape
            mask = glyph > 0
            patch = reveal[top:top+glyph_height, left:left+glyph_width]
            patch[mask] = local[mask]
            owners[top:top+glyph_height, left:left+glyph_width][mask] = index
            for stroke in strokes:
                stroke['points'] = (np.array(stroke['points']) + [left, top]).tolist()
                stroke['character_index'] = index
            segments.extend(strokes)
        character_intervals.append({'index':index,'character':character,'start':cursor,'end':cursor+interval})
        cursor += interval
    metadata = {'type':'handwritten_text','text':text,'font_size':size,'width':width,'height':height,
                'segments':segments,'text_origin':layout['origin'],'safe_margin':5,'characters':character_intervals}
    return pixels, {'reveal': reveal, 'owners': owners}, metadata


def _polygon_mask(size, polygon):
    region = Image.new('L', size)
    ImageDraw.Draw(region).polygon([tuple(point) for point in polygon * [size[0]-1, size[1]-1]], fill=255)
    return np.array(region) > 0


def build_illustration(artwork, max_width, max_height, parts=None, outline_mask=None):
    """artwork: PIL image (RGB/RGBA). parts: ordered [{'id', 'polygon' (normalized), 'exclude_polygons'?}].
    Returns (rgba uint8 array, {'ink','color','ink_weight','owners'} maps, metadata)."""
    artwork = artwork.convert('RGBA')
    source_size = artwork.size
    if artwork.getextrema()[3] == (255, 255):
        rgb = np.array(artwork)[:, :, :3]
        alpha = np.rint(np.clip((253-rgb.min(axis=2).astype(float))/18, 0, 1)*255).astype(np.uint8)
        artwork = Image.fromarray(np.dstack([rgb, alpha]))
    scale = min(max_width/artwork.width, max_height/artwork.height)
    artwork = artwork.resize((max(1,round(artwork.width*scale)),max(1,round(artwork.height*scale))),Image.Resampling.LANCZOS)
    pixels=np.array(artwork)
    maximum=pixels[:,:,:3].max(axis=2)
    alpha=pixels[:,:,3]
    red,green,blue=[pixels[:,:,channel].astype(float) for channel in range(3)]
    cool_ink=(blue>=red+4)&(blue>=green-4)&(red<218)
    dark=((maximum<125)|cool_ink)&(alpha>30)
    depth=ndimage.distance_transform_edt(dark)
    outline=dark&(depth<5.2)
    ink_weight=dark.astype(float)*np.clip((6.-depth)/1.,0,1)
    if outline_mask is not None:
        explicit = outline_mask.convert('L')
        if explicit.size != source_size:
            raise ValueError('Outline mask must match source image dimensions')
        explicit = explicit.resize(artwork.size,Image.Resampling.NEAREST)
        outline = (np.array(explicit)>127)&(alpha>0)
        ink_weight = outline.astype(float)
    fill_mask=(alpha>0)&(ink_weight<.99)
    ys, xs = np.where(alpha > 0)
    if not len(xs):
        raise ValueError('Illustration is empty after background removal')
    parts = list(parts or [])
    if not parts:
        parts = [{'id': 'object', 'polygon': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
    owners = np.full(alpha.shape, -1, dtype=np.int16)
    names = []
    for part in parts:
        if not part.get('id') or part['id'] in names:
            raise ValueError('Every semantic part needs a unique id')
        polygon = np.asarray(part['polygon'], dtype=float)
        if len(polygon)<3 or not ((polygon>=0)&(polygon<=1)).all():
            raise ValueError('Part polygons must have >=3 normalized vertices')
        mask = _polygon_mask(artwork.size, polygon) & (alpha>0) & (owners<0)
        for excluded_polygon in part.get('exclude_polygons', []):
            excluded_polygon = np.asarray(excluded_polygon, dtype=float)
            mask &= ~_polygon_mask(artwork.size, excluded_polygon)
        names.append(part['id'])
        owners[mask] = len(names) - 1
    if ((alpha>0)&(owners<0)).any():
        names.append('rest')
        owners[(alpha>0)&(owners<0)] = len(names) - 1
    # Re-own fill pixels per colour component (majority part) so paint never stops at a polygon edge.
    if fill_mask.any():
        palette = np.array(Image.fromarray(pixels[:, :, :3]).quantize(colors=8, method=Image.Quantize.FASTOCTREE))
        components = np.zeros(alpha.shape, dtype=np.int64)
        offset = 0
        for color_id in np.unique(palette[fill_mask]):
            labels, count = ndimage.label((palette == color_id) & fill_mask)
            components[labels > 0] = labels[labels > 0] + offset
            offset += count
        sel = components > 0
        comp, own = components[sel], owners[sel].astype(np.int64)
        votes = np.zeros((offset + 1, len(names)), dtype=np.int64)
        np.add.at(votes, (comp, own), 1)
        majority = votes.argmax(axis=1).astype(np.int16)
        owners[sel] = majority[comp]
    part_masks = [(owners == index) for index in range(len(names))]
    keep = [index for index, mask in enumerate(part_masks) if mask.any()]
    skipped = [names[index] for index in range(len(names)) if index not in keep]
    remap = np.full(len(names) + 1, -1, dtype=np.int16)
    for new, old in enumerate(keep):
        remap[old] = new
    owners = np.where(owners >= 0, remap[owners], -1).astype(np.int16)
    names = [names[index] for index in keep]
    part_masks = [part_masks[index] for index in keep]
    ink_reveal = np.full(alpha.shape,np.inf,dtype=np.float32)
    color_reveal = np.full(alpha.shape,np.inf,dtype=np.float32)
    segments, part_reports = [], []
    part_paths = [ordered_paths(outline&mask) if (outline&mask).any() else [] for mask in part_masks]
    ink_weights = [sum(max(1.,lengths(path)[-1]) for path in paths) for paths in part_paths]
    ink_duration = (.59 if fill_mask.any() else 1.) if sum(ink_weights) else 0.
    cursor = 0.
    previous_tip = np.array([xs.mean(),ys.mean()])
    for index,(mask,paths,weight) in enumerate(zip(part_masks,part_paths,ink_weights)):
        interval = ink_duration*weight/max(1.,sum(ink_weights))
        if paths:
            local,strokes = time_paths(paths,alpha.shape,cursor,interval*.96)
            ink_reveal[mask] = local[mask]
            for stroke in strokes:
                stroke.update(part_id=names[index],part_index=index,phase='outline')
            segments.extend(strokes)
            previous_tip=paths[-1][-1]
        part_reports.append({'id':names[index],'index':index,'outline_start':cursor,'outline_end':cursor+interval})
        cursor+=interval
    fill_weights = [math.sqrt(int((mask&fill_mask).sum())) for mask in part_masks]
    fill_start = ( .61 if sum(ink_weights) else 0. ) if fill_mask.any() else 1.
    cursor=fill_start
    painting={'region_count':0,'brush_pass_count':0,'maximum_brush_radius':0}
    for index,(mask,weight) in enumerate(zip(part_masks,fill_weights)):
        interval=(1.-fill_start)*weight/max(1.,sum(fill_weights))
        local,strokes,statistics=build_painting(mask&fill_mask,previous_tip,cursor,interval*.96,pixels)
        color_reveal[mask]=local[mask]
        for stroke in strokes:
            stroke.update(part_id=names[index],part_index=index,phase='fill')
        segments.extend(strokes)
        part_reports[index].update(fill_start=cursor,fill_end=cursor+interval)
        if strokes:
            previous_tip=np.array(strokes[-1]['points'][-1])
        for field in ('region_count','brush_pass_count'):
            painting[field]+=statistics[field]
        painting['maximum_brush_radius']=max(painting['maximum_brush_radius'],statistics['maximum_brush_radius'])
        cursor+=interval
    # Pixels never reached by a pass (e.g. ink-only art with no outline in a part) appear at the end.
    ink_reveal[~np.isfinite(ink_reveal) & (ink_weight > .01) & (alpha > 0)] = 1.
    color_reveal[~np.isfinite(color_reveal) & (ink_weight < .99) & (alpha > 0)] = 1.
    maps = {'ink': ink_reveal, 'color': color_reveal, 'ink_weight': ink_weight.astype(np.float32), 'owners': owners}
    metadata = {'type':'illustration','width':artwork.width,'height':artwork.height,'segments':segments,
                'painting':painting,'parts':part_reports,'skipped_parts':skipped}
    return pixels, maps, metadata
