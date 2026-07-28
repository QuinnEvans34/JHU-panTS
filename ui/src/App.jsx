import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BadgeCheck,
  BookOpen,
  Box,
  Check,
  ChevronRight,
  CircleAlert,
  Crosshair,
  Database,
  Download,
  Eye,
  Info,
  Layers3,
  LayoutGrid,
  LoaderCircle,
  MessageSquareWarning,
  Microscope,
  Radio,
  RotateCcw,
  ScanLine,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  WifiOff,
  X,
} from 'lucide-react'
const NiivueViewer = lazy(() => import('./components/NiivueViewer.jsx'))

const BASE = '/cases'
const API_BASE = 'http://localhost:8000'
const STORAGE_KEY = 'pants-review-status-v1'
const CURATED_CASE_IDS = ['PanTS_00000029', 'PanTS_00000008', 'PanTS_00000011']
const CURATED_CASE_SET = new Set(CURATED_CASE_IDS)

const CASE_PROFILES = {
  PanTS_00000029: {
    label: 'Strong overlap',
    eyebrow: 'True-positive showcase',
    summary: 'The model and source of truth identify the same lesion.',
    interpretation: 'Strong pancreas segmentation and good lesion localization, with modest boundary differences.',
    strength: 'Correctly localized the lesion and closely followed the pancreatic boundary.',
    limitation: 'The predicted lesion boundary does not exactly match the reference contour.',
    tone: 'positive',
    order: 1,
  },
  PanTS_00000008: {
    label: 'Small false positive',
    eyebrow: 'Failure analysis',
    summary: 'The model flags a very small region where the source of truth contains no lesion.',
    interpretation: 'Pancreas segmentation remains strong, but a tiny false-positive lesion is introduced.',
    strength: 'Maintains a strong pancreas outline on a lesion-negative case.',
    limitation: 'Flags a 47 mm³ region that is absent from the source-of-truth mask.',
    tone: 'caution',
    order: 2,
  },
  PanTS_00000011: {
    label: 'Large false positive',
    eyebrow: 'Failure analysis',
    summary: 'The model over-calls a larger lesion-like region on a lesion-negative case.',
    interpretation: 'A useful example of why detection specificity and human review remain important.',
    strength: 'Produces a high-quality pancreas segmentation.',
    limitation: 'Predicts a substantial lesion region where the source of truth has none.',
    tone: 'caution',
    order: 3,
  },
}

function approxDiameterMm(volumeMm3) {
  if (!volumeMm3) return 0
  return Math.round(2 * Math.cbrt((3 * volumeMm3) / (4 * Math.PI)))
}

function modelSignal(confidence) {
  if (confidence >= 0.8) return 'Higher model signal'
  if (confidence >= 0.55) return 'Moderate model signal'
  return 'Lower model signal'
}

function formatCaseId(caseId) {
  return caseId?.replace('PanTS_', 'PanTS ')
}

function friendlyScanLabel(caseId, endpointLabel) {
  const profileLabel = CASE_PROFILES[caseId]?.label
  if (profileLabel) return profileLabel

  const formattedId = formatCaseId(caseId)
  if (
    typeof endpointLabel === 'string'
    && endpointLabel.trim()
    && endpointLabel !== caseId
    && endpointLabel !== formattedId
  ) {
    return endpointLabel
  }

  return 'Unmarked pancreas CT'
}

function formatScoreTime(date = new Date()) {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

async function fetchJson(url, options = {}, timeoutMs = 5000) {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    if (!response.ok) throw new Error(`Endpoint returned ${response.status}`)
    return await response.json()
  } finally {
    window.clearTimeout(timeoutId)
  }
}

function readStoredStatuses() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function statusLabel(status) {
  if (status === 'reviewed') return 'Reviewed'
  if (status === 'discussion') return 'Discussion'
  return 'Unreviewed'
}

function StatusPill({ status }) {
  const icon = status === 'reviewed'
    ? <Check size={13} aria-hidden="true" />
    : status === 'discussion'
      ? <MessageSquareWarning size={13} aria-hidden="true" />
      : <span className="status-dot" aria-hidden="true" />

  return (
    <span className={`status-pill status-pill--${status || 'unreviewed'}`}>
      {icon}
      {statusLabel(status)}
    </span>
  )
}

function LayerSwitch({ checked, onChange, label, color }) {
  return (
    <label className="layer-switch">
      <span className={`layer-swatch layer-swatch--${color}`} aria-hidden="true" />
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="switch-track" aria-hidden="true"><span /></span>
    </label>
  )
}

function ViewerSuspense({ children }) {
  return (
    <Suspense fallback={<div className="viewer-module-loading" role="status">Preparing medical viewer…</div>}>
      {children}
    </Suspense>
  )
}

function EmptyState() {
  return (
    <main className="empty-state">
      <Database size={28} aria-hidden="true" />
      <h1>No prepared cases found</h1>
      <p>The application could not find a case manifest at <code>/cases/results.json</code>.</p>
    </main>
  )
}

export default function App() {
  const [cases, setCases] = useState({})
  const [loadError, setLoadError] = useState('')
  const [activeTab, setActiveTab] = useState('queue')
  const [caseId, setCaseId] = useState(null)
  const [reviewStatuses, setReviewStatuses] = useState(readStoredStatuses)
  const [reviewMode, setReviewMode] = useState('2d')
  const [comparisonMode, setComparisonMode] = useState('2d')
  const [showFull, setShowFull] = useState(false)
  const [showPancreas, setShowPancreas] = useState(true)
  const [showLesion, setShowLesion] = useState(true)
  const [overlayOpacity, setOverlayOpacity] = useState(0.68)
  const [ctOpacity, setCtOpacity] = useState(0.18)
  const [clipEnabled, setClipEnabled] = useState(true)
  const [clipDepth, setClipDepth] = useState(0)
  const [resetToken, setResetToken] = useState(0)
  const [showAbout, setShowAbout] = useState(false)
  const [apiCases, setApiCases] = useState([])
  const [endpointStatus, setEndpointStatus] = useState('checking')
  const [liveResults, setLiveResults] = useState({})
  const [inferenceState, setInferenceState] = useState({ status: 'idle', caseId: null })
  const [truthRevealedCaseId, setTruthRevealedCaseId] = useState(null)

  useEffect(() => {
    fetch(`${BASE}/results.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Case manifest returned ${response.status}`)
        return response.json()
      })
      .then((data) => {
        setCases(data)
        const ids = Object.keys(data).sort((a, b) => {
          const aOrder = CASE_PROFILES[a]?.order ?? 99
          const bOrder = CASE_PROFILES[b]?.order ?? 99
          return aOrder - bOrder
        })
        setCaseId(ids[0] || null)
      })
      .catch((error) => setLoadError(error.message))
  }, [])

  useEffect(() => {
    let cancelled = false

    fetchJson(`${API_BASE}/cases`)
      .then((data) => {
        if (!Array.isArray(data) || !data.length) throw new Error('No live cases available')
        const available = data.filter((item) => (
          item
          && typeof item.case_id === 'string'
          && typeof item.label === 'string'
        ))
        if (!available.length) throw new Error('Invalid live case catalog')
        if (!cancelled) {
          setApiCases(available)
          setEndpointStatus('online')
        }
      })
      .catch(() => {
        if (!cancelled) setEndpointStatus('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewStatuses))
  }, [reviewStatuses])

  const caseIds = useMemo(
    () => Object.keys(cases).sort((a, b) => {
      const aOrder = CASE_PROFILES[a]?.order ?? 99
      const bOrder = CASE_PROFILES[b]?.order ?? 99
      return aOrder - bOrder
    }),
    [cases],
  )
  const curatedCaseIds = useMemo(
    () => CURATED_CASE_IDS.filter((id) => cases[id]),
    [cases],
  )

  const scanOptions = useMemo(() => {
    const liveOptions = apiCases
      .filter((item) => cases[item.case_id])
      .map((item) => ({
        caseId: item.case_id,
        label: friendlyScanLabel(item.case_id, item.label),
      }))
    if (liveOptions.length) return liveOptions
    return caseIds.map((id) => ({
      caseId: id,
      label: friendlyScanLabel(id, null),
    }))
  }, [apiCases, caseIds, cases])

  const libraryCases = useMemo(() => {
    const source = apiCases.length
      ? apiCases
      : Object.keys(cases).sort().map((id) => ({ case_id: id, label: null }))

    return source.map((item, index) => ({
      caseId: item.case_id,
      label: friendlyScanLabel(item.case_id, item.label),
      cachedCase: cases[item.case_id] || null,
      curated: CURATED_CASE_SET.has(item.case_id),
      studyNumber: String(index + 1).padStart(2, '0'),
    }))
  }, [apiCases, cases])

  const currentCase = caseId ? cases[caseId] : null
  const currentLive = caseId ? liveResults[caseId] : null
  const isAnalyzing = inferenceState.status === 'loading' && inferenceState.caseId === caseId
  const hasLiveResult = Boolean(currentLive)
  const isCuratedCase = CURATED_CASE_SET.has(caseId)
  const isTruthRevealed = !isCuratedCase && hasLiveResult && truthRevealedCaseId === caseId
  const revealStage = isCuratedCase ? null : isTruthRevealed ? 3 : hasLiveResult ? 2 : 1
  const reviewSources = isCuratedCase
    ? ['pred']
    : isTruthRevealed
      ? ['pred', 'gt']
      : hasLiveResult
        ? ['pred']
        : []
  const showModelOverlay = reviewSources.includes('pred')
  const overlapPancreas = Number.isFinite(currentLive?.result?.dice_pancreas)
    ? currentLive.result.dice_pancreas
    : currentCase?.dice_pancreas
  const overlapLesion = Number.isFinite(currentLive?.result?.dice_lesion)
    ? currentLive.result.dice_lesion
    : currentCase?.dice_lesion
  const findingHasLesion = hasLiveResult ? currentLive.result.lesion_flagged : currentCase?.pred_has_lesion
  const findingVolumeMm3 = hasLiveResult
    ? currentLive.result.lesion_volume_mm3
    : currentCase?.lesion_volume_mm3 || 0
  const findingConfidence = hasLiveResult
    ? currentLive.result.global_peak_lesion_confidence
    : currentCase?.confidence || 0
  const currentProfile = CASE_PROFILES[caseId] || {
    label: 'Unmarked scan',
    eyebrow: 'Prospective review',
    summary: 'A clean CT awaiting a live model score.',
    interpretation: 'Run live inference before reviewing the model proposal.',
    strength: 'The CT can be inspected without model or reference annotations.',
    limitation: 'No prediction is shown until live analysis completes.',
    tone: 'neutral',
  }

  function openCase(id, destination = 'review') {
    setCaseId(id)
    setActiveTab(destination)
    setTruthRevealedCaseId(null)
    setInferenceState({ status: 'idle', caseId: null })
  }

  function selectScan(id) {
    setCaseId(id)
    setTruthRevealedCaseId(null)
    if (!CURATED_CASE_SET.has(id)) {
      setLiveResults((previous) => {
        const next = { ...previous }
        delete next[id]
        return next
      })
    }
    setInferenceState({ status: 'idle', caseId: null })
  }

  async function analyzeScan(targetCaseId) {
    const requestedCaseId = typeof targetCaseId === 'string' ? targetCaseId : caseId
    if (!requestedCaseId || inferenceState.status === 'loading') return

    setTruthRevealedCaseId(null)
    setLiveResults((previous) => {
      const next = { ...previous }
      delete next[requestedCaseId]
      return next
    })
    setInferenceState({ status: 'loading', caseId: requestedCaseId })

    try {
      const result = await fetchJson(
        `${API_BASE}/predict`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ case_id: requestedCaseId, split: 'test' }),
        },
        30000,
      )
      if (
        result?.case_id !== requestedCaseId
        || typeof result.lesion_flagged !== 'boolean'
        || !Number.isFinite(result.lesion_volume_mm3)
        || !Number.isFinite(result.global_peak_lesion_confidence)
        || !Number.isFinite(result.inference_seconds)
      ) {
        throw new Error('Invalid prediction response')
      }
      setLiveResults((previous) => ({
        ...previous,
        [requestedCaseId]: {
          result,
          scoredAt: formatScoreTime(),
        },
      }))
      setEndpointStatus('online')
      setInferenceState({ status: 'complete', caseId: requestedCaseId })
    } catch {
      setLiveResults((previous) => {
        const next = { ...previous }
        delete next[requestedCaseId]
        return next
      })
      setEndpointStatus('offline')
      setInferenceState({ status: 'offline', caseId: requestedCaseId })
    }
  }

  function loadLibraryScan(id) {
    if (!cases[id] || inferenceState.status === 'loading') return
    selectScan(id)
    setActiveTab('review')
  }

  function revealSourceOfTruth() {
    if (isCuratedCase || !hasLiveResult || !caseId) return
    setShowPancreas(true)
    setShowLesion(true)
    setTruthRevealedCaseId(caseId)
  }

  function resetUnmarkedScan() {
    if (isCuratedCase || !caseId) return
    setLiveResults((previous) => {
      const next = { ...previous }
      delete next[caseId]
      return next
    })
    setTruthRevealedCaseId(null)
    setInferenceState({ status: 'idle', caseId: null })
    setShowPancreas(true)
    setShowLesion(true)
    setResetToken((value) => value + 1)
  }

  function setReviewStatus(status) {
    if (!caseId) return
    setReviewStatuses((previous) => ({ ...previous, [caseId]: status }))
  }

  function resetDemo() {
    setReviewStatuses({})
    localStorage.removeItem(STORAGE_KEY)
  }

  if (loadError) return <EmptyState />

  return (
    <div className="app">
      <header className="app-header">
        <button className="brand" type="button" onClick={() => setActiveTab('queue')} aria-label="Open case queue">
          <span className="brand-mark"><ScanLine size={19} aria-hidden="true" /></span>
          <span className="brand-copy">
            <strong>PanTS Review</strong>
            <span>Pancreas segmentation workspace</span>
          </span>
        </button>

        <nav className="primary-nav" aria-label="Primary navigation">
          <button className={activeTab === 'queue' ? 'active' : ''} onClick={() => setActiveTab('queue')}>
            Case queue
          </button>
          <button className={activeTab === 'library' ? 'active' : ''} onClick={() => setActiveTab('library')}>
            Scan library
          </button>
          <button className={activeTab === 'review' ? 'active' : ''} onClick={() => setActiveTab('review')} disabled={!currentCase}>
            Review workspace
          </button>
          <button
            className={activeTab === 'comparison' ? 'active' : ''}
            onClick={() => setActiveTab('comparison')}
            disabled={!currentCase || !isCuratedCase}
          >
            Scientific comparison
          </button>
        </nav>

        <div className="header-actions">
          <div className="header-provenance">
            <span className="prepared-badge">
              <Activity size={13} aria-hidden="true" />
              Model: pancreas-lesion-segmenter v1 · checkpoint step 18000
            </span>
            <span className="header-freshness">
              <Radio size={11} aria-hidden="true" />
              Predictions are computed live by a deployed FastAPI endpoint when available, with cached results as fallback.
            </span>
          </div>
          <button className="icon-button" onClick={() => setShowAbout(true)} aria-label="About this research interface">
            <Info size={18} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="research-notice">
        <ShieldCheck size={14} aria-hidden="true" />
        <span><strong>Research use only.</strong> Segmentation and annotation-assist interface—not a diagnosis.</span>
        <span className="notice-detail">Prepared cases work offline; live scores are labeled with their scoring time.</span>
      </div>

      {activeTab === 'queue' && (
        <main className="queue-page">
          <section className="queue-hero">
            <div>
              <span className="eyebrow">Five-week project · prepared demonstration</span>
              <h1>Review the model as a scientist would.</h1>
              <p>
                Three deliberately selected cases show where pancreas-aware segmentation succeeds,
                where it over-calls, and why the source of truth matters.
              </p>
            </div>
            <div className="queue-summary" aria-label="Prepared case summary">
              <div><strong>{curatedCaseIds.length}</strong><span>curated cases</span></div>
              <div><strong>1</strong><span>strong result</span></div>
              <div><strong>2</strong><span>failure analyses</span></div>
            </div>
          </section>

          <section className="queue-section">
            <div className="section-heading">
              <div>
                <h2>Case queue</h2>
                <p>Open a saved scan and its model output instantly—no live inference or waiting.</p>
              </div>
              <button className="text-button" onClick={resetDemo}>Reset review status</button>
            </div>

            <div className="case-table" role="table" aria-label="Prepared demonstration cases">
              <div className="case-table__header" role="row">
                <span>Case</span>
                <span>Model summary</span>
                <span>Scientific role</span>
                <span>Status</span>
                <span />
              </div>
              {curatedCaseIds.map((id) => {
                const item = cases[id]
                const profile = CASE_PROFILES[id]
                const status = reviewStatuses[id] || 'unreviewed'
                return (
                  <div className="case-row" role="row" key={id}>
                    <div className="case-identity">
                      <span className={`case-indicator case-indicator--${profile.tone}`} aria-hidden="true" />
                      <div>
                        <strong>{formatCaseId(id)}</strong>
                        <span>Prepared validation case</span>
                      </div>
                    </div>
                    <div>
                      <strong>{item.pred_has_lesion ? 'Possible finding flagged' : 'No finding flagged'}</strong>
                      <span>{approxDiameterMm(item.lesion_volume_mm3)} mm estimated diameter · {modelSignal(item.confidence)}</span>
                    </div>
                    <div>
                      <strong>{profile.label}</strong>
                      <span>{profile.eyebrow}</span>
                    </div>
                    <StatusPill status={status} />
                    <button className="review-button" onClick={() => openCase(id)}>
                      Review <ChevronRight size={15} aria-hidden="true" />
                    </button>
                  </div>
                )
              })}
            </div>
          </section>

          <section className="workflow-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Presentation workflow</span>
                <h2>One honest story, from prediction to evidence.</h2>
              </div>
            </div>
            <div className="workflow-grid">
              <article>
                <span className="step-number">01</span>
                <Target size={20} aria-hidden="true" />
                <h3>Select a prepared case</h3>
                <p>The CT, segmentation, surface meshes, and result summary are already available.</p>
              </article>
              <article>
                <span className="step-number">02</span>
                <Eye size={20} aria-hidden="true" />
                <h3>Inspect the proposal</h3>
                <p>Review the predicted pancreas and lesion in synchronized planes or 3D.</p>
              </article>
              <article>
                <span className="step-number">03</span>
                <Microscope size={20} aria-hidden="true" />
                <h3>Reveal the source of truth</h3>
                <p>Compare identical views and explain agreement, over-segmentation, or false positives.</p>
              </article>
              <article>
                <span className="step-number">04</span>
                <BadgeCheck size={20} aria-hidden="true" />
                <h3>Record the review</h3>
                <p>Mark the case reviewed or flag it for a deeper scientific discussion.</p>
              </article>
            </div>
          </section>
        </main>
      )}

      {activeTab === 'library' && (
        <main className="library-page">
          <section className="library-hero">
            <div>
              <span className="eyebrow">Prepared scan repository</span>
              <h1>Choose a study. Score it live.</h1>
              <p>
                Curated studies open with their scientific evidence. Every other card opens as a
                clean, unmarked CT. Analyze reveals the model proposal; source of truth remains
                concealed until you explicitly reveal it.
              </p>
            </div>
            <div className="library-source" aria-live="polite">
              <span className={`library-source__signal library-source__signal--${endpointStatus}`} aria-hidden="true" />
              <div>
                <strong>
                  {endpointStatus === 'online'
                    ? 'Live endpoint connected'
                    : endpointStatus === 'offline'
                      ? 'Cached library available'
                      : 'Checking live endpoint'}
                </strong>
                <span>
                  {endpointStatus === 'online'
                    ? `${libraryCases.length} scans discovered by FastAPI`
                    : `${libraryCases.length} scans loaded from results.json`}
                </span>
              </div>
            </div>
          </section>

          <section className="library-section">
            <div className="section-heading">
              <div>
                <h2>Available studies</h2>
                <p>Unmarked studies move from clean CT, to live prediction, to an optional source-of-truth reveal.</p>
              </div>
              <span className="library-count"><LayoutGrid size={14} aria-hidden="true" /> {libraryCases.length} scans</span>
            </div>

            <div className="scan-gallery" aria-label="Available scan library">
              {libraryCases.map((scan) => {
                return (
                  <button
                    type="button"
                    className="scan-card"
                    key={scan.caseId}
                    onClick={() => loadLibraryScan(scan.caseId)}
                    disabled={!scan.cachedCase || inferenceState.status === 'loading'}
                    aria-label={`Load ${scan.caseId}, ${scan.label}`}
                  >
                    <span className="scan-card__topline">
                      <span>Study {scan.studyNumber}</span>
                      <span className={scan.curated ? 'scan-card__status scan-card__status--live' : 'scan-card__status'}>
                        {scan.curated ? 'Curated evidence' : endpointStatus === 'online' ? 'Ready to analyze' : 'CT available'}
                      </span>
                    </span>
                    <span className="scan-card__visual" aria-hidden="true">
                      <ScanLine size={27} />
                      <span><i /><i /><i /><i /></span>
                    </span>
                    <span className="scan-card__copy">
                      <strong>{scan.label}</strong>
                      <code>{scan.caseId}</code>
                    </span>
                    <span className="scan-card__meta">
                      <span>{scan.cachedCase?.spacing_mm?.[0]?.toFixed(1) || '1.5'} mm voxels</span>
                      <span>{scan.curated ? 'CT + scientific evidence' : 'CT only until analyzed'}</span>
                    </span>
                    <span className="scan-card__action">
                      {scan.curated
                        ? <Microscope size={15} aria-hidden="true" />
                        : <ScanLine size={15} aria-hidden="true" />}
                      {scan.curated ? 'Open curated review' : 'Load clean scan'}
                      <ChevronRight size={15} aria-hidden="true" />
                    </span>
                  </button>
                )
              })}
            </div>
          </section>
        </main>
      )}

      {activeTab === 'review' && currentCase && (
        <main className="workspace">
          <aside className="case-rail" aria-label="Prepared cases">
            <div className="rail-heading">
              <span className="eyebrow">Scan library</span>
              <strong>{caseIds.length} studies</strong>
            </div>
            <div className="rail-list">
              {caseIds.map((id) => {
                const profile = CASE_PROFILES[id] || { label: 'Unmarked scan', tone: 'neutral' }
                return (
                  <button
                    key={id}
                    className={`rail-case ${id === caseId ? 'active' : ''}`}
                    onClick={() => selectScan(id)}
                  >
                    <span className={`case-indicator case-indicator--${profile.tone}`} aria-hidden="true" />
                    <span>
                      <strong>{formatCaseId(id)}</strong>
                      <small>{profile.label}</small>
                    </span>
                    <StatusPill status={reviewStatuses[id] || 'unreviewed'} />
                  </button>
                )
              })}
            </div>
            {isCuratedCase ? (
              <button className="rail-comparison" onClick={() => setActiveTab('comparison')}>
                <Microscope size={16} aria-hidden="true" />
                Open scientific comparison
              </button>
            ) : (
              <button className="rail-comparison" onClick={() => setActiveTab('library')}>
                <LayoutGrid size={16} aria-hidden="true" />
                Return to scan library
              </button>
            )}
          </aside>

          <section className="viewer-workspace">
            <header className="workspace-toolbar">
              <div>
                <span className="eyebrow">
                  {isCuratedCase
                    ? currentProfile.eyebrow
                    : revealStage === 3
                      ? 'Stage 3 · Source of truth'
                      : revealStage === 2
                        ? 'Stage 2 · Live prediction'
                        : 'Stage 1 · Unmarked'}
                </span>
                <strong>{formatCaseId(caseId)} · {currentProfile.label}</strong>
              </div>
              <div className="toolbar-actions">
                <div className="segmented-control" aria-label="Viewer mode">
                  <button className={reviewMode === '2d' ? 'active' : ''} onClick={() => setReviewMode('2d')}>
                    <Crosshair size={15} aria-hidden="true" /> Three planes
                  </button>
                  <button className={reviewMode === '3d' ? 'active' : ''} onClick={() => setReviewMode('3d')}>
                    <Box size={15} aria-hidden="true" /> 3D
                  </button>
                </div>
                <button className="tool-button" onClick={() => setResetToken((value) => value + 1)}>
                  <RotateCcw size={15} aria-hidden="true" /> Reset view
                </button>
              </div>
            </header>

            <div className="primary-viewer">
              <ViewerSuspense>
                <NiivueViewer
                  caseData={currentCase}
                  sources={reviewSources}
                  mode={reviewMode}
                  showFull={showFull}
                  overlayOpacity={overlayOpacity}
                  ctOpacity={ctOpacity}
                  showPancreas={showPancreas}
                  showLesion={showLesion}
                  clip={{
                    enabled: clipEnabled,
                    depth: clipDepth,
                    azimuth: 0,
                    elevation: 0,
                  }}
                  resetToken={resetToken}
                  label={`${formatCaseId(caseId)} ${
                    isTruthRevealed
                      ? 'model prediction and source of truth'
                      : showModelOverlay
                        ? 'model prediction'
                        : 'unmarked CT'
                  }`}
                />
              </ViewerSuspense>
              <div className="viewer-legend">
                {showModelOverlay ? (
                  <>
                    <span><i className="legend-dot legend-dot--pancreas" /> Model pancreas</span>
                    <span><i className="legend-dot legend-dot--lesion" /> Model lesion</span>
                  </>
                ) : (
                  <span className="viewer-unmarked"><ScanLine size={12} aria-hidden="true" /> CT only · model layers concealed</span>
                )}
                {isTruthRevealed && (
                  <>
                    <span><i className="legend-dot legend-dot--truth-pancreas" /> Truth pancreas</span>
                    <span><i className="legend-dot legend-dot--truth-lesion" /> Truth lesion</span>
                  </>
                )}
                <span className="viewer-instructions">
                  {reviewMode === '3d' ? 'Drag to rotate · scroll to zoom' : 'Scroll slices · drag crosshair to synchronize planes'}
                </span>
              </div>
            </div>
          </section>

          <aside className="finding-panel">
            <section className="live-inference">
              <div className="panel-title"><Radio size={15} aria-hidden="true" /><span>Live inference</span></div>
              {!isCuratedCase && (
                <div className="reveal-progress" aria-label={`Progressive reveal, stage ${revealStage} of 3`}>
                  {[
                    ['01', 'Unmarked'],
                    ['02', 'Prediction'],
                    ['03', 'Truth'],
                  ].map(([number, label], index) => {
                    const stage = index + 1
                    const state = revealStage === stage ? 'active' : revealStage > stage ? 'complete' : 'pending'
                    return (
                      <div className={`reveal-progress__step reveal-progress__step--${state}`} key={number}>
                        <span>{state === 'complete' ? <Check size={11} aria-hidden="true" /> : number}</span>
                        <small>{label}</small>
                      </div>
                    )
                  })}
                </div>
              )}
              <div className="scan-analyzer">
                <label>
                  <span className="sr-only">Select a scan to analyze</span>
                  <select
                    value={caseId || ''}
                    onChange={(event) => selectScan(event.target.value)}
                    aria-label="Scan picker"
                  >
                    {scanOptions.map((option) => (
                      <option value={option.caseId} key={option.caseId}>
                        {formatCaseId(option.caseId)} · {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="analyze-button"
                  type="button"
                  onClick={analyzeScan}
                  disabled={!caseId || isAnalyzing}
                >
                  {isAnalyzing
                    ? <LoaderCircle size={15} className="spin" aria-hidden="true" />
                    : <Activity size={15} aria-hidden="true" />}
                  {isAnalyzing ? 'Analyzing' : 'Analyze scan'}
                </button>
              </div>
              {endpointStatus === 'offline' && !isAnalyzing && (
                <p className="endpoint-note endpoint-note--offline" role="status">
                  <WifiOff size={13} aria-hidden="true" />
                  {isCuratedCase
                    ? 'endpoint offline — showing cached result'
                    : 'endpoint offline — live analysis unavailable'}
                </p>
              )}
              {isAnalyzing && (
                <div className="inference-loading" role="status" aria-live="polite">
                  <LoaderCircle size={18} className="spin" aria-hidden="true" />
                  <span>
                    <strong>Scoring local scan</strong>
                    <small>Running the whole-box model…</small>
                  </span>
                </div>
              )}
              {!isCuratedCase && revealStage > 1 && !isAnalyzing && (
                <button className="reset-scan-button" type="button" onClick={resetUnmarkedScan}>
                  <RotateCcw size={13} aria-hidden="true" /> Reset / new scan
                </button>
              )}
            </section>

            {!isCuratedCase && !hasLiveResult ? (
              <section className={`unmarked-finding${isAnalyzing ? ' unmarked-finding--loading' : ''}`}>
                <span className="unmarked-badge"><ScanLine size={12} aria-hidden="true" /> Unmarked scan</span>
                <div className="unmarked-finding__icon"><Crosshair size={24} aria-hidden="true" /></div>
                <h2>{isAnalyzing ? 'Analyzing clean CT…' : 'Ready for model analysis'}</h2>
                <p>
                  {isAnalyzing
                    ? 'The CT remains unmarked while the live endpoint computes its score.'
                    : 'No prediction or reference contour is visible. Select Analyze scan to reveal the model proposal.'}
                </p>
                <span className="unmarked-finding__rule">CT only · no hidden ground-truth view</span>
              </section>
            ) : (
              <>
                <div className="finding-heading">
                  <div className="finding-badges">
                    <span className="proposal-badge"><Activity size={13} aria-hidden="true" /> Model proposal</span>
                    <span className={`result-source-badge${hasLiveResult ? ' result-source-badge--live' : ''}`}>
                      {hasLiveResult ? <Radio size={12} aria-hidden="true" /> : <Database size={12} aria-hidden="true" />}
                      {hasLiveResult
                        ? isCuratedCase
                          ? `Live · scored ${currentLive.scoredAt}`
                          : `Live · scored ${currentLive.scoredAt} · ${currentLive.result.inference_seconds.toFixed(1)}s`
                        : 'Precomputed'}
                    </span>
                  </div>
                  <h2>{findingHasLesion ? 'Possible finding' : 'No finding flagged'}</h2>
                  <p>
                    {findingHasLesion
                      ? 'Review the highlighted region within the pancreas in every available view.'
                      : 'The current score did not retain a possible-lesion region.'}
                  </p>
                </div>

                <div className={`measurement-list${isAnalyzing ? ' measurement-list--loading' : ''}`}>
                  <div><span>CADe flag</span><strong>{findingHasLesion ? 'Possible lesion' : 'Not flagged'}</strong></div>
                  <div><span>Approx. diameter</span><strong>{approxDiameterMm(findingVolumeMm3)} mm</strong></div>
                  <div><span>Predicted volume</span><strong>{(findingVolumeMm3 / 1000).toFixed(2)} cm³</strong></div>
                  <div><span>Confidence</span><strong>{Math.round(findingConfidence * 100)}%</strong></div>
                  <div><span>Location</span><strong>Pancreatic region</strong></div>
                  {hasLiveResult && (
                    <div className="inference-time">
                      <span>Inference</span>
                      <strong>scored in {currentLive.result.inference_seconds.toFixed(1)}s</strong>
                    </div>
                  )}
                  {hasLiveResult && (
                    <p className="live-viewer-note">Live measurements · prepared model contour revealed in the viewer.</p>
                  )}
                </div>
              </>
            )}

            {!isCuratedCase && hasLiveResult && !isTruthRevealed && (
              <section className="truth-reveal-cta">
                <div className="truth-reveal-cta__icon"><BookOpen size={20} aria-hidden="true" /></div>
                <span className="eyebrow">Stage 3 is ready</span>
                <h2>Put the prediction to the test.</h2>
                <p>
                  Reveal the independent reference contours beside the model proposal in the same
                  synchronized 2D and 3D views.
                </p>
                <button className="reveal-truth-button" type="button" onClick={revealSourceOfTruth}>
                  <Microscope size={16} aria-hidden="true" /> Reveal source of truth
                  <ChevronRight size={15} aria-hidden="true" />
                </button>
              </section>
            )}

            {isTruthRevealed && (
              <section
                className="truth-payoff"
                aria-label={`Overlap with source of truth — pancreas Dice ${overlapPancreas?.toFixed(3)}, lesion Dice ${overlapLesion?.toFixed(3)}`}
              >
                <div className="truth-payoff__heading">
                  <span className="truth-payoff__icon"><ShieldCheck size={18} aria-hidden="true" /></span>
                  <div>
                    <span className="eyebrow">Stage 3 · Scientific payoff</span>
                    <h2>Overlap with source of truth</h2>
                  </div>
                </div>
                <div className="truth-payoff__metrics">
                  <div>
                    <span><i className="legend-dot legend-dot--truth-pancreas" /> Pancreas Dice</span>
                    <strong>{overlapPancreas?.toFixed(3) ?? '—'}</strong>
                  </div>
                  <div>
                    <span><i className="legend-dot legend-dot--truth-lesion" /> Lesion Dice</span>
                    <strong>{overlapLesion?.toFixed(3) ?? '—'}</strong>
                  </div>
                </div>
                <p className="truth-payoff__summary">
                  Prediction remains teal/red. Source of truth is now overlaid in blue/amber so
                  agreement and boundary error are visible together.
                </p>
              </section>
            )}

            <section className="panel-section">
              <div className="panel-title"><Layers3 size={15} aria-hidden="true" /><span>Visible layers</span></div>
              {showModelOverlay ? (
                <>
                  <LayerSwitch
                    checked={showPancreas}
                    onChange={(event) => setShowPancreas(event.target.checked)}
                    label="Pancreas"
                    color="pancreas"
                  />
                  <LayerSwitch
                    checked={showLesion}
                    onChange={(event) => setShowLesion(event.target.checked)}
                    label="Possible lesion"
                    color="lesion"
                  />
                  <label className="range-control">
                    <span>Overlay opacity <strong>{Math.round(overlayOpacity * 100)}%</strong></span>
                    <input
                      type="range"
                      min="0.1"
                      max="1"
                      step="0.05"
                      value={overlayOpacity}
                      onChange={(event) => setOverlayOpacity(Number(event.target.value))}
                    />
                  </label>
                </>
              ) : (
                <p className="layers-locked"><ScanLine size={13} aria-hidden="true" /> Model layers unlock after a successful live analysis.</p>
              )}
            </section>

            <section className="panel-section">
              <div className="panel-title"><SlidersHorizontal size={15} aria-hidden="true" /><span>View controls</span></div>
              <label className="layer-switch">
                <span className="control-icon"><ScanLine size={14} aria-hidden="true" /></span>
                <span>Full abdominal CT</span>
                <input
                  type="checkbox"
                  checked={showFull}
                  disabled={!currentCase.files.ct_full}
                  onChange={(event) => setShowFull(event.target.checked)}
                />
                <span className="switch-track" aria-hidden="true"><span /></span>
              </label>
              {reviewMode === '3d' && (
                <>
                  <label className="range-control">
                    <span>CT volume opacity <strong>{Math.round(ctOpacity * 100)}%</strong></span>
                    <input
                      type="range"
                      min="0"
                      max="0.75"
                      step="0.05"
                      value={ctOpacity}
                      onChange={(event) => setCtOpacity(Number(event.target.value))}
                    />
                  </label>
                  <label className="layer-switch">
                    <span className="control-icon"><Crosshair size={14} aria-hidden="true" /></span>
                    <span>Cut away CT</span>
                    <input
                      type="checkbox"
                      checked={clipEnabled}
                      onChange={(event) => setClipEnabled(event.target.checked)}
                    />
                    <span className="switch-track" aria-hidden="true"><span /></span>
                  </label>
                  {clipEnabled && (
                    <label className="range-control">
                      <span>CT cut depth <strong>{clipDepth.toFixed(2)}</strong></span>
                      <input
                        type="range"
                        min="-0.5"
                        max="0.5"
                        step="0.01"
                        value={clipDepth}
                        onChange={(event) => setClipDepth(Number(event.target.value))}
                      />
                    </label>
                  )}
                </>
              )}
            </section>

            <section className="review-actions">
              <div className="review-actions__row">
                <button className="primary-button" onClick={() => setReviewStatus('reviewed')}>
                  <Check size={16} aria-hidden="true" /> Mark reviewed
                </button>
                <button className="secondary-button" onClick={() => setReviewStatus('discussion')}>
                  <MessageSquareWarning size={16} aria-hidden="true" /> Discuss
                </button>
              </div>
              {showModelOverlay && (
                <a className="export-button" href={`${BASE}/${currentCase.files.pred}`} download>
                  <Download size={16} aria-hidden="true" /> Export predicted mask
                </a>
              )}
              {isCuratedCase && (
                <button className="comparison-link" onClick={() => setActiveTab('comparison')}>
                  Compare with source of truth <ChevronRight size={15} aria-hidden="true" />
                </button>
              )}
            </section>
          </aside>
        </main>
      )}

      {activeTab === 'comparison' && currentCase && isCuratedCase && (
        <main className="comparison-page">
          <section className="comparison-header">
            <div>
              <span className="eyebrow">Validation mode · source of truth visible</span>
              <h1>Prediction, evidence, and error—side by side.</h1>
              <p>
                The same prepared scan is shown three ways so the audience can inspect what the
                model captured, what it missed, and where it predicted too much.
              </p>
            </div>
            <div className="comparison-controls">
              <label>
                <span>Case</span>
                <select value={caseId} onChange={(event) => setCaseId(event.target.value)}>
                  {curatedCaseIds.map((id) => <option value={id} key={id}>{formatCaseId(id)} · {CASE_PROFILES[id]?.label}</option>)}
                </select>
              </label>
              <div className="segmented-control" aria-label="Scientific comparison view">
                <button className={comparisonMode === '2d' ? 'active' : ''} onClick={() => setComparisonMode('2d')}>Three planes</button>
                <button className={comparisonMode === '3d' ? 'active' : ''} onClick={() => setComparisonMode('3d')}>3D surfaces</button>
              </div>
            </div>
          </section>

          <section className="evidence-strip">
            <div>
              <span>Validation outcome</span>
              <strong>{currentCase.gt_has_lesion ? 'True positive' : 'False positive'}</strong>
            </div>
            <div>
              <span>Pancreas Dice</span>
              <strong>{currentCase.dice_pancreas.toFixed(3)}</strong>
            </div>
            <div>
              <span>Lesion Dice</span>
              <strong>{currentCase.dice_lesion.toFixed(3)}</strong>
            </div>
            <div>
              <span>Predicted lesion</span>
              <strong>{(currentCase.lesion_volume_mm3 / 1000).toFixed(2)} cm³</strong>
            </div>
          </section>

          <section className="comparison-grid">
            <article className="comparison-view">
              <header>
                <div>
                  <span className="view-number">01</span>
                  <h2>Model prediction</h2>
                </div>
                <span className="view-badge">Proposal</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`pred-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['pred']}
                  mode={comparisonMode}
                  overlayOpacity={0.72}
                  ctOpacity={0.1}
                  compact
                  label={`${formatCaseId(caseId)} model prediction`}
                />
              </ViewerSuspense>
              <footer>
                <span><i className="legend-dot legend-dot--pancreas" /> Predicted pancreas</span>
                <span><i className="legend-dot legend-dot--lesion" /> Predicted lesion</span>
              </footer>
            </article>

            <article className="comparison-view comparison-view--truth">
              <header>
                <div>
                  <span className="view-number">02</span>
                  <h2>Source of truth</h2>
                </div>
                <span className="view-badge view-badge--truth"><BookOpen size={12} aria-hidden="true" /> Reference</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`gt-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['gt']}
                  mode={comparisonMode}
                  overlayOpacity={0.72}
                  ctOpacity={0.1}
                  compact
                  label={`${formatCaseId(caseId)} source-of-truth segmentation`}
                />
              </ViewerSuspense>
              <footer>
                <span><i className="legend-dot legend-dot--truth-pancreas" /> Reference pancreas</span>
                <span><i className="legend-dot legend-dot--truth-lesion" /> Reference lesion</span>
              </footer>
            </article>

            <article className="comparison-view comparison-view--overlay">
              <header>
                <div>
                  <span className="view-number">03</span>
                  <h2>Combined overlay</h2>
                </div>
                <span className="view-badge view-badge--analysis">Analysis</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`both-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['gt', 'pred']}
                  mode={comparisonMode}
                  overlayOpacity={0.6}
                  ctOpacity={0.08}
                  compact
                  label={`${formatCaseId(caseId)} prediction and source-of-truth overlay`}
                />
              </ViewerSuspense>
              <footer>
                <span>Prediction + source of truth</span>
                <span>Inspect boundary agreement</span>
              </footer>
            </article>
          </section>

          <section className="analysis-section">
            <article className="analysis-narrative">
              <span className={`analysis-icon analysis-icon--${currentProfile.tone}`}>
                {currentCase.gt_has_lesion
                  ? <BadgeCheck size={20} aria-hidden="true" />
                  : <CircleAlert size={20} aria-hidden="true" />}
              </span>
              <div>
                <span className="eyebrow">What this case demonstrates</span>
                <h2>{currentProfile.interpretation}</h2>
                <p>
                  The overlays are intentionally shown without hiding disagreement. This is a scientific
                  comparison of a saved model result—not a claim of diagnostic reliability.
                </p>
              </div>
            </article>
            <div className="analysis-table">
              <div className="analysis-row analysis-row--header">
                <span>Structure</span><span>What worked</span><span>Where it falls short</span>
              </div>
              <div className="analysis-row">
                <strong>Pancreas</strong>
                <span>{currentProfile.strength}</span>
                <span>Small boundary disagreements remain visible in the combined view.</span>
              </div>
              <div className="analysis-row">
                <strong>Lesion</strong>
                <span>{currentCase.gt_has_lesion ? 'Correct region identified.' : 'No matching reference lesion is present.'}</span>
                <span>{currentProfile.limitation}</span>
              </div>
            </div>
          </section>
        </main>
      )}

      {showAbout && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowAbout(false)}>
          <section className="about-modal" role="dialog" aria-modal="true" aria-labelledby="about-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowAbout(false)} aria-label="Close about panel"><X size={18} /></button>
            <span className="brand-mark brand-mark--large"><ScanLine size={24} aria-hidden="true" /></span>
            <span className="eyebrow">About this interface</span>
            <h2 id="about-title">A transparent segmentation demonstration.</h2>
            <p>
              PanTS Review presents pancreas and lesion segmentations from a five-week machine-learning
              project. It is designed to make both model strengths and errors inspectable.
            </p>
            <div className="about-provenance">
              <Activity size={17} aria-hidden="true" />
              <div>
                <strong>Model provenance</strong>
                <code>Model: pancreas-lesion-segmenter v1 · checkpoint step 18000</code>
              </div>
            </div>
            <div className="about-points">
              <div><Radio size={17} aria-hidden="true" /><span><strong>Data freshness</strong>Predictions are computed live by a deployed FastAPI endpoint when available, with cached results as fallback. Live results show their scoring time and inference duration in the finding panel.</span></div>
              <div><Database size={17} aria-hidden="true" /><span><strong>Cached results</strong>Saved NIfTI volumes, surface meshes, and measurements keep every prepared case reviewable when the inference endpoint is offline.</span></div>
              <div><Microscope size={17} aria-hidden="true" /><span><strong>Scientific transparency</strong>Source-of-truth contours and case metrics live in a dedicated validation surface.</span></div>
              <div><ShieldCheck size={17} aria-hidden="true" /><span><strong>Research scope</strong>This is an annotation-assist and segmentation project, not a diagnostic system.</span></div>
            </div>
            <button className="primary-button" onClick={() => setShowAbout(false)}>Return to workspace</button>
          </section>
        </div>
      )}
    </div>
  )
}
