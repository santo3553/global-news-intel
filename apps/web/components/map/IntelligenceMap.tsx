"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { 
  Globe2, 
  Layers, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  MapPin, 
  Flame, 
  ShieldCheck, 
  Filter, 
  Maximize2,
  Compass,
  Radar,
  Radio,
  Satellite,
  Activity,
  Crosshair,
  SlidersHorizontal,
  Eye,
  Map as MapIcon,
  CircleDot
} from "lucide-react";
import { EventItem } from "@/lib/api";
import "maplibre-gl/dist/maplibre-gl.css";

export interface FocusedEventLocation {
  lng: number;
  lat: number;
  id?: string;
  title?: string;
  city?: string;
  country?: string;
  category?: string;
  location_confidence?: number;
}

interface IntelligenceMapProps {
  events: EventItem[];
  onSelectEvent: (eventId: string) => void;
  onBoundsChange?: (bbox: string, zoom: number) => void;
  selectedCategory?: string;
  onCategoryChange?: (category: string) => void;
  resetViewTrigger?: number;
  focusedEventCoords?: FocusedEventLocation | null;
}

const REGION_PRESETS = [
  { name: "Global", center: [10, 20], zoom: 1.5 },
  { name: "Central Asia & Caspian", center: [58, 42], zoom: 3.2 },
  { name: "Europe", center: [15, 50], zoom: 3.8 },
  { name: "Middle East", center: [45, 28], zoom: 4.0 },
  { name: "Asia-Pacific", center: [115, 20], zoom: 3.2 },
  { name: "Americas", center: [-85, 20], zoom: 2.8 },
  { name: "Africa", center: [20, 5], zoom: 3.2 },
];

/**
 * Calculates a realistic geographical impact buffer (km) based on event category and severity
 */
function getEventImpactRadiusKm(event: EventItem): number {
  const importance = event.importance_score || 5.0;
  switch (event.category) {
    case "natural_disaster":
      // Earthquakes, tsunamis, hurricanes have vast geographical shockwaves: 80 - 320 km
      return Math.round(Math.min(320, Math.max(75, importance * 34)));
    case "conflict":
    case "security":
      // Military operations, missile defense, drone strikes: 40 - 180 km
      return Math.round(Math.min(180, Math.max(40, (event.human_impact_score || importance) * 20)));
    case "politics":
      // Diplomatic pacts, border protocols, capital city jurisdictions: 25 - 80 km
      return Math.round(Math.min(80, Math.max(25, (event.political_impact_score || importance) * 9)));
    case "economy":
      // Trade corridors, shipping hubs, financial zones: 30 - 100 km
      return Math.round(Math.min(100, Math.max(30, (event.economic_impact_score || importance) * 11)));
    case "science":
      // Space observatories, research facilities, environmental preserves: 40 - 120 km
      return Math.round(Math.min(120, Math.max(40, importance * 13)));
    default:
      return Math.round(Math.min(140, Math.max(30, importance * 15)));
  }
}

/**
 * Generates geodesic circle coordinates (polygon) on the globe avoiding Mercator distortion
 */
function createGeodesicCircle(center: [number, number], radiusKm: number, points: number = 48): number[][] {
  const [lng, lat] = center;
  const coords: number[][] = [];
  const latRad = (lat * Math.PI) / 180;
  const deltaY = radiusKm / 110.574;
  const deltaX = radiusKm / (111.320 * Math.max(0.05, Math.cos(latRad)));

  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI);
    const x = deltaX * Math.cos(theta);
    const y = deltaY * Math.sin(theta);
    coords.push([Number((lng + x).toFixed(5)), Number((lat + y).toFixed(5))]);
  }
  coords.push(coords[0]); // close loop
  return coords;
}

/**
 * Formats decimal degrees to degrees-minutes-seconds (DMS) cardinal notation
 */
function formatDMS(deg: number, isLat: boolean): string {
  const absolute = Math.abs(deg);
  const degrees = Math.floor(absolute);
  const minutesNotTruncated = (absolute - degrees) * 60;
  const minutes = Math.floor(minutesNotTruncated);
  const seconds = Math.floor((minutesNotTruncated - minutes) * 60);
  const direction = isLat ? (deg >= 0 ? "N" : "S") : (deg >= 0 ? "E" : "W");
  return `${degrees}°${minutes}'${seconds}" ${direction}`;
}

export default function IntelligenceMap({
  events,
  onSelectEvent,
  onBoundsChange,
  selectedCategory = "all",
  onCategoryChange,
  resetViewTrigger,
  focusedEventCoords
}: IntelligenceMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const maplibreglRef = useRef<any>(null);
  const focusedMarkerRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1.8);
  const [activeCategory, setActiveCategory] = useState<string>(selectedCategory);
  const [activeBasemap, setActiveBasemap] = useState<"dark" | "satellite" | "streets">("dark");
  const [activeViewMode, setActiveViewMode] = useState<"markers" | "heatmap" | "impact_zones">("markers");
  const [showImpactZones, setShowImpactZones] = useState<boolean>(true);
  const [cursorCoords, setCursorCoords] = useState<{ lng: number; lat: number } | null>(null);

  // Convert events to GeoJSON Points
  const toGeoJSON = useCallback((eventsList: EventItem[]) => {
    const filtered = activeCategory === "all" 
      ? eventsList 
      : eventsList.filter(e => e.category === activeCategory);

    return {
      type: "FeatureCollection" as const,
      features: filtered.map(e => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [e.longitude, e.latitude]
        },
        properties: {
          id: e.id,
          canonical_title: e.canonical_title,
          category: e.category,
          importance: e.importance_score,
          confidence: e.confidence_score,
          velocity: e.development_velocity_score,
          location_confidence: e.location_confidence,
          city: e.city || "",
          country: e.country || "",
          articles: e.article_count || 1,
          radius_km: getEventImpactRadiusKm(e)
        }
      }))
    };
  }, [activeCategory]);

  // Convert events to Geodesic Impact Buffers (Polygons)
  const toImpactZonesGeoJSON = useCallback((eventsList: EventItem[]) => {
    const filtered = activeCategory === "all" 
      ? eventsList 
      : eventsList.filter(e => e.category === activeCategory);

    return {
      type: "FeatureCollection" as const,
      features: filtered.map(e => {
        const radiusKm = getEventImpactRadiusKm(e);
        return {
          type: "Feature" as const,
          geometry: {
            type: "Polygon" as const,
            coordinates: [createGeodesicCircle([e.longitude, e.latitude], radiusKm, 48)]
          },
          properties: {
            id: e.id,
            canonical_title: e.canonical_title,
            category: e.category,
            importance: e.importance_score,
            radius_km: radiusKm,
            city: e.city || "",
            country: e.country || ""
          }
        };
      })
    };
  }, [activeCategory]);

  // Tactical Range Rings for Focused Event
  const createRangeRingsGeoJSON = useCallback((center: [number, number]) => {
    const rings = [50, 100, 250]; // km
    return {
      type: "FeatureCollection" as const,
      features: rings.map(r => ({
        type: "Feature" as const,
        geometry: {
          type: "Polygon" as const,
          coordinates: [createGeodesicCircle(center, r, 64)]
        },
        properties: {
          radius_km: r,
          label: `${r} km`
        }
      }))
    };
  }, []);

  // Initialize MapLibre GL
  useEffect(() => {
    let map: any = null;

    async function initMap() {
      if (!mapContainer.current || mapRef.current) return;

      const maplibreglModule: any = await import("maplibre-gl");
      const maplibregl = maplibreglModule.default || maplibreglModule;
      maplibreglRef.current = maplibregl;

      // Fix Next.js Webpack "Worker failed to load"
      if (typeof window !== "undefined") {
        const origin = window.location.origin;
        const isDev = process.env.NODE_ENV === "development";
        const workerUrl = `${origin}${isDev ? "/maplibre-gl-worker-dev.mjs" : "/maplibre-gl-worker.mjs"}`;
        
        if (maplibregl.setWorkerUrl) {
          maplibregl.setWorkerUrl(workerUrl);
        }
        if (maplibregl.config) {
          maplibregl.config.WORKER_URL = workerUrl;
        }
      }

      const cartoKey = process.env.NEXT_PUBLIC_CARTO_API_KEY || "cb1_45at_1_455a79593c372358fd20425c";

      map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
          sources: {
            "carto-dark": {
              type: "raster",
              tiles: [
                `https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://b.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://c.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://d.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png?key=${cartoKey}`
              ],
              tileSize: 256,
              attribution: '&copy; CARTO &copy; OpenStreetMap'
            },
            "esri-satellite": {
              type: "raster",
              tiles: [
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              ],
              tileSize: 256,
              attribution: '&copy; Esri, Maxar, Earthstar Geographics'
            },
            "carto-voyager": {
              type: "raster",
              tiles: [
                `https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png?key=${cartoKey}`,
                `https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png?key=${cartoKey}`
              ],
              tileSize: 256,
              attribution: '&copy; CARTO &copy; OpenStreetMap'
            }
          },
          layers: [
            {
              id: "carto-dark-layer",
              type: "raster",
              source: "carto-dark",
              minzoom: 0,
              maxzoom: 19,
              layout: { visibility: "visible" }
            },
            {
              id: "esri-satellite-layer",
              type: "raster",
              source: "esri-satellite",
              minzoom: 0,
              maxzoom: 19,
              layout: { visibility: "none" }
            },
            {
              id: "carto-voyager-layer",
              type: "raster",
              source: "carto-voyager",
              minzoom: 0,
              maxzoom: 19,
              layout: { visibility: "none" }
            }
          ]
        },
        center: [15, 25],
        zoom: 1.8,
        minZoom: 1.2,
        maxZoom: 17
      });

      // Add scale control
      map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-right");

      map.on("load", () => {
        mapRef.current = map;
        setMapLoaded(true);

        // 1. Add Tactical Geodesic Impact Buffer Source
        map.addSource("impact-zones-source", {
          type: "geojson",
          data: toImpactZonesGeoJSON(events)
        });

        // Layer: Impact Buffer Fill
        map.addLayer({
          id: "impact-zones-fill",
          type: "fill",
          source: "impact-zones-source",
          layout: { visibility: "visible" },
          paint: {
            "fill-color": [
              "match",
              ["get", "category"],
              "natural_disaster", "#f59e0b",
              "conflict", "#ef4444",
              "security", "#ef4444",
              "politics", "#0284c7",
              "economy", "#10b981",
              "science", "#8b5cf6",
              "#38bdf8"
            ],
            "fill-opacity": 0.14
          }
        });

        // Layer: Impact Buffer Perimeter Ring
        map.addLayer({
          id: "impact-zones-line",
          type: "line",
          source: "impact-zones-source",
          layout: { visibility: "visible" },
          paint: {
            "line-color": [
              "match",
              ["get", "category"],
              "natural_disaster", "#f59e0b",
              "conflict", "#ef4444",
              "security", "#ef4444",
              "politics", "#0284c7",
              "economy", "#10b981",
              "science", "#8b5cf6",
              "#38bdf8"
            ],
            "line-width": 1.5,
            "line-dasharray": [3, 2],
            "line-opacity": 0.7
          }
        });

        // 2. Add Tactical Range Rings Source (for focused event)
        map.addSource("range-rings-source", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] }
        });

        map.addLayer({
          id: "range-rings-line",
          type: "line",
          source: "range-rings-source",
          paint: {
            "line-color": "#38bdf8",
            "line-width": 1.2,
            "line-dasharray": [4, 4],
            "line-opacity": 0.8
          }
        });

        // 3. Add Point Events Source
        map.addSource("events-source", {
          type: "geojson",
          data: toGeoJSON(events),
          cluster: true,
          clusterMaxZoom: 9,
          clusterRadius: 35
        });

        // 4. Intelligence Heatmap Layer
        map.addLayer({
          id: "events-heatmap",
          type: "heatmap",
          source: "events-source",
          maxzoom: 10,
          layout: { visibility: "none" },
          paint: {
            "heatmap-weight": [
              "interpolate",
              ["linear"],
              ["get", "importance"],
              1.0, 0.2,
              5.0, 0.6,
              10.0, 1.0
            ],
            "heatmap-intensity": [
              "interpolate",
              ["linear"],
              ["zoom"],
              0, 1,
              9, 3
            ],
            "heatmap-color": [
              "interpolate",
              ["linear"],
              ["heatmap-density"],
              0, "rgba(33, 102, 172, 0)",
              0.2, "rgba(56, 189, 248, 0.5)",
              0.4, "rgba(74, 222, 128, 0.7)",
              0.7, "rgba(251, 191, 36, 0.85)",
              0.95, "rgba(244, 63, 94, 0.95)"
            ],
            "heatmap-radius": [
              "interpolate",
              ["linear"],
              ["zoom"],
              0, 6,
              9, 36
            ],
            "heatmap-opacity": 0.8
          }
        });

        // 5. Cluster Circles Layer
        map.addLayer({
          id: "clusters",
          type: "circle",
          source: "events-source",
          filter: ["has", "point_count"],
          paint: {
            "circle-color": [
              "step",
              ["get", "point_count"],
              "#0284c7",  // <= 3
              4,
              "#f59e0b",  // 4 - 7
              8,
              "#ef4444"   // >= 8
            ],
            "circle-radius": [
              "step",
              ["get", "point_count"],
              16,
              4,
              22,
              8,
              28
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-opacity": 0.6
          }
        });

        // 6. Cluster Count Number
        map.addLayer({
          id: "cluster-count",
          type: "symbol",
          source: "events-source",
          filter: ["has", "point_count"],
          layout: {
            "text-field": "{point_count_abbreviated}",
            "text-size": 12,
            "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"]
          },
          paint: {
            "text-color": "#ffffff"
          }
        });

        // 7. Unclustered Glowing Background Halo
        map.addLayer({
          id: "unclustered-point-glow",
          type: "circle",
          source: "events-source",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": [
              "match",
              ["get", "category"],
              "natural_disaster", "#f59e0b",
              "conflict", "#ef4444",
              "security", "#ef4444",
              "politics", "#0284c7",
              "economy", "#10b981",
              "science", "#8b5cf6",
              "#38bdf8"
            ],
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["get", "importance"],
              1.0, 14,
              5.0, 20,
              10.0, 28
            ],
            "circle-opacity": 0.28,
            "circle-blur": 0.6
          }
        });

        // 8. Unclustered Individual Event Pinpoint
        map.addLayer({
          id: "unclustered-point",
          type: "circle",
          source: "events-source",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": [
              "match",
              ["get", "category"],
              "natural_disaster", "#f59e0b",
              "conflict", "#ef4444",
              "security", "#ef4444",
              "politics", "#0284c7",
              "economy", "#10b981",
              "science", "#8b5cf6",
              "#38bdf8"
            ],
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["get", "importance"],
              1.0, 7,
              5.0, 11,
              10.0, 16
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-opacity": 0.95
          }
        });

        // 9. Unclustered White Center Core Dot
        map.addLayer({
          id: "unclustered-point-core",
          type: "circle",
          source: "events-source",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": "#ffffff",
            "circle-radius": 3
          }
        });

        // 10. Actual Location City & Region Labels
        map.addLayer({
          id: "unclustered-city-labels",
          type: "symbol",
          source: "events-source",
          filter: ["!", ["has", "point_count"]],
          minzoom: 2.2,
          layout: {
            "text-field": [
              "case",
              ["!=", ["get", "city"], ""],
              ["concat", "📍 ", ["get", "city"]],
              ["concat", "📍 ", ["get", "country"]]
            ],
            "text-size": 11,
            "text-offset": [0, 1.3],
            "text-anchor": "top",
            "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
            "text-allow-overlap": false
          },
          paint: {
            "text-color": "#ffffff",
            "text-halo-color": "#060a14",
            "text-halo-width": 2.5
          }
        });

        // Interactive Hover Tooltip
        const hoverPopup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
          offset: 15
        });

        map.on("mousemove", "unclustered-point", (e: any) => {
          if (!e.features || !e.features[0]) return;
          const feat = e.features[0];
          const coords = feat.geometry.coordinates.slice();
          const props = feat.properties;

          map.getCanvas().style.cursor = "pointer";

          const categoryColor = 
            props.category === "natural_disaster" ? "#f59e0b" :
            props.category === "conflict" || props.category === "security" ? "#ef4444" :
            props.category === "politics" ? "#0284c7" :
            props.category === "economy" ? "#10b981" :
            props.category === "science" ? "#8b5cf6" : "#38bdf8";

          const html = `
            <div style="font-family: inherit; max-width: 270px;">
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px;">
                <span style="background: ${categoryColor}25; color: ${categoryColor}; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; border: 1px solid ${categoryColor}40;">
                  ${props.category?.replace("_", " ")}
                </span>
                <span style="color: #fbbf24; font-size: 11px; font-weight: 700;">
                  ★ ${Number(props.importance).toFixed(1)}/10 Impact
                </span>
              </div>
              <div style="font-size: 12px; font-weight: 700; color: #f8fafc; line-height: 1.35; margin-bottom: 6px;">
                ${props.canonical_title}
              </div>
              <div style="font-size: 11px; color: #cbd5e1; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #1e293b; padding-top: 6px; margin-bottom: 4px;">
                <span style="color: #38bdf8; font-weight: 600;">
                  📍 ${props.city ? props.city + ", " : ""}${props.country || "Global"}
                </span>
                <span style="color: #94a3b8; font-size: 10px; font-family: monospace;">
                  ${Number(coords[1]).toFixed(2)}°, ${Number(coords[0]).toFixed(2)}°
                </span>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; font-size: 10px; color: #94a3b8;">
                <span>Zone of Influence: <strong style="color: #38bdf8;">~${props.radius_km || 80} km</strong></span>
                <span style="color: #34d399;">${Math.round((props.confidence || 0.9) * 100)}% Verified</span>
              </div>
              <div style="font-size: 10px; color: #38bdf8; margin-top: 6px; text-align: right; opacity: 0.9;">
                Click to inspect full dossier →
              </div>
            </div>
          `;

          hoverPopup.setLngLat(coords).setHTML(html).addTo(map);
        });

        map.on("mouseleave", "unclustered-point", () => {
          map.getCanvas().style.cursor = "";
          hoverPopup.remove();
        });

        // Event click handling
        map.on("click", "unclustered-point", (e: any) => {
          if (!e.features || !e.features[0]) return;
          const feat = e.features[0];
          const eventId = feat.properties.id;
          if (eventId) {
            onSelectEvent(eventId);
          }
        });

        // Cluster click to zoom in and expand
        map.on("click", "clusters", (e: any) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ["clusters"] });
          const clusterId = features[0].properties.cluster_id;
          map.getSource("events-source").getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
            if (err) return;
            map.easeTo({
              center: features[0].geometry.coordinates,
              zoom: zoom + 1.2
            });
          });
        });

        map.on("mouseenter", "clusters", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "clusters", () => {
          map.getCanvas().style.cursor = "";
        });

        // Live Cursor Coordinates Tracking
        map.on("mousemove", (e: any) => {
          setCursorCoords({
            lng: Number(e.lngLat.lng.toFixed(4)),
            lat: Number(e.lngLat.lat.toFixed(4))
          });
        });

        map.on("mouseout", () => {
          setCursorCoords(null);
        });

        // Viewport bounding box listener
        const emitBounds = () => {
          const currentZoom = Math.round(map.getZoom() * 10) / 10;
          setZoomLevel(currentZoom);
          if (onBoundsChange) {
            const bounds = map.getBounds();
            const bbox = `${bounds.getWest().toFixed(3)},${bounds.getSouth().toFixed(3)},${bounds.getEast().toFixed(3)},${bounds.getNorth().toFixed(3)}`;
            onBoundsChange(bbox, currentZoom);
          }
        };

        map.on("moveend", emitBounds);
        emitBounds();
      });
    }

    initMap();

    return () => {
      if (map) {
        map.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Handle Basemap Switch (0ms flicker-free layout property toggle)
  const handleBasemapChange = (style: "dark" | "satellite" | "streets") => {
    setActiveBasemap(style);
    if (!mapRef.current) return;
    mapRef.current.setLayoutProperty("carto-dark-layer", "visibility", style === "dark" ? "visible" : "none");
    mapRef.current.setLayoutProperty("esri-satellite-layer", "visibility", style === "satellite" ? "visible" : "none");
    mapRef.current.setLayoutProperty("carto-voyager-layer", "visibility", style === "streets" ? "visible" : "none");
  };

  // Handle View Mode Switch (Markers vs Density Heatmap vs Impact Zones)
  const handleViewModeChange = (mode: "markers" | "heatmap" | "impact_zones") => {
    setActiveViewMode(mode);
    if (!mapRef.current) return;

    const isHeatmap = mode === "heatmap";
    mapRef.current.setLayoutProperty("events-heatmap", "visibility", isHeatmap ? "visible" : "none");

    const showPoints = !isHeatmap;
    mapRef.current.setLayoutProperty("clusters", "visibility", showPoints ? "visible" : "none");
    mapRef.current.setLayoutProperty("cluster-count", "visibility", showPoints ? "visible" : "none");
    mapRef.current.setLayoutProperty("unclustered-point", "visibility", showPoints ? "visible" : "none");
    mapRef.current.setLayoutProperty("unclustered-point-glow", "visibility", showPoints ? "visible" : "none");
    mapRef.current.setLayoutProperty("unclustered-point-core", "visibility", showPoints ? "visible" : "none");
    mapRef.current.setLayoutProperty("unclustered-city-labels", "visibility", showPoints ? "visible" : "none");

    const showZones = mode === "impact_zones" || (mode === "markers" && showImpactZones);
    mapRef.current.setLayoutProperty("impact-zones-fill", "visibility", showZones ? "visible" : "none");
    mapRef.current.setLayoutProperty("impact-zones-line", "visibility", showZones ? "visible" : "none");
  };

  const toggleImpactZones = () => {
    const next = !showImpactZones;
    setShowImpactZones(next);
    if (!mapRef.current) return;
    if (activeViewMode !== "heatmap") {
      mapRef.current.setLayoutProperty("impact-zones-fill", "visibility", next ? "visible" : "none");
      mapRef.current.setLayoutProperty("impact-zones-line", "visibility", next ? "visible" : "none");
    }
  };

  // Handle external reset to global view
  useEffect(() => {
    if (resetViewTrigger && mapRef.current) {
      if (focusedMarkerRef.current) {
        focusedMarkerRef.current.remove();
        focusedMarkerRef.current = null;
      }
      const rangeSource = mapRef.current.getSource("range-rings-source");
      if (rangeSource) {
        rangeSource.setData({ type: "FeatureCollection", features: [] });
      }
      mapRef.current.flyTo({
        center: [15, 25],
        zoom: 1.8,
        essential: true,
        duration: 1400
      });
    }
  }, [resetViewTrigger]);

  // Handle focusing map to a specific event's exact location
  useEffect(() => {
    if (focusedEventCoords && mapRef.current && maplibreglRef.current) {
      const { lng, lat, title, city, country, category, location_confidence } = focusedEventCoords;

      // Draw Tactical Concentric Range Rings (50km, 100km, 250km)
      const rangeSource = mapRef.current.getSource("range-rings-source");
      if (rangeSource) {
        rangeSource.setData(createRangeRingsGeoJSON([lng, lat]));
      }

      // Center map smoothly on the actual location
      mapRef.current.flyTo({
        center: [lng, lat],
        zoom: Math.max(mapRef.current.getZoom(), 5.8),
        essential: true,
        duration: 1600
      });

      // Clear any prior focused marker
      if (focusedMarkerRef.current) {
        focusedMarkerRef.current.remove();
        focusedMarkerRef.current = null;
      }

      // Create an animated HTML pinpoint beacon element
      const el = document.createElement("div");
      el.className = "cursor-pointer group select-none";
      el.innerHTML = `
        <div class="relative flex flex-col items-center -translate-x-1/2 -translate-y-full">
          <div class="absolute -bottom-1 h-5 w-5 rounded-full bg-rose-500/70 animate-ping"></div>
          <div class="relative flex items-center gap-1.5 rounded-full bg-rose-600 px-3 py-1 text-white shadow-2xl border-2 border-white ring-4 ring-rose-500/40">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            <span class="text-[11px] font-bold tracking-wide">${city || country || "Event Location"}</span>
          </div>
          <div class="w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-rose-600"></div>
        </div>
      `;

      el.addEventListener("click", () => {
        if (focusedEventCoords.id) {
          onSelectEvent(focusedEventCoords.id);
        }
      });

      // Open interactive popup at the exact location
      const popup = new maplibreglRef.current.Popup({
        offset: 35,
        closeButton: true,
        closeOnClick: false
      }).setHTML(`
        <div style="font-family: inherit; max-width: 270px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px;">
            <span style="background: rgba(244,63,94,0.2); color: #fb7185; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; border: 1px solid rgba(244,63,94,0.3);">
              ${category?.replace("_", " ") || "EVENT LOCATION"}
            </span>
            <span style="color: #34d399; font-size: 10px; font-weight: 600;">
              ${Math.round((location_confidence || 0.96) * 100)}% GPS Grounded
            </span>
          </div>
          <h4 style="font-weight: 700; color: #ffffff; font-size: 13px; line-height: 1.35; margin-bottom: 6px;">
            ${title || "Active News Event"}
          </h4>
          <div style="font-size: 11px; color: #cbd5e1; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #1e293b; padding-top: 6px;">
            <span>📍 <strong>${city ? `${city}, ` : ""}${country || "Global"}</strong></span>
            <span style="color: #64748b; font-size: 10px; font-family: monospace;">
              ${lat.toFixed(3)}°, ${lng.toFixed(3)}°
            </span>
          </div>
          <div style="margin-top: 4px; font-size: 10px; color: #38bdf8;">
            Concentric 50km, 100km & 250km tactical range rings active
          </div>
        </div>
      `);

      const marker = new maplibreglRef.current.Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(mapRef.current);

      popup.addTo(mapRef.current);
      focusedMarkerRef.current = marker;
    }
  }, [focusedEventCoords, onSelectEvent, createRangeRingsGeoJSON]);

  // Sync category if controlled from parent
  useEffect(() => {
    if (selectedCategory && selectedCategory !== activeCategory) {
      setActiveCategory(selectedCategory);
    }
  }, [selectedCategory]);

  // Update source data when events or category changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const source = mapRef.current.getSource("events-source");
    if (source) {
      source.setData(toGeoJSON(events));
    }
    const impactSource = mapRef.current.getSource("impact-zones-source");
    if (impactSource) {
      impactSource.setData(toImpactZonesGeoJSON(events));
    }
  }, [events, activeCategory, mapLoaded, toGeoJSON, toImpactZonesGeoJSON]);

  const handleRegionJump = (center: number[], zoom: number) => {
    if (!mapRef.current) return;
    mapRef.current.flyTo({
      center,
      zoom,
      essential: true,
      duration: 1800
    });
  };

  const handleCategorySelect = (cat: string) => {
    setActiveCategory(cat);
    if (onCategoryChange) {
      onCategoryChange(cat);
    }
  };

  const handleResetBearing = () => {
    if (!mapRef.current) return;
    mapRef.current.resetNorthPitch({ duration: 800 });
  };

  return (
    <div className="relative h-[640px] w-full overflow-hidden rounded-2xl border border-slate-800 bg-[#060a14] shadow-2xl flex flex-col justify-between">
      {/* Map Canvas */}
      <div ref={mapContainer} className="h-full w-full" />

      {/* Top Floating Master Control Bar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Left: Category Filters */}
        <div className="pointer-events-auto flex flex-wrap items-center gap-1 rounded-xl border border-slate-800/80 bg-slate-950/85 p-1 shadow-lg backdrop-blur-md">
          <span className="px-2 text-[10px] font-bold tracking-wider text-slate-400 uppercase flex items-center gap-1">
            <Filter className="h-3 w-3 text-sky-400" />
            Category:
          </span>
          {[
            { id: "all", label: "All" },
            { id: "natural_disaster", label: "Disasters" },
            { id: "conflict", label: "Conflict" },
            { id: "politics", label: "Politics" },
            { id: "economy", label: "Economy" },
            { id: "science", label: "Science" }
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => handleCategorySelect(cat.id)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                activeCategory === cat.id
                  ? "bg-sky-500 text-white shadow-sm"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Center: Intelligence View Modes */}
        <div className="pointer-events-auto hidden md:flex items-center gap-1 rounded-xl border border-slate-800/80 bg-slate-950/85 p-1 shadow-lg backdrop-blur-md">
          <button
            onClick={() => handleViewModeChange("markers")}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
              activeViewMode === "markers"
                ? "bg-sky-600 text-white shadow-sm"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="Display verified individual event markers and regional clusters"
          >
            <MapPin className="h-3.5 w-3.5" />
            <span>Pinpoints</span>
          </button>
          <button
            onClick={() => handleViewModeChange("impact_zones")}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
              activeViewMode === "impact_zones"
                ? "bg-amber-600 text-white shadow-sm"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="Display geographical zones of influence (80-350 km impact radii)"
          >
            <Radar className="h-3.5 w-3.5" />
            <span>Impact Zones</span>
          </button>
          <button
            onClick={() => handleViewModeChange("heatmap")}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
              activeViewMode === "heatmap"
                ? "bg-rose-600 text-white shadow-sm"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="WebGL event intensity and impact density heatmap"
          >
            <Flame className="h-3.5 w-3.5" />
            <span>Density Heatmap</span>
          </button>
        </div>

        {/* Right: High-Accuracy Basemap Switcher */}
        <div className="pointer-events-auto flex items-center gap-1 rounded-xl border border-slate-800/80 bg-slate-950/85 p-1 shadow-lg backdrop-blur-md">
          <span className="px-1.5 text-[10px] font-bold text-slate-400 uppercase hidden sm:inline">
            Layer:
          </span>
          <button
            onClick={() => handleBasemapChange("dark")}
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all ${
              activeBasemap === "dark"
                ? "bg-slate-800 text-sky-400 border border-slate-700 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Tactical dark matter vector/raster basemap"
          >
            <span>🌙 Dark</span>
          </button>
          <button
            onClick={() => handleBasemapChange("satellite")}
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all ${
              activeBasemap === "satellite"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Real-world high-resolution satellite imagery (Esri World Imagery)"
          >
            <Satellite className="h-3 w-3" />
            <span>Satellite</span>
          </button>
          <button
            onClick={() => handleBasemapChange("streets")}
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all ${
              activeBasemap === "streets"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Topographical Street and Administrative Border Map"
          >
            <MapIcon className="h-3 w-3" />
            <span>Street / Topo</span>
          </button>
        </div>
      </div>

      {/* Top Secondary Sub-bar: Tactical Region Jump Shortcuts */}
      <div className="absolute top-16 right-3 z-10 hidden lg:flex items-center gap-1 rounded-xl border border-slate-800/80 bg-slate-950/80 p-1 shadow-lg backdrop-blur-md">
        {REGION_PRESETS.map(r => (
          <button
            key={r.name}
            onClick={() => handleRegionJump(r.center, r.zoom)}
            className="rounded-lg px-2 py-0.5 text-[10px] font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          >
            {r.name}
          </button>
        ))}
      </div>

      {/* Bottom Live Tactical HUD (Heads-Up Display) */}
      <div className="absolute bottom-3 left-3 right-16 z-10 pointer-events-none flex flex-wrap items-center justify-between gap-2">
        {/* Left: Tactical Coordinates Crosshair HUD */}
        <div className="pointer-events-auto flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-950/90 px-3 py-1.5 text-xs backdrop-blur-md shadow-xl text-slate-300">
          <div className="flex items-center gap-1.5 font-mono text-[11px] text-sky-400">
            <Crosshair className="h-3.5 w-3.5 text-sky-400" />
            {cursorCoords ? (
              <span>
                {formatDMS(cursorCoords.lat, true)}, {formatDMS(cursorCoords.lng, false)}
                <span className="text-slate-500 ml-1.5">({cursorCoords.lat.toFixed(4)}°, {cursorCoords.lng.toFixed(4)}°)</span>
              </span>
            ) : (
              <span className="text-slate-400">Move cursor to inspect coordinates</span>
            )}
          </div>

          <div className="h-3 w-px bg-slate-700 hidden sm:block" />

          {/* Zoom & Elevation Status */}
          <div className="font-mono text-[11px] text-slate-400 hidden sm:flex items-center gap-2">
            <span>Zoom: <strong className="text-white">{zoomLevel.toFixed(1)}x</strong></span>
            <span>Basemap: <strong className="text-sky-300 capitalize">{activeBasemap}</strong></span>
          </div>

          <div className="h-3 w-px bg-slate-700 hidden md:block" />

          {/* Quick Impact Zone Toggle Button */}
          <button
            onClick={toggleImpactZones}
            className={`pointer-events-auto flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border transition-all ${
              showImpactZones 
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40" 
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
            title="Toggle geographic impact radius zones"
          >
            <CircleDot className="h-3 w-3" />
            <span>Impact Zones: {showImpactZones ? "ON" : "OFF"}</span>
          </button>
        </div>

        {/* Category Legend Strip */}
        <div className="pointer-events-auto hidden xl:flex items-center gap-2.5 rounded-xl border border-slate-800/80 bg-slate-950/85 px-3 py-1.5 text-xs backdrop-blur-md shadow-xl">
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#f59e0b]" />
            <span className="text-[10px] text-slate-300">Disaster</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#ef4444]" />
            <span className="text-[10px] text-slate-300">Conflict</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#0284c7]" />
            <span className="text-[10px] text-slate-300">Politics</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#10b981]" />
            <span className="text-[10px] text-slate-300">Economy</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#8b5cf6]" />
            <span className="text-[10px] text-slate-300">Science</span>
          </div>
        </div>
      </div>

      {/* Bottom Right Floating Map Controls */}
      <div className="absolute bottom-3 right-3 z-10 flex flex-col gap-1 rounded-xl border border-slate-800/80 bg-slate-950/90 p-1 shadow-xl backdrop-blur-md">
        <button
          onClick={() => mapRef.current?.zoomIn()}
          className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={() => mapRef.current?.zoomOut()}
          className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={handleResetBearing}
          className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          title="Reset True North Bearing"
        >
          <Compass className="h-4 w-4 text-sky-400" />
        </button>
        <button
          onClick={() => handleRegionJump([15, 25], 1.8)}
          className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          title="Reset Global View"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
