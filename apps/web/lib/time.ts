/**
 * Global Real-Time News Intelligence Time Formatting Utility
 * Provides relative live time formatting ('Just now', '4m ago', '2h ago')
 * and breaking status detection for real-time news tracking.
 */

export function formatTimeAgo(dateString?: string | null): string {
  if (!dateString) return "Just now";

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Just now";

    const now = Date.now();
    const diffMs = now - date.getTime();

    // If future timestamp or within 60 seconds
    if (diffMs < 60_000) {
      return "Just now";
    }

    const diffMinutes = Math.floor(diffMs / 60_000);
    if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    }

    const diffHours = Math.floor(diffMs / 3_600_000);
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }

    const diffDays = Math.floor(diffMs / 86_400_000);
    if (diffDays < 30) {
      return `${diffDays}d ago`;
    }

    // Fallback to month & day for older archives
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "Just now";
  }
}

/**
 * Returns true if the event/article was published or updated within the last 45 minutes
 */
export function isLiveBreaking(dateString?: string | null): boolean {
  if (!dateString) return false;

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return false;

    const diffMs = Date.now() - date.getTime();
    return diffMs >= 0 && diffMs <= 45 * 60_000;
  } catch {
    return false;
  }
}

/**
 * Format exact human-readable date & time for hover tooltips
 */
export function formatExactTime(dateString?: string | null): string {
  if (!dateString) return "N/A";

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "N/A";

    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  } catch {
    return "N/A";
  }
}
