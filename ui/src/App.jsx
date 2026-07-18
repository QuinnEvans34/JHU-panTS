import { useEffect, useRef, useState } from 'react'
import { Niivue } from '@niivue/niivue'

// Static-first viewer: everything is loaded from /public/cases/ (see docs/ui.md).
// Swap the synthetic "sample" case for real ones by running scripts/export_case.py
// and copying its outputs/ui_cases/* into public/cases/.
const BASE = '/cases'
// NiiVue wants mesh colors as a Uint8Array; a plain array silently falls back to white.
const PANCREAS_RGBA = [46, 204, 113, 105]  // translucent green shell (see the lesion through it)
const LESION_RGBA = [239, 68, 68, 255]     // solid red nodule

function suspicionBand(c) {
  if (!c || !c.pred_has_lesion) return { label: 'No lesion flagged', color: 'var(--green)' }
  if (c.confidence >= 0.66) return { label: 'Possible lesion — higher suspicion', color: 'var(--red)' }
  if (c.confidence >= 0.4) return { label: 'Possible lesion — moderate suspicion', color: 'var(--amber)' }
  return { label: 'Possible lesion — lower suspicion', color: 'var(--amber)' }
}

function approxDiameterMm(volMm3) {
  if (!volMm3) return 0
  return Math.round(2 * Math.cbrt((3 * volMm3) / (4 * Math.PI)))
}

export default function App() {
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const [cases, setCases] = useState({})
  const [caseId, setCaseId] = useState(null)
  const [showPred, setShowPred] = useState(true)
  const [showFull, setShowFull] = useState(false)   // full abdomen CT vs the pancreas ROI
  const [viewMode, setViewMode] = useState('3d')    // '3d' render or '2d' slices
  const [ctOpacity, setCtOpacity] = useState(0.0)   // CT off by default: the clean meshes are the hero
  const [clipOn, setClipOn] = useState(false)
  const [depth, setDepth] = useState(0)
  const [azimuth, setAzimuth] = useState(0)
  const [elevation, setElevation] = useState(0)
  const [status, setStatus] = useState('loading…')

  // one-time NiiVue init
  useEffect(() => {
    const nv = new Niivue({
      backColor: [0.03, 0.05, 0.09, 1],
      show3Dcrosshair: false,
      isColorbar: false,
    })
    nv.attachToCanvas(canvasRef.current)
    nv.setSliceType(nv.sliceTypeRender)   // 3D render mode (rotatable), not 2D slices
    nv.setRenderAzimuthElevation(120, 15)
    nvRef.current = nv
    fetch(`${BASE}/results.json`)
      .then((r) => r.json())
      .then((d) => {
        setCases(d)
        setCaseId(Object.keys(d)[0] || null)
      })
      .catch(() => setStatus('could not load /cases/results.json'))
  }, [])

  // (re)load the scene when the case or prediction/truth toggle changes
  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !caseId || !cases[caseId]) return
    const c = cases[caseId]
    const suffix = showPred ? 'pred' : 'gt'
    let cancelled = false
    ;(async () => {
      try {
        setStatus('rendering…')
        // CT volume is always loaded (so the opacity slider works) but starts invisible.
        // Full-scan mode swaps in the whole abdomen CT when it was exported.
        const ctUrl = (showFull && c.files.ct_full) ? c.files.ct_full : c.files.ct
        await nv.loadVolumes([{ url: `${BASE}/${ctUrl}`, colormap: 'gray', opacity: ctOpacity }])

        // clear any previous meshes, then load pancreas + lesion for this source
        ;(nv.meshes || []).slice().forEach((m) => { try { nv.removeMesh(m) } catch (e) { /* noop */ } })
        const meshes = []
        const colors = []
        const pm = c.files.mesh?.[`pancreas_${suffix}`]
        const lm = c.files.mesh?.[`lesion_${suffix}`]
        if (pm) { meshes.push({ url: `${BASE}/${pm}`, rgba255: new Uint8Array(PANCREAS_RGBA) }); colors.push(PANCREAS_RGBA) }
        if (lm) { meshes.push({ url: `${BASE}/${lm}`, rgba255: new Uint8Array(LESION_RGBA) }); colors.push(LESION_RGBA) }
        if (meshes.length) {
          await nv.loadMeshes(meshes)
          // force the colors after load (belt-and-suspenders across NiiVue versions)
          ;(nv.meshes || []).forEach((m, i) => {
            if (colors[i]) { try { nv.setMeshProperty(m.id, 'rgba255', new Uint8Array(colors[i])) } catch (e) { /* noop */ } }
          })
        }
        if (nv.volumes && nv.volumes.length) nv.setOpacity(0, ctOpacity)
        if (!cancelled) { nv.drawScene(); setStatus(`${(nv.meshes || []).length} surface(s) loaded`) }
      } catch (e) {
        if (!cancelled) setStatus('render error: ' + e.message)
      }
    })()
    return () => { cancelled = true }
  }, [caseId, showPred, showFull, cases])

  // live control: 3D render vs 2D multiplanar slices (the classic way to read a CT)
  useEffect(() => {
    const nv = nvRef.current
    if (!nv) return
    nv.setSliceType(viewMode === '3d' ? nv.sliceTypeRender : nv.sliceTypeMultiplanar)
    nv.drawScene()
  }, [viewMode])

  // live control: CT volume opacity
  useEffect(() => {
    const nv = nvRef.current
    if (nv && nv.volumes && nv.volumes.length) { nv.setOpacity(0, ctOpacity); nv.drawScene() }
  }, [ctOpacity])

  // live control: clip plane. depth of 2 is outside the volume => effectively no clipping.
  useEffect(() => {
    const nv = nvRef.current
    if (!nv) return
    nv.setClipPlane(clipOn ? [depth, azimuth, elevation] : [2, 0, 0])
  }, [clipOn, depth, azimuth, elevation])

  const c = caseId ? cases[caseId] : null
  const band = suspicionBand(c)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ background: '#3b2f0b', borderBottom: '1px solid #a16207', color: '#fde68a',
        padding: '8px 16px', fontSize: 13 }}>
        ⚠ Segmentation / annotation-assist tool — not a diagnosis. A clinician reviews and decides.
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1, position: 'relative', minWidth: 0 }}>
          <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
          {status && (
            <div style={{ position: 'absolute', top: 12, left: 12, background: '#111827cc',
              border: '1px solid var(--border)', borderRadius: 6, padding: '4px 10px', fontSize: 12,
              color: 'var(--muted)' }}>{status}</div>
          )}
          <div style={{ position: 'absolute', bottom: 12, left: 12, fontSize: 11, color: 'var(--dim)' }}>
            drag to rotate · scroll to zoom · <span style={{ color: '#2ecc71' }}>green = pancreas</span> · <span style={{ color: '#ef4444' }}>red = lesion</span>
          </div>
        </div>

        <div style={{ width: 320, background: 'var(--panel)', borderLeft: '1px solid var(--border)',
          padding: 16, overflowY: 'auto' }}>
          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>PanTS CADe · 3D viewer</div>
          <div style={{ fontSize: 11, color: 'var(--dim)', marginBottom: 12 }}>
            3D pancreas (green) with any lesion (red). Fade the CT in for context.
          </div>

          <div style={{ background: '#0b0f17', border: '1px solid var(--border)', borderRadius: 8,
            padding: 12, marginBottom: 8 }}>
            <div style={{ color: band.color, fontWeight: 700, fontSize: 14 }}>{band.label}</div>
            {c && c.pred_has_lesion && (
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 6, lineHeight: 1.5 }}>
                Approx size: {approxDiameterMm(c.lesion_volume_mm3)} mm
                ({(c.lesion_volume_mm3 / 1000).toFixed(1)} cm³)<br />
                Location: within the pancreas region
              </div>
            )}
          </div>

          <label>Showcase case</label>
          <select value={caseId || ''} onChange={(e) => setCaseId(e.target.value)}>
            {Object.keys(cases).map((k) => (
              <option key={k} value={k}>{cases[k].case_id || k}</option>
            ))}
          </select>

          <label>Contour source</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className={showPred ? 'active' : ''} style={{ flex: 1 }} onClick={() => setShowPred(true)}>
              Model prediction
            </button>
            <button className={!showPred ? 'active' : ''} style={{ flex: 1 }} onClick={() => setShowPred(false)}>
              Ground truth
            </button>
          </div>

          <label>View</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className={viewMode === '3d' ? 'active' : ''} style={{ flex: 1 }} onClick={() => setViewMode('3d')}>3D</button>
            <button className={viewMode === '2d' ? 'active' : ''} style={{ flex: 1 }} onClick={() => setViewMode('2d')}>Slices</button>
          </div>

          <label>CT scan</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className={!showFull ? 'active' : ''} style={{ flex: 1 }} onClick={() => setShowFull(false)}>Pancreas ROI</button>
            <button className={showFull ? 'active' : ''} style={{ flex: 1 }} disabled={!c?.files?.ct_full}
              onClick={() => { setShowFull(true); if (ctOpacity === 0) setCtOpacity(0.5) }}>Full scan</button>
          </div>

          <label>CT volume opacity — {ctOpacity.toFixed(2)} {ctOpacity === 0 ? '(hidden)' : ''}</label>
          <input type="range" min="0" max="1" step="0.01" value={ctOpacity}
            onChange={(e) => setCtOpacity(parseFloat(e.target.value))} />

          <label style={{ marginTop: 16 }}>
            <input type="checkbox" checked={clipOn} onChange={(e) => setClipOn(e.target.checked)}
              style={{ width: 'auto', marginRight: 6 }} />
            Cut plane (move through the volume in 3D)
          </label>
          {clipOn && (
            <div style={{ paddingLeft: 4 }}>
              <label>Depth — {depth.toFixed(2)}</label>
              <input type="range" min="-0.5" max="0.5" step="0.01" value={depth}
                onChange={(e) => setDepth(parseFloat(e.target.value))} />
              <label>Azimuth — {azimuth}°</label>
              <input type="range" min="0" max="360" step="1" value={azimuth}
                onChange={(e) => setAzimuth(parseInt(e.target.value))} />
              <label>Elevation — {elevation}°</label>
              <input type="range" min="-90" max="90" step="1" value={elevation}
                onChange={(e) => setElevation(parseInt(e.target.value))} />
            </div>
          )}

          <button style={{ width: '100%', marginTop: 16 }} onClick={() => {
            const nv = nvRef.current; if (nv) { nv.setRenderAzimuthElevation(120, 15); nv.drawScene() }
          }}>Reset view</button>

          {c && (
            <div style={{ marginTop: 20, paddingTop: 12, borderTop: '1px solid var(--border)',
              fontSize: 11, color: 'var(--dim)' }}>
              <div style={{ marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
                Validation (hidden from clinicians)
              </div>
              pancreas Dice {c.dice_pancreas} · lesion Dice {c.dice_lesion}<br />
              confidence {c.confidence} · gt lesion {String(c.gt_has_lesion)} · pred lesion {String(c.pred_has_lesion)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
