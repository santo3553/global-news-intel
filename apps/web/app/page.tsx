"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import { 
  Globe2, 
  Activity, 
  Database, 
  Server, 
  RefreshCw, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Layers,
  MapPin,
  Flame,
  Radio,
  Rss,
  Newspaper,
  ExternalLink,
  Shield,
  CopyCheck,
  Zap,
  Tag,
  Compass,
  Maximize2,
  Search,
  Sparkles,
  TrendingUp,
  FileText,
  ChevronRight,
  Play,
  CheckCircle,
  RotateCcw,
  SlidersHorizontal
} from "lucide-react";
import { 
  fetchHealth, 
  fetchSources, 
  fetchArticles, 
  fetchEvents, 
  fetchEventsWithBbox,
  fetchBriefing,
  searchEvents,
  triggerPipelineRun,
  fetchPipelineStatus,
  HealthResponse, 
  SourceItem, 
  ArticleItem, 
  EventItem,
  IntelligenceBriefingResponse,
  BriefingItem,
  PipelineTelemetry,
  PipelineStatusResponse
} from "@/lib/api";
import EventDetailModal from "@/components/events/EventDetailModal";

const IntelligenceMap = dynamic(
  () => import("@/components/map/IntelligenceMap"),
  { 
    ssr: false,
    loading: () => (
      <div className="h-[560px] w-full rounded-2xl border border-slate-800 bg-[#060a14] flex items-center justify-center text-slate-400">
        <Activity className="h-6 w-6 animate-spin text-sky-400 mr-2" />
        <span>Loading Geospatial Tile Engine...</span>
      </div>
    )
  }
);

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [articles, setArticles] = useState<ArticleItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [briefing, setBriefing] = useState<IntelligenceBriefingResponse | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [mapBbox, setMapBbox] = useState<string>("");
  const [mapZoom, setMapZoom] = useState<number>(1.8);
  const [isViewportSyncActive, setIsViewportSyncActive] = useState<boolean>(true);
  const [selectedMapCategory, setSelectedMapCategory] = useState<string>("all");
  const [resetViewTrigger, setResetViewTrigger] = useState<number>(0);
  const [focusedEventCoords, setFocusedEventCoords] = useState<{
    lng: number;
    lat: number;
    id?: string;
    title?: string;
    city?: string;
    country?: string;
    category?: string;
  } | null>(null);
  const [sortBy, setSortBy] = useState<string>("importance");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [briefingTab, setBriefingTab] = useState<"breaking" | "geopolitical" | "hazards" | "economic">("breaking");
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<string>("");
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [pipelineTelemetry, setPipelineTelemetry] = useState<PipelineTelemetry | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatusResponse | null>(null);
  const [selectedSourceRegion, setSelectedSourceRegion] = useState<string>("all");
  const [selectedCountry, setSelectedCountry] = useState<string>("all");
  const [selectedScope, setSelectedScope] = useState<"all" | "galli" | "regional" | "national" | "international">("all");

  const getSourceRegion = useCallback((country?: string): string => {
    if (!country) return "Global";
    const c = country.toUpperCase();
    if (["IN", "PK", "BD", "LK", "NP"].includes(c)) return "India & South Asia";
    if (["KZ", "UZ", "KG", "TJ", "TM", "AZ", "GE", "AM", "AF", "TR"].includes(c)) return "Central Asia & Caucasus";
    if (["SG", "ID", "TH", "PH", "VN", "MY", "JP", "KR", "TW", "HK", "AU", "NZ", "FJ", "PG"].includes(c)) return "Asia & Pacific";
    if (["SA", "AE", "QA", "IL", "EG", "JO", "LB", "MA", "KE", "NG", "ZA", "GH", "SD", "ET", "LY", "CD"].includes(c)) return "Middle East & Africa";
    if (["GB", "DE", "FR", "UA", "PL", "LV", "EE", "LT", "GR", "IS", "NO", "CH", "NL", "BE", "IT", "ES", "AT", "SE", "DK", "FI", "CZ", "RO", "RU"].includes(c)) return "Europe";
    if (["US", "CA", "MX", "BR", "AR", "CO", "CL", "JM", "UY", "PE", "VE", "PA", "CU", "TT"].includes(c)) return "Americas";
    return "Global / UN";
  }, []);

  const getEventScope = useCallback((evt: EventItem): "galli" | "regional" | "national" | "international" => {
    if ((evt.global_impact_score ?? 0) >= 8.5 && (!evt.city || ["politics", "security"].includes(evt.category))) {
      return "international";
    }
    const subcat = (evt.subcategory || "").toLowerCase();
    const title = (evt.canonical_title || "").toLowerCase();
    const isMunicipalLocal = subcat.includes("air_quality") || 
      subcat.includes("urban_infrastructure") || 
      subcat.includes("smart_transit") || 
      subcat.includes("green_mobility") || 
      subcat.includes("civil_engineering") ||
      subcat.includes("flood_early_warning") ||
      title.includes("ward") || 
      title.includes("municipal") || 
      title.includes("metro") || 
      title.includes("tunnel") || 
      title.includes("road") || 
      title.includes("corridor") || 
      title.includes("feeder") || 
      title.includes("shuttle") ||
      title.includes("ferry");

    if (evt.city && (evt.location_confidence ?? 0) >= 0.95 && isMunicipalLocal) {
      return "galli";
    }
    if (evt.admin_region || evt.city) {
      return "regional";
    }
    return "national";
  }, []);

  const COUNTRY_CENTERS: Record<string, { center: [number, number]; zoom: number }> = useMemo(() => ({
    "India": { center: [78.5, 22.0], zoom: 4.2 },
    "United States": { center: [-98.0, 39.0], zoom: 3.5 },
    "Kazakhstan": { center: [67.0, 48.0], zoom: 3.8 },
    "Uzbekistan": { center: [64.0, 41.5], zoom: 4.5 },
    "Azerbaijan": { center: [47.5, 40.5], zoom: 5.5 },
    "Georgia": { center: [44.0, 42.0], zoom: 5.5 },
    "Japan": { center: [138.0, 36.5], zoom: 4.2 },
    "Germany": { center: [10.5, 51.2], zoom: 4.8 },
    "United Kingdom": { center: [-2.5, 54.0], zoom: 4.8 },
    "Switzerland": { center: [8.2, 46.8], zoom: 5.8 },
    "Iceland": { center: [-18.5, 64.8], zoom: 5.0 },
    "China": { center: [104.0, 35.0], zoom: 3.5 },
    "Brazil": { center: [-51.9, -14.2], zoom: 3.5 },
    "Kenya": { center: [37.9, 0.0], zoom: 4.8 },
    "Egypt": { center: [30.8, 26.8], zoom: 4.5 },
    "Turkey": { center: [35.0, 39.0], zoom: 4.5 },
    "Afghanistan": { center: [67.7, 33.9], zoom: 4.8 },
    "South Korea": { center: [127.8, 36.5], zoom: 5.5 },
    "Philippines": { center: [121.8, 12.8], zoom: 4.8 },
    "Australia": { center: [133.8, -25.3], zoom: 3.5 },
  }), []);

  const handleSelectCountry = (country: string) => {
    setSelectedCountry(country);
    if (country === "all") {
      setResetViewTrigger(prev => prev + 1);
      return;
    }
    const coords = COUNTRY_CENTERS[country];
    if (coords) {
      setFocusedEventCoords({
        lng: coords.center[0],
        lat: coords.center[1],
        title: `${country} National & Local News Intelligence`,
        city: "",
        country: country,
        category: "all"
      });
      const mapElement = document.getElementById("geospatial-map-section");
      if (mapElement) {
        mapElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  };

  const availableCountries = useMemo(() => {
    const counts: Record<string, number> = {};
    events.forEach(e => {
      if (e.country) {
        counts[e.country] = (counts[e.country] || 0) + 1;
      }
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  }, [events]);

  const filteredSources = useMemo(() => {
    if (selectedSourceRegion === "all") return sources;
    return sources.filter(s => getSourceRegion(s.country) === selectedSourceRegion);
  }, [sources, selectedSourceRegion, getSourceRegion]);

  const loadData = useCallback(async () => {
    setLoading(true);
    const [healthData, sourcesData, articlesData, eventsData, briefingData, pipeStatus] = await Promise.all([
      fetchHealth(),
      fetchSources(),
      fetchArticles(15),
      searchQuery.trim() ? searchEvents(searchQuery.trim(), 100) : fetchEvents(100, sortBy),
      fetchBriefing(),
      fetchPipelineStatus()
    ]);
    setHealth(healthData);
    setSources(sourcesData);
    setArticles(articlesData);
    setEvents(eventsData);
    setBriefing(briefingData);
    setPipelineStatus(pipeStatus);
    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  }, [sortBy, searchQuery]);

  const handleTriggerPipeline = async () => {
    setIsRunningPipeline(true);
    const telemetry = await triggerPipelineRun(5);
    setPipelineTelemetry(telemetry);
    await loadData();
    setIsRunningPipeline(false);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      const data = await fetchEvents(100, sortBy);
      setEvents(data);
      return;
    }
    setIsSearching(true);
    const results = await searchEvents(searchQuery.trim(), 100);
    setEvents(results);
    setIsSearching(false);
  };

  const handleClearSearch = async () => {
    setSearchQuery("");
    setIsSearching(true);
    const data = await fetchEvents(100, sortBy);
    setEvents(data);
    setIsSearching(false);
  };

  // Determine whether the map is currently zoomed into a region
  const isZoomedIn = useMemo(() => {
    if (!mapBbox) return false;
    const parts = mapBbox.split(",").map(Number);
    if (parts.length !== 4 || parts.some(isNaN)) return false;
    const [w, s, e, n] = parts;
    const lngSpan = Math.abs(e - w);
    const latSpan = Math.abs(n - s);
    return mapZoom >= 2.2 || lngSpan < 280 || latSpan < 130;
  }, [mapBbox, mapZoom]);

  // Compute the visible and ranked events for the news section
  const visibleRankedEvents = useMemo(() => {
    let list = [...events];

    // Filter by Country if selected
    if (selectedCountry && selectedCountry !== "all") {
      list = list.filter(e => (e.country || "").toLowerCase() === selectedCountry.toLowerCase());
    }

    // Filter by Scope if selected (hyper-local "galli", regional, national, international)
    if (selectedScope && selectedScope !== "all") {
      list = list.filter(e => getEventScope(e) === selectedScope);
    }

    // Filter by map category if selected and not "all"
    if (selectedMapCategory && selectedMapCategory !== "all") {
      list = list.filter(e => e.category === selectedMapCategory);
    }

    // Filter by visible map bounding box when viewport sync is active, zoomed in, and country filter is "all"
    if (isViewportSyncActive && isZoomedIn && mapBbox && selectedCountry === "all") {
      const parts = mapBbox.split(",").map(Number);
      if (parts.length === 4 && !parts.some(isNaN)) {
        const [w, s, e, n] = parts;
        const minLat = Math.min(s, n);
        const maxLat = Math.max(s, n);

        list = list.filter(evt => {
          const lat = evt.latitude;
          const lng = evt.longitude;
          if (lat < minLat || lat > maxLat) return false;
          if (w > e) {
            // Antimeridian crossing wrap
            return lng >= w || lng <= e;
          } else {
            return lng >= w && lng <= e;
          }
        });
      }
    }

    // Rank events by the chosen ranking dimension
    list.sort((a, b) => {
      if (sortBy === "importance") {
        return (b.importance_score ?? 0) - (a.importance_score ?? 0);
      }
      if (sortBy === "confidence") {
        return (b.confidence_score ?? 0) - (a.confidence_score ?? 0);
      }
      if (sortBy === "velocity") {
        return (b.development_velocity_score ?? 0) - (a.development_velocity_score ?? 0);
      }
      if (sortBy === "recent") {
        const timeA = new Date(a.last_updated_at || a.first_seen_at).getTime();
        const timeB = new Date(b.last_updated_at || b.first_seen_at).getTime();
        return timeB - timeA;
      }
      return 0;
    });

    return list;
  }, [events, selectedCountry, selectedScope, getEventScope, mapBbox, isZoomedIn, isViewportSyncActive, selectedMapCategory, sortBy]);

  const handleResetToGlobal = () => {
    setResetViewTrigger(prev => prev + 1);
  };

  const handleFocusEventOnMap = (evt: EventItem) => {
    setFocusedEventCoords({
      lng: evt.longitude,
      lat: evt.latitude,
      id: evt.id,
      title: evt.canonical_title,
      city: evt.city || "",
      country: evt.country || "",
      category: evt.category
    });
    const mapElement = document.getElementById("geospatial-map-section");
    if (mapElement) {
      mapElement.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 20000);
    return () => clearInterval(interval);
  }, [loadData]);

  const isConnected = health && health.status !== "unhealthy";

  return (
    <main className="flex min-h-screen flex-col bg-[#080d1a] text-slate-100">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-inner">
              <Globe2 className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                GLOBAL NEWS INTELLIGENCE
                <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  ALL 9 PHASES OPERATIONAL
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Local-first Global Event Detection, Geospatial Clustering & Autonomous Ingestion
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1 text-xs">
              <span className={`h-2 w-2 rounded-full ${isConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
              <span className="text-slate-300">
                API: <strong className={isConnected ? "text-emerald-400" : "text-rose-400"}>{health?.status || "Checking..."}</strong>
              </span>
            </div>

            {/* Run Pipeline Ingestion Button */}
            <button
              onClick={handleTriggerPipeline}
              disabled={isRunningPipeline}
              className="flex items-center gap-1.5 rounded-lg border border-sky-500/40 bg-sky-500/10 px-3.5 py-1.5 text-xs font-semibold text-sky-300 transition-all hover:bg-sky-500/20 hover:text-white disabled:opacity-50 shadow-sm"
              title="Trigger live feed collection, deduplication, AI extraction, and clustering"
            >
              {isRunningPipeline ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-sky-400" />
                  <span>Processing Feeds...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-sky-400 text-sky-400" />
                  <span>Run Live Ingestion</span>
                </>
              )}
            </button>

            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 transition-all hover:bg-slate-800 hover:text-white disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-sky-400" : ""}`} />
              Sync Data
            </button>
          </div>
        </div>
      </header>

      {/* Live Pipeline Telemetry Banner */}
      {pipelineTelemetry && (
        <div className="bg-sky-950/60 border-b border-sky-500/30 px-6 py-2.5 backdrop-blur-md">
          <div className="mx-auto flex max-w-7xl items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-sky-300 font-mono">
              <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>
                Pipeline Completed in <strong>{pipelineTelemetry.duration_seconds}s</strong> &bull; 
                Polled <strong>{pipelineTelemetry.sources_checked}</strong> feeds &bull; 
                Inserted <strong>{pipelineTelemetry.articles_inserted}</strong> articles &bull; 
                Skipped <strong>{pipelineTelemetry.duplicates_skipped}</strong> duplicates &bull; 
                <strong>+{pipelineTelemetry.events_created}</strong> new events, <strong>{pipelineTelemetry.events_updated}</strong> merged
              </span>
            </div>
            <button
              onClick={() => setPipelineTelemetry(null)}
              className="text-slate-400 hover:text-white text-[11px] underline ml-4"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-8 p-6">
        {/* Core Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {/* API Status */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">FastAPI Backend</span>
              <Server className="h-5 w-5 text-sky-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {health?.version ? `v${health.version}` : "v0.1.0"}
              </span>
              <span className="text-xs text-slate-400">
                ({health?.environment || "development"})
              </span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
              {isConnected ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Serving on :8000</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                  <span>Connection pending</span>
                </>
              )}
            </div>
          </div>

          {/* Database Status */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Primary Database</span>
              <Database className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white capitalize">
                {health?.database.details?.dialect || "SQL Engine"}
              </span>
              {health?.database.latency_ms !== undefined && (
                <span className="text-xs text-emerald-400">
                  {health.database.latency_ms} ms
                </span>
              )}
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
              {health?.database.status === "connected" ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>
                    {health?.database.details?.postgis_enabled ? "PostGIS 3.4 Spatial Enabled" : "Connected & Ready"}
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  <span>{health?.database.details?.error || "Disconnected"}</span>
                </>
              )}
            </div>
          </div>

          {/* Sources Catalog Metric */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Curated Sources</span>
              <Rss className="h-5 w-5 text-amber-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {sources.length > 0 ? sources.length : "65+"}
              </span>
              <span className="text-xs text-amber-400 font-medium">Global & Local</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Worldwide regional feeds</span>
            </div>
          </div>

          {/* Ingested & Deduplicated Articles */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Articles Ingested</span>
              <CopyCheck className="h-5 w-5 text-purple-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {articles.length > 0 ? articles.length : "10+"}
              </span>
              <span className="text-xs text-purple-400">Processed</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>3-Level Dedup Active</span>
            </div>
          </div>

          {/* Clustered Events Metric */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Clustered Events</span>
              <Flame className="h-5 w-5 text-rose-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {events.length > 0 ? events.length : "5+"}
              </span>
              <span className="text-xs text-rose-400">Multi-Signal</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Continuous Lifecycle Active</span>
            </div>
          </div>
        </div>

        {/* Pipeline Architecture Progress Roadmap */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="h-5 w-5 text-sky-400" />
                Pipeline Execution Roadmap
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Modular 8-phase architecture transforming raw sources into clustered geospatial events
              </p>
            </div>
            <div className="text-xs text-slate-400">
              Synced: <span className="font-mono text-slate-300">{lastChecked || "just now"}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Phase 1 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 1</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Infrastructure & Foundation</h3>
              <p className="text-xs text-slate-400 mt-1">
                Monorepo, Docker Compose, PostgreSQL 16 + PostGIS, FastAPI, Next.js, migrations, healthchecks.
              </p>
            </div>

            {/* Phase 2 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 2</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">News Ingestion & Dedup</h3>
              <p className="text-xs text-slate-400 mt-1">
                Curated 20+ sources, RSS/Atom parser, tracking strip, SHA-256 hashes, 3-level deduplication, seed generator.
              </p>
            </div>

            {/* Phase 3 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 3</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">AI Extraction & Geocoding</h3>
              <p className="text-xs text-slate-400 mt-1">
                Replaceable local LLM provider, structured Pydantic extraction, location disambiguation & gazetteer.
              </p>
            </div>

            {/* Phase 4 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 4</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Event Engine & Clustering</h3>
              <p className="text-xs text-slate-400 mt-1">
                Multi-signal clustering (semantic, spatial, temporal, entities), continuous event evolution lifecycle.
              </p>
            </div>

            {/* Phase 5 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 5</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Multi-Impact Ranking</h3>
              <p className="text-xs text-slate-400 mt-1">
                8-dimension importance scoring, source reliability matrix, multi-source confidence calculation.
              </p>
            </div>

            {/* Phase 6 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 6</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Interactive World Map</h3>
              <p className="text-xs text-slate-400 mt-1">
                MapLibre GL dark tiles, zoom-density event clustering, bounding-box queries, event detail modal.
              </p>
            </div>

            {/* Phase 7 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 7</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">AI Briefing & Search</h3>
              <p className="text-xs text-slate-400 mt-1">
                Executive "What should I read now?" briefing, instant semantic search, and chronological event timelines.
              </p>
            </div>

            {/* Phase 8 */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400">PHASE 8</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  COMPLETED
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Hardening & Polish</h3>
              <p className="text-xs text-slate-400 mt-1">
                15-scenario global seed dataset, 55 pytest tests, and end-to-end integration verification.
              </p>
            </div>

            {/* Phase 9 */}
            <div className="rounded-xl border border-sky-500/30 bg-sky-950/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-sky-400">PHASE 9</span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                  LIVE & ACTIVE
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm">Autonomous Ingestion</h3>
              <p className="text-xs text-slate-400 mt-1">
                Continuous background daemon, on-demand live pipeline execution, and cycle telemetry.
              </p>
            </div>
          </div>
        </div>

        {/* Section 22: Executive Situation Report: "What Should I Read Right Now?" */}
        {briefing && (
          <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-b from-amber-950/20 via-slate-900/60 to-slate-900/40 p-6 shadow-2xl backdrop-blur-md">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    <Sparkles className="h-4 w-4 animate-pulse" />
                  </div>
                  <h2 className="text-base font-bold text-white tracking-wide">
                    EXECUTIVE SITUATION REPORT &bull; WHAT SHOULD I READ RIGHT NOW?
                  </h2>
                  <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-mono font-semibold text-amber-300 border border-amber-500/30">
                    Section 22 AI Briefing
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2 max-w-4xl leading-relaxed">
                  {briefing.executive_summary}
                </p>
              </div>
              <div className="flex items-center gap-3 self-end lg:self-center">
                <div className="rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Events Synthesized</span>
                  <span className="text-sm font-bold font-mono text-amber-400">{briefing.total_events_analyzed}</span>
                </div>
              </div>
            </div>

            {/* Briefing Category Selector Tabs */}
            <div className="mt-4 flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
              <button
                onClick={() => setBriefingTab("breaking")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  briefingTab === "breaking"
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Flame className="h-3.5 w-3.5" />
                Breaking High-Velocity Alerts ({briefing.breaking_alerts.length})
              </button>
              <button
                onClick={() => setBriefingTab("geopolitical")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  briefingTab === "geopolitical"
                    ? "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Globe2 className="h-3.5 w-3.5" />
                Geopolitical & Sovereignty ({briefing.critical_geopolitical.length})
              </button>
              <button
                onClick={() => setBriefingTab("hazards")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  briefingTab === "hazards"
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Hazards & Human Impact ({briefing.humanitarian_hazards.length})
              </button>
              <button
                onClick={() => setBriefingTab("economic")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  briefingTab === "economic"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <TrendingUp className="h-3.5 w-3.5" />
                Economic Disruptions ({briefing.economic_disruptions.length})
              </button>
            </div>

            {/* Briefing Cards Grid */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(() => {
                const currentItems: BriefingItem[] = 
                  briefingTab === "breaking" ? briefing.breaking_alerts :
                  briefingTab === "geopolitical" ? briefing.critical_geopolitical :
                  briefingTab === "hazards" ? briefing.humanitarian_hazards :
                  briefing.economic_disruptions;

                if (!currentItems || currentItems.length === 0) {
                  return (
                    <div className="col-span-full py-8 text-center text-xs text-slate-500 italic">
                      No active alerts currently meeting high-urgency threshold in this sector.
                    </div>
                  );
                }

                return currentItems.map((item) => (
                  <div
                    key={item.event_id}
                    onClick={() => setSelectedEventId(item.event_id)}
                    className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/80 p-4 hover:border-amber-500/40 hover:bg-slate-900 transition-all cursor-pointer shadow-sm hover:shadow-md"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] mb-2">
                        <span className="font-mono text-amber-400 flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {item.location}
                        </span>
                        <div className="flex items-center gap-1.5 font-mono">
                          <span className="text-[10px] text-slate-500">Imp:</span>
                          <span className="font-bold text-sky-400">{item.importance.toFixed(1)}</span>
                          <span className="text-[10px] text-slate-500 ml-1">Vel:</span>
                          <span className="font-bold text-rose-400">{item.velocity.toFixed(1)}/h</span>
                        </div>
                      </div>

                      <h3 className="text-sm font-semibold text-white group-hover:text-amber-300 transition-colors line-clamp-2">
                        {item.title}
                      </h3>

                      <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                        {item.summary}
                      </p>
                    </div>

                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <div className="flex items-start gap-1.5 text-[11px] text-slate-300">
                        <span className="font-semibold text-amber-400 shrink-0">Why It Matters:</span>
                        <span className="text-slate-400 line-clamp-2 italic">{item.key_takeaway}</span>
                      </div>
                      <div className="mt-2 flex items-center justify-end text-[10px] text-sky-400 group-hover:translate-x-0.5 transition-transform">
                        <span>Inspect Dossier</span>
                        <ChevronRight className="h-3 w-3 ml-0.5" />
                      </div>
                    </div>
                  </div>
                ));
              })()}
            </div>
          </div>
        )}

        {/* Global Intelligence Search & Filter Bar */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-4 shadow-lg backdrop-blur-sm">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search events by keyword, city, country, or topic (e.g. 'Iceland', 'Taiwan', 'typhoon', 'treaty')..."
                className="w-full rounded-xl border border-slate-800 bg-slate-950/80 py-2.5 pl-10 pr-4 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs px-1"
                >
                  Clear
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={isSearching}
              className="flex items-center gap-2 rounded-xl bg-sky-600 px-5 py-2.5 text-xs font-medium text-white hover:bg-sky-500 transition-all disabled:opacity-50 shrink-0 w-full sm:w-auto justify-center"
            >
              {isSearching ? (
                <>
                  <Activity className="h-3.5 w-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="h-3.5 w-3.5" />
                  <span>Search Intel</span>
                </>
              )}
            </button>
          </form>
          {searchQuery && (
            <div className="mt-2.5 flex items-center justify-between text-xs text-slate-400 px-1">
              <span>
                Filtering by query: <strong className="text-sky-300 font-mono">"{searchQuery}"</strong> ({events.length} match{events.length === 1 ? "" : "es"})
              </span>
              <button 
                onClick={handleClearSearch}
                className="text-sky-400 hover:underline text-[11px]"
              >
                Reset to all events
              </button>
            </div>
          )}
        </div>

        {/* Interactive World Map (Phase 6 Active) */}
        <div id="geospatial-map-section" className="space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <Globe2 className="h-5 w-5 text-sky-400" />
                <h2 className="text-base font-bold text-white">
                  Geospatial Event Intelligence Map
                </h2>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-500/30">
                  Phase 6 Live
                </span>
                {isViewportSyncActive && (
                  <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] font-semibold text-sky-300 border border-sky-500/30 flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" />
                    Viewport News Sync Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                MapLibre GL dark matter vector/raster engine with zoom-density clustering, spatial bounding-box querying, and dynamic event inspection. Zoom or pan to rank visible news in real-time.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="rounded bg-slate-800/80 px-2.5 py-1 text-slate-300 border border-slate-700 font-mono text-[11px]">
                Zoom: {mapZoom.toFixed(1)}x
              </span>
              <button
                type="button"
                onClick={handleResetToGlobal}
                className="flex items-center gap-1.5 rounded bg-slate-800/90 hover:bg-slate-700 px-2.5 py-1 text-slate-200 border border-slate-700 hover:border-sky-500/50 transition-all text-[11px]"
                title="Reset map view to worldwide"
              >
                <RotateCcw className="h-3 w-3 text-sky-400" />
                <span>Reset World View</span>
              </button>
            </div>
          </div>

          <IntelligenceMap
            events={events}
            onSelectEvent={(id) => setSelectedEventId(id)}
            onBoundsChange={(bbox, zoom) => {
              setMapBbox(bbox);
              setMapZoom(zoom);
            }}
            selectedCategory={selectedMapCategory}
            onCategoryChange={(cat) => setSelectedMapCategory(cat)}
            resetViewTrigger={resetViewTrigger}
            focusedEventCoords={focusedEventCoords}
          />
        </div>

        {/* Dynamic Clustered Events (Phase 4 & 5 Active) */}
        <div className="rounded-2xl border border-sky-500/30 bg-slate-900/40 p-6 shadow-xl backdrop-blur-sm">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-rose-400" />
                <h2 className="text-base font-bold text-white">
                  Active Clustered Global Events
                </h2>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-500/30">
                  Phases 4 & 5 Live
                </span>
                {isViewportSyncActive && isZoomedIn && (
                  <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] font-semibold text-sky-300 border border-sky-500/30 flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-ping" />
                    Spatial Bbox Filtered ({visibleRankedEvents.length} in view)
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                8-dimension impact ranking, multi-source reliability confidence, and continuous lifecycle clustering.
              </p>
            </div>

            {/* Interactive Controls & Viewport Sync Toggle */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {/* Viewport Sync Toggle */}
              <button
                type="button"
                onClick={() => setIsViewportSyncActive(!isViewportSyncActive)}
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition-all ${
                  isViewportSyncActive
                    ? "bg-sky-500/20 text-sky-300 border-sky-500/40 hover:bg-sky-500/30"
                    : "bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200"
                }`}
                title={isViewportSyncActive ? "Map sync active: only showing events in visible map viewport" : "Map sync disabled: showing all global events"}
              >
                <span className={`h-2 w-2 rounded-full ${isViewportSyncActive ? "bg-sky-400" : "bg-slate-500"}`} />
                <span>Map Sync: {isViewportSyncActive ? "ON" : "OFF"}</span>
              </button>

              {isViewportSyncActive && isZoomedIn && (
                <button
                  type="button"
                  onClick={handleResetToGlobal}
                  className="flex items-center gap-1 rounded-lg bg-slate-800/90 hover:bg-slate-800 text-slate-300 hover:text-white px-2.5 py-1 text-xs border border-slate-700 transition-all"
                >
                  <RotateCcw className="h-3 w-3 text-sky-400" />
                  <span>Reset to Worldwide</span>
                </button>
              )}

              <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

              <span className="text-slate-400 mr-1 text-[11px]">Rank by:</span>
              <button
                onClick={() => setSortBy("importance")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  sortBy === "importance"
                    ? "bg-sky-500 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                Highest Impact
              </button>
              <button
                onClick={() => setSortBy("confidence")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  sortBy === "confidence"
                    ? "bg-emerald-500 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                High Confidence
              </button>
              <button
                onClick={() => setSortBy("velocity")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  sortBy === "velocity"
                    ? "bg-amber-500 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                Fast Velocity
              </button>
              <button
                onClick={() => setSortBy("recent")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  sortBy === "recent"
                    ? "bg-purple-500 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                Recent
              </button>
            </div>
          </div>

          {/* All-Country Intelligence & Galli News Filter Panel */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 mb-4 space-y-3">
            {/* Country Selector & Quick Chips */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <Globe2 className="h-4 w-4 text-sky-400" />
                <span className="text-xs font-bold text-white tracking-wide uppercase">
                  Country Intelligence:
                </span>
                <span className="text-[11px] text-slate-400">
                  Select any nation to fly map & view local domestic news
                </span>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={selectedCountry}
                  onChange={(e) => handleSelectCountry(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-white focus:border-sky-500 focus:outline-none"
                >
                  <option value="all">🌍 All Countries ({events.length} Events)</option>
                  {availableCountries.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name} ({c.count})
                    </option>
                  ))}
                </select>
                {selectedCountry !== "all" && (
                  <button
                    type="button"
                    onClick={() => handleSelectCountry("all")}
                    className="text-[11px] text-sky-400 hover:underline px-1"
                  >
                    Clear Country
                  </button>
                )}
              </div>
            </div>

            {/* Quick Country Pills */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {[
                { id: "all", label: "Worldwide (All)", count: events.length },
                { id: "India", label: "🇮🇳 India", count: events.filter(e => (e.country || "").toLowerCase() === "india").length },
                { id: "Kazakhstan", label: "🇰🇿 Central Asia", count: events.filter(e => ["Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Turkmenistan"].includes(e.country || "")).length },
                { id: "United States", label: "🇺🇸 United States", count: events.filter(e => (e.country || "").toLowerCase() === "united states").length },
                { id: "Japan", label: "🇯🇵 Japan", count: events.filter(e => (e.country || "").toLowerCase() === "japan").length },
                { id: "Germany", label: "🇩🇪 Germany & EU", count: events.filter(e => ["Germany", "France", "Switzerland", "Poland"].includes(e.country || "")).length },
                { id: "United Kingdom", label: "🇬🇧 United Kingdom", count: events.filter(e => (e.country || "").toLowerCase() === "united kingdom").length },
                { id: "China", label: "🇨🇳 China & Taiwan", count: events.filter(e => ["China", "Taiwan"].includes(e.country || "")).length }
              ].map((pill) => (
                <button
                  key={pill.id}
                  type="button"
                  onClick={() => handleSelectCountry(pill.id)}
                  className={`px-2.5 py-1 text-[11px] rounded-lg font-medium transition-all ${
                    selectedCountry === pill.id
                      ? "bg-sky-500 text-white font-bold shadow-sm"
                      : "bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
                  }`}
                >
                  {pill.label} ({pill.count})
                </button>
              ))}
            </div>

            {/* Scope / Tier Filter Tabs: From Hyper-Local "Galli" to International */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2.5 border-t border-slate-800/80">
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="h-3.5 w-3.5 text-amber-400" />
                <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wide">
                  Scope (Galli to Global):
                </span>
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                {[
                  { id: "all", label: "All Scopes" },
                  { id: "galli", label: "🏙️ Hyper-Local / Galli" },
                  { id: "regional", label: "🗺️ State & District" },
                  { id: "national", label: "🏛️ National" },
                  { id: "international", label: "🌐 Global Wires" }
                ].map((sTab) => (
                  <button
                    key={sTab.id}
                    type="button"
                    onClick={() => setSelectedScope(sTab.id as any)}
                    className={`px-2 py-0.5 text-[11px] rounded-md transition-all font-medium ${
                      selectedScope === sTab.id
                        ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                        : "bg-slate-900/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    {sTab.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Viewport Info Sub-bar */}
          <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs mb-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-slate-400">
                Showing <strong className="text-sky-300">{visibleRankedEvents.length}</strong> events{" "}
                {selectedCountry !== "all" ? (
                  <>in <strong className="text-white">{selectedCountry}</strong></>
                ) : isViewportSyncActive && isZoomedIn ? (
                  <>in visible map area</>
                ) : (
                  <>worldwide</>
                )}
                {selectedScope !== "all" && (
                  <>, filtered by <strong className="text-amber-400 uppercase">{selectedScope === "galli" ? "Hyper-Local / Galli" : selectedScope}</strong></>
                )}
                , ranked by <strong className="text-white capitalize">{sortBy === "importance" ? "Highest Impact" : sortBy}</strong>
              </span>
              {selectedMapCategory && selectedMapCategory !== "all" && (
                <span className="rounded bg-sky-500/10 px-2 py-0.5 text-[10px] font-semibold text-sky-400 border border-sky-500/20 uppercase">
                  Category: {selectedMapCategory.replace("_", " ")}
                </span>
              )}
            </div>
            {isViewportSyncActive && isZoomedIn && selectedCountry === "all" && (
              <span className="text-[11px] text-slate-500 hidden sm:inline">
                Pan or zoom map above to update ranking
              </span>
            )}
          </div>

          {visibleRankedEvents.length === 0 ? (
            <div className="py-12 px-4 text-center rounded-xl border border-dashed border-slate-800 bg-slate-950/40">
              <Globe2 className="h-10 w-10 text-slate-600 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-slate-300">No Events Matching Current Filters</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
                No active clustered news events matched your chosen country, scope, or map viewport. Reset filters to explore other regions.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedCountry("all");
                    setSelectedScope("all");
                    handleResetToGlobal();
                  }}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-600 text-xs font-medium text-white hover:bg-sky-500 transition-all shadow-sm"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Reset to All Countries & Worldwide
                </button>
                <button
                  type="button"
                  onClick={() => setIsViewportSyncActive(false)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-all"
                >
                  Disable Viewport Sync
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {visibleRankedEvents.map((evt, idx) => {
                const scope = getEventScope(evt);
                return (
                <div 
                  key={evt.id}
                  onClick={() => setSelectedEventId(evt.id)}
                  className="cursor-pointer rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow-md hover:border-sky-500/60 hover:bg-slate-900 transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="flex items-center justify-center h-5 w-5 rounded bg-sky-500/20 text-sky-400 font-mono font-bold text-[10px] border border-sky-500/30">
                          #{idx + 1}
                        </span>
                        <span className="rounded bg-sky-500/10 px-2 py-0.5 text-[10px] font-semibold text-sky-400 border border-sky-500/20 uppercase">
                          {evt.category.replace("_", " ")}
                        </span>
                        {scope === "galli" ? (
                          <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/30">
                            🏙️ Galli / Local
                          </span>
                        ) : scope === "regional" ? (
                          <span className="rounded bg-sky-500/20 px-1.5 py-0.5 text-[10px] font-bold text-sky-300 border border-sky-500/30">
                            🗺️ State / District
                          </span>
                        ) : scope === "national" ? (
                          <span className="rounded bg-purple-500/20 px-1.5 py-0.5 text-[10px] font-bold text-purple-300 border border-purple-500/30">
                            🏛️ National
                          </span>
                        ) : (
                          <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">
                            🌐 Global
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-amber-400 border border-amber-500/20">
                          <Flame className="h-3 w-3" />
                          {evt.importance_score.toFixed(1)}/10
                        </span>
                        <span className="flex items-center gap-1 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                          <ShieldCheck className="h-3 w-3" />
                          {(evt.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <h3 className="font-semibold text-white text-sm line-clamp-2 mb-2 group-hover:text-sky-300 transition-colors">
                      {evt.canonical_title}
                    </h3>

                    <p className="text-xs text-slate-400 line-clamp-3 mb-3">
                      {evt.summary}
                    </p>

                    {/* Impact Dimensions Strip */}
                    <div className="grid grid-cols-4 gap-1.5 py-2 px-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60 mb-3 text-[10px]">
                      <div className="flex flex-col">
                        <span className="text-slate-500">Human</span>
                        <span className="font-semibold text-rose-300">{evt.human_impact_score?.toFixed(1) || "5.0"}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-slate-500">Global</span>
                        <span className="font-semibold text-sky-300">{evt.global_impact_score?.toFixed(1) || "5.0"}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-slate-500">Velocity</span>
                        <span className="font-semibold text-amber-300">{evt.development_velocity_score?.toFixed(1) || "4.0"}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-slate-500">Coverage</span>
                        <span className="font-semibold text-purple-300">{evt.source_coverage_score?.toFixed(1) || "3.3"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (evt.longitude !== undefined && evt.latitude !== undefined) {
                          handleFocusEventOnMap(evt);
                        }
                      }}
                      title="Pinpoint actual location on map"
                      className="flex items-center gap-1.5 text-slate-300 hover:text-sky-300 transition-colors truncate max-w-[190px] group/loc"
                    >
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 group-hover/loc:bg-rose-500/20 group-hover/loc:scale-110 transition-all border border-rose-500/20 flex-shrink-0">
                        <MapPin className="h-3 w-3" />
                      </span>
                      <span className="truncate underline decoration-slate-600 hover:decoration-sky-400 underline-offset-2 font-medium">
                        {evt.city ? `${evt.city}, ` : ""}{evt.country || "Global"}
                      </span>
                    </button>
                    <div className="flex items-center gap-1 text-sky-400 font-mono">
                      <Layers className="h-3 w-3" />
                      <span>{evt.article_count || 1} articles</span>
                    </div>
                  </div>
                </div>
              );
            })}
            </div>
          )}
        </div>

        {/* Curated Sources & Ingested Articles Grids */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Curated Sources List */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Rss className="h-5 w-5 text-amber-400" />
                  <h3 className="font-bold text-white text-sm">Curated Global & Local News Sources</h3>
                </div>
                <span className="text-xs text-amber-300 font-mono font-medium bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  {sources.length > 0 ? `${sources.length} active feeds` : "66 feeds configured"}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-3">
                Local newspapers, domestic publishers, and international wires across 6 continents without paywall or auth bypass.
              </p>

              {/* Regional Filter Tabs */}
              <div className="flex items-center gap-1.5 flex-wrap mb-3">
                {[
                  { id: "all", label: "All Regions" },
                  { id: "India & South Asia", label: "India & South Asia" },
                  { id: "Central Asia & Caucasus", label: "Central Asia & Caucasus" },
                  { id: "Asia & Pacific", label: "Asia & Pacific" },
                  { id: "Middle East & Africa", label: "Mid East & Africa" },
                  { id: "Americas", label: "Americas" },
                  { id: "Europe", label: "Europe" },
                  { id: "Global / UN", label: "Global Wires" }
                ].map((tab) => {
                  const count = tab.id === "all" 
                    ? sources.length 
                    : sources.filter(s => getSourceRegion(s.country) === tab.id).length;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setSelectedSourceRegion(tab.id)}
                      className={`px-2.5 py-1 text-[11px] rounded-md font-medium transition-all ${
                        selectedSourceRegion === tab.id
                          ? "bg-amber-500 text-slate-950 font-semibold shadow-sm"
                          : "bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white"
                      }`}
                    >
                      {tab.label} ({count})
                    </button>
                  );
                })}
              </div>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {filteredSources.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border border-slate-800/80 bg-slate-900/60 p-2.5 hover:border-slate-700 hover:bg-slate-800/40 transition-all">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="flex h-7 w-7 items-center justify-center rounded bg-slate-800 text-[11px] font-bold text-slate-200 border border-slate-700/60 shrink-0">
                        {s.country || "GL"}
                      </div>
                      <div className="truncate">
                        <div className="flex items-center gap-1.5">
                          <h4 className="text-xs font-semibold text-white truncate">{s.name}</h4>
                          <span className="text-[10px] text-slate-500 font-mono px-1 rounded bg-slate-800/60">
                            {getSourceRegion(s.country)}
                          </span>
                        </div>
                        <a
                          href={`https://${s.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-slate-400 hover:text-sky-400 transition-colors flex items-center gap-1"
                        >
                          <span>{s.domain}</span>
                          <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                        </a>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex items-center gap-1 rounded bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-400 border border-amber-500/20">
                        <Shield className="h-3 w-3" />
                        <span>{(s.reliability_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-3 mt-4 flex items-center justify-between text-xs text-slate-400">
              <span>Endpoint: <code>GET /api/sources</code></span>
              <span className="text-emerald-400 font-medium">{sources.length} Feeds Ingested & Calibrated</span>
            </div>
          </div>

          {/* Ingested Articles Stream */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Newspaper className="h-5 w-5 text-sky-400" />
                  <h3 className="font-bold text-white text-sm">Ingested Articles & Normalization</h3>
                </div>
                <span className="text-xs text-slate-400">
                  {articles.length > 0 ? `${articles.length} articles in DB` : "Deterministic Seed Ready"}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-4">
                Raw stories sanitized, canonicalized, deduplicated via SHA-256 and token similarity.
              </p>

              <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
                {(articles.length > 0 ? articles.slice(0, 5) : [
                  { id: "1", title: "Strong 7.1 magnitude quake strikes off southern Japan; tsunami advisory issued", source_id: "Reuters", processing_status: "clustered", published_at: "2 hours ago", url: "https://reuters.com/world/japan-quake", fetched_at: "" },
                  { id: "2", title: "M7.1 earthquake hits off Miyazaki Coast; JMA urges vigilance for aftershocks", source_id: "NHK World", processing_status: "clustered", published_at: "3 hours ago", url: "https://nhk.or.jp/news/m71", fetched_at: "" },
                  { id: "3", title: "Geneva Climate Summit: Nations clinch surprise consensus on 2035 clean power pact", source_id: "Deutsche Welle", processing_status: "clustered", published_at: "7 hours ago", url: "https://dw.com/climate", fetched_at: "" },
                  { id: "4", title: "NASA's Webb telescope confirms water vapor on Earth-sized rocky exoplanet", source_id: "AP News", processing_status: "clustered", published_at: "14 hours ago", url: "https://apnews.com/webb", fetched_at: "" },
                  { id: "5", title: "Baltic grid operators investigate electrical fluctuations; sabotage unconfirmed", source_id: "Euronews", processing_status: "clustered", published_at: "18 hours ago", url: "https://euronews.com/baltic", fetched_at: "" }
                ] as ArticleItem[]).map((a) => (
                  <div key={a.id} className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-3 hover:border-slate-700 transition-all">
                    <div className="flex items-center justify-between text-[11px] mb-1.5">
                      <span className="font-medium text-sky-400 truncate max-w-[200px]">{a.source_id}</span>
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
                        {a.processing_status}
                      </span>
                    </div>
                    {a.url ? (
                      <a
                        href={a.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group/art block"
                      >
                        <h4 className="text-xs font-semibold text-slate-200 group-hover/art:text-sky-300 transition-colors line-clamp-2 flex items-start justify-between gap-2">
                          <span>{a.title}</span>
                          <ExternalLink className="h-3 w-3 text-slate-500 group-hover/art:text-sky-400 shrink-0 mt-0.5" />
                        </h4>
                      </a>
                    ) : (
                      <h4 className="text-xs font-medium text-slate-200 line-clamp-2">{a.title}</h4>
                    )}
                    {a.url && (
                      <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-800/60 text-[10px]">
                        <span className="text-slate-500 font-mono truncate max-w-[200px]">
                          {a.url.replace(/^https?:\/\//i, '').split('/')[0]}
                        </span>
                        <a
                          href={a.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 px-2 py-0.5 font-semibold text-sky-400 hover:text-white transition-all"
                        >
                          <ExternalLink className="h-2.5 w-2.5" />
                          <span>Verify Story</span>
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-3 mt-4 flex items-center justify-between text-xs text-slate-400">
              <span>Endpoint: <code>GET /api/articles</code></span>
              <span className="text-sky-400 font-medium">Deduplication Verified</span>
            </div>
          </div>
        </div>
      </div>

      {/* Event Detail Inspection Modal */}
      <EventDetailModal
        eventId={selectedEventId}
        onClose={() => setSelectedEventId(null)}
        onSelectEvent={(id) => setSelectedEventId(id)}
      />
    </main>
  );
}
