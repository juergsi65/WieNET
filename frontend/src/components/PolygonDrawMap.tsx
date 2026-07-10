import { useEffect, useRef, useState } from "react";
import maplibregl, { Map as MLMap } from "maplibre-gl";
import * as turf from "@turf/turf";

interface Props {
  onComplete: (geojson: any, flaecheM2: number, umfangM: number) => void;
  center?: [number, number];
}

export default function PolygonDrawMap({ onComplete, center = [14.2858, 48.3069] }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const [points, setPoints] = useState<[number, number][]>([]);
  const [flaeche, setFlaeche] = useState(0);
  const [umfang, setUmfang] = useState(0);
  const pointsRef = useRef<[number, number][]>([]);
  pointsRef.current = points;

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256 },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center, zoom: 15,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("draw-polygon", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "draw-fill", type: "fill", source: "draw-polygon",
        paint: { "fill-color": "#f59e0b", "fill-opacity": 0.25 },
      });
      map.addLayer({
        id: "draw-line", type: "line", source: "draw-polygon",
        paint: { "line-color": "#f59e0b", "line-width": 2 },
      });
      map.addLayer({
        id: "draw-points", type: "circle", source: "draw-polygon",
        filter: ["==", "$type", "Point"],
        paint: { "circle-radius": 5, "circle-color": "#f59e0b", "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
      });
    });

    map.on("click", (e) => {
      const next: [number, number][] = [...pointsRef.current, [e.lngLat.lng, e.lngLat.lat]];
      setPoints(next);
      updateSource(map, next);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateSource(map: MLMap, pts: [number, number][]) {
    const features: any[] = pts.map((p) => ({ type: "Feature", geometry: { type: "Point", coordinates: p }, properties: {} }));
    if (pts.length >= 2) {
      features.push({ type: "Feature", geometry: { type: "LineString", coordinates: pts }, properties: {} });
    }
    if (pts.length >= 3) {
      const ring = [...pts, pts[0]];
      features.push({ type: "Feature", geometry: { type: "Polygon", coordinates: [ring] }, properties: {} });
      const poly = turf.polygon([ring]);
      setFlaeche(turf.area(poly));
      setUmfang(turf.length(poly, { units: "meters" }));
    } else {
      setFlaeche(0);
      setUmfang(0);
    }
    (map.getSource("draw-polygon") as maplibregl.GeoJSONSource)?.setData({ type: "FeatureCollection", features });
  }

  function handleUndo() {
    const next = points.slice(0, -1);
    setPoints(next);
    if (mapRef.current) updateSource(mapRef.current, next);
  }

  function handleReset() {
    setPoints([]);
    if (mapRef.current) updateSource(mapRef.current, []);
  }

  function handleFinish() {
    if (points.length < 3) return;
    const ring = [...points, points[0]];
    const geojson = { type: "Polygon", coordinates: [ring] };
    onComplete(geojson, flaeche, umfang);
  }

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      <div className="absolute top-3 left-3 bg-white/95 dark:bg-slate-800/95 rounded-lg shadow-lg p-3 text-sm space-y-2 w-56">
        <p className="font-medium text-slate-700 dark:text-slate-200">Polygon zeichnen</p>
        <p className="text-xs text-slate-500">Klicken zum Setzen von Punkten. Mindestens 3 Punkte nötig.</p>
        <div className="text-xs space-y-0.5">
          <p>Fläche: <strong>{(flaeche / 10000).toFixed(3)} ha</strong></p>
          <p>Umfang: <strong>{umfang.toFixed(0)} m</strong></p>
          <p>Punkte: <strong>{points.length}</strong></p>
        </div>
        <div className="flex gap-1.5">
          <button onClick={handleUndo} disabled={points.length === 0}
                  className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-md py-1.5 text-xs disabled:opacity-40">
            Rückgängig
          </button>
          <button onClick={handleReset} disabled={points.length === 0}
                  className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-md py-1.5 text-xs disabled:opacity-40">
            Zurücksetzen
          </button>
        </div>
        <button onClick={handleFinish} disabled={points.length < 3}
                className="w-full bg-brand-600 text-white rounded-md py-1.5 text-xs font-medium disabled:opacity-40">
          Polygon übernehmen
        </button>
      </div>
    </div>
  );
}
