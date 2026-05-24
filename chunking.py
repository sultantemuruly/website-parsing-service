"""Chunk crawled markdown for RAG via recursive character splitting."""

from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Firecrawl RAG guide defaults: https://www.firecrawl.dev/blog/best-chunking-strategies-rag
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
MARKDOWN_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@lru_cache(maxsize=1)
def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=MARKDOWN_SEPARATORS,
    )


def chunk_markdown(text: str) -> list[str]:
    """Split markdown into overlapping chunks at paragraph, line, and sentence boundaries."""
    stripped = text.strip()
    if not stripped:
        return []
    return _splitter().split_text(stripped)


SAMPLE_MARKDOWN = r"""
    ---
title: "The Ultimate Guide to Tech Stack Optimization - v2.4.1 (DEPRECATED)"
seo_keywords: ["tech", "optimization", "clean code", "devops", "cloud"]
author_id: 94812
cache_status: "MISS"
---
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The Ultimate Guide to Tech Stack Optimization",
  "datePublished": "2026-04-12"
}
</script>
<style>
.flex-container { display: flex; flex-direction: column; padding: 20px; }
.hidden-mobile { display: none; }
@media (max-width: 600px) { .ad-slot-300 { width: 100%; } }
</style>

<div id="react-root" class="theme--dark app-layout col-lg-12 col-md-12 col-sm-12 global-wrapper__overflow-x">
  
  <!-- UI NAVIGATION BANNER (SCRAPED INADVERTENTLY) -->
  <header class="site-header fixed-top navbar-expand-lg navigation-widget__container">
    <div class="hamburger-menu-icon" onclick="toggleMenu()"><span></span><span></span><span></span></div>
    <a href="/?ref=nav_logo" class="tracking-link-analytics" data-analytics-id="logo_click_01">
      <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgZmlsbD0icmVkIi8+PC9zdmc+" alt="Brand Logo Icon Inline Base64">
    </a>
    <span class="user-welcome-msg">Welcome, Guest! <a href="/login" class="btn btn-outline-light btn-sm login-trigger-modal">Sign In</a></span>
  </header>

  <main class="main-content-area grid-system-override layout-padding-large">
    <section class="breadcrumbs-list-wrapper">
      <ol class="breadcrumb" itemscope itemtype="https://schema.org">
        <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org"><a href="/" itemprop="item"><span itemprop="name">Home</span></a><meta itemprop="position" content="1" /></li>
        <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org"><a href="/blog" itemprop="item"><span itemprop="name">Resources</span></a><meta itemprop="position" content="2" /></li>
        <li class="breadcrumb-item active" aria-current="page">Tech Stack</li>
      </ol>
    </section>

    <!-- TRIPLE NESTED CONTENT WRAPPER -->
    <div class="row match-height-container">
      <div class="col-xl-8 col-lg-8 col-md-12 content-body-column-left-side">
        <article class="journal-article-node-id-499211 node-published status-public user-role-anonymous">
          
          <header class="article-header-meta-block">
            <h1 class="entry-title main-heading-hero font-weight-black text-uppercase tracking-tight" id="main-title-anchor">
              The Ultimate Guide to Tech Stack Optimization &amp; Architecture Scaling&#8482;
            </h1>
            <div class="meta-authorship-grid text-muted small-text-variant">
              <span class="author-label">Written by:</span> <a href="/authors/profile/alex-rivera?source=post_header" rel="author" class="link-underlined-hover">Alex Rivera, CTO</a>
              <span class="bull-divider">&bull;</span>
              <span class="publish-date-timestamp">Updated: <time datetime="2026-04-12T14:32:01Z">April 12, 2026 at 2:32 PM UTC</time></span>
              <span class="bull-divider">&bull;</span>
              <span class="reading-time-estimation"><i class="icon-clock-svg-wrapper"></i> 12 min read</span>
            </div>
          </header>

          <hr class="section-divider-gradient-line">

          <!-- INLINE NEWSLETTER CTA BREAKOUT -->
          <div class="newsletter-inline-box-wrapper alert alert-info contextual-callout-border mb-4 card-shadow-sm" role="alert">
            <div class="d-flex align-items-center justify-content-between layout-mobile-stack">
              <p class="mb-0 text-dark-emphasis font-size-medium weight-600">🚀 Get architectural blueprints delivered directly to your inbox weekly!</p>
              <form id="inline-subscribe-form" class="form-inline custom-form-validation-target" action="https://domain.com" method="POST">
                <input type="hidden" name="form_id" value="blog_mid_post_cta">
                <input type="email" required name="email_address" placeholder="enter email..." class="form-control form-control-sm mr-2 input-border-radius">
                <button type="submit" class="btn btn-primary btn-sm submit-bounce-animation font-weight-bold">Join 50k+ Devs</button>
              </form>
            </div>
          </div>

          <!-- ACTUAL ARTICLE CONTENT BODY BODY -->
          <div class="article-rich-text-content-wrapper dropcap-initialized paragraph-spacing-classic line-height-relaxed text-justified-mobile">
            <p><span class="first-letter-dropcap text-primary font-weight-bold display-4 float-left mr-2 lh-1">M</span>odern software development requires strict adherence to lean design systems. When you build infrastructure, efficiency isn&rsquo;t just a nice feature to have; it&rsquo;s absolute critical path operational bedrock. &nbsp; &nbsp; &nbsp; &nbsp; Many engineering teams fall trap to the dangerous allure of &ldquo;resume-driven development,&rdquo; which directly leads to massive tech-debt overhead accumulation.</p>

            <div class="interstitial-ad-container-slot box-advertisement center-aligned mt-3 mb-3 border-top-bottom-gray">
              <span class="ad-disclosure-text-label block-display text-muted text-center micro-text">ADVERTISEMENT</span>
              <div id="div-gpt-ad-1672394-0" class="google-ad-unit-wrapper" style="min-width: 300px; min-height: 250px;">
                <script>googletag.cmd.push(function() { googletag.display('div-gpt-ad-1672394-0'); });</script>
              </div>
            </div>

            <h2 class="section-subtitle-heading-h2 sub-target-scroll-marker" id="h2-metrics-matter">1. Metrics That Matter &amp; KPI Trees</h2>
            <p>To optimize efficiently, you must carefully monitor your telemetry pipelines. The core algorithmic constraint for continuous ingestion scaling is represented mathematically by the relationship formula shown down below:</p>
            
            <!-- LATEX MIXED WITH RAW INLINE STYLES AND UNPARSED SYMBOLS -->
            <div class="equation-block-container mathematics-render-engine-katex style-center-margin" style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; font-family: monospace; overflow-x: auto;">
              \[\lim_{n \to \infty} \sum_{i=1}^{n} \frac{\Delta T_{ingress} \times \mathcal{O}(log \, n)}{\psi \cdot \beta_{bandwidth}} \le \epsilon_{latency}\]
            </div>
            
            <p>If your system baseline exceeds \(\epsilon_{latency}\), your message queuing queue broker (\(e.g.\), Apache Kafka, RabbitMQ) will quickly bottleneck, causing major downstream cascading database failures.</p>

            <h3 class="nested-sub-heading-h3 text-secondary mt-4 mb-2" id="h3-data-structures">A. Recommended In-Memory Data Tier Setup</h3>
            <p>We ran comprehensive comparative benchmarks across several operational environments. The resulting structural choice matrix can be clearly broken down into the following key points:</p>
            
            <!-- MIXED LIST WITH NESTED PARAGRAPHS, INLINE STYLES, SPANS AND CHOTIC MARKUP -->
            <ul class="styled-bullet-points-custom-listfa margin-left-medium line-item-gap-small">
              <li class="list-item-node-element unique-li-class-1">
                <strong class="highlight-text-orange font-weight-semibold">Redis Cluster Architecture:</strong> Best option for fast sub-millisecond atomic key-value operations. 
                <span class="badge text-bg-success software-version-tag">v7.2 Stable</span>
                <p class="list-item-sub-description-text text-muted italic-font-style">Note: You absolutely must configure eviction policies to <code>volatile-lru</code> to prevent catastrophic memory exhaustion crashes.</p>
              </li>
              <li class="list-item-node-element unique-li-class-2">
                <strong class="highlight-text-purple font-weight-semibold">Memcached Invalidation Tier:</strong> Highly effective for raw object block caching structures.
                <div class="nested-warning-callout mt-1 p-2 bg-light-yellow border-left-warning small">
                  <span class="warning-icon-placeholder">⚠️</span> <strong>Warning:</strong> Lacks out-of-the-box native cluster replication features.
                </div>
              </li>
            </ul>

            <h2 class="section-subtitle-heading-h2 sub-target-scroll-marker" id="h2-code-snippet">2. Production Implementation Reference</h2>
            <p>Below is a working production code snippet that demonstrates asynchronous connection pool initialization handling routines:</p>

            <!-- CODE BLOCK MIXED WITH SYNTAX HIGHLIGHTING HTML THAT SHOULD BE PURE MARKDOWN -->
            <div class="code-block-syntax-highlighter-wrapper-element positioning-relative">
              <div class="code-header-filename-bar d-flex justify-content-between p-2 bg-dark text-white font-monospace font-size-xs rounded-top">
                <span>pool_manager.py</span>
                <button class="btn-copy-to-clipboard-js-action btn-xs text-muted-white border-0 bg-transparent" data-clipboard-target="#code-snippet-data-id-9982"><i class="fa fa-copy"></i> Copy</button>
              </div>
              <pre class="bg-dark text-light p-3 font-monospace font-size-sm rounded-bottom unified-syntax-coloring" id="code-snippet-data-id-9982"><code><span class="python-keyword" style="color: #ff79c6;">import</span> asyncio
<span class="python-keyword" style="color: #ff79c6;">import</span> aioredis


"""


def _demo() -> None:
    text = SAMPLE_MARKDOWN.strip()
    chunks = chunk_markdown(text)
    sizes = [len(c) for c in chunks]

    print(f"input: {len(text)} chars")
    print(f"chunks: {len(chunks)} (avg {sum(sizes) // len(sizes) if sizes else 0} chars)\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"--- chunk {i} ({len(chunk)} chars) ---")
        print(chunk[:200] + ("..." if len(chunk) > 200 else ""))
        print()


if __name__ == "__main__":
    _demo()
