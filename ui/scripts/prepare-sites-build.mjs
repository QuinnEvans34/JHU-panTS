import { copyFile, mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = process.cwd()
const serverDir = resolve(root, 'dist', 'server')
const metadataDir = resolve(root, 'dist', '.openai')

await mkdir(serverDir, { recursive: true })
await mkdir(metadataDir, { recursive: true })

await writeFile(
  resolve(serverDir, 'index.js'),
  `const worker = {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request)
    if (response.status !== 404) return response

    const url = new URL(request.url)
    url.pathname = '/index.html'
    return env.ASSETS.fetch(new Request(url, request))
  },
}

export default worker
`,
)

await copyFile(
  resolve(root, '.openai', 'hosting.json'),
  resolve(metadataDir, 'hosting.json'),
)
