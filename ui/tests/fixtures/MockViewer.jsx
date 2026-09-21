import React from 'react'
export default function MockViewer({ mode, activePlane, visibleSources, resetToken }) {
  return <div role="status" aria-label="Synthetic viewer stub">
    SYNTHETIC UI FIXTURE — NO CT / NO WEBGL
    <pre>{JSON.stringify({ mode, activePlane, visibleSources, resetToken })}</pre>
  </div>
}
