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

interface IntelligenceMapProps {
  events: EventItem[];
  onSelectEvent: (eventId: string) => void;
  onBoundsChange?: (bbox: string) => void;
  selectedCategory?: string;
  onCategoryChange?: (category: string) => void;
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
  onCategoryChange
}: IntelligenceMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1.5);
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

      const cartoKey = process.env.NEXT_PUBLIC_CARTO_API_KEY || "cb1_45at_1_455a79593c372358fd20425c";

      map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
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
          clusterMaxZoom: 12,
          clusterRadius: 45
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

        // Layer 3: Unclustered individual event circles
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
              10.0, 18
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-opacity": 0.8
          }
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

        // Cluster click to zoom in
        map.on("click", "clusters", (e: any) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ["clusters"] });
          const clusterId = features[0].properties.cluster_id;
          map.getSource("events-source").getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
            if (err) return;
            map.easeTo({
              center: features[0].geometry.coordinates,
              zoom: zoom + 0.5
            });
          });
        });

        // Cursor pointer styling
        map.on("mouseenter", "unclustered-point", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "unclustered-point", () => {
          map.getCanvas().style.cursor = "";
        });
        map.on("mouseenter", "clusters", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "clusters", () => {
          map.getCanvas().style.cursor = "";
        });

        // Viewport bounding box listener
        map.on("moveend", () => {
          setZoomLevel(Math.round(map.getZoom() * 10) / 10);
          if (onBoundsChange) {
            const bounds = map.getBounds();
            const bbox = `${bounds.getWest().toFixed(3)},${bounds.getSouth().toFixed(3)},${bounds.getEast().toFixed(3)},${bounds.getNorth().toFixed(3)}`;
            onBoundsChange(bbox);
          }
        });
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
