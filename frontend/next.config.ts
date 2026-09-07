import type { NextConfig } from 'next'

const apiTarget = process.env.NEXT_PUBLIC_API_URL || process.env.API_INTERNAL_URL || 'http://127.0.0.1:8000'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiTarget}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
