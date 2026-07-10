import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../lib/api";
import { useAppStore } from "../store/useAppStore";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const setAuth = useAppStore((s) => s.setAuth);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      setAuth(res.data.access_token, res.data.role, res.data.full_name);
      navigate("/");
    } catch {
      setError("E-Mail oder Passwort falsch.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-blueprint-900">
      {/* Linke Spalte: Marke / Kontext, blaupausenartige Textur */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-blueprint text-paper flex-col justify-between p-12 blueprint-grid">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-conduit-500 flex items-center justify-center font-display font-bold text-sm">
            W
          </div>
          <span className="font-display font-semibold text-lg tracking-tight">WieNet</span>
        </div>

        <div className="max-w-md survey-marks pl-1">
          <p className="text-xs uppercase tracking-widest text-signal-300 font-medium mb-3">
            Tiefbau- &amp; Glasfaser-Infrastruktur
          </p>
          <h1 className="font-display text-3xl font-semibold leading-tight mb-4">
            Jede Trasse, jedes Rohr, jede Faser — an ihrem realen Ort.
          </h1>
          <p className="text-sm text-ink-100/70 leading-relaxed">
            Kartenbasierte Verwaltung von Trassen, Rohrbelegung, Netzschema und
            Bauabschnitten, organisiert nach Gebiet, Cluster und Projekt.
          </p>
        </div>

        <p className="text-xs text-ink-100/40 font-data">wienet · self-hosted</p>
      </div>

      {/* Rechte Spalte: Anmeldung */}
      <div className="flex-1 flex items-center justify-center bg-paper px-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-md bg-conduit-500 flex items-center justify-center text-white font-display font-bold text-sm">
              W
            </div>
            <span className="font-display font-semibold text-lg text-ink-900">WieNet</span>
          </div>

          <h2 className="font-display text-xl font-semibold text-ink-900 mb-1">Anmelden</h2>
          <p className="text-sm text-ink-400 mb-6">Zugang zur Infrastrukturplattform.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium uppercase tracking-wide text-ink-400">E-Mail</label>
              <input
                type="email" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-md border border-ink-100 bg-white px-3 py-2.5 text-sm text-ink-900 placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 transition"
              />
            </div>
            <div>
              <label className="text-xs font-medium uppercase tracking-wide text-ink-400">Passwort</label>
              <input
                type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 w-full rounded-md border border-ink-100 bg-white px-3 py-2.5 text-sm text-ink-900 focus:outline-none focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 transition"
              />
            </div>
            {error && (
              <p className="text-sm text-conduit-700 bg-conduit-50 border border-conduit-100 rounded-md px-3 py-2 animate-shake">{error}</p>
            )}
            <button
              type="submit" disabled={loading}
              className="w-full bg-ink-900 hover:bg-blueprint text-white rounded-md py-2.5 text-sm font-medium transition disabled:opacity-60"
            >
              {loading ? "Anmelden…" : "Anmelden"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
