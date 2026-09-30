"use client";

import { useEffect, useState } from "react";
import { 
  X, 
  MapPin, 
  Flame, 
  ShieldCheck, 
  Activity, 
  Layers, 
  ExternalLink, 
  Radio, 
  Clock, 
  Globe2, 
  Compass,
  AlertCircle,
  GitCommit,
  History
} from "lucide-react";
import { 
  EventItem, 
  EventDetailItem, 
  NearbyEventItem, 
  EventTimelineResponse,
  fetchEventDetail, 
  fetchNearbyEvents,
  fetchEventTimeline 
} from "@/lib/api";

interface EventDetailModalProps {
  eventId: string | null;
  onClose: () => void;
  onSelectEvent: (eventId: string) => void;
}

export default function EventDetailModal({
  eventId,
  onClose,
  onSelectEvent
}: EventDetailModalProps) {
  const [detail, setDetail] = useState<EventDetailItem | null>(null);
  const [nearby, setNearby] = useState<NearbyEventItem[]>([]);
  const [timeline, setTimeline] = useState<EventTimelineResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "articles">("timeline");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!eventId) return;

    let isMounted = true;
    setLoading(true);

    async function loadData() {
      const [data, timelineData] = await Promise.all([
        fetchEventDetail(eventId!),
        fetchEventTimeline(eventId!)
      ]);
      if (!isMounted) return;
      setDetail(data);
      setTimeline(timelineData);

      if (data && data.latitude !== undefined && data.longitude !== undefined) {
        const nearbyEvents = await fetchNearbyEvents(data.latitude, data.longitude, 500);
        if (isMounted) {
          // Filter out current event
          setNearby(nearbyEvents.filter(e => e.id !== data.id).slice(0, 4));
        }
      }
      if (isMounted) setLoading(false);
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [eventId]);

  if (!eventId) return null;

  const categoryColors: Record<string, string> = {
    natural_disaster: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    security: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    conflict: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    politics: "bg-sky-500/10 text-sky-400 border-sky-500/30",
    economy: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    science: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  };

  const catStyle = detail?.category ? (categoryColors[detail.category] || "bg-sky-500/10 text-sky-400 border-sky-500/30") : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div 
        className="relative flex h-full w-full max-w-2xl flex-col bg-[#0b1329] border-l border-slate-800 text-slate-100 shadow-2xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-6 py-4 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-rose-400 animate-pulse" />
            <span className="text-xs font-bold tracking-widest text-slate-400 uppercase">
              Intelligence Dossier
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-all"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex flex-1 items-center justify-center p-12 text-slate-400">
            <Activity className="h-6 w-6 animate-spin text-sky-400 mr-3" />
            <span>Assembling event telemetry & source corroboration...</span>
          </div>
        ) : !detail ? (
          <div className="p-8 text-center text-slate-400">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 text-rose-400" />
            <span>Event data currently unavailable</span>
          </div>
        ) : (
          <div className="flex-1 space-y-6 p-6">
            {/* Badges & Meta */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className={`rounded px-2.5 py-0.5 text-xs font-bold border uppercase ${catStyle}`}>
                  {detail.category.replace("_", " ")}
                </span>
                {detail.subcategory && (
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300">
                    {detail.subcategory}
                  </span>
                )}
                <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[11px] font-mono text-slate-300">
                  Status: <strong className="text-emerald-400">{detail.status}</strong>
                </span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 rounded bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-400 border border-amber-500/20">
                  <Flame className="h-3.5 w-3.5" />
                  <span>Impact: {detail.importance_score.toFixed(1)}/10</span>
                </div>
                <div className="flex items-center gap-1 rounded bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Conf: {(detail.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            {/* Canonical Title & Summary */}
            <div>
              <h2 className="text-xl font-bold text-white leading-snug">
                {detail.canonical_title}
              </h2>
              <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
                <MapPin className="h-3.5 w-3.5 text-rose-400" />
                <span className="text-slate-200">
                  {detail.city ? `${detail.city}, ` : ""}{detail.admin_region ? `${detail.admin_region}, ` : ""}{detail.country || "Global"}
                </span>
                <span className="font-mono text-slate-500">
                  ({detail.latitude.toFixed(2)}°, {detail.longitude.toFixed(2)}°)
                </span>
                <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400">
                  Loc Conf: {(detail.location_confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
                {detail.summary}
              </p>
            </div>

            {/* 8-Dimensional Impact Radar / Gauge Breakdown */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <Compass className="h-4 w-4 text-sky-400" />
                Multi-Impact Evaluation Matrix (Section 16)
              </h3>

              <div className="space-y-3">
                {[
                  { label: "Human Impact (Casualties / Population)", score: detail.human_impact_score, weight: "25%", color: "bg-rose-500" },
                  { label: "Global & Geopolitical Ramifications", score: detail.global_impact_score, weight: "20%", color: "bg-sky-500" },
                  { label: "Economic & Supply Chain Disruption", score: detail.economic_impact_score, weight: "10%", color: "bg-emerald-500" },
                  { label: "Political Stability Impact", score: detail.political_impact_score, weight: "10%", color: "bg-indigo-500" },
                  { label: "Novelty & Historical Precedent", score: detail.novelty_score, weight: "10%", color: "bg-amber-500" },
                  { label: "Development Velocity", score: detail.development_velocity_score, weight: "5%", color: "bg-orange-500" },
                  { label: "Multi-Source Coverage Breadth", score: detail.source_coverage_score, weight: "5%", color: "bg-purple-500" }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{item.label}</span>
                      <span className="font-mono text-slate-400">
                        {item.score?.toFixed(1) || "5.0"}/10 <span className="text-slate-500 text-[10px]">({item.weight})</span>
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                      <div 
                        className={`h-full ${item.color} transition-all duration-500`}
                        style={{ width: `${Math.min(100, ((item.score || 5.0) / 10) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tabbed Chronological Timeline & Corroborating Articles */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
              <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab("timeline")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      activeTab === "timeline"
                        ? "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <History className="h-3.5 w-3.5" />
                    Evolution Timeline ({timeline?.total_articles || detail.articles?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("articles")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      activeTab === "articles"
                        ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Layers className="h-3.5 w-3.5" />
                    Corroborating Dispatches ({detail.articles?.length || 0})
                  </button>
                </div>
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  Section 23
                </span>
              </div>

              {activeTab === "timeline" ? (
                <div className="space-y-4 max-h-72 overflow-y-auto pr-2 relative">
                  {timeline && timeline.timeline.length > 0 ? (
                    <div className="relative pl-6 border-l-2 border-slate-800 space-y-4 ml-2">
                      {timeline.timeline.map((entry, idx) => {
                        const relBadge = 
                          entry.relationship_type === "primary"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : entry.relationship_type === "update"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            : "bg-sky-500/10 text-sky-400 border-sky-500/30";

                        return (
                          <div key={entry.article_id || idx} className="relative group">
                            <span 
                              className={`absolute -left-[31px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-slate-950 ${
                                entry.relationship_type === "primary" 
                                  ? "bg-emerald-400" 
                                  : entry.relationship_type === "update" 
                                  ? "bg-amber-400" 
                                  : "bg-sky-400"
                              }`}
                            />
                            <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 hover:border-slate-700 transition-all">
                              <div className="flex items-center justify-between text-[11px] mb-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-slate-200">{entry.source_name}</span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase font-mono ${relBadge}`}>
                                    {entry.relationship_type}
                                  </span>
                                </div>
                                {entry.published_at && (
                                  <span className="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                                    <Clock className="h-3 w-3" />
                                    {new Date(entry.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })}
                                  </span>
                                )}
                              </div>
                              <h4 className="text-xs font-medium text-slate-100 mb-1">
                                {entry.title}
                              </h4>
                              {entry.excerpt && (
                                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                                  {entry.excerpt}
                                </p>
                              )}
                              <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                                <span>Domain: {entry.source_domain}</span>
                                <span className="font-mono text-sky-400">Similarity: {(entry.similarity_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic p-2">Chronological timeline synthesized from founding report.</p>
                  )}
                </div>
              ) : (
                <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                  {detail.articles && detail.articles.length > 0 ? (
                    detail.articles.map((art) => (
                      <div 
                        key={art.id}
                        className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 hover:border-slate-700 transition-all"
                      >
                        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                          <span className="font-semibold text-sky-400">{art.source_id}</span>
                          {art.published_at && (
                            <span className="flex items-center gap-1 font-mono text-[10px]">
                              <Clock className="h-3 w-3" />
                              {new Date(art.published_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                        <h4 className="text-xs font-medium text-slate-200 line-clamp-2">
                          {art.title}
                        </h4>
                        {art.url && (
                          <a
                            href={art.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-2 inline-flex items-center gap-1 text-[10px] text-sky-400 hover:underline"
                          >
                            <ExternalLink className="h-3 w-3" />
                            <span>View original dispatch</span>
                          </a>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 italic">Founding primary wire report linked.</p>
                  )}
                </div>
              )}
            </div>

            {/* Nearby Related Events */}
            {nearby.length > 0 && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                  <Globe2 className="h-4 w-4 text-emerald-400" />
                  Nearby Geographic Events (&lt;500 km)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {nearby.map((evt) => (
                    <button
                      key={evt.id}
                      onClick={() => onSelectEvent(evt.id)}
                      className="text-left rounded-lg border border-slate-800 bg-slate-900/60 p-3 hover:border-sky-500/40 transition-all flex flex-col justify-between"
                    >
                      <span className="text-xs font-medium text-white line-clamp-2">
                        {evt.canonical_title}
                      </span>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
                        <span>{evt.city || evt.country}</span>
                        <span className="font-mono text-emerald-400">~{evt.distance_km} km away</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
