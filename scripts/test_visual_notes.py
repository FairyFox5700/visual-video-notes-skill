import json
import sys
from pathlib import Path
import pytest
from PIL import Image
from pypdf import PdfReader
sys.path.insert(0,str(Path(__file__).resolve().parent))
import visual_notes as vn

def test_timestamps():
 assert vn.parse_timestamp('75')==75
 assert vn.parse_timestamp('01:15')==75
 assert vn.parse_timestamp('1:01:15.5')==3675.5
 with pytest.raises(ValueError): vn.parse_timestamp('1:99')

def test_latest_entry():
 entries=[{'id':'old','timestamp':100},{'id':'new','timestamp':300},{'id':'mid','timestamp':200}]
 assert vn.select_latest_entry(entries)['id']=='new'

def test_frame_name():
 assert vn.timestamped_frame_name(1,8)=='frame_00001_000000.jpg'
 assert vn.timestamped_frame_name(3,8)=='frame_00003_000016.jpg'

def test_dynamic_pdf(tmp_path):
 img=tmp_path/'frame.jpg';Image.new('RGB',(1280,720),'white').save(img)
 slides=[{'timestamp':f'00:{10+i:02d}','title':f'Slide {i+1}','image':str(img),'notes':['Detail','Second detail'],'why_it_matters':'Reason'} for i in range(3)]
 manifest={'report_title':'Report','video_title':'Video','source_url':'https://youtu.be/abcdefghijk','slides':slides}
 out=tmp_path/'out.pdf';vn.build_pdf(manifest,out,tmp_path)
 reader=PdfReader(str(out));assert len(reader.pages)==4
 text='\n'.join(p.extract_text() or '' for p in reader.pages);assert 'Slide 1' in text and 'Slide 3' in text

def test_manifest_rejects_empty_slides(tmp_path):
 with pytest.raises(ValueError,match='slides'): vn.validate_manifest({'report_title':'R','video_title':'V','source_url':'u','slides':[]},tmp_path)

def test_prepare_local_recording_with_transcript(tmp_path):
 video=tmp_path/'meeting.mp4';transcript=tmp_path/'meeting.vtt'
 transcript.write_text('WEBVTT\n\n00:00.000 --> 00:01.000\nDecision recorded.\n',encoding='utf-8')
 vn._run(['ffmpeg','-y','-f','lavfi','-i','color=c=navy:s=320x180:d=2','-pix_fmt','yuv420p',str(video)])
 result=vn.prepare(video,tmp_path/'run',1,transcript,'Architecture review','https://example.sharepoint.com/private-recording')
 assert result['frames'] >= 1
 assert Path(result['video']) == video.resolve()
 assert (tmp_path/'run'/'transcript.vtt').is_file()
 manifest=json.loads((tmp_path/'run'/'manifest.template.json').read_text(encoding='utf-8'))
 assert manifest['video_title']=='Architecture review'
 assert manifest['source_url']=='https://example.sharepoint.com/private-recording'