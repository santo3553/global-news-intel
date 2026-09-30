"use client";

import { useEffect, useRef, useState, useCallback } from "react";
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
  Maximize2 
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
  { name: "Europe", center: [15, 50], zoom: 3.8 },
  { name: "Middle East", center: [45, 28], zoom: 4.0 },
  { name: "Asia-Pacific", center: [115, 20], zoom: 3.2 },
  { name: "Americas", center: [-85, 20], zoom: 2.8 },
  { name: "Africa", center: [20, 5], zoom: 3.2 },
];

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

  // Convert events to GeoJSON
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
          city: e.city || "",
          country: e.country || "",
          articles: e.article_count || 1
        }
      }))
    };
  }, [activeCategory]);

  // Initialize MapLibre GL
  useEffect(() => {
    let map: any = null;

    async function initMap() {
      if (!mapContainer.current || mapRef.current) return;

      const maplibreglModule: any = await import("maplibre-gl");
      const maplibregl = maplibreglModule.default || maplibreglModule;
      maplibreglRef.current = maplibregl;

      // Fix Next.js Webpack "Worker failed to load. Check that the worker URL is correct."
      // Point MapLibre to the local static worker served from /public
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
              attribution: '&copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener noreferrer">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'
            }
          },
          layers: [
            {
              id: "carto-dark-layer",
              type: "raster",
              source: "carto-dark",
              minzoom: 0,
              maxzoom: 19
            }
          ]
        },
        center: [15, 25],
        zoom: 1.8,
        minZoom: 1.2,
        maxZoom: 16
      });

      map.on("load", () => {
        mapRef.current = map;
        setMapLoaded(true);

        // Add clustered GeoJSON source
        map.addSource("events-source", {
          type: "geojson",
          data: toGeoJSON(events),
          cluster: true,
          clusterMaxZoom: 9,
          clusterRadius: 35
        });

        // Layer 1: Cluster circles
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
            "circle-stroke-opacity": 0.5
          }
        });

        // Layer 2: Cluster count text
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

        // Layer 3: Unclustered glowing background halo
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
            "circle-opacity": 0.25,
            "circle-blur": 0.6
          }
        });

        // Layer 4: Unclustered individual event circles
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
            "circle-stroke-opacity": 0.9
          }
        });

        // Layer 5: Unclustered white core pinpoint
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

        // Layer 6: Actual Location City & Region Labels
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

        // Interactive Hover Tooltip for Actual News Location
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
            <div style="font-family: inherit; max-width: 260px;">
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
              <div style="font-size: 11px; color: #cbd5e1; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #1e293b; padding-top: 6px;">
                <span style="color: #38bdf8; font-weight: 600;">
                  📍 ${props.city ? props.city + ", " : ""}${props.country || "Global"}
                </span>
                <span style="color: #64748b; font-size: 10px;">
                  ${Number(coords[1]).toFixed(2)}°, ${Number(coords[0]).toFixed(2)}°
                </span>
              </div>
              <div style="font-size: 10px; color: #38bdf8; margin-top: 5px; text-align: right; opacity: 0.9;">
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

        // Cursor pointer styling
        map.on("mouseenter", "clusters", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "clusters", () => {
          map.getCanvas().style.cursor = "";
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
        // Call immediately on load to establish baseline bounds
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

  // Handle external reset to global view
  useEffect(() => {
    if (resetViewTrigger && mapRef.current) {
      if (focusedMarkerRef.current) {
        focusedMarkerRef.current.remove();
        focusedMarkerRef.current = null;
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
      const { lng, lat, title, city, country, category } = focusedEventCoords;

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
          <div class="absolute -bottom-1 h-4 w-4 rounded-full bg-rose-500/60 animate-ping"></div>
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
        <div style="font-family: inherit; max-width: 260px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px;">
            <span style="background: rgba(244,63,94,0.2); color: #fb7185; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; border: 1px solid rgba(244,63,94,0.3);">
              ${category?.replace("_", " ") || "EVENT LOCATION"}
            </span>
            <span style="color: #64748b; font-size: 10px; font-family: monospace;">
              ${lat.toFixed(2)}°, ${lng.toFixed(2)}°
            </span>
          </div>
          <h4 style="font-weight: 700; color: #ffffff; font-size: 13px; line-height: 1.35; margin-bottom: 6px;">
            ${title || "Active News Event"}
          </h4>
          <div style="font-size: 11px; color: #cbd5e1; display: flex; align-items: center; gap: 4px; border-top: 1px solid #1e293b; padding-top: 6px;">
            <span>📍 <strong>${city ? `${city}, ` : ""}${country || "Global"}</strong></span>
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
  }, [focusedEventCoords, onSelectEvent]);

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
  }, [events, activeCategory, mapLoaded, toGeoJSON]);

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

  return (
    <div className="relative h-[560px] w-full overflow-hidden rounded-2xl border border-slate-800 bg-[#060a14] shadow-2xl">
      {/* Map Canvas */}
      <div ref={mapContainer} className="h-full w-full" />

      {/* Top Floating Category Filter Bar */}
      <div className="absolute top-4 left-4 z-10 flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-800/80 bg-slate-950/80 p-1.5 shadow-lg backdrop-blur-md">
        <span className="px-2 text-[10px] font-bold tracking-wider text-slate-400 uppercase flex items-center gap-1">
          <Filter className="h-3 w-3 text-sky-400" />
          Filter:
        </span>
        {[
          { id: "all", label: "All Events" },
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

      {/* Top Right Region Presets */}
      <div className="absolute top-4 right-4 z-10 hidden sm:flex items-center gap-1 rounded-xl border border-slate-800/80 bg-slate-950/80 p-1.5 shadow-lg backdrop-blur-md">
        {REGION_PRESETS.map(r => (
          <button
            key={r.name}
            onClick={() => handleRegionJump(r.center, r.zoom)}
            className="rounded-lg px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
          >
            {r.name}
          </button>
        ))}
      </div>

      {/* Bottom Left Legend & Status */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-950/85 px-3 py-2 text-xs backdrop-blur-md shadow-lg">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]" />
          <span className="text-[11px] text-slate-300">Disaster</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ef4444]" />
          <span className="text-[11px] text-slate-300">Conflict</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#0284c7]" />
          <span className="text-[11px] text-slate-300">Politics</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#10b981]" />
          <span className="text-[11px] text-slate-300">Economy</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#8b5cf6]" />
          <span className="text-[11px] text-slate-300">Science</span>
        </div>

        <div className="border-l border-slate-700 pl-3 font-mono text-[11px] text-slate-400">
          Zoom: {zoomLevel}x
        </div>
      </div>

      {/* Bottom Right Map Controls */}
      <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-1 rounded-xl border border-slate-800/80 bg-slate-950/85 p-1 shadow-lg backdrop-blur-md">
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
