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
  MessageSquareWarning,
  Microscope,
  RotateCcw,
  ScanLine,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  X,
} from 'lucide-react'
const NiivueViewer = lazy(() => import('./components/NiivueViewer.jsx'))

const BASE = '/cases'
const STORAGE_KEY = 'pants-review-status-v1'

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
  const [clipEnabled, setClipEnabled] = useState(false)
  const [clipDepth, setClipDepth] = useState(0)
  const [resetToken, setResetToken] = useState(0)
  const [showAbout, setShowAbout] = useState(false)

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

  const currentCase = caseId ? cases[caseId] : null
  const currentProfile = CASE_PROFILES[caseId] || {
    label: 'Prepared case',
    eyebrow: 'Model result',
    summary: 'A prepared segmentation result for scientific review.',
    interpretation: 'Review the model output against the source-of-truth contours.',
    strength: 'Pancreas and lesion output are available for inspection.',
    limitation: 'This case has not been assigned a presentation narrative.',
    tone: 'neutral',
  }

  function openCase(id, destination = 'review') {
    setCaseId(id)
    setActiveTab(destination)
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
          <button className={activeTab === 'review' ? 'active' : ''} onClick={() => setActiveTab('review')} disabled={!currentCase}>
            Review workspace
          </button>
          <button className={activeTab === 'comparison' ? 'active' : ''} onClick={() => setActiveTab('comparison')} disabled={!currentCase}>
            Scientific comparison
          </button>
        </nav>

        <div className="header-actions">
          <span className="prepared-badge"><Database size={13} aria-hidden="true" /> Precomputed cases</span>
          <button className="icon-button" onClick={() => setShowAbout(true)} aria-label="About this research interface">
            <Info size={18} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="research-notice">
        <ShieldCheck size={14} aria-hidden="true" />
        <span><strong>Research use only.</strong> Segmentation and annotation-assist interface—not a diagnosis.</span>
        <span className="notice-detail">Every result shown was computed before the demonstration.</span>
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
              <div><strong>{caseIds.length}</strong><span>prepared cases</span></div>
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
              {caseIds.map((id) => {
                const item = cases[id]
                const profile = CASE_PROFILES[id] || currentProfile
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

      {activeTab === 'review' && currentCase && (
        <main className="workspace">
          <aside className="case-rail" aria-label="Prepared cases">
            <div className="rail-heading">
              <span className="eyebrow">Case queue</span>
              <strong>{caseIds.length} prepared</strong>
            </div>
            <div className="rail-list">
              {caseIds.map((id) => {
                const profile = CASE_PROFILES[id] || currentProfile
                return (
                  <button
                    key={id}
                    className={`rail-case ${id === caseId ? 'active' : ''}`}
                    onClick={() => setCaseId(id)}
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
            <button className="rail-comparison" onClick={() => setActiveTab('comparison')}>
              <Microscope size={16} aria-hidden="true" />
              Open scientific comparison
            </button>
          </aside>

          <section className="viewer-workspace">
            <header className="workspace-toolbar">
              <div>
                <span className="eyebrow">{currentProfile.eyebrow}</span>
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
                  sources={['pred']}
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
                  label={`${formatCaseId(caseId)} model prediction`}
                />
              </ViewerSuspense>
              <div className="viewer-legend">
                <span><i className="legend-dot legend-dot--pancreas" /> Model pancreas</span>
                <span><i className="legend-dot legend-dot--lesion" /> Model lesion</span>
                <span className="viewer-instructions">
                  {reviewMode === '3d' ? 'Drag to rotate · scroll to zoom' : 'Scroll slices · drag crosshair to synchronize planes'}
                </span>
              </div>
            </div>
          </section>

          <aside className="finding-panel">
            <div className="finding-heading">
              <span className="proposal-badge"><Activity size={13} aria-hidden="true" /> Model proposal</span>
              <h2>{currentCase.pred_has_lesion ? 'Possible finding' : 'No finding flagged'}</h2>
              <p>
                {currentCase.pred_has_lesion
                  ? 'Review the highlighted region within the pancreas in every available view.'
                  : 'No lesion contour was produced for this prepared case.'}
              </p>
            </div>

            <div className="measurement-list">
              <div><span>Approx. diameter</span><strong>{approxDiameterMm(currentCase.lesion_volume_mm3)} mm</strong></div>
              <div><span>Predicted volume</span><strong>{(currentCase.lesion_volume_mm3 / 1000).toFixed(2)} cm³</strong></div>
              <div><span>Location</span><strong>Pancreatic region</strong></div>
              <div><span>Model signal</span><strong>{modelSignal(currentCase.confidence)}</strong></div>
            </div>

            <section className="panel-section">
              <div className="panel-title"><Layers3 size={15} aria-hidden="true" /><span>Visible layers</span></div>
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
              <a className="export-button" href={`${BASE}/${currentCase.files.pred}`} download>
                <Download size={16} aria-hidden="true" /> Export predicted mask
              </a>
              <button className="comparison-link" onClick={() => setActiveTab('comparison')}>
                Compare with source of truth <ChevronRight size={15} aria-hidden="true" />
              </button>
            </section>
          </aside>
        </main>
      )}

      {activeTab === 'comparison' && currentCase && (
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
                  {caseIds.map((id) => <option value={id} key={id}>{formatCaseId(id)} · {CASE_PROFILES[id]?.label}</option>)}
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
              PanTS Review presents precomputed pancreas and lesion segmentations from a five-week
              machine-learning project. It is designed to make both model strengths and errors inspectable.
            </p>
            <div className="about-points">
              <div><Database size={17} aria-hidden="true" /><span><strong>Prepared results</strong>Cases load saved NIfTI volumes and surface meshes. Selecting a case does not run inference.</span></div>
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
