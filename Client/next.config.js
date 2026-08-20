/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
  async rewrites() {
    const isProd = process.env.NODE_ENV === 'production';
    const apiUrl = isProd ? 'https://santibet-api.onrender.com' : 'http://127.0.0.1:8000';
    
    return [
      {
        source: '/v1/:path*',
        destination: `${apiUrl}/v1/:path*`,
      },
    ]
  },
};

module.exports = nextConfig;
