#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--preview-ai", required=True)
    parser.add_argument("--preview-png", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    candidates = [item for item in job.get("candidates", []) if str(item.get("id")) == str(args.candidate_id) and item.get("status") != "rejected"]
    if len(candidates) != 1:
        raise SystemExit("candidate_not_available_for_preview")
    source = Path(job["source_ai"]).resolve()
    preview_ai = Path(args.preview_ai).resolve()
    preview_png = Path(args.preview_png).resolve()
    if preview_ai == source:
        raise SystemExit("preview_ai_must_not_equal_source_ai")
    if not preview_ai.is_file():
        raise SystemExit("preview_ai_copy_missing")
    asset = Path(candidates[0]["path"]).resolve()
    if not asset.is_file():
        raise SystemExit("candidate_asset_missing")
    target = job["target"]
    payload = {
        "preview_ai": str(preview_ai),
        "preview_name": preview_ai.name,
        "preview_png": str(preview_png),
        "asset_path": str(asset),
        "layer": target.get("layer", "印刷"),
        "group_index": int(target["group_index"]),
        "bounds": target["target_bounds"],
        "raster_indices": sorted(set(int(value) for value in target["raster_indices"]), reverse=True),
        "primary_raster_index": int(target.get("primary_raster_index", target["raster_indices"][0])),
        "fit": target.get("fit", "contain"),
        "candidate_id": args.candidate_id,
    }
    code = f'''(function(){{
try{{
var job={json.dumps(payload, ensure_ascii=False)},doc=app.activeDocument;
if(String(doc.name).toLowerCase()!==String(job.preview_name).toLowerCase())throw new Error('preview_document_mismatch');
function findLayer(name){{for(var i=0;i<doc.layers.length;i++)if(doc.layers[i].name===name)return doc.layers[i];throw new Error('layer_not_found:'+name);}}
function topGroups(layer){{var out=[];for(var i=0;i<layer.groupItems.length;i++)if(layer.groupItems[i].parent===layer)out.push(layer.groupItems[i]);return out;}}
function collectRasters(container,out){{for(var i=0;i<container.pageItems.length;i++){{var item=container.pageItems[i];if(item.typename==='RasterItem'||item.typename==='PlacedItem')out.push(item);if(item.typename==='GroupItem')collectRasters(item,out);}}}}
var groups=topGroups(findLayer(job.layer)),group=groups[job.group_index];if(!group)throw new Error('group_not_found');
var rasters=[];collectRasters(group,rasters);var anchor=rasters[job.primary_raster_index];if(!anchor)throw new Error('primary_raster_not_found');
var placed=doc.placedItems.add(),f=new File(job.asset_path);if(!f.exists)throw new Error('candidate_missing');placed.file=f;
var b=job.bounds,w=b[2]-b[0],h=b[1]-b[3],sx=w/placed.width,sy=h/placed.height,scale=job.fit==='cover'?Math.max(sx,sy):Math.min(sx,sy);
placed.width*=scale;placed.height*=scale;placed.left=b[0]+(w-placed.width)/2;placed.top=b[1]-(h-placed.height)/2;placed.move(anchor,ElementPlacement.PLACEBEFORE);
for(var r=0;r<job.raster_indices.length;r++){{var idx=job.raster_indices[r];if(idx<0||idx>=rasters.length)throw new Error('raster_index_invalid:'+idx);rasters[idx].remove();}}
var options=new ImageCaptureOptions();options.resolution=120;options.antiAliasing=true;options.transparency=false;doc.imageCapture(new File(job.preview_png),group.geometricBounds,options);
return 'PREVIEW_EXPORTED candidate_id='+job.candidate_id+' path='+job.preview_png;
}}catch(e){{return 'FAILED '+String(e)+' line='+String(e.line||'');}}
}})();'''
    Path(args.output).write_text(code, encoding="utf-8-sig")
    print(json.dumps({"output": str(Path(args.output).resolve()), "candidate_id": args.candidate_id, "preview_png": str(preview_png)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
