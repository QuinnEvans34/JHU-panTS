import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))

it('locks prediction and reference before analysis', async () => {
  render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.getByRole('button', { name: 'Model prediction' }).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Source of truth' }).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Original CT' }).getAttribute('aria-pressed')).toBe('true')
})

it('changes 2D/3D, toggles library, and resets after switching case', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  expect(screen.getByRole('button', { name: '3D', exact: true }).getAttribute('aria-pressed')).toBe('true')
  await user.click(screen.getByRole('button', { name: 'Collapse scan library' }))
  expect(screen.getByRole('main').classList.contains('review-workspace-v2--drawer-closed')).toBe(true)
  expect(screen.getByRole('button', { name: 'Open scan library' })).toBeTruthy()
  rerender(<ReviewWorkspace {...workspaceProps({ caseId: 'SYNTHETIC_B' })} />)
  await waitFor(() => expect(screen.getByRole('button', { name: '2D', exact: true }).getAttribute('aria-pressed')).toBe('true'))
  expect(screen.getByRole('main').classList.contains('review-workspace-v2--drawer-closed')).toBe(false)
})
