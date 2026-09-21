import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import ReviewWorkspace from '../../src/components/ReviewWorkspace.jsx'
import '../../src/index.css'
import { workspaceProps } from './workspace.js'

function Fixture() {
  const [caseId, setCaseId] = useState('SYNTHETIC_A')
  return <>
    <header>SYNTHETIC UI BASELINE — viewer stub, no patient data
      <button onClick={() => setCaseId(caseId === 'SYNTHETIC_A' ? 'SYNTHETIC_B' : 'SYNTHETIC_A')}>Switch synthetic case</button>
    </header>
    <ReviewWorkspace {...workspaceProps({ caseId })} />
  </>
}
createRoot(document.getElementById('root')).render(<Fixture />)
