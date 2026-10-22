import { useState, type ChangeEvent, type DragEvent } from "react";

type Roll = {
  kind: string;
  side: string;
  territory: string;
  owner: string;
};

type RollResult = {
  game: string;
  round: number | null;
  rolls: Roll[];
};

const PLACEHOLDER_ROLLS: Roll[] = [
  { kind: "Infrastructure", side: "Axis", territory: "—", owner: "" },
  { kind: "Infrastructure", side: "Allied", territory: "—", owner: "" },
  { kind: "Partisans", side: "Axis", territory: "—", owner: "" },
  { kind: "Partisans", side: "Allied", territory: "—", owner: "" },
];

class RollError extends Error {
  constructor(message: string, readonly detail: string) {
    super(message);
  }
}

async function rollSave(file: File): Promise<RollResult> {
  const res = await fetch("/api/roll", {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: file,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const short = res.status === 422 ? "Not a readable save" : `Server error (${res.status})`;
    throw new RollError(short, data?.error ?? short);
  }
  return data as RollResult;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<RollResult | null>(null);
  const [error, setError] = useState<{ message: string; detail: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);

  async function run(f: File) {
    setFile(f);
    setLoading(true);
    setError(null);
    try {
      setResult(await rollSave(f));
    } catch (e) {
      setResult(null);
      const message = e instanceof Error ? e.message : String(e);
      setError({ message, detail: e instanceof RollError ? e.detail : message });
    } finally {
      setLoading(false);
    }
  }

  function onPick(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) run(f);
    e.target.value = "";
  }

  function onDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) run(f);
  }

  const rolls = result?.rolls ?? PLACEHOLDER_ROLLS;
  const status = loading ? "Rolling…" : error?.message ?? (result ? null : "No save loaded");

  return (
    <main>
      <header>
        <h1>EBGB TripleA Helper</h1>
      </header>

      <label
        className={`drop${dragging ? " dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input type="file" accept=".tsvg" onChange={onPick} />
        <span className="drop-main" title={file?.name}>
          {file ? file.name : "Upload file"}
        </span>
      </label>

      <section className={`results${loading ? " loading" : ""}`}>
        <div className="results-head">
          <div className="round">Round {result?.round ?? "—"}</div>
          <div className={`status${error ? " error" : ""}`} title={error?.detail}>
            {status}
          </div>
        </div>
        <ol>
          {rolls.map((r) => (
            <li key={`${r.kind}-${r.side}`}>
              <span className={`tag ${r.side.toLowerCase()}`}>
                {r.kind} · {r.side}
              </span>
              <span className="territory" title={r.territory}>
                {r.territory}
              </span>
              <span className="owner">
                {r.owner ? `held by ${r.owner.replace("_", " ")}` : ""}
              </span>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
