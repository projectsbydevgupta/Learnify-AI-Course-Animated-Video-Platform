import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: "/login",
        destination: "/sign-in",
        permanent: false,
      },
      {
        source: "/signup",
        destination: "/sign-up",
        permanent: false,
      },
      {
        source: "/register",
        destination: "/sign-up",
        permanent: false,
      },
      {
        source: "/dashboard/generate_course",
        destination: "/dashboard/generate-course",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
