import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import type { ServerResponse } from "node:http";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const API_URL = "http://127.0.0.1:8000";
const VENV_PYTHON = ".venv/bin/python";

/**
 * Start the local Python API (api/roll.py) alongside the Vite dev server,
 * mirroring how Vercel serves /api in production.
 */
function pythonApi(): Plugin {
  let proc: ChildProcess | undefined;
  return {
    name: "python-api",
    apply: "serve",
    configureServer() {
      // vercel dev serves /api itself, so only spawn under plain `npm run dev`
      if (process.env.VERCEL || process.env.VERCEL_ENV || process.env.NOW_REGION) return;
      const python = existsSync(VENV_PYTHON) ? VENV_PYTHON : "python3";
      proc = spawn(python, ["api/roll.py"], { stdio: "inherit" });
      proc.on("error", (e) => console.error(`[api] failed to start ${python}: ${e.message}`));
      const stop = () => proc?.kill();
      process.once("exit", stop);
      process.once("SIGINT", () => {
        stop();
        process.exit();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), pythonApi()],
  server: {
    proxy: {
      "/api": {
        target: API_URL,
        configure: (proxy) => {
          proxy.on("error", (err, _req, res) => {
            const out = res as ServerResponse;
            if (out.headersSent) return;
            out.writeHead(502, { "Content-Type": "application/json" });
            out.end(
              JSON.stringify({
                error: `Local API at ${API_URL} is unreachable (${err.message}). Check the terminal for [api] errors.`,
              }),
            );
          });
        },
      },
    },
  },
});
