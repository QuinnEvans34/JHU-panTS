"""Local, fixed-case coverage contact sheets. No diagnosis or eligibility decision."""
import json
from pathlib import Path
from uuid import uuid4

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw
import yaml

from scripts.acquisition.download_pants import mounted
from src.data.manifest_records import canonical, digest
from src.data.protected_identity import accepted_pants_members
from src.data.source_evidence import measure_nifti, resolve_file, identity

REPO = Path(__file__).resolve().parents[2]
SHA = 'd5f9849da0ac39919ce6ec0c199ea218deeb0b28b0dd981b01682322de90f57b'
URI = 'PanTSMini_ImageTr_00000001_00001000/PanTS_00000078/ct.nii.gz'


def sheet(data, window):
    low, high = window
    panels = [(2, int(i), 'Axial', 'R', 'A') for i in np.linspace(0,data.shape[2]-1,10).round()]
    panels += [(1, int(i), 'Coronal', 'R', 'S') for i in np.linspace(0,data.shape[1]-1,5).round()]
    panels += [(0, int(i), 'Sagittal', 'A', 'S') for i in np.linspace(0,data.shape[0]-1,5).round()]
    canvas = Image.new('RGB',(1500,1380),'#111111')
    draw = ImageDraw.Draw(canvas)
    draw.text((15,12),'PanTS_00000078 | coverage review only | canonical RAS voxel axes',fill='white')
    draw.text((15,32),f'Window [{low}, {high}] scaled CT values | all source slices loaded; selected planes shown',fill='white')
    for n,(axis,index,name,left,top) in enumerate(panels):
        plane = np.take(data,index,axis=axis).T[::-1,::-1]
        pixels = np.rint(np.clip((plane-low)/(high-low),0,1)*255).astype(np.uint8)
        tile=Image.fromarray(pixels).convert('RGB')
        tile.thumbnail((270,280),Image.Resampling.NEAREST)
        x=(n%5)*300; y=70+(n//5)*325
        canvas.paste(tile,(x+(300-tile.width)//2,y+25+(280-tile.height)//2))
        draw.text((x+10,y),f'{name} index {index} | left={left}, top={top}',fill='white')
    return canvas, [dict(axis=a,index=i,plane=n,left=l,top=t) for a,i,n,l,t in panels]


def main():
    train=accepted_pants_members((REPO/'outputs/splits/train.txt').read_bytes(),'train')
    if 'pants:study:PanTS_00000078' not in {i.study_id for i in train}:
        raise ValueError('Case not in approved training membership')
    registry=yaml.safe_load((REPO/'configs/local/roots.yaml').read_text())
    primary=registry['failure_domains']['external_primary']; mount=Path(primary['mount_path'])
    device=mounted(mount,primary['volume_uuid'])
    def check(): mounted(mount,primary['volume_uuid'],device)
    root=Path(registry['roots']['pants_source']['acquisition_parent'])/'extraction-3b1cd6110811-20260922'
    if not root.is_relative_to(mount): raise ValueError('Unexpected source root')
    evidence=measure_nifti({'coverage_source':root},'coverage_source',URI,check)
    if evidence['file']['content_sha256'] != SHA or evidence['issue_codes']:
        raise ValueError('Changed CT or unresolved header geometry')
    path=resolve_file({'coverage_source':root},'coverage_source',URI)
    before=identity(path.stat())
    image=nib.load(path)
    if image.shape != (225,197,115): raise ValueError('Scope/size changed')
    oriented=nib.as_closest_canonical(image)
    data=oriented.get_fdata(dtype=np.float32)
    if not np.isfinite(data).all(): raise ValueError('Nonfinite CT')
    check()
    if identity(path.stat()) != before: raise ValueError('CT changed while loading')
    parent=REPO/'outputs/prowl'
    if parent.resolve()!=parent: raise ValueError('Noncanonical output parent')
    destination=parent/('case78-coverage-'+str(uuid4())); destination.mkdir(exist_ok=False)
    views={}
    for name,window in [('soft',(-160,240)),('bone',(-400,1400))]:
        rendered,planes=sheet(data,window)
        filename=name+'.png'
        rendered.save(destination/filename)
        views[filename]=dict(window=list(window),planes=planes,
                             sha256=digest((destination/filename).read_bytes()))
    # Rehash the fixed 5.8 MB source after rendering as an independent unchanged check.
    after=measure_nifti({'coverage_source':root},'coverage_source',URI,check)
    if after['file']!=evidence['file']: raise ValueError('CT content changed')
    record=dict(source=evidence,canonical_axes=list(nib.aff2axcodes(oriented.affine)),
                canonical_affine=oriented.affine.tolist(),canonical_shape=list(data.shape),
                orientation_only=True,interpolation='none; display nearest-neighbor',views=views,
                code_sha256=digest(Path(__file__).read_bytes()),eligibility='not_assessed')
    with (destination/'evidence.json').open('xb') as stream: stream.write(canonical(record))
    print(destination)


if __name__=='__main__': main()
