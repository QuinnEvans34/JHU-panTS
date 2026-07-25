import { useEffect, useRef, useState } from 'react'
import { Niivue } from '@niivue/niivue'
import { LoaderCircle, TriangleAlert } from 'lucide-react'

const BASE = '/cases'

const SOURCE_COLORS = {
  pred: {
    pancreas: [38, 197, 166, 112],
    lesion: [249, 99, 99, 255],
  },
  gt: {
    pancreas: [56, 189, 248, 105],
    lesion: [251, 191, 36, 255],
  },
}

function labelColormap(source, showPancreas, showLesion) {
  const colors = SOURCE_COLORS[source]
  return {
    R: [0, colors.pancreas[0], colors.lesion[0]],
    G: [0, colors.pancreas[1], colors.lesion[1]],
    B: [0, colors.pancreas[2], colors.lesion[2]],
    A: [0, showPancreas ? colors.pancreas[3] : 0, showLesion ? colors.lesion[3] : 0],
    I: [0, 1, 2],
    labels: ['Background', 'Pancreas', 'Lesion'],
  }
}

function clearMeshes(nv) {
  ;(nv.meshes || []).slice().forEach((mesh) => {
    try {
      nv.removeMesh(mesh)
    } catch {
      // A mesh can already be gone while NiiVue is switching cases.
    }
  })
}

export default function NiivueViewer({
  caseData,
  sources = ['pred'],
  mode = '2d',
  showFull = false,
  overlayOpacity = 0.68,
  ctOpacity = 0.18,
  showPancreas = true,
  showLesion = true,
  clip = null,
  resetToken = 0,
  compact = false,
  label = 'Medical image viewer',
}) {
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const [state, setState] = useState({ status: 'loading', message: 'Preparing viewer' })

  useEffect(() => {
    if (!canvasRef.current) return undefined

    const nv = new Niivue({
      backColor: [0.025, 0.035, 0.055, 1],
      show3Dcrosshair: false,
      isColorbar: false,
      multiplanarShowRender: 0,
      clipPlaneColor: [0, 0, 0, 0],
      isClipPlanesCutaway: true,
      isClipAllVolumes: false,
    })

    nv.attachToCanvas(canvasRef.current)
    nvRef.current = nv

    return () => {
      nvRef.current = null
    }
  }, [compact])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !caseData) return undefined

    let cancelled = false

    async function loadScene() {
      try {
        setState({ status: 'loading', message: 'Loading prepared scan' })

        const ctPath = showFull && caseData.files.ct_full
          ? caseData.files.ct_full
          : caseData.files.ct

        if (mode === '2d') {
          clearMeshes(nv)
          const volumes = [{
            url: `${BASE}/${ctPath}`,
            colormap: 'gray',
            opacity: 1,
          }]

          sources.forEach((source) => {
            const maskPath = caseData.files[source]
            if (maskPath) {
              volumes.push({
                url: `${BASE}/${maskPath}`,
                colormap: 'warm',
                opacity: overlayOpacity,
                cal_min: 0,
                cal_max: 2,
              })
            }
          })

          await nv.loadVolumes(volumes)
          sources.forEach((source, sourceIndex) => {
            const volume = nv.volumes[sourceIndex + 1]
            if (!volume) return
            volume.setColormapLabel(labelColormap(source, showPancreas, showLesion))
            nv.setOpacity(sourceIndex + 1, overlayOpacity)
          })
          nv.setSliceType(nv.sliceTypeMultiplanar)
          nv.setCrosshairColor([0.42, 0.52, 0.64, 0.8])
          nv.updateGLVolume()
        } else {
          clearMeshes(nv)
          const volumes = [{
            url: `${BASE}/${ctPath}`,
            colormap: 'gray',
            opacity: ctOpacity,
          }]

          sources.forEach((source) => {
            const maskPath = caseData.files[source]
            if (maskPath) {
              volumes.push({
                url: `${BASE}/${maskPath}`,
                colormap: 'warm',
                opacity: overlayOpacity,
                cal_min: 0,
                cal_max: 2,
              })
            }
          })

          await nv.loadVolumes(volumes)
          sources.forEach((source, sourceIndex) => {
            const volume = nv.volumes[sourceIndex + 1]
            if (!volume) return
            volume.setColormapLabel(labelColormap(source, showPancreas, showLesion))
            nv.setOpacity(sourceIndex + 1, overlayOpacity)
          })
          nv.setSliceType(nv.sliceTypeRender)
          nv.setRenderAzimuthElevation(120, 15)
          nv.setOpacity(0, ctOpacity)
          // Cut only the CT context. Pancreas and lesion overlays remain fully
          // visible, and the clipping surface itself stays transparent.
          nv.setClipPlaneColor([0, 0, 0, 0])
          nv.setClipPlane(clip?.enabled
            ? [clip.depth, clip.azimuth, clip.elevation]
            : [2, 0, 0])
          nv.updateGLVolume()
          nv.drawScene()
        }

        if (!cancelled) {
          setState({ status: 'ready', message: 'Prepared result loaded' })
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'The prepared scan could not be displayed.',
          })
        }
      }
    }

    loadScene()
    return () => {
      cancelled = true
    }
  }, [
    caseData,
    sources.join('|'),
    mode,
    showFull,
    overlayOpacity,
    ctOpacity,
    showPancreas,
    showLesion,
  ])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || mode !== '3d') return
    nv.setClipPlane(clip?.enabled
      ? [clip.depth, clip.azimuth, clip.elevation]
      : [2, 0, 0])
    nv.drawScene()
  }, [clip, mode])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv) return
    if (mode === '3d') {
      nv.setRenderAzimuthElevation(120, 15)
    } else {
      nv.setSliceType(nv.sliceTypeMultiplanar)
    }
    nv.drawScene()
  }, [resetToken, mode])

  return (
    <div className={`niivue-frame${compact ? ' niivue-frame--compact' : ''}`}>
      <canvas ref={canvasRef} aria-label={label} />
      {state.status === 'loading' && (
        <div className="viewer-state" role="status">
          <LoaderCircle size={16} className="spin" aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'error' && (
        <div className="viewer-state viewer-state--error" role="alert">
          <TriangleAlert size={16} aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'ready' && (
        <span className="viewer-ready" aria-label="Prepared result loaded">Prepared result</span>
      )}
    </div>
  )
}
