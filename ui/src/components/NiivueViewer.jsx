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

function voxelToWorld(volume, voxel) {
  const affine = volume?.hdr?.affine
  if (!Array.isArray(affine) || !Array.isArray(affine[0])) return null

  const [x, y, z] = voxel
  const world = [
    affine[0][0] * x + affine[0][1] * y + affine[0][2] * z + affine[0][3],
    affine[1][0] * x + affine[1][1] * y + affine[1][2] * z + affine[1][3],
    affine[2][0] * x + affine[2][1] * y + affine[2][2] * z + affine[2][3],
  ]
  return world.every(Number.isFinite) ? world : null
}

function pancreasCentroidMM(volume) {
  const image = volume?.img
  const dims = volume?.hdr?.dims
  if (!image || !dims || dims.length < 4) return null

  const nx = Number(dims[1])
  const ny = Number(dims[2])
  const nz = Number(dims[3])
  const voxelCount = nx * ny * nz
  if (!Number.isFinite(voxelCount) || voxelCount <= 0 || image.length < voxelCount) return null

  let pancreasCount = 0
  let pancreasX = 0
  let pancreasY = 0
  let pancreasZ = 0
  let foregroundCount = 0
  let foregroundX = 0
  let foregroundY = 0
  let foregroundZ = 0

  for (let index = 0; index < voxelCount; index += 1) {
    const value = Math.round(Number(image[index]))
    if (value <= 0) continue

    const x = index % nx
    const yz = Math.floor(index / nx)
    const y = yz % ny
    const z = Math.floor(yz / ny)
    foregroundCount += 1
    foregroundX += x
    foregroundY += y
    foregroundZ += z

    if (value === 1) {
      pancreasCount += 1
      pancreasX += x
      pancreasY += y
      pancreasZ += z
    }
  }

  if (pancreasCount > 0) {
    return voxelToWorld(volume, [
      pancreasX / pancreasCount,
      pancreasY / pancreasCount,
      pancreasZ / pancreasCount,
    ])
  }
  if (foregroundCount > 0) {
    return voxelToWorld(volume, [
      foregroundX / foregroundCount,
      foregroundY / foregroundCount,
      foregroundZ / foregroundCount,
    ])
  }
  return null
}

function focusOnWorldPoint(nv, worldMM, mode) {
  if (!worldMM) return false
  const fraction = nv.mm2frac(worldMM, 0, true)
  if (!fraction || !Array.from(fraction).every(Number.isFinite)) return false

  nv.scene.crosshairPos = new Float32Array(Array.from(fraction, (value) => (
    Math.min(1, Math.max(0, value))
  )))
  if (mode === '3d') {
    nv.pivot3D = [...worldMM]
  }
  return true
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
  const focusMmRef = useRef(null)
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
        focusMmRef.current = null

        const ctPath = showFull && caseData.files.ct_full
          ? caseData.files.ct_full
          : caseData.files.ct
        const overlaySources = sources.filter((source) => caseData.files[source])

        if (mode === '2d') {
          clearMeshes(nv)
          const volumes = [{
            url: `${BASE}/${ctPath}`,
            colormap: 'gray',
            opacity: 1,
          }]

          overlaySources.forEach((source) => {
            const maskPath = caseData.files[source]
            volumes.push({
              url: `${BASE}/${maskPath}`,
              colormap: 'warm',
              opacity: overlayOpacity,
              cal_min: 0,
              cal_max: 2,
            })
          })

          await nv.loadVolumes(volumes)
          overlaySources.forEach((source, sourceIndex) => {
            const volume = nv.volumes[sourceIndex + 1]
            if (!volume) return
            volume.setColormapLabel(labelColormap(source, showPancreas, showLesion))
            nv.setOpacity(sourceIndex + 1, overlayOpacity)
          })
          nv.setSliceType(nv.sliceTypeMultiplanar)
          nv.setCrosshairColor([0.42, 0.52, 0.64, 0.8])
          if (showFull && nv.volumes[1]) {
            focusMmRef.current = pancreasCentroidMM(nv.volumes[1])
            focusOnWorldPoint(nv, focusMmRef.current, mode)
          }
          nv.updateGLVolume()
          nv.drawScene()
        } else {
          clearMeshes(nv)
          // 3D shows the marching-cubes SURFACE MESHES (pancreas + lesion) exported
          // per case, with the CT rendered faintly behind them for context. The meshes
          // are world-aligned (mm) via the CT affine, so they land in the right place.
          const volumes = [{
            url: `${BASE}/${ctPath}`,
            colormap: 'gray',
            opacity: ctOpacity,
          }]
          // The hidden label volume supplies a reliable world-space pancreas centroid.
          // It stays invisible in 3D; the exported surface meshes remain the visible result.
          if (showFull && overlaySources.length) {
            volumes.push({
              url: `${BASE}/${caseData.files[overlaySources[0]]}`,
              colormap: 'warm',
              opacity: 0,
              cal_min: 0,
              cal_max: 2,
            })
          }
          await nv.loadVolumes(volumes)

          const meshFiles = caseData.files.mesh || {}
          const meshLayers = []
          sources.forEach((source) => {
            const colors = SOURCE_COLORS[source]
            const pancreasMesh = meshFiles[`pancreas_${source}`]
            const lesionMesh = meshFiles[`lesion_${source}`]
            // Pancreas semi-transparent so a lesion inside it stays visible; lesion solid.
            if (showPancreas && pancreasMesh) {
              meshLayers.push({
                url: `${BASE}/${pancreasMesh}`,
                rgba255: [colors.pancreas[0], colors.pancreas[1], colors.pancreas[2], 150],
              })
            }
            if (showLesion && lesionMesh) {
              meshLayers.push({
                url: `${BASE}/${lesionMesh}`,
                rgba255: [colors.lesion[0], colors.lesion[1], colors.lesion[2], 255],
              })
            }
          })
          if (meshLayers.length) {
            await nv.loadMeshes(meshLayers)
          }

          nv.setSliceType(nv.sliceTypeRender)
          nv.setRenderAzimuthElevation(120, 15)
          nv.setOpacity(0, ctOpacity)
          // Cut only the CT context; the surface meshes stay whole, and the
          // clipping surface itself stays transparent.
          nv.setClipPlaneColor([0, 0, 0, 0])
          nv.setClipPlane(clip?.enabled
            ? [clip.depth, clip.azimuth, clip.elevation]
            : [2, 0, 0])
          if (showFull && nv.volumes[1]) {
            focusMmRef.current = pancreasCentroidMM(nv.volumes[1])
            focusOnWorldPoint(nv, focusMmRef.current, mode)
          }
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
    if (showFull && focusMmRef.current) {
      focusOnWorldPoint(nv, focusMmRef.current, mode)
    }
    nv.drawScene()
  }, [resetToken, mode, showFull])

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
