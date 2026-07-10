export function SkeletonLine({ width = "100%", height = "1rem" }: { width?: string; height?: string }) {
  return <div className="skeleton" style={{ width, height }} />;
}

export function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 space-y-2">
      <SkeletonLine width="60%" height="0.65rem" />
      <SkeletonLine width="40%" height="1.5rem" />
    </div>
  );
}

export function SkeletonCardGrid({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => <SkeletonCard key={i} />)}
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div className="space-y-1.5">
        <SkeletonLine width="10rem" height="0.85rem" />
        <SkeletonLine width="6rem" height="0.65rem" />
      </div>
      <SkeletonLine width="3.5rem" height="1.25rem" />
    </div>
  );
}

export function SkeletonList({ count = 5 }: { count?: number }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-ink-100 dark:divide-slate-700">
      {Array.from({ length: count }).map((_, i) => <SkeletonRow key={i} />)}
    </div>
  );
}
