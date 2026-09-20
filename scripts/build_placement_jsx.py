#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    if job.get("status") != "approved":
        raise SystemExit("job_status_must_be_approved")
    candidates = [item for item in job.get("candidates", []) if item.get("status") == "approved"]
    selected = job.get("approved_candidate_id")
    if len(candidates) != 1 or str(candidates[0].get("id")) != str(selected):
        raise SystemExit("exactly_one_matching_approved_candidate_required")
    source = Path(job["source_ai"]).resolve()
    output_ai = Path(job["output_ai"]).resolve()
    asset = Path(candidates[0]["path"]).resolve()
    if source == output_ai:
        raise SystemExit("refusing_to_overwrite_source_ai")
    if not asset.is_file():
        raise SystemExit("approved_candidate_missing")
    target = job["target"]
    payload = {
        "output_ai": str(output_ai),
        "output_name": output_ai.name,
        "asset_path": str(asset),
        "layer": target.get("layer", "印刷"),
        "group_index": int(target["group_index"]),
        "bounds": target["target_bounds"],
        "raster_indices": sorted(set(int(value) for value in target["raster_indices"]), reverse=True),
        "primary_raster_index": int(target.get("primary_raster_index", target["raster_indices"][0])),
        "fit": target.get("fit", "contain"),
        "allow_crop": bool(target.get("allow_crop", False)),
        "embed": bool(target.get("embed", True)),
        "protected_layers": job.get("protected_layers", []),
        "candidate_id": selected,
    }
    code = f'''(function(){{
try{{
var job={json.dumps(payload, ensure_ascii=False)},doc=app.activeDocument;
if(String(doc.name).toLowerCase()!==String(job.output_name).toLowerCase())throw new Error('target_document_mismatch');
function findLayer(name){{for(var i=0;i<doc.layers.length;i++)if(doc.layers[i].name===name)return doc.layers[i];throw new Error('layer_not_found:'+name);}}
function topGroups(layer){{var out=[];for(var i=0;i<layer.groupItems.length;i++)if(layer.groupItems[i].parent===layer)out.push(layer.groupItems[i]);return out;}}
function collectRasters(container,out){{for(var i=0;i<container.pageItems.length;i++){{var item=container.pageItems[i];if(item.typename==='RasterItem'||item.typename==='PlacedItem')out.push(item);if(item.typename==='GroupItem')collectRasters(item,out);}}}}
function itemSig(item){{var b='';try{{b=item.geometricBounds.join(',');}}catch(e){{}}var t='';try{{if(item.typename==='TextFrame')t=item.contents;}}catch(e2){{}}return [item.typename,item.name,item.visible,item.locked,b,t].join('|');}}
function layerSig(layer){{var parts=[layer.name,layer.visible,layer.locked,layer.pageItems.length];for(var i=0;i<layer.pageItems.length;i++)parts.push(itemSig(layer.pageItems[i]));return parts.join('~');}}
var protectedBefore={{}};for(var p=0;p<job.protected_layers.length;p++){{var pn=job.protected_layers[p];protectedBefore[pn]=layerSig(findLayer(pn));}}
var layer=findLayer(job.layer),groups=topGroups(layer),group=groups[job.group_index];if(!group)throw new Error('group_not_found:'+job.group_index);
var rasters=[];collectRasters(group,rasters),anchor=rasters[job.primary_raster_index];if(!anchor)throw new Error('primary_raster_not_found');
if(job.fit==='cover'&&(!job.allow_crop||anchor.parent.typename!=='GroupItem'||!anchor.parent.clipped))throw new Error('cover_requires_existing_clipping_group');
var f=new File(job.asset_path);if(!f.exists)throw new Error('approved_asset_missing');
var placed=doc.placedItems.add();placed.file=f;
var b=job.bounds,w=b[2]-b[0],h=b[1]-b[3],sx=w/placed.width,sy=h/placed.height,scale=job.fit==='cover'?Math.max(sx,sy):Math.min(sx,sy);
placed.width=placed.width*scale;placed.height=placed.height*scale;placed.left=b[0]+(w-placed.width)/2;placed.top=b[1]-(h-placed.height)/2;
placed.move(anchor,ElementPlacement.PLACEBEFORE);
for(var r=0;r<job.raster_indices.length;r++){{var idx=job.raster_indices[r];if(idx<0||idx>=rasters.length)throw new Error('raster_index_invalid:'+idx);rasters[idx].remove();}}
if(job.embed)placed.embed();
for(var q=0;q<job.protected_layers.length;q++){{var qn=job.protected_layers[q];if(protectedBefore[qn]!==layerSig(findLayer(qn)))throw new Error('protected_layer_changed:'+qn);}}
doc.save();return 'ARTWORK_PLACED candidate_id='+job.candidate_id+' group_index='+job.group_index+' fit='+job.fit+' embedded='+job.embed;
}}catch(e){{return 'FAILED '+String(e)+' line='+String(e.line||'');}}
}})();'''
    Path(args.output).write_text(code, encoding="utf-8-sig")
    print(json.dumps({"output": str(Path(args.output).resolve()), "candidate_id": selected}, ensure_ascii=False))


if __name__ == "__main__":
    main()
