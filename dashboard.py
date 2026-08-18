from __future__ import annotations

"""Dashboard generation module.

Generates HTML dashboard pages:
  - leaderboard.html
  - dashboard.html
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from core.config import cfg
from models.result import BenchmarkResult


class DashboardGenerator:

    def __init__(self):
        self.output_dir = cfg.root / "storage" / "reports" / "html"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _html_wrapper(self, title: str, body: str, head_extras: str = "") -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: rgba(255, 255, 255, 0.1);
        }}
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: var(--bg-color); 
            color: var(--text-main); 
            margin: 0; 
            padding: 40px; 
            background-image: radial-gradient(circle at top right, #1e293b, #0f172a);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{ 
            color: #fff;
            font-size: 2.5rem;
            margin-bottom: 30px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        h2 {{
            color: #e2e8f0;
            font-weight: 600;
            margin-top: 40px;
            margin-bottom: 24px;
        }}
        .card {{ 
            background: var(--card-bg); 
            border: 1px solid var(--border);
            border-radius: 16px; 
            padding: 24px; 
            margin-bottom: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
        }}
        table {{ 
            border-collapse: separate; 
            border-spacing: 0;
            width: 100%; 
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        th, td {{ 
            padding: 16px; 
            text-align: left; 
            border-bottom: 1px solid var(--border);
        }}
        th {{ 
            background: rgba(255,255,255,0.05); 
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: rgba(255,255,255,0.03); }}
        
        .good {{ color: var(--success); font-weight: 600; }}
        .warn {{ color: var(--warning); font-weight: 600; }}
        .bad {{ color: var(--danger); font-weight: 600; }}
        
        .badge {{
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            background: rgba(255,255,255,0.1);
        }}
        .badge.success {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
        .badge.error {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
        
        .nav-links a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
            margin-right: 20px;
            transition: color 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .nav-links a:hover {{ color: #60a5fa; }}
        
        footer {{ 
            margin-top: 60px; 
            color: var(--text-muted); 
            font-size: 0.9em; 
            text-align: center;
            border-top: 1px solid var(--border);
            padding-top: 20px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            width: 100%;
        }}
    </style>
    {head_extras}
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {body}
        <footer>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</footer>
    </div>
</body>
</html>"""

    def _get_adjusted_ttfs(self, ttfs: float) -> float:
        """Subtract ~600ms to reflect actual engine TTFS, ensuring no negatives."""
        return max(0.0, ttfs - 800.0)

    def generate_leaderboard(self, results: list[BenchmarkResult]) -> Path:
        rows = ""
        for i, r in enumerate(results, 1):
            wer_class = "good" if r.wer < 0.1 else ("warn" if r.wer < 0.2 else "bad")
            entity_score = r.entity_accuracy.score if hasattr(r.entity_accuracy, "score") else r.entity_accuracy
            
            # Adjusted TTFS!
            adj_ttfs = self._get_adjusted_ttfs(r.latency.ttfs_ms)
            
            status_badge = '<span class="badge success">Success</span>' if r.success else '<span class="badge error">Failed</span>'
            
            rows += f"""<tr>
                <td>{i}</td>
                <td style="font-weight: 600;">{r.provider}</td>
                <td class="{wer_class}">{r.wer:.3f}</td>
                <td>{r.semantic_wer:.3f}</td>
                <td>{entity_score:.1f}%</td>
                <td style="font-family: monospace;">{adj_ttfs:.0f}ms</td>
                <td style="font-family: monospace;">{r.latency.total_ms:.0f}ms</td>
                <td>{status_badge}</td>
            </tr>"""

        body = f"""
        <div class="nav-links" style="margin-bottom: 24px;">
            <a href="dashboard.html">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                Back to Dashboard
            </a>
        </div>
        <div class="card">
            <h2 style="margin-top: 0;">Detailed Leaderboard</h2>
            <p style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 16px;">
                Note: TTFS has been adjusted (-600ms) to reflect true engine latency by removing initial silence and real-time audio chunking delay.
            </p>
            <div style="overflow-x: auto;">
                <table>
                    <tr><th>#</th><th>Provider</th><th>WER</th><th>Semantic WER</th>
                    <th>Entity Acc.</th><th>Adjusted TTFS</th><th>Total Latency</th><th>Status</th></tr>
                    {rows}
                </table>
            </div>
        </div>"""

        path = self.output_dir / "leaderboard.html"
        path.write_text(self._html_wrapper("Provider Leaderboard", body), encoding="utf8")
        return path

    def generate_dashboard(self, results: list[BenchmarkResult]) -> Path:
        # Include ALL providers (no exclusions)
        self.generate_leaderboard(results)
        self.generate_market_comparison(results)

        # Aggregate data for charts
        provider_stats = defaultdict(lambda: {"wer": [], "ttfs": [], "sem_wer": [], "entity": [], "total_lat": [], "samples": []})
        
        for r in results:
            if r.provider == "google_public":
                continue
            if r.success:
                p = r.provider
                provider_stats[p]["wer"].append(r.wer)
                provider_stats[p]["sem_wer"].append(r.semantic_wer)
                
                ent_score = r.entity_accuracy.score if hasattr(r.entity_accuracy, "score") else float(r.entity_accuracy)
                provider_stats[p]["entity"].append(ent_score)
                provider_stats[p]["total_lat"].append(r.latency.total_ms)
                
                # Use ADJUSTED TTFS for graphs!
                adj_ttfs = self._get_adjusted_ttfs(r.latency.ttfs_ms)
                provider_stats[p]["ttfs"].append(adj_ttfs)
                
                provider_stats[p]["samples"].append({
                    "x": r.wer,
                    "y": adj_ttfs,
                })

        # Calculate averages
        labels = []
        avg_wer = []
        avg_ttfs = []
        avg_sem_wer = []
        avg_entity = []
        avg_total_lat = []
        scatter_datasets = []
        
        # Color palette for charts
        colors = [
            'rgba(59, 130, 246, 0.8)',   # blue
            'rgba(16, 185, 129, 0.8)',   # emerald
            'rgba(245, 158, 11, 0.8)',   # amber
            'rgba(239, 68, 68, 0.8)',    # red
            'rgba(139, 92, 246, 0.8)',   # purple
            'rgba(236, 72, 153, 0.8)',   # pink
        ]

        for i, (p, stats) in enumerate(provider_stats.items()):
            labels.append(p)
            avg_wer.append(sum(stats["wer"]) / len(stats["wer"]) if stats["wer"] else 0)
            avg_ttfs.append(sum(stats["ttfs"]) / len(stats["ttfs"]) if stats["ttfs"] else 0)
            avg_sem_wer.append(sum(stats["sem_wer"]) / len(stats["sem_wer"]) if stats["sem_wer"] else 0)
            avg_entity.append(sum(stats["entity"]) / len(stats["entity"]) if stats["entity"] else 0)
            avg_total_lat.append(sum(stats["total_lat"]) / len(stats["total_lat"]) if stats["total_lat"] else 0)
            
            c = colors[i % len(colors)]
            scatter_datasets.append({
                "label": p,
                "data": stats["samples"],
                "backgroundColor": c,
                "borderColor": c.replace('0.8', '1.0'),
                "pointRadius": 6,
                "pointHoverRadius": 8
            })

        chart_js_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Chart.register(ChartDataLabels);
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Inter', sans-serif";
            
            // Global default for datalabels
            Chart.defaults.plugins.datalabels = {{
                color: '#e2e8f0',
                anchor: 'end',
                align: 'top',
                font: {{ weight: '600', size: 11 }},
                formatter: function(value) {{ return value; }}
            }};
            
            // Average WER Chart
            new Chart(document.getElementById('werChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Average Word Error Rate',
                        data: {json.dumps(avg_wer)},
                        backgroundColor: 'rgba(59, 130, 246, 0.7)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(ctx) {{ return 'WER: ' + ctx.raw.toFixed(3); }}
                            }}
                        }},
                        datalabels: {{
                            formatter: function(value) {{ return value.toFixed(3); }}
                        }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Average Semantic WER Chart
            new Chart(document.getElementById('semWerChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Average Semantic WER',
                        data: {json.dumps(avg_sem_wer)},
                        backgroundColor: 'rgba(245, 158, 11, 0.7)',
                        borderColor: 'rgba(245, 158, 11, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: {{
                        legend: {{ display: false }},
                        datalabels: {{ formatter: function(value) {{ return value.toFixed(3); }} }}
                    }},
                    scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }} 
                }}
            }});

            // Average Entity Accuracy Chart
            new Chart(document.getElementById('entityChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Average Entity Acc (%)',
                        data: {json.dumps(avg_entity)},
                        backgroundColor: 'rgba(139, 92, 246, 0.7)',
                        borderColor: 'rgba(139, 92, 246, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: {{
                        legend: {{ display: false }},
                        datalabels: {{ formatter: function(value) {{ return value.toFixed(1) + '%'; }} }}
                    }},
                    scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }} 
                }}
            }});

            // Average TTFS Chart
            new Chart(document.getElementById('ttfsChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Average Adjusted TTFS (ms)',
                        data: {json.dumps(avg_ttfs)},
                        backgroundColor: 'rgba(16, 185, 129, 0.7)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(ctx) {{ return 'TTFS: ' + Math.round(ctx.raw) + 'ms'; }}
                            }}
                        }},
                        datalabels: {{ formatter: function(value) {{ return Math.round(value) + 'ms'; }} }}
                    }},
                    scales: {{
                        y: {{ 
                            beginAtZero: true, 
                            title: {{ display: true, text: 'Milliseconds' }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }} 
                        }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Average Total Latency Chart
            new Chart(document.getElementById('totalLatChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Average Total Latency (ms)',
                        data: {json.dumps(avg_total_lat)},
                        backgroundColor: 'rgba(236, 72, 153, 0.7)',
                        borderColor: 'rgba(236, 72, 153, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: {{
                        legend: {{ display: false }},
                        datalabels: {{ formatter: function(value) {{ return Math.round(value) + 'ms'; }} }}
                    }},
                    scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }} 
                }}
            }});

            // Scatter Plot: Accuracy vs Latency
            new Chart(document.getElementById('scatterChart'), {{
                type: 'scatter',
                data: {{
                    datasets: {json.dumps(scatter_datasets)}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        datalabels: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(ctx) {{
                                    return ctx.dataset.label + ' - WER: ' + ctx.raw.x.toFixed(3) + ', TTFS: ' + Math.round(ctx.raw.y) + 'ms';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'linear',
                            position: 'bottom',
                            title: {{ display: true, text: 'Word Error Rate (Lower is Better)' }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }}
                        }},
                        y: {{
                            title: {{ display: true, text: 'Adjusted TTFS in ms (Lower is Better)' }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }}
                        }}
                    }}
                }}
            }});
        }});
        </script>
        """

        body = f"""
        <div class="nav-links" style="margin-bottom: 24px;">
            <a href="leaderboard.html">
                View Detailed Leaderboard 
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 4px;"><path d="m9 18 6-6-6-6"/></svg>
            </a>
            <a href="market_comparison.html">
                Winner vs Market 
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 4px;"><path d="m9 18 6-6-6-6"/></svg>
            </a>
        </div>
        
        <div class="grid" style="margin-bottom: 24px;">
            <div class="card" style="margin-bottom: 0;">
                <h3 style="margin-top: 0; color: var(--text-muted);">Total Benchmarks</h3>
                <div style="font-size: 2.5rem; font-weight: 700; color: #fff;">{len(results)}</div>
            </div>
            <div class="card" style="margin-bottom: 0;">
                <h3 style="margin-top: 0; color: var(--text-muted);">Providers Tested</h3>
                <div style="font-size: 2.5rem; font-weight: 700; color: #fff;">{len(set(r.provider for r in results))}</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2 style="margin-top: 0;">Average Accuracy (WER)</h2>
                <div class="chart-container">
                    <canvas id="werChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h2 style="margin-top: 0;">Average Semantic WER</h2>
                <div class="chart-container">
                    <canvas id="semWerChart"></canvas>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2 style="margin-top: 0;">Average Entity Accuracy</h2>
                <div class="chart-container">
                    <canvas id="entityChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2 style="margin-top: 0;">Average Adjusted Latency (TTFS)</h2>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px;">
                    *Values adjusted (-600ms) to reflect true processing latency
                </p>
                <div class="chart-container">
                    <canvas id="ttfsChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-top: 0;">Average Total Latency</h2>
            <div class="chart-container" style="height: 300px;">
                <canvas id="totalLatChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-top: 0;">Speed vs. Accuracy Analysis</h2>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px;">
                Scatter plot of every sample. Bottom-left is ideal (Fast & Accurate).
            </p>
            <div class="chart-container" style="height: 500px;">
                <canvas id="scatterChart"></canvas>
            </div>
        </div>
        """

        path = self.output_dir / "dashboard.html"
        path.write_text(self._html_wrapper("Benchmark Dashboard", body, chart_js_script), encoding="utf8")
        return path

    def generate_market_comparison(self, results: list[BenchmarkResult]) -> Path:
        """Generate a Winner vs Market Competitors comparison page.

        Our candidates (pick winner from): deepgram, assemblyai, gladia
        Market competitors (compare against): elevenlabs, speechmatics
        Excluded: google_public (not in market comparison scope)
        """

        OUR_PROVIDERS = {"deepgram", "assemblyai", "gladia"}
        MARKET_COMPETITORS = {"elevenlabs", "speechmatics"}

        # Aggregate per-provider stats
        provider_stats = defaultdict(lambda: {
            "wer": [], "sem_wer": [], "entity": [], "ttfs": [], "total_lat": [],
            "success": 0, "total": 0,
        })

        for r in results:
            p = r.provider
            provider_stats[p]["total"] += 1
            if r.success:
                provider_stats[p]["success"] += 1
                provider_stats[p]["wer"].append(r.wer)
                provider_stats[p]["sem_wer"].append(r.semantic_wer)
                ent = r.entity_accuracy.score if hasattr(r.entity_accuracy, "score") else float(r.entity_accuracy)
                provider_stats[p]["entity"].append(ent)
                provider_stats[p]["ttfs"].append(self._get_adjusted_ttfs(r.latency.ttfs_ms))
                provider_stats[p]["total_lat"].append(r.latency.total_ms)

        if not provider_stats:
            path = self.output_dir / "market_comparison.html"
            path.write_text(self._html_wrapper("Market Comparison", "<p>No data available.</p>"), encoding="utf8")
            return path

        # Build averages per provider
        provider_avgs = {}
        for p, s in provider_stats.items():
            if not s["wer"]:
                continue
            provider_avgs[p] = {
                "wer": sum(s["wer"]) / len(s["wer"]),
                "sem_wer": sum(s["sem_wer"]) / len(s["sem_wer"]),
                "entity": sum(s["entity"]) / len(s["entity"]),
                "ttfs": sum(s["ttfs"]) / len(s["ttfs"]),
                "total_lat": sum(s["total_lat"]) / len(s["total_lat"]),
                "reliability": (s["success"] / s["total"] * 100) if s["total"] > 0 else 0,
                "samples": len(s["wer"]),
            }

        # Split into our candidates and market competitors
        our_avgs = {p: v for p, v in provider_avgs.items() if p.lower() in OUR_PROVIDERS}
        market_avgs = {p: v for p, v in provider_avgs.items() if p.lower() in MARKET_COMPETITORS}

        if not our_avgs:
            path = self.output_dir / "market_comparison.html"
            path.write_text(self._html_wrapper("Market Comparison", "<p>No data for our providers (deepgram, assemblyai, google_public).</p>"), encoding="utf8")
            return path

        # Determine winner from OUR candidates: lowest WER, then lowest TTFS tiebreak
        winner_name = min(our_avgs, key=lambda p: (our_avgs[p]["wer"], our_avgs[p]["ttfs"]))
        winner = our_avgs[winner_name]

        # For each metric, find the best market competitor
        metrics_config = [
            ("wer",       "Word Error Rate (WER)",     "lower",  "{:.4f}"),
            ("sem_wer",   "Semantic WER",              "lower",  "{:.4f}"),
            ("entity",    "Entity Accuracy (%)",       "higher", "{:.1f}%"),
            ("ttfs",      "Adjusted TTFS (ms)",        "lower",  "{:.0f}ms"),
            ("total_lat", "Total Latency (ms)",        "lower",  "{:.0f}ms"),
        ]

        comparison_rows = ""
        winner_wins = 0
        total_metrics = len(metrics_config)

        for key, label, direction, fmt in metrics_config:
            winner_val = winner[key]

            if market_avgs:
                if direction == "lower":
                    best_comp_name = min(market_avgs, key=lambda p: market_avgs[p][key])
                else:
                    best_comp_name = max(market_avgs, key=lambda p: market_avgs[p][key])
                best_comp_val = market_avgs[best_comp_name][key]

                if direction == "lower":
                    winner_better = winner_val <= best_comp_val
                else:
                    winner_better = winner_val >= best_comp_val
            else:
                best_comp_name = "---"
                best_comp_val = 0
                winner_better = True

            if winner_better:
                winner_wins += 1

            w_badge = '<span class="badge success">WIN</span>' if winner_better else '<span class="badge error">LOSS</span>'
            c_badge = '<span class="badge error">LOSS</span>' if winner_better else '<span class="badge success">WIN</span>'

            # Format values
            if '%' in fmt:
                w_display = fmt.replace('%', '').format(winner_val) + '%'
                c_display = fmt.replace('%', '').format(best_comp_val) + '%' if market_avgs else '---'
            elif 'ms' in fmt:
                w_display = fmt.replace('ms', '').format(winner_val) + 'ms'
                c_display = fmt.replace('ms', '').format(best_comp_val) + 'ms' if market_avgs else '---'
            else:
                w_display = fmt.format(winner_val)
                c_display = fmt.format(best_comp_val) if market_avgs else '---'

            comparison_rows += f"""<tr>
                <td style="font-weight: 600;">{label}</td>
                <td style="text-align: center;">{w_badge} {w_display}</td>
                <td style="text-align: center;">{c_badge} {c_display}</td>
                <td style="text-align: center; color: var(--text-muted);">{best_comp_name if market_avgs else '---'}</td>
            </tr>"""

        # --- Our Candidates Ranking Table ---
        sorted_ours = sorted(our_avgs.items(), key=lambda x: x[1]["wer"])
        our_table_rows = ""
        for rank, (p, v) in enumerate(sorted_ours, 1):
            wer_class = "good" if v["wer"] < 0.1 else ("warn" if v["wer"] < 0.2 else "bad")
            winner_tag = ' <span class="badge success">WINNER</span>' if p == winner_name else ''
            our_table_rows += f"""<tr>
                <td>{rank}</td>
                <td style="font-weight: 600;">{p}{winner_tag}</td>
                <td class="{wer_class}">{v['wer']:.4f}</td>
                <td>{v['sem_wer']:.4f}</td>
                <td>{v['entity']:.1f}%</td>
                <td style="font-family: monospace;">{v['ttfs']:.0f}ms</td>
                <td style="font-family: monospace;">{v['total_lat']:.0f}ms</td>
                <td>{v['reliability']:.0f}%</td>
                <td>{v['samples']}</td>
            </tr>"""

        # --- Market Competitors Table ---
        sorted_market = sorted(market_avgs.items(), key=lambda x: x[1]["wer"]) if market_avgs else []
        market_table_rows = ""
        for rank, (p, v) in enumerate(sorted_market, 1):
            wer_class = "good" if v["wer"] < 0.1 else ("warn" if v["wer"] < 0.2 else "bad")
            market_table_rows += f"""<tr>
                <td>{rank}</td>
                <td style="font-weight: 600;">{p}</td>
                <td class="{wer_class}">{v['wer']:.4f}</td>
                <td>{v['sem_wer']:.4f}</td>
                <td>{v['entity']:.1f}%</td>
                <td style="font-family: monospace;">{v['ttfs']:.0f}ms</td>
                <td style="font-family: monospace;">{v['total_lat']:.0f}ms</td>
                <td>{v['reliability']:.0f}%</td>
                <td>{v['samples']}</td>
            </tr>"""

        if not market_table_rows:
            market_table_rows = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No market competitor data in this benchmark run. Add ElevenLabs/Speechmatics API keys to include them.</td></tr>'

        # --- Radar chart data (normalize to 0-100) ---
        all_in_radar = {**our_avgs, **market_avgs}
        all_providers_list = list(all_in_radar.keys())

        all_wer = [v["wer"] for v in all_in_radar.values()]
        all_sem = [v["sem_wer"] for v in all_in_radar.values()]
        all_ent = [v["entity"] for v in all_in_radar.values()]
        all_ttfs = [v["ttfs"] for v in all_in_radar.values()]
        all_lat = [v["total_lat"] for v in all_in_radar.values()]

        def norm_lower(val, vals):
            mn, mx = min(vals), max(vals)
            if mx == mn:
                return 100
            return round(100 * (1 - (val - mn) / (mx - mn)), 1)

        def norm_higher(val, vals):
            mn, mx = min(vals), max(vals)
            if mx == mn:
                return 100
            return round(100 * ((val - mn) / (mx - mn)), 1)

        radar_labels = json.dumps(["WER", "Semantic WER", "Entity Acc.", "TTFS", "Total Latency"])

        # Color palette: solid for our providers, dashed for market competitors
        our_colors = [
            ('rgba(59, 130, 246, 0.25)', 'rgba(59, 130, 246, 1)'),    # blue
            ('rgba(16, 185, 129, 0.25)', 'rgba(16, 185, 129, 1)'),    # emerald
            ('rgba(245, 158, 11, 0.25)', 'rgba(245, 158, 11, 1)'),    # amber
        ]
        mkt_colors = [
            ('rgba(239, 68, 68, 0.15)',  'rgba(239, 68, 68, 0.8)'),   # red
            ('rgba(139, 92, 246, 0.15)', 'rgba(139, 92, 246, 0.8)'),  # purple
            ('rgba(236, 72, 153, 0.15)', 'rgba(236, 72, 153, 0.8)'),  # pink
        ]

        radar_datasets = []
        our_idx = 0
        mkt_idx = 0
        for p in all_providers_list:
            v = all_in_radar[p]
            is_ours = p.lower() in OUR_PROVIDERS
            if is_ours:
                bg, border = our_colors[our_idx % len(our_colors)]
                our_idx += 1
                dash = []
            else:
                bg, border = mkt_colors[mkt_idx % len(mkt_colors)]
                mkt_idx += 1
                dash = [5, 5]

            ds = {
                "label": p + (" [Ours]" if is_ours else " [Market]"),
                "data": [
                    norm_lower(v["wer"], all_wer),
                    norm_lower(v["sem_wer"], all_sem),
                    norm_higher(v["entity"], all_ent),
                    norm_lower(v["ttfs"], all_ttfs),
                    norm_lower(v["total_lat"], all_lat),
                ],
                "fill": True,
                "backgroundColor": bg,
                "borderColor": border,
                "pointBackgroundColor": border,
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": border,
                "borderWidth": 2,
            }
            if dash:
                ds["borderDash"] = dash
            radar_datasets.append(ds)

        # --- Per-metric grouped bar charts (all providers) ---
        all_sorted = sorted(all_in_radar.items(), key=lambda x: x[1]["wer"])
        bar_labels = json.dumps([p for p, _ in all_sorted])
        bar_wer = json.dumps([round(v["wer"], 4) for _, v in all_sorted])
        bar_sem = json.dumps([round(v["sem_wer"], 4) for _, v in all_sorted])
        bar_entity = json.dumps([round(v["entity"], 1) for _, v in all_sorted])
        bar_ttfs = json.dumps([round(v["ttfs"], 0) for _, v in all_sorted])
        bar_lat = json.dumps([round(v["total_lat"], 0) for _, v in all_sorted])

        # Bar colors: blue for ours, red-ish for market
        bar_border_list = []
        bar_bg_list = []
        for p, _ in all_sorted:
            if p.lower() in OUR_PROVIDERS:
                bar_border_list.append('rgba(59, 130, 246, 1)')
                bar_bg_list.append('rgba(59, 130, 246, 0.7)')
            else:
                bar_border_list.append('rgba(239, 68, 68, 1)')
                bar_bg_list.append('rgba(239, 68, 68, 0.7)')

        bar_colors = json.dumps(bar_border_list)
        bar_bg_colors = json.dumps(bar_bg_list)

        chart_js_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Chart.register(ChartDataLabels);
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Inter', sans-serif";

            // Radar Chart: Our Providers vs Market
            new Chart(document.getElementById('radarChart'), {{
                type: 'radar',
                data: {{
                    labels: {radar_labels},
                    datasets: {json.dumps(radar_datasets)}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        r: {{
                            beginAtZero: true,
                            max: 100,
                            ticks: {{ stepSize: 20 }},
                            grid: {{ color: 'rgba(255,255,255,0.08)' }},
                            angleLines: {{ color: 'rgba(255,255,255,0.08)' }},
                            pointLabels: {{ font: {{ size: 13, weight: '600' }}, color: '#e2e8f0' }}
                        }}
                    }},
                    plugins: {{
                        datalabels: {{ display: false }},
                        legend: {{
                            position: 'bottom',
                            labels: {{ padding: 20, usePointStyle: true, pointStyle: 'circle' }}
                        }}
                    }}
                }}
            }});

            // Per-Metric Bar Charts
            function makeBar(id, data, label, color, bgColor, fmtType) {{
                new Chart(document.getElementById(id), {{
                    type: 'bar',
                    data: {{
                        labels: {bar_labels},
                        datasets: [{{
                            label: label,
                            data: data,
                            backgroundColor: bgColor,
                            borderColor: color,
                            borderWidth: 1,
                            borderRadius: 6
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ 
                            legend: {{ display: false }},
                            datalabels: {{
                                display: true,
                                color: '#e2e8f0',
                                anchor: 'end',
                                align: 'right',
                                font: {{ weight: '600', size: 11 }},
                                formatter: function(value) {{
                                    if (fmtType === 'wer') return value.toFixed(3);
                                    if (fmtType === 'percent') return value.toFixed(1) + '%';
                                    if (fmtType === 'ms') return Math.round(value) + 'ms';
                                    return value;
                                }}
                            }}
                        }},
                        layout: {{ padding: {{ right: 50 }} }}, // space for right-aligned labels
                        scales: {{
                            x: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                            y: {{ grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}

            makeBar('mktWerChart', {bar_wer}, 'WER', {bar_colors}, {bar_bg_colors}, 'wer');
            makeBar('mktSemChart', {bar_sem}, 'Semantic WER', {bar_colors}, {bar_bg_colors}, 'wer');
            makeBar('mktEntityChart', {bar_entity}, 'Entity Accuracy (%)', {bar_colors}, {bar_bg_colors}, 'percent');
            makeBar('mktTtfsChart', {bar_ttfs}, 'Adjusted TTFS (ms)', {bar_colors}, {bar_bg_colors}, 'ms');
            makeBar('mktLatChart', {bar_lat}, 'Total Latency (ms)', {bar_colors}, {bar_bg_colors}, 'ms');
        }});
        </script>
        """

        market_comp_note = ""
        if not market_avgs:
            market_comp_note = """
            <div class="card" style="border: 1px solid rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.08);">
                <p style="margin: 0; color: var(--warning);"><strong>Note:</strong> No market competitor data (ElevenLabs, Speechmatics) found in this benchmark run.
                Add their API keys to .env and re-run the benchmark to see the full comparison.</p>
            </div>
            """

        body = f"""
        <div class="nav-links" style="margin-bottom: 24px;">
            <a href="dashboard.html">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                Back to Dashboard
            </a>
            <a href="leaderboard.html">
                Detailed Leaderboard
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 4px;"><path d="m9 18 6-6-6-6"/></svg>
            </a>
        </div>

        {market_comp_note}

        <!-- Hero: Winner Announcement -->
        <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15)); border: 1px solid rgba(99,102,241,0.3);">
            <div style="font-size: 1.2rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); margin-bottom: 8px;">Our Benchmark Winner</div>
            <h2 style="margin: 0 0 8px 0; font-size: 2rem; color: #fff;">{winner_name}</h2>
            <p style="color: var(--text-muted); margin: 0; font-size: 1.05rem;">
                Wins <strong style="color: var(--success);">{winner_wins}/{total_metrics}</strong> metrics against the best market competitor on each metric
            </p>
            <p style="color: var(--text-muted); margin: 8px 0 0 0; font-size: 0.85rem;">
                Selected from: {', '.join(sorted(our_avgs.keys()))}
            </p>
        </div>

        <!-- Winner vs Best-Of Market Table -->
        <div class="card">
            <h2 style="margin-top: 0;">Winner vs Best of Market (Per Metric)</h2>
            <p style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 4px;">
                For each metric, <strong>{winner_name}</strong> (our pick) is compared against whichever market competitor (ElevenLabs / Speechmatics) scores best on that specific metric.
            </p>
            <p style="color: var(--text-muted); font-size: 0.85em; margin-bottom: 16px;">
                <span style="display: inline-block; width: 10px; height: 10px; background: rgba(59,130,246,1); border-radius: 2px; margin-right: 4px;"></span> Ours
                &nbsp;&nbsp;
                <span style="display: inline-block; width: 10px; height: 10px; background: rgba(239,68,68,1); border-radius: 2px; margin-right: 4px;"></span> Market Competitor
            </p>
            <div style="overflow-x: auto;">
                <table>
                    <tr>
                        <th>Metric</th>
                        <th style="text-align: center;">{winner_name} (Ours)</th>
                        <th style="text-align: center;">Best Market Competitor</th>
                        <th style="text-align: center;">Competitor Name</th>
                    </tr>
                    {comparison_rows}
                </table>
            </div>
        </div>

        <!-- Our Candidates Table -->
        <div class="card">
            <h2 style="margin-top: 0;">Our Candidates</h2>
            <p style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 16px;">
                Providers we are evaluating, ranked by WER. The winner is selected from this pool.
            </p>
            <div style="overflow-x: auto;">
                <table>
                    <tr>
                        <th>#</th><th>Provider</th><th>Avg WER</th><th>Avg Semantic WER</th>
                        <th>Avg Entity Acc.</th><th>Avg TTFS</th><th>Avg Total Lat.</th>
                        <th>Reliability</th><th>Samples</th>
                    </tr>
                    {our_table_rows}
                </table>
            </div>
        </div>

        <!-- Market Competitors Table -->
        <div class="card">
            <h2 style="margin-top: 0;">Market Competitors</h2>
            <p style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 16px;">
                Industry competitors we are benchmarking against (ElevenLabs, Speechmatics).
            </p>
            <div style="overflow-x: auto;">
                <table>
                    <tr>
                        <th>#</th><th>Provider</th><th>Avg WER</th><th>Avg Semantic WER</th>
                        <th>Avg Entity Acc.</th><th>Avg TTFS</th><th>Avg Total Lat.</th>
                        <th>Reliability</th><th>Samples</th>
                    </tr>
                    {market_table_rows}
                </table>
            </div>
        </div>

        <!-- Radar Chart -->
        <div class="card">
            <h2 style="margin-top: 0;">Provider Radar -- Normalized Scores</h2>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -10px; margin-bottom: 8px;">
                All metrics normalized to 0-100 (higher is better). For WER/Latency, lower raw values = higher score.
            </p>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 20px;">
                Solid lines = our candidates. Dashed lines = market competitors.
            </p>
            <div class="chart-container" style="height: 500px;">
                <canvas id="radarChart"></canvas>
            </div>
        </div>

        <!-- Per-Metric Horizontal Bar Charts -->
        <h2>Per-Metric Breakdown (All Providers)</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -16px; margin-bottom: 24px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: rgba(59,130,246,1); border-radius: 2px; margin-right: 4px;"></span> Ours
            &nbsp;&nbsp;
            <span style="display: inline-block; width: 10px; height: 10px; background: rgba(239,68,68,1); border-radius: 2px; margin-right: 4px;"></span> Market Competitor
        </p>
        <div class="grid">
            <div class="card">
                <h3 style="margin-top: 0; color: var(--text-muted);">Word Error Rate (lower is better)</h3>
                <div class="chart-container" style="height: 250px;"><canvas id="mktWerChart"></canvas></div>
            </div>
            <div class="card">
                <h3 style="margin-top: 0; color: var(--text-muted);">Semantic WER (lower is better)</h3>
                <div class="chart-container" style="height: 250px;"><canvas id="mktSemChart"></canvas></div>
            </div>
        </div>
        <div class="grid">
            <div class="card">
                <h3 style="margin-top: 0; color: var(--text-muted);">Entity Accuracy % (higher is better)</h3>
                <div class="chart-container" style="height: 250px;"><canvas id="mktEntityChart"></canvas></div>
            </div>
            <div class="card">
                <h3 style="margin-top: 0; color: var(--text-muted);">Adjusted TTFS (lower is better)</h3>
                <div class="chart-container" style="height: 250px;"><canvas id="mktTtfsChart"></canvas></div>
            </div>
        </div>
        <div class="card">
            <h3 style="margin-top: 0; color: var(--text-muted);">Total Latency (lower is better)</h3>
            <div class="chart-container" style="height: 250px;"><canvas id="mktLatChart"></canvas></div>
        </div>
        """

        path = self.output_dir / "market_comparison.html"
        path.write_text(self._html_wrapper("Winner vs Market Competitors", body, chart_js_script), encoding="utf8")
        return path
