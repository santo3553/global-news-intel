export interface ComponentHealth {
  status: "connected" | "disconnected" | "degraded";
  latency_ms?: number;
  details?: Record<string, any>;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  timestamp: string;
  database: ComponentHealth;
  redis: ComponentHealth;
}

export interface SourceItem {
  id: string;
  name: string;
  domain: string;
  feed_url: string;
  source_type: string;
  country?: string;
  language: string;
  reliability_score: number;
  active: boolean;
}

export interface ArticleItem {
  id: string;
  source_id: string;
  title: string;
  url: string;
  canonical_url?: string;
  author?: string;
  published_at?: string;
  fetched_at: string;
  language: string;
  cleaned_content?: string;
  processing_status: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Health check returned status HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err: any) {
    return {
      status: "unhealthy",
      version: "unknown",
      environment: "disconnected",
      timestamp: new Date().toISOString(),
      database: {
        status: "disconnected",
        details: { error: err.message || "Failed to reach backend API" },
      },
      redis: {
        status: "disconnected",
      },
    };
  }
}

export async function fetchSources(): Promise<SourceItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/sources`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchArticles(limit: number = 10): Promise<ArticleItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/articles?limit=${limit}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export interface EventItem {
  id: string;
  canonical_title: string;
  summary: string;
  category: string;
  subcategory?: string;
  latitude: number;
  longitude: number;
  country?: string;
  admin_region?: string;
  city?: string;
  location_confidence: number;
  importance_score: number;
  confidence_score: number;
  human_impact_score: number;
  global_impact_score: number;
  economic_impact_score: number;
  political_impact_score: number;
  novelty_score: number;
  development_velocity_score: number;
  source_coverage_score: number;
  first_seen_at: string;
  last_updated_at: string;
  status: string;
  article_count?: number;
}

export interface EventDetailItem extends EventItem {
  articles: ArticleItem[];
  entities: Array<{
    id: string;
    name: string;
    entity_type: string;
    mentions_count?: number;
  }>;
}

export interface NearbyEventItem extends EventItem {
  distance_km: number;
}

export async function fetchEvents(limit: number = 20, sortBy: string = "importance"): Promise<EventItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events?limit=${limit}&sort_by=${sortBy}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchEventsWithBbox(
  bbox: string,
  category?: string,
  minImportance?: number,
  sortBy: string = "importance",
  limit: number = 100
): Promise<EventItem[]> {
  try {
    const params = new URLSearchParams({
      bbox,
      sort_by: sortBy,
      limit: String(limit)
    });
    if (category) params.append("category", category);
    if (minImportance !== undefined) params.append("min_importance", String(minImportance));

    const res = await fetch(`${API_BASE_URL}/api/events?${params.toString()}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchTopEvents(limit: number = 5): Promise<EventItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/top?limit=${limit}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchEventDetail(eventId: string): Promise<EventDetailItem | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchNearbyEvents(lat: number, lng: number, radiusKm: number = 300): Promise<NearbyEventItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/nearby?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export interface BriefingItem {
  event_id: string;
  title: string;
  category: string;
  location: string;
  importance: number;
  confidence: number;
  velocity: number;
  summary: string;
  key_takeaway: string;
}

export interface IntelligenceBriefingResponse {
  generated_at: string;
  executive_summary: string;
  total_events_analyzed: number;
  breaking_alerts: BriefingItem[];
  critical_geopolitical: BriefingItem[];
  humanitarian_hazards: BriefingItem[];
  economic_disruptions: BriefingItem[];
}

export interface TimelineEntry {
  article_id: string;
  title: string;
  source_name: string;
  source_domain: string;
  published_at?: string;
  relationship_type: string;
  similarity_score: number;
  excerpt?: string;
}

export interface EventTimelineResponse {
  event_id: string;
  canonical_title: string;
  first_seen_at: string;
  last_updated_at: string;
  total_articles: number;
  timeline: TimelineEntry[];
}

export async function fetchBriefing(): Promise<IntelligenceBriefingResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/briefing`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function searchEvents(q: string, limit: number = 20): Promise<EventItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/search?q=${encodeURIComponent(q)}&limit=${limit}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchEventTimeline(eventId: string): Promise<EventTimelineResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/${eventId}/timeline`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface PipelineTelemetry {
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  sources_checked: number;
  articles_fetched: number;
  articles_inserted: number;
  duplicates_skipped: number;
  articles_processed: number;
  events_created: number;
  events_updated: number;
  events_decayed: number;
  status: string;
  errors: string[];
}

export interface PipelineStatusResponse {
  daemon_active: boolean;
  interval_seconds: number;
  total_cycles_run: number;
  last_run_at: string | null;
  last_telemetry: PipelineTelemetry | null;
}

export async function triggerPipelineRun(maxFeeds?: number): Promise<PipelineTelemetry | null> {
  try {
    const url = maxFeeds 
      ? `${API_BASE_URL}/api/pipeline/run?max_feeds=${maxFeeds}`
      : `${API_BASE_URL}/api/pipeline/run`;

    const res = await fetch(url, {
      method: "POST",
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchPipelineStatus(): Promise<PipelineStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/pipeline/status`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}


