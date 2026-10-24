#!/usr/bin/env python
"""Prepare and build content-driven visual notes from videos."""
from __future__ import annotations
import argparse,csv,json,math,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from typing import Any
from PIL import Image,ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
NAVY=colors.HexColor('#14213D');BLUE=colors.HexColor('#2563EB');CYAN=colors.HexColor('#0891B2');INK=colors.HexColor('#172033');MUTED=colors.HexColor('#5B6472');LIGHT=colors.HexColor('#EEF4FF');PALE=colors.HexColor('#F7F9FC');LINE=colors.HexColor('#D8DFEA');WHITE=colors.white
PAGE_W,PAGE_H=landscape(A4)
BODY=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=12.2,textColor=INK)
BULLET=ParagraphStyle('bullet',parent=BODY,leftIndent=12,firstLineIndent=-8,spaceAfter=4)
CALLOUT=ParagraphStyle('callout',fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=NAVY)
def parse_timestamp(value):
 if isinstance(value,(int,float)):
  if value<0: raise ValueError('timestamp cannot be negative')
  return float(value)
 text=str(value).strip()
 if re.fullmatch(r'\d+(?:\.\d+)?',text): return float(text)
 parts=text.split(':')
 if len(parts) not in (2,3): raise ValueError(f'invalid timestamp: {value}')
 try: nums=[float(p) for p in parts]
 except ValueError as exc: raise ValueError(f'invalid timestamp: {value}') from exc
 if len(nums)==2:
  minutes,seconds=nums
  if not 0<=seconds<60: raise ValueError(f'invalid timestamp: {value}')
  return minutes*60+seconds
 hours,minutes,seconds=nums
 if not(0<=minutes<60 and 0<=seconds<60): raise ValueError(f'invalid timestamp: {value}')
 return hours*3600+minutes*60+seconds
def format_timestamp(seconds):
 seconds=max(0,float(seconds));hours=int(seconds//3600);minutes=int((seconds%3600)//60);secs=seconds%60
 sec_text=f'{secs:04.1f}' if not secs.is_integer() else f'{int(secs):02d}'
 return f'{hours}:{minutes:02d}:{sec_text}' if hours else f'{minutes:02d}:{sec_text}'
def timestamped_frame_name(index,interval):
 if index<1 or interval<=0: raise ValueError('index must be >= 1 and interval must be positive')
 return f'frame_{index:05d}_{int(round((index-1)*interval)):06d}.jpg'
def select_latest_entry(entries):
 if not entries: raise ValueError('channel returned no videos')
 if any(e.get('timestamp') is not None for e in entries): return max(entries,key=lambda e:float(e.get('timestamp') or 0))
 return entries[0]
def _resolve_path(value,base_dir):
 p=Path(value);return (p if p.is_absolute() else base_dir/p).resolve()
def validate_manifest(manifest,base_dir):
 for key in ('report_title','video_title','source_url','slides'):
  if key not in manifest: raise ValueError(f'manifest missing {key}')
 if not isinstance(manifest['slides'],list) or not manifest['slides']: raise ValueError('manifest slides must contain at least one selected item')
 result=dict(manifest);normalized=[]
 for idx,raw in enumerate(manifest['slides'],1):
  item=dict(raw)
  for key in ('timestamp','title','image','notes','why_it_matters'):
   if key not in item: raise ValueError(f'slide {idx} missing {key}')
  image=_resolve_path(str(item['image']),base_dir)
  if not image.is_file(): raise ValueError(f'slide {idx} image not found: {image}')
  if not isinstance(item['notes'],list) or not item['notes']: raise ValueError(f'slide {idx} notes must be a non-empty list')
  item['image']=str(image);item['seconds']=parse_timestamp(item['timestamp']);item['timestamp']=format_timestamp(item['seconds']);item['layout']=item.get('layout','standard')
  crop=item.get('crop')
  if crop is not None:
   if not(isinstance(crop,list) and len(crop)==4 and all(isinstance(v,(int,float)) for v in crop)): raise ValueError(f'slide {idx} crop must be [x1,y1,x2,y2]')
   x1,y1,x2,y2=crop
   if x2<=x1 or y2<=y1: raise ValueError(f'slide {idx} crop has invalid bounds')
  normalized.append(item)
 result['slides']=normalized;return result
def _image_for_item(item):
 image=Image.open(item['image']).convert('RGB')
 return image.crop(tuple(item['crop'])) if item.get('crop') else image
def _draw_fitted(c,image,x,y,w,h):
 iw,ih=image.size;scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale
 c.setFillColor(WHITE);c.roundRect(x,y,w,h,3*mm,fill=1,stroke=0);c.drawImage(ImageReader(image),x+(w-dw)/2,y+(h-dh)/2,dw,dh,preserveAspectRatio=True,mask='auto');c.setStrokeColor(LINE);c.roundRect(x,y,w,h,3*mm,fill=0,stroke=1)
def _header(c,index,timestamp,title,subtitle=None):
 c.setFillColor(NAVY);c.rect(0,PAGE_H-16*mm,PAGE_W,16*mm,fill=1,stroke=0);c.setFillColor(CYAN);c.rect(0,PAGE_H-16*mm,64*mm,2.2*mm,fill=1,stroke=0);c.setFillColor(WHITE);c.setFont('Helvetica-Bold',8.5);c.drawString(14*mm,PAGE_H-10*mm,f'KEY FRAME {index}  •  {timestamp}');c.setFillColor(NAVY);c.setFont('Helvetica-Bold',21);c.drawString(14*mm,PAGE_H-29*mm,str(title)[:90])
 if subtitle: c.setFillColor(MUTED);c.setFont('Helvetica',9.2);c.drawString(14*mm,PAGE_H-35*mm,str(subtitle)[:140])
def _footer(c,page,url):
 c.setStrokeColor(LINE);c.line(14*mm,10*mm,PAGE_W-14*mm,10*mm);c.setFillColor(MUTED);c.setFont('Helvetica',6.7);c.drawString(14*mm,5.7*mm,f'Source: {url}'[:165]);c.drawRightString(PAGE_W-14*mm,5.7*mm,str(page))
def _notes(c,notes,why,x,y,w,h):
 c.setFillColor(PALE);c.roundRect(x,y,w,h,4*mm,fill=1,stroke=0);c.setFillColor(CYAN);c.roundRect(x,y+h-15*mm,w,15*mm,4*mm,fill=1,stroke=0);c.rect(x,y+h-15*mm,w,5*mm,fill=1,stroke=0);c.setFillColor(WHITE);c.setFont('Helvetica-Bold',11);c.drawString(x+6*mm,y+h-9.5*mm,'NOTES');cy=y+h-22*mm;why_h=34*mm
 for note in notes:
  p=Paragraph('• '+str(note),BULLET);_,ph=p.wrap(w-12*mm,max(1,cy-y-why_h-10*mm));p.drawOn(c,x+6*mm,cy-ph);cy-=ph+1.2*mm
 c.setFillColor(LIGHT);c.roundRect(x+5*mm,y+5*mm,w-10*mm,why_h,3*mm,fill=1,stroke=0);c.setFillColor(BLUE);c.setFont('Helvetica-Bold',7.5);c.drawString(x+10*mm,y+why_h-1*mm,'CORE IDEA');p=Paragraph(str(why),CALLOUT);_,ph=p.wrap(w-20*mm,why_h-13*mm);p.drawOn(c,x+10*mm,y+7*mm)
def build_pdf(manifest,output,base_dir=None):
 base_dir=Path(base_dir or '.').resolve();data=validate_manifest(manifest,base_dir);output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True);c=canvas.Canvas(str(output),pagesize=(PAGE_W,PAGE_H),pageCompression=1);c.setTitle(str(data['report_title']));c.setAuthor(str(data.get('author','Hermes Agent')));c.setSubject('Complete visual notes')
 c.setFillColor(NAVY);c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0);c.setFillColor(CYAN);c.rect(0,PAGE_H-7*mm,PAGE_W,7*mm,fill=1,stroke=0);c.setFillColor(colors.HexColor('#9ED6E0'));c.setFont('Helvetica-Bold',10);c.drawString(18*mm,PAGE_H-25*mm,'VISUAL NOTES  •  COMPLETE GUIDE');c.setFillColor(WHITE);c.setFont('Helvetica-Bold',27);c.drawString(18*mm,PAGE_H-44*mm,str(data['report_title'])[:72]);c.setFont('Helvetica',16);c.drawString(18*mm,PAGE_H-56*mm,str(data['video_title'])[:90]);c.setFillColor(colors.HexColor('#C7D2E4'));c.setFont('Helvetica',9.2);meta=str(data.get('duration','')).strip();c.drawString(18*mm,PAGE_H-66*mm,meta[:120]);c.setFillColor(colors.HexColor('#1E2B4A'));c.roundRect(18*mm,30*mm,260*mm,70*mm,5*mm,fill=1,stroke=0);cy=86*mm
 for text in [f"{len(data['slides'])} substantive visual(s), selected by content",'Repeated builds, presenter-only shots, and filler excluded','Output length expands or contracts with the source material','Claims, uncertainty, and caveats are labeled clearly']:
  p=Paragraph('• '+text,ParagraphStyle('cover',parent=BULLET,textColor=WHITE,fontSize=11,leading=15));_,ph=p.wrap(245*mm,18*mm);p.drawOn(c,27*mm,cy-ph);cy-=ph+3*mm
 c.setFont('Helvetica-Oblique',7.4);c.setFillColor(colors.HexColor('#C7D2E4'));c.drawString(18*mm,17*mm,str(data['source_url'])[:165]);c.showPage()
 for idx,item in enumerate(data['slides'],1):
  _header(c,str(idx),item['timestamp'],item['title'],item.get('subtitle'));image=_image_for_item(item)
  if item.get('layout')=='wide': _draw_fitted(c,image,14*mm,76*mm,269*mm,81*mm);_notes(c,item['notes'],item['why_it_matters'],14*mm,18*mm,269*mm,51*mm)
  else: _draw_fitted(c,image,14*mm,22*mm,172*mm,137*mm);_notes(c,item['notes'],item['why_it_matters'],193*mm,22*mm,90*mm,137*mm)
  _footer(c,idx+1,str(data['source_url']));c.showPage()
 c.save();return output
def _run(cmd): return subprocess.run(cmd,text=True,capture_output=True,check=True)
def probe_duration(video):
 result=_run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(video)])
 return float(result.stdout.strip() or 0)
def _yt_json(source,flat=False):
 cmd=[sys.executable,'-m','yt_dlp','--dump-single-json','--skip-download']
 if flat: cmd+=['--flat-playlist','--playlist-end','12']
 cmd.append(source);return json.loads(_run(cmd).stdout)
def resolve_video(source):
 collection=any(x in source for x in ('/videos','/channel/','/@')) and 'watch?v=' not in source
 if not collection:
  meta=_yt_json(source);return str(meta.get('webpage_url') or source),meta
 listing=_yt_json(source,True);entry=select_latest_entry(listing.get('entries') or []);vid=entry.get('id')
 if not vid: raise ValueError('latest channel entry had no video id')
 url=f'https://www.youtube.com/watch?v={vid}';return url,_yt_json(url)
def make_contact_sheets(frames,outdir,per_sheet=18):
 outdir.mkdir(parents=True,exist_ok=True);sheets=[]
 for start in range(0,len(frames),per_sheet):
  thumbs=[]
  for path in frames[start:start+per_sheet]:
   im=Image.open(path).convert('RGB');im.thumbnail((360,203));tile=Image.new('RGB',(370,228),'white');tile.paste(im,((370-im.width)//2,0));ImageDraw.Draw(tile).text((8,207),path.stem,fill='black');thumbs.append(tile)
  sheet=Image.new('RGB',(1110,math.ceil(len(thumbs)/3)*228),(226,226,226))
  for i,tile in enumerate(thumbs): sheet.paste(tile,((i%3)*370,(i//3)*228))
  out=outdir/f'contact_{start//per_sheet+1:02d}.jpg';sheet.save(out,quality=91);sheets.append(out)
 return sheets
def prepare(source,workdir,interval=8,transcript=None,title=None,source_url=None):
 workdir=Path(workdir).resolve();workdir.mkdir(parents=True,exist_ok=True);local=Path(source).expanduser()
 if local.is_file():
  video=local.resolve();url=source_url or video.as_uri();meta={'title':title or video.stem,'webpage_url':url,'duration':probe_duration(video),'extractor':'local-file'}
  if transcript:
   transcript_path=Path(transcript).expanduser().resolve()
   if not transcript_path.is_file(): raise FileNotFoundError(f'transcript not found: {transcript_path}')
   shutil.copy2(transcript_path,workdir/f'transcript{transcript_path.suffix.lower()}')
 else:
  url,meta=resolve_video(source);download_url=url
  if title: meta['title']=title
  if source_url: url=source_url;meta['webpage_url']=source_url
  _run([sys.executable,'-m','yt_dlp','-f','bv*[height<=720]+ba/b[height<=720]','--merge-output-format','mp4','-o',str(workdir/'video.%(ext)s'),download_url]);video=next(workdir.glob('video.*'),None)
  if not video: raise RuntimeError('yt-dlp finished without creating a video file')
  try: _run([sys.executable,'-m','yt_dlp','--write-auto-subs','--write-subs','--sub-langs','en.*,en','--convert-subs','vtt','--skip-download','-o',str(workdir/'transcript.%(ext)s'),download_url])
  except subprocess.CalledProcessError: pass
 (workdir/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
 frames_dir=workdir/'candidates';frames_dir.mkdir(exist_ok=True)
 for stale in frames_dir.glob('*.jpg'): stale.unlink()
 _run(['ffmpeg','-y','-i',str(video),'-vf',f'fps=1/{interval}','-q:v','2',str(frames_dir/'raw_%05d.jpg')]);frames=[]
 for index,raw in enumerate(sorted(frames_dir.glob('raw_*.jpg')),1):
  target=frames_dir/timestamped_frame_name(index,interval);raw.replace(target);frames.append(target)
 contacts_dir=workdir/'contact_sheets';contacts_dir.mkdir(exist_ok=True)
 for stale in contacts_dir.glob('*.jpg'): stale.unlink()
 contacts=make_contact_sheets(frames,contacts_dir);video_title=meta.get('title') or 'Video recording';manifest={'report_title':f'Visual Notes — {video_title}','video_title':video_title,'source_url':url,'duration':format_timestamp(float(meta.get('duration') or 0)),'selection_policy':'Include every unique substantive argument, decision, data set, workflow, or architecture visual; omit repeated builds, presenter details, promotions, and filler.','slides':[]};(workdir/'manifest.template.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');return {'video_url':url,'video':str(video),'frames':len(frames),'contact_sheets':[str(p) for p in contacts],'manifest':str(workdir/'manifest.template.json')}
def package_frames(manifest,base_dir,output_zip):
 data=validate_manifest(manifest,base_dir);output_zip=Path(output_zip);output_zip.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output_zip,'w',zipfile.ZIP_DEFLATED) as zf:
  rows=[]
  for idx,item in enumerate(data['slides'],1):
   image=_image_for_item(item);name=f"{idx:02d}_{item['timestamp'].replace(':','')}_{Path(item['image']).stem}.jpg";temp=output_zip.parent/('.__'+name);image.save(temp,quality=96);zf.write(temp,name);temp.unlink();rows.append((idx,item['timestamp'],item['title'],name))
  index=output_zip.parent/'.__index.csv'
  with index.open('w',newline='',encoding='utf-8-sig') as fh: w=csv.writer(fh);w.writerow(['order','timestamp','title','file']);w.writerows(rows)
  zf.write(index,'index.csv');index.unlink()
 return output_zip
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True);prep=sub.add_parser('prepare');prep.add_argument('source');prep.add_argument('--workdir',required=True,type=Path);prep.add_argument('--interval',type=float,default=8);prep.add_argument('--transcript',type=Path);prep.add_argument('--title');prep.add_argument('--source-url');build=sub.add_parser('build');build.add_argument('manifest',type=Path);build.add_argument('--output',required=True,type=Path);build.add_argument('--zip',dest='zip_output',type=Path);a=p.parse_args(argv)
 if a.command=='prepare': print(json.dumps(prepare(a.source,a.workdir,a.interval,a.transcript,a.title,a.source_url),indent=2));return 0
 manifest=json.loads(a.manifest.read_text(encoding='utf-8'));build_pdf(manifest,a.output,a.manifest.parent);result={'pdf':str(a.output.resolve()),'slides':len(manifest['slides'])}
 if a.zip_output: package_frames(manifest,a.manifest.parent,a.zip_output);result['zip']=str(a.zip_output.resolve())
 print(json.dumps(result,indent=2));return 0
if __name__=='__main__': raise SystemExit(main())