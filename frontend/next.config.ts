import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Separate build state when comparing the integration checkout side by side.
  distDir: process.env.MAYA_ISOLATED_PREVIEW === "true" ? ".next-integration" : ".next",
  // The documented local URL uses 127.0.0.1. Next.js otherwise blocks its
  // development client resources because the dev server advertises localhost.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
