// DiskMind API Client — with mock data fallback
// Set VITE_USE_MOCK=true or if backend is unreachable, falls back to mock data

import type {
  StorageSummary, Forecast, StorageSnapshot, Recommendation,
  Anomaly, SimulationResult, FileTypeBreakdown, DirectoryInfo, ChatMessage
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

async function apiWithFallback<T>(path: string, mockFn: () => T, options?: RequestInit): Promise<T> {
  if (USE_MOCK) return mockFn();
  try {
    return await apiFetch<T>(path, options);
  } catch {
    return mockFn();
  }
}

// ── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_SUMMARY: StorageSummary = {
  health_score: 62,
  utilization_pct: 85.5,
  used_bytes: 438_600_000_000,
  free_bytes: 73_400_000_000,
  total_bytes: 512_000_000_000,
  used_gb: 438.6,
  free_gb: 73.4,
  total_gb: 512,
  duplicate_wasted_bytes: 20_700_000_000,
  duplicate_wasted_gb: 20.7,
  inactive_bytes: 12_500_000_000,
  cache_bytes: 9_400_000_000,
  anomaly_count: 1,
  pending_recommendations: 6,
  total_recoverable_bytes: 31_700_000_000,
  total_recoverable_gb: 31.7,
  days_until_90pct: 13,
};

const now = Date.now() / 1000;

const MOCK_SNAPSHOTS: StorageSnapshot[] = Array.from({ length: 31 }, (_, i) => {
  const day = i - 30;
  const base = 408e9;
  const growth = 1.3e9 * (i);
  const spike = i === 20 ? 17e9 : 0;
  const used = base + growth + spike;
  return {
    id: i + 1,
    recorded_at: now + day * 86400,
    mount_point: '/',
    total_bytes: 512e9,
    used_bytes: used,
    free_bytes: 512e9 - used,
    file_count: 45000 + i * 50,
    daily_growth_bytes: i === 20 ? 17e9 : 1.3e9,
    utilization_pct: +((used / 512e9) * 100).toFixed(2),
  };
});

const MOCK_FORECAST: Forecast = {
  model_type: 'random_forest',
  training_samples: 31,
  avg_daily_growth_bytes: 1_300_000_000,
  current_used_bytes: 438_600_000_000,
  total_bytes: 512_000_000_000,
  predictions: {
    days_7:  { used_bytes: 447_700_000_000, free_bytes: 64_300_000_000, utilization_pct: 87.4 },
    days_14: { used_bytes: 456_800_000_000, free_bytes: 55_200_000_000, utilization_pct: 89.2 },
    days_30: { used_bytes: 477_600_000_000, free_bytes: 34_400_000_000, utilization_pct: 93.3 },
    days_60: { used_bytes: 516_600_000_000, free_bytes: 0,              utilization_pct: 100.0 },
    days_90: { used_bytes: 516_600_000_000, free_bytes: 0,              utilization_pct: 100.0 },
  },
  thresholds: {
    days_until_90pct: 13,
    days_until_95pct: 28,
    days_until_100pct: 56,
  },
  daily_series: Array.from({ length: 31 }, (_, i) => {
    const used = 438.6 + 1.3 * i;
    return { day: i, used_bytes: used * 1e9, utilization_pct: +((used / 512) * 100).toFixed(2) };
  }),
};

const MOCK_RECOMMENDATIONS: Recommendation[] = [
  {
    id: 1, created_at: now, action: 'CLEANUP',
    target_path: JSON.stringify(['/home/user/Downloads/vacation_2023.mp4', '/home/user/Downloads/family_dinner.mp4']),
    target_type: 'duplicate_group',
    size_bytes: 12_300_000_000, confidence: 0.998, risk_level: 'LOW', risk_score: 3,
    reason: '🔵 17.8 GB of duplicate video files detected',
    explanation: 'SHA-256 hash confirmed: exact identical copies. Keeping most recently accessed originals in ~/Videos. Moving 2 duplicates in ~/Downloads to Trash saves 12.3 GB.',
    status: 'PENDING', duplicate_group: 'abc123', category: 'duplicates',
  },
  {
    id: 2, created_at: now, action: 'CLEANUP',
    target_path: '[pip/yarn cache files]',
    target_type: 'file_type',
    size_bytes: 2_100_000_000, confidence: 0.97, risk_level: 'LOW', risk_score: 5,
    reason: '🟡 pip/yarn cache consuming 2.1 GB',
    explanation: 'Application cache files for pip and yarn. These are automatically regenerated on next install. 100% safe to remove.',
    status: 'PENDING', duplicate_group: null, category: 'cache',
  },
  {
    id: 3, created_at: now, action: 'CLEANUP',
    target_path: '[docker log files]',
    target_type: 'file_type',
    size_bytes: 4_200_000_000, confidence: 0.91, risk_level: 'LOW', risk_score: 8,
    reason: '🟠 Docker container logs consuming 4.2 GB',
    explanation: 'Docker container log files — source of the +17 GB anomaly spike detected on day 20. Safe to truncate. Docker will recreate these logs.',
    status: 'PENDING', duplicate_group: null, category: 'log',
  },
  {
    id: 4, created_at: now, action: 'CLEANUP',
    target_path: '[npm/cargo build artifacts]',
    target_type: 'file_type',
    size_bytes: 4_500_000_000, confidence: 0.88, risk_level: 'LOW', risk_score: 10,
    reason: '🟣 Build artifacts (node_modules, Rust target) consuming 4.5 GB',
    explanation: 'Compiled build output from old_webapp (last used 400 days ago). Regeneratable with npm install / cargo build.',
    status: 'PENDING', duplicate_group: null, category: 'build_artifact',
  },
  {
    id: 5, created_at: now, action: 'ARCHIVE',
    target_path: '/home/user/Downloads/old_dataset.tar.gz',
    target_type: 'file',
    size_bytes: 4_400_000_000, confidence: 0.84, risk_level: 'MEDIUM', risk_score: 22,
    reason: '⚪ Large archive not accessed for 420 days (inactivity: 88/100)',
    explanation: '4.4 GB compressed dataset not accessed in over a year. Consider archiving to external storage. Not safe to delete without review.',
    status: 'PENDING', duplicate_group: null, category: 'inactive',
  },
  {
    id: 6, created_at: now, action: 'CLEANUP',
    target_path: JSON.stringify(['/home/user/backup/ubuntu-22.04.iso']),
    target_type: 'duplicate_group',
    size_bytes: 3_800_000_000, confidence: 0.999, risk_level: 'LOW', risk_score: 2,
    reason: '🔵 Duplicate Ubuntu ISO in ~/backup',
    explanation: 'SHA-256 confirmed: identical copy of ubuntu-22.04.iso exists in ~/Downloads. Moving the ~/backup copy to Trash recovers 3.8 GB.',
    status: 'PENDING', duplicate_group: 'def456', category: 'duplicates',
  },
  {
    id: 7, created_at: now, action: 'KEEP',
    target_path: '/home/user/.ssh/config',
    target_type: 'file',
    size_bytes: 1024, confidence: 1.0, risk_level: 'PROTECTED', risk_score: 100,
    reason: '🔴 SSH configuration — PROTECTED',
    explanation: 'SSH configuration file. This path is permanently protected. DiskMind will never recommend deletion of SSH, GPG, or system configuration files.',
    status: 'PENDING', duplicate_group: null, category: 'config',
  },
];

const MOCK_ANOMALIES: Anomaly[] = [
  {
    id: 1, detected_at: now - 10 * 86400,
    anomaly_score: 0.87, growth_gb: 17.0,
    description: 'Abnormal storage growth detected: +17.0 GB in a single day',
    top_directories: JSON.stringify([
      { path: '/var/log/docker', size_bytes: 8_100_000_000 },
      { path: '/home/user/.cache/google-chrome', size_bytes: 4_200_000_000 },
      { path: '/home/user/Downloads', size_bytes: 3_700_000_000 },
      { path: '/home/user/Videos', size_bytes: 1_000_000_000 },
    ]),
    is_resolved: 0,
  },
];

const MOCK_DIRS: DirectoryInfo[] = [
  { top_dir: '/home/user/Downloads', total_size: 87_000_000_000, file_count: 234 },
  { top_dir: '/home/user/Videos', total_size: 64_000_000_000, file_count: 18 },
  { top_dir: '/home/user/Projects', total_size: 53_000_000_000, file_count: 12450 },
  { top_dir: '/home/user/.docker', total_size: 41_000_000_000, file_count: 89 },
  { top_dir: '/home/user/Documents', total_size: 21_000_000_000, file_count: 567 },
  { top_dir: '/home/user/.cache', total_size: 18_000_000_000, file_count: 4320 },
  { top_dir: '/var/log', total_size: 12_000_000_000, file_count: 145 },
  { top_dir: '/home/user/backup', total_size: 8_000_000_000, file_count: 23 },
  { top_dir: '/home/user/Music', total_size: 6_000_000_000, file_count: 892 },
  { top_dir: '/home/user/.local', total_size: 5_800_000_000, file_count: 2341 },
];

const MOCK_FILE_TYPES: FileTypeBreakdown[] = [
  { file_type: 'media',          file_count: 256,   total_bytes: 94_000_000_000, total_gb: 94.0 },
  { file_type: 'build_artifact', file_count: 18450, total_bytes: 72_000_000_000, total_gb: 72.0 },
  { file_type: 'archive',        file_count: 89,    total_bytes: 48_000_000_000, total_gb: 48.0 },
  { file_type: 'log',            file_count: 245,   total_bytes: 38_000_000_000, total_gb: 38.0 },
  { file_type: 'cache',          file_count: 8900,  total_bytes: 31_000_000_000, total_gb: 31.0 },
  { file_type: 'document',       file_count: 1200,  total_bytes: 24_000_000_000, total_gb: 24.0 },
  { file_type: 'source_code',    file_count: 15600, total_bytes: 18_000_000_000, total_gb: 18.0 },
  { file_type: 'config',         file_count: 3400,  total_bytes: 2_000_000_000,  total_gb: 2.0  },
  { file_type: 'other',          file_count: 4500,  total_bytes: 14_000_000_000, total_gb: 14.0 },
];

// ── API Functions ────────────────────────────────────────────────────────────

export const getOverview = () =>
  apiWithFallback('/api/storage/overview',
    () => ({ summary: MOCK_SUMMARY, forecast: MOCK_FORECAST })
  );

export const getSnapshots = (_limit = 30) =>
  apiWithFallback('/api/storage/snapshots', () => MOCK_SNAPSHOTS);

export const getDirectoryTree = () =>
  apiWithFallback('/api/storage/tree',
    () => ({ directories: MOCK_DIRS, file_types: MOCK_FILE_TYPES })
  );

export const triggerScan = () =>
  apiWithFallback('/api/storage/scan',
    () => ({ message: 'Demo mode: scan simulated', demo_mode: true })
  );

export const getRecommendations = () =>
  apiWithFallback('/api/ai/recommendations', () => MOCK_RECOMMENDATIONS);

export const sendChat = async (messages: ChatMessage[]) => {
  if (USE_MOCK) {
    const lastMsg = messages[messages.length - 1]?.content?.toLowerCase() || '';
    let response = '';
    if (lastMsg.includes('why') && lastMsg.includes('full')) {
      response = `Your disk is **85.5% full** (438.6 GB / 512 GB).\n\nThe largest contributors are:\n\n- 🔴 **Downloads**: 87 GB\n- 🎬 **Videos**: 64 GB (including 20.7 GB in duplicates)\n- 🔧 **Projects**: 53 GB (including 4.5 GB build artifacts)\n- 🐳 **Docker**: 41 GB\n\nI identified **31.7 GB** of potentially recoverable storage. At your current growth rate of **1.3 GB/day**, your disk will reach 90% capacity in approximately **13 days**.`;
    } else if (lastMsg.includes('safely') || lastMsg.includes('remove') || lastMsg.includes('clean')) {
      response = `Based on my analysis, you can safely recover **31.7 GB** with these LOW-risk actions:\n\n1. 🔵 **Duplicate videos** — 12.3 GB (99.8% confidence, LOW risk)\n2. 🟠 **Docker logs** — 4.2 GB (91% confidence, LOW risk)\n3. 🟣 **Build artifacts** — 4.5 GB (88% confidence, LOW risk)\n4. 🟡 **pip/yarn cache** — 2.1 GB (97% confidence, LOW risk)\n5. 🔵 **Duplicate ISO** — 3.8 GB (99.9% confidence, LOW risk)\n\n⚡ Total recoverable: **31.7 GB** | All actions require your explicit approval.`;
    } else if (lastMsg.includes('when') || lastMsg.includes('90') || lastMsg.includes('forecast') || lastMsg.includes('predict')) {
      response = `**Storage Forecast:**\n\n- Current: **85.5%** (438.6 GB / 512 GB)\n- Daily growth: **1.3 GB/day**\n- ⚠️ **90% capacity**: 13 days from now\n- 🔴 **95% capacity**: 28 days from now\n- 💀 **100% capacity**: 56 days from now\n\nIf you execute the recommended 31.7 GB cleanup, the 90% threshold would be delayed by approximately **+24 days** (from day 13 to day 37).`;
    } else if (lastMsg.includes('anomal') || lastMsg.includes('spike')) {
      response = `⚠️ **Anomaly Detected on Day -10:**\n\nAn abnormal storage growth spike of **+17 GB in a single day** was detected 10 days ago.\n\n**Root causes identified:**\n- 🐳 /var/log/docker — +8.1 GB\n- 🌐 Browser cache — +4.2 GB  \n- 📥 Downloads — +3.7 GB\n\nAnomalyy score: **87/100** (high severity). Isolation Forest model flagged this as a statistical outlier based on 31 days of history.`;
    } else {
      response = `👋 I'm **DiskMind**, your AI Storage Copilot.\n\n**Current Status:**\n- 🏥 Health Score: **62/100**\n- 💾 Disk Usage: **85.5%** (438.6 / 512 GB)\n- ♻️ Recoverable: **31.7 GB**\n- ⏰ 90% in: **13 days**\n- ⚠️ Anomalies: **1 detected**\n\nTry asking:\n- *"Why is my disk almost full?"*\n- *"What can I safely remove?"*\n- *"When will I reach 90% capacity?"*\n- *"What caused the storage spike?"*`;
    }
    return { response, tool_calls: [] };
  }
  return apiFetch<{ response: string; tool_calls: unknown[] }>('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, session_id: 'default' }),
  });
};

export const simulate = (recommendation_ids: number[]) => {
  const mockResult: SimulationResult = {
    selected_recommendations: recommendation_ids.length,
    total_recoverable_bytes: 31_700_000_000,
    total_recoverable_gb: 31.7,
    before: {
      used_bytes: 438_600_000_000, free_bytes: 73_400_000_000,
      utilization_pct: 85.5, used_gb: 438.6, free_gb: 73.4,
      days_until_90pct: 13, days_until_95pct: 28, days_until_100pct: 56,
    },
    after: {
      used_bytes: 406_900_000_000, free_bytes: 105_100_000_000,
      utilization_pct: 79.5, used_gb: 406.9, free_gb: 105.1,
      days_until_90pct: 37, days_until_95pct: 52, days_until_100pct: 80,
    },
    impact: { days_gained_until_90pct: 24, utilization_reduction_pct: 6.0 },
    recommendations: MOCK_RECOMMENDATIONS
      .filter(r => recommendation_ids.includes(r.id))
      .map(r => ({
        id: r.id, category: r.category || 'other',
        reason: r.reason, size_gb: r.size_bytes / 1e9, risk_level: r.risk_level,
      })),
  };
  return apiWithFallback('/api/ai/simulate', () => mockResult, {
    method: 'POST',
    body: JSON.stringify({ recommendation_ids }),
  });
};

export const getForecast = () =>
  apiWithFallback('/api/forecast/prediction', () => MOCK_FORECAST);

export const getAnomalies = () =>
  apiWithFallback('/api/forecast/anomalies',
    () => ({ anomalies: MOCK_ANOMALIES, count: 1 })
  );

export const approveRecommendations = (ids: number[]) =>
  apiWithFallback('/api/cleanup/approve', () => ({ approved: ids, count: ids.length }), {
    method: 'POST', body: JSON.stringify({ recommendation_ids: ids }),
  });

export const executeRecommendations = (ids: number[]) =>
  apiWithFallback('/api/cleanup/execute', () => ({
    results: ids.map(id => ({ rec_id: id, status: 'executed_demo' })),
    total_recovered_bytes: 31_700_000_000,
    total_recovered_gb: 31.7,
  }), { method: 'POST', body: JSON.stringify({ recommendation_ids: ids }) });

export const getActionHistory = () =>
  apiWithFallback('/api/cleanup/history', () => []);

export const undoAction = (id: number) =>
  apiWithFallback(`/api/cleanup/undo/${id}`, () => ({ restored: 'demo' }), { method: 'POST' });
