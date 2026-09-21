import { afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })
// Unit/component tests must never fetch demo scans or call an inference service.
beforeEach(() => vi.stubGlobal('fetch', () => { throw new Error('Network forbidden in synthetic UI tests') }))
