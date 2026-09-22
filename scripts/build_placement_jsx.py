#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_support import PATH_GUARD_JS, source_path_is_unambiguous, utf8_output


def main() -> None:
    utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--preview-png", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).resolve().read_text(encoding="utf-8-sig"))
    if job.get("schema_version") != 3:
        raise SystemExit("schema_version_must_be_3")
    if job.get("status") != "selected":
        raise SystemExit("job_status_must_be_selected")
    candidate = job.get("candidate", {})
    if candidate.get("status") != "selected":
        raise SystemExit("candidate_must_be_selected")

    source = Path(job["source_ai"]).resolve()
    if not source_path_is_unambiguous(str(source)):
        raise SystemExit("source_path_contains_percent_escape: rename the AI path before placement")
    asset = Path(candidate.get("effective_asset_path", "")).resolve()
    preview_png = Path(args.preview_png).resolve()
    if not source.is_file() or source.suffix.lower() != ".ai":
        raise SystemExit("source_ai_missing")
    if not asset.is_file():
        raise SystemExit("selected_candidate_missing")
    if preview_png.suffix.lower() != ".png":
        raise SystemExit("preview_must_be_png")

    target = job["target"]
    payload = {
        "source_ai": str(source),
        "asset_path": str(asset),
        "preview_png": str(preview_png),
        "layer": target["layer"],
        "scope_id": target["scope_id"],
        "group_index": int(target["group_index"]),
        "bounds": target["target_bounds"],
        "raster_indices": sorted(set(int(value) for value in target["raster_indices"]), reverse=True),
        "primary_raster_index": int(target.get("primary_raster_index", target["raster_indices"][0])),
        "fit": target.get("fit", "contain"),
        "allow_crop": bool(target.get("allow_crop", False)),
        "embed": bool(target.get("embed", True)),
        "candidate_id": candidate.get("id", "candidate"),
    }
    # URI encoding prevents ExtendScript File from interpreting literal % escapes
    # and handles Unicode/space paths consistently on both operating systems.
    payload["source_uri"] = source.as_uri()
    payload["asset_uri"] = asset.as_uri()
    payload["preview_uri"] = preview_png.as_uri()
    code = f'''(function(){{
try{{
var job={json.dumps(payload, ensure_ascii=True)},doc=app.activeDocument;
{PATH_GUARD_JS}
if(!sameDocumentPath(doc.fullName.fsName,new File(job.source_uri).fsName,File.fs==='Windows'))throw new Error('target_document_path_mismatch');
function findLayer(name){{for(var i=0;i<doc.layers.length;i++)if(doc.layers[i].name===name)return doc.layers[i];throw new Error('layer_not_found:'+name);}}
function layerNameExists(name){{for(var i=0;i<doc.layers.length;i++)if(doc.layers[i].name===name)return true;return false;}}
function versionBase(original,scopeId){{return 'aicreate-'+original+'-'+scopeId;}}
function nextLayerName(original,scopeId){{var base=versionBase(original,scopeId);if(!layerNameExists(base))return base;for(var n=2;n<1000;n++){{var suffix=n<10?'0'+n:String(n),candidate=base+'-'+suffix;if(!layerNameExists(candidate))return candidate;}}throw new Error('aicreate_layer_name_exhausted');}}
function isScopedVersion(name,base){{if(name===base)return true;if(name.indexOf(base+'-')!==0)return false;var suffix=name.substring(base.length+1);return /^\\d+$/.test(suffix);}}
function hideOlderVersions(original,scopeId,current){{var base=versionBase(original,scopeId);for(var i=0;i<doc.layers.length;i++){{var layer=doc.layers[i],name=String(layer.name);if(layer!==current&&isScopedVersion(name,base))layer.visible=false;}}}}
function createSiblingLayer(source,name){{var target=doc.layers.add();target.name=name;target.move(source,ElementPlacement.PLACEBEFORE);target.locked=false;target.visible=true;return target;}}
function topGroups(layer){{var out=[];for(var i=0;i<layer.groupItems.length;i++)if(layer.groupItems[i].parent===layer)out.push(layer.groupItems[i]);return out;}}
function collectRasters(container,out){{for(var i=0;i<container.pageItems.length;i++){{var item=container.pageItems[i];if(item.typename==='RasterItem'||item.typename==='PlacedItem')out.push(item);if(item.typename==='GroupItem')collectRasters(item,out);}}}}
function contained(outer,inner,t){{return inner[0]>=outer[0]-t&&inner[2]<=outer[2]+t&&inner[1]<=outer[1]+t&&inner[3]>=outer[3]-t;}}
var sourceLayer=findLayer(job.layer);sourceLayer.locked=false;sourceLayer.visible=true;
var groups=topGroups(sourceLayer),group=groups[job.group_index];if(!group)throw new Error('group_not_found:'+job.group_index);
var rasters=[];collectRasters(group,rasters);var anchor=rasters[job.primary_raster_index];if(!anchor)throw new Error('primary_raster_not_found');
if(job.fit==='cover'&&(!job.allow_crop||anchor.parent.typename!=='GroupItem'||!anchor.parent.clipped))throw new Error('cover_requires_existing_clipping_group');
var file=new File(job.asset_uri);if(!file.exists)throw new Error('selected_asset_missing');
var newLayer=createSiblingLayer(sourceLayer,nextLayerName(sourceLayer.name,job.scope_id));doc.activeLayer=newLayer;
var placed=doc.placedItems.add();placed.file=file;placed.move(newLayer,ElementPlacement.PLACEATBEGINNING);
var b=job.bounds,w=b[2]-b[0],h=b[1]-b[3],sx=w/placed.width,sy=h/placed.height,scale=job.fit==='cover'?Math.max(sx,sy):Math.min(sx,sy);
placed.width*=scale;placed.height*=scale;placed.left=b[0]+(w-placed.width)/2;placed.top=b[1]-(h-placed.height)/2;
var placedBounds=placed.geometricBounds;if(job.fit==='contain'&&!contained(b,placedBounds,0.75))throw new Error('replacement_outside_target');
for(var r=0;r<job.raster_indices.length;r++){{var idx=job.raster_indices[r];if(idx<0||idx>=rasters.length)throw new Error('raster_index_invalid:'+idx);rasters[idx].hidden=true;}}
if(job.embed)placed.embed();
hideOlderVersions(sourceLayer.name,job.scope_id,newLayer);sourceLayer.visible=true;newLayer.visible=true;
if(!sourceLayer.visible||!newLayer.visible)throw new Error('layer_visibility_verification_failed');
var preview=new File(job.preview_uri),options=new ImageCaptureOptions();options.resolution=120;options.antiAliasing=true;options.transparency=false;doc.imageCapture(preview,group.geometricBounds,options);
if(!preview.exists||preview.length<=0)throw new Error('final_preview_export_failed');
doc.save();
return 'VERIFIED candidate_id='+job.candidate_id+' layer='+newLayer.name+' preview='+job.preview_png;
}}catch(e){{return 'FAILED '+String(e)+' line='+String(e.line||'');}}
}})();'''
    output = Path(args.output).resolve()
    output.write_text(code, encoding="utf-8-sig")
    print(json.dumps({"output": str(output), "candidate_id": candidate.get("id", "candidate"), "source_ai": str(source), "preview_png": str(preview_png)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
