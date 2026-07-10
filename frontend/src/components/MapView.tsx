import { useEffect, useRef } from "react";
import maplibregl, { Map as MLMap } from "maplibre-gl";
import { mapApi, adminClusterApi } from "../lib/api";
import { useAppStore } from "../store/useAppStore";

const STATUS_COLOR: Record<string, string> = {
  aktiv: "#16a34a",
  geplant: "#64748b",
  stillgelegt: "#94a3b8",
  gestoert: "#dc2626",
};

const NETZELEMENT_COLOR: Record<string, string> = {
  olt: "#7c3aed", pon: "#a855f7", splitter: "#f59e0b", pop: "#7c3aed",
  fcp: "#0ea5e9", verteiler: "#0ea5e9", muffe: "#eab308", schacht: "#334155",
  kasten: "#334155", hausanschluss: "#16a34a", gebaeude: "#94a3b8",
  technikstandort: "#7c3aed",
};

interface Props {
  onSelect: (typ: string, id: string) => void;
}

export default function MapView({ onSelect }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const activeLayers = useAppStore((s) => s.activeLayers);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap-Mitwirkende",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [14.2858, 48.3069],
      zoom: 15,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("clusters", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "clusters-fill", type: "fill", source: "clusters",
        paint: { "fill-color": ["get", "farbe"], "fill-opacity": 0.15 },
      });
      map.addLayer({
        id: "clusters-outline", type: "line", source: "clusters",
        paint: { "line-color": ["get", "farbe"], "line-width": 2, "line-dasharray": [3, 2] },
      });
      map.addLayer({
        id: "clusters-label", type: "symbol", source: "clusters",
        layout: { "text-field": ["get", "name"], "text-size": 11, "text-anchor": "center" },
        paint: { "text-color": "#334155", "text-halo-color": "#ffffff", "text-halo-width": 1.5 },
      });

      adminClusterApi.list({ with_geometry: true }).then((res) => {
        const features = res.data.map((c: any) => ({
          type: "Feature", geometry: c.geometrie,
          properties: { id: c.id, name: c.name, farbe: c.farbe, status: c.status },
        }));
        (map.getSource("clusters") as maplibregl.GeoJSONSource)?.setData({ type: "FeatureCollection", features });
      }).catch(() => {});

      const clusterPopup = new maplibregl.Popup({ closeButton: true });
      map.on("click", "clusters-fill", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        clusterPopup
          .setLngLat(e.lngLat)
          .setHTML(`<div style="font-size:13px"><strong>${f.properties!.name}</strong><br/>Status: ${f.properties!.status}<br/><a href="/admin/cluster/${f.properties!.id}" style="color:#0d80c2">Cluster-Dashboard öffnen →</a></div>`)
          .addTo(map);
      });
      map.on("mouseenter", "clusters-fill", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "clusters-fill", () => { map.getCanvas().style.cursor = ""; });

      map.addSource("trassen", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addSource("netzelemente", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

      // Trassen als Linien: gestrichelt=geplant, durchgezogen=aktiv, ausgegraut=stillgelegt
      map.addLayer({
        id: "trassen-linie",
        type: "line",
        source: "trassen",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": [
            "match", ["get", "status"],
            "aktiv", STATUS_COLOR.aktiv,
            "geplant", STATUS_COLOR.geplant,
            "stillgelegt", STATUS_COLOR.stillgelegt,
            "gestoert", STATUS_COLOR.gestoert,
            "#3b82f6",
          ],
          "line-width": 4,
          "line-dasharray": ["case", ["==", ["get", "status"], "geplant"], ["literal", [2, 2]], ["literal", [1, 0]]],
          "line-opacity": ["case", ["==", ["get", "status"], "stillgelegt"], 0.4, 0.9],
        },
      });

      // Netzelemente als Punkte, farbcodiert nach Typ, Radius nach Belegung
      map.addLayer({
        id: "netzelemente-punkte",
        type: "circle",
        source: "netzelemente",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 4, 18, 9],
          "circle-color": [
            "match", ["get", "typ"],
            "olt", NETZELEMENT_COLOR.olt, "pon", NETZELEMENT_COLOR.pon,
            "splitter", NETZELEMENT_COLOR.splitter, "fcp", NETZELEMENT_COLOR.fcp,
            "verteiler", NETZELEMENT_COLOR.verteiler, "muffe", NETZELEMENT_COLOR.muffe,
            "schacht", NETZELEMENT_COLOR.schacht, "hausanschluss", NETZELEMENT_COLOR.hausanschluss,
            "#334155",
          ],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      // Störungen rot hervorheben
      map.addLayer({
        id: "netzelemente-stoerung",
        type: "circle",
        source: "netzelemente",
        filter: ["==", ["get", "status"], "gestoert"],
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 8, 18, 14],
          "circle-color": "transparent",
          "circle-stroke-width": 3,
          "circle-stroke-color": "#dc2626",
        },
      });

      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });

      map.on("click", "trassen-linie", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        onSelect("trasse", f.properties!.id);
      });
      map.on("click", "netzelemente-punkte", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        onSelect(f.properties!.objekt_typ === "netzelement" ? f.properties!.typ : "netzelement", f.properties!.id);
      });

      ["trassen-linie", "netzelemente-punkte"].forEach((layer) => {
        map.on("mouseenter", layer, (e) => {
          map.getCanvas().style.cursor = "pointer";
          const f = e.features?.[0];
          if (!f) return;
          const props = f.properties!;
          const html = `<div style="font-size:13px"><strong>${props.name}</strong><br/>Status: ${props.status}${
            props.belegung_pct != null ? `<br/>Belegung: ${props.belegung_pct}%` : ""
          }</div>`;
          popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
        });
        map.on("mouseleave", layer, () => {
          map.getCanvas().style.cursor = "";
          popup.remove();
        });
      });

      loadData(map);
    });

    map.on("moveend", () => loadData(map));

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadData(map: MLMap) {
    const zoom = Math.round(map.getZoom());
    const b = map.getBounds();
    const bbox = `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`;
    try {
      const [trassenRes, netzRes] = await Promise.all([
        mapApi.trassen(zoom, bbox),
        mapApi.netzelemente(zoom, bbox),
      ]);
      const trassenSrc = map.getSource("trassen") as maplibregl.GeoJSONSource;
      const netzSrc = map.getSource("netzelemente") as maplibregl.GeoJSONSource;
      trassenSrc?.setData(trassenRes.data as any);
      netzSrc?.setData(netzRes.data as any);
    } catch (err) {
      console.error("Kartendaten konnten nicht geladen werden", err);
    }
  }

  // Layer-Sichtbarkeit je nach Sidebar-Auswahl aktualisieren
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("trassen-linie")) return;
    map.setLayoutProperty("trassen-linie", "visibility", activeLayers.trassen ? "visible" : "none");
  }, [activeLayers.trassen]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("clusters-fill")) return;
    const vis = activeLayers.cluster ? "visible" : "none";
    map.setLayoutProperty("clusters-fill", "visibility", vis);
    map.setLayoutProperty("clusters-outline", "visibility", vis);
    map.setLayoutProperty("clusters-label", "visibility", vis);
  }, [activeLayers.cluster]);

  return <div ref={mapContainer} className="w-full h-full" />;
}
