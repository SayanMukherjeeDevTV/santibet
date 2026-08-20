/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
  async rewrites() {
    let apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) {
      apiUrl = process.env.NODE_ENV === 'production' 
        ? 'https://santibet-api.onrender.com'
        : 'http://127.0.0.1:8000';
    }
    if (!apiUrl.startsWith('http')) {
      apiUrl = `https://${apiUrl}`;
    }
    apiUrl = apiUrl.replace(/\/$/, '');
    
    return [
      {
        source: '/v1/:path*',
        destination: `${apiUrl}/v1/:path*`,
      },
    ]
  },
};

module.exports = nextConfig;
