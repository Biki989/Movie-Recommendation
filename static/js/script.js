/**
 * script.js – CinematIX Global JavaScript
 * Netflix-style poster loading, localStorage caching, sliding shelves, and AJAX actions.
 */

"use strict";

const TMDB_API_KEY = "bdfc018dbdb7c243dc7cb1454ff74b95";

/* ── Navbar Scroll Color Transition ────────────────────────────── */
const navbar = document.getElementById("mainNavbar");
if (navbar) {
  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 40);
  });
  // Trigger initially if page is loaded scrolled
  navbar.classList.toggle("scrolled", window.scrollY > 40);
}

/* ── Auto-dismiss flash notifications ─────────────────────────── */
document.querySelectorAll(".flash-toast").forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    bsAlert?.close();
  }, 5000);
});

/* ── Dynamic Live Search suggestions (Navbar) ────────────────── */
const navSearch   = document.getElementById("navSearchInput");
const suggestions = document.getElementById("searchSuggestions");

if (navSearch && suggestions) {
  let debounceTimer;

  navSearch.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = navSearch.value.trim();
    if (q.length < 2) { suggestions.classList.remove("show"); return; }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(data => {
          suggestions.innerHTML = "";
          if (!data.length) { suggestions.classList.remove("show"); return; }
          data.slice(0, 6).forEach(movie => {
            const div = document.createElement("div");
            div.className = "suggestion-item";
            div.innerHTML = `
              <i class="bi bi-film text-danger"></i>
              <span class="fw-semibold text-white">${movie.title}</span>
              <small class="text-muted ms-auto">${movie.genres.split("|")[0]}</small>`;
            div.addEventListener("click", () => {
              window.location.href = `/search?q=${encodeURIComponent(movie.title)}`;
            });
            suggestions.appendChild(div);
          });
          suggestions.classList.add("show");
        })
        .catch(() => suggestions.classList.remove("show"));
    }, 300);
  });

  document.addEventListener("click", e => {
    if (!navSearch.contains(e.target) && !suggestions.contains(e.target)) {
      suggestions.classList.remove("show");
    }
  });
}

/* ── Horizontal Scroll Rows Navigation ───────────────────────── */
window.scrollShelf = function(btn, direction) {
  const wrapper = btn.closest('.movie-shelf-wrapper');
  const shelf = wrapper.querySelector('.movie-shelf');
  if (shelf) {
    const scrollAmount = shelf.clientWidth * 0.75;
    shelf.scrollBy({
      left: scrollAmount * direction,
      behavior: 'smooth'
    });
  }
};

/* ── Dynamic TMDb Movie Poster Engine ────────────────────────── */

// Extract title & year for precise TMDb queries
function cleanMovieTitle(title) {
  let query = title.trim();
  let year = "";
  const match = title.match(/(.*)\s\((\d{4})\)/);
  if (match) {
    query = match[1].trim();
    year = match[2].trim();
  }
  // Format standard MovieLens title modifiers: "Matrix, The (1999)" -> "The Matrix"
  const commaMatch = query.match(/(.*),\s(The|A|An)$/i);
  if (commaMatch) {
    query = commaMatch[2] + " " + commaMatch[1];
  }
  return { query, year };
}

// Generate premium fallback SVG poster for card
window.showFallbackPoster = function(img) {
  const title = img.closest('.movie-card')?.dataset.title || img.alt || "CinematIX";
  triggerFallback(img, title);
};

function triggerFallback(img, title) {
  if (img.classList.contains('history-thumb')) {
    // Generate a sleek micro canvas with initial letter for small list tables
    const canvas = document.createElement('canvas');
    canvas.width = 40;
    canvas.height = 60;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#220305';
    ctx.fillRect(0, 0, 40, 60);
    ctx.fillStyle = '#e50914';
    ctx.font = 'bold 22px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(title.charAt(0).toUpperCase(), 20, 30);
    img.src = canvas.toDataURL();
    img.onerror = null; // Prevent loops
    return;
  }
  
  const wrap = img.closest('.movie-poster-wrap');
  if (!wrap) return;
  wrap.innerHTML = `
    <div class="fallback-poster">
      <div class="fallback-poster-icon"><i class="bi bi-film"></i></div>
      <div class="fallback-poster-title">${title}</div>
    </div>
  `;
}

// Dynamically fetch and cache TMDb posters in browser client
async function fetchAndCachePosters() {
  // Clear stale fallback caches once when key is updated
  if (localStorage.getItem("cinematix_key_version") !== "v2") {
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith("cinematix_poster_")) {
        localStorage.removeItem(key);
      }
    }
    localStorage.setItem("cinematix_key_version", "v2");
  }

  const movieCards = document.querySelectorAll('.movie-card, .history-thumb');
  
  movieCards.forEach(async (card) => {
    let title = card.dataset.title || card.alt;
    if (!title) return;

    let img = card.classList.contains('history-thumb') ? card : card.querySelector('.movie-poster');
    if (!img) return;

    const cacheKey = `cinematix_poster_${title}`;
    const cachedUrl = localStorage.getItem(cacheKey);

    if (cachedUrl) {
      if (cachedUrl === "fallback") {
        triggerFallback(img, title);
      } else {
        img.src = cachedUrl;
      }
      return;
    }

    const { query, year } = cleanMovieTitle(title);
    let url = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(query)}`;
    if (year) {
      url += `&year=${year}`;
    }

    try {
      const resp = await fetch(url);
      if (resp.ok) {
        const data = await resp.json();
        if (data.results && data.results.length > 0 && data.results[0].poster_path) {
          const posterUrl = `https://image.tmdb.org/t/p/w500${data.results[0].poster_path}`;
          img.src = posterUrl;
          localStorage.setItem(cacheKey, posterUrl);
        } else {
          // Retry without year if search returned empty
          if (year) {
            const retryUrl = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(query)}`;
            const retryResp = await fetch(retryUrl);
            if (retryResp.ok) {
              const retryData = await retryResp.json();
              if (retryData.results && retryData.results.length > 0 && retryData.results[0].poster_path) {
                const posterUrl = `https://image.tmdb.org/t/p/w500${retryData.results[0].poster_path}`;
                img.src = posterUrl;
                localStorage.setItem(cacheKey, posterUrl);
                return;
              }
            }
          }
          triggerFallback(img, title);
          localStorage.setItem(cacheKey, "fallback");
        }
      } else {
        triggerFallback(img, title);
      }
    } catch (e) {
      triggerFallback(img, title);
    }
  });
}

// Proactively launch poster loader on DOMContentLoaded
document.addEventListener("DOMContentLoaded", fetchAndCachePosters);

/* ── Interactive Unified Star Rating Widget ──────────────────── */
document.addEventListener("click", e => {
  const star = e.target.closest(".rating-star");
  if (!star) return;

  const widget = star.closest(".star-rating-widget");
  if (!widget) return;

  const stars   = widget.querySelectorAll(".rating-star");
  const movieId = widget.dataset.movieId;
  const title   = widget.dataset.title;
  const genres  = widget.dataset.genres;
  const rating  = parseInt(star.dataset.value);

  fetch('/rate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ movie_id: movieId, title, genres, rating })
  })
  .then(r => r.json())
  .then(d => {
    stars.forEach(s => {
      const v = parseInt(s.dataset.value);
      s.classList.toggle('text-warning', v <= rating);
      s.classList.toggle('text-muted', v > rating);
    });
    showToastMsg(d.message || `Rated ${title} → ${rating} ★`, "success");
  })
  .catch(() => showToastMsg("Could not submit rating. Are you logged in?", "danger"));
});

document.addEventListener("mouseover", e => {
  const star = e.target.closest(".rating-star");
  if (!star) return;

  const widget = star.closest(".star-rating-widget");
  if (!widget) return;

  const stars = widget.querySelectorAll(".rating-star");
  const val = parseInt(star.dataset.value);
  stars.forEach(s => {
    s.classList.toggle('hovered', parseInt(s.dataset.value) <= val);
  });
});

document.addEventListener("mouseout", e => {
  const star = e.target.closest(".rating-star");
  if (!star) return;

  const widget = star.closest(".star-rating-widget");
  if (!widget) return;

  const stars = widget.querySelectorAll(".rating-star");
  stars.forEach(s => s.classList.remove('hovered'));
});

/* ── AJAX Bookmarking Toggle ─────────────────────────────────── */
document.addEventListener("click", e => {
  const btn = e.target.closest(".bookmark-btn");
  if (!btn) return;

  const movieId = btn.dataset.movieId;
  const title   = btn.dataset.title;
  const genres  = btn.dataset.genres;

  fetch("/bookmark", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_id: movieId, title, genres })
  })
  .then(r => r.json())
  .then(d => {
    if (d.success) {
      const icon = btn.querySelector("i");
      if (d.bookmarked) {
        icon.className = "bi bi-check-lg";
        btn.classList.add("active");
        btn.title = "Remove from My List";
        showToastMsg("Added to My List", "success");
      } else {
        icon.className = "bi bi-plus-lg";
        btn.classList.remove("active");
        btn.title = "Add to My List";
        showToastMsg("Removed from My List", "info");
      }
    }
  })
  .catch(() => showToastMsg("Could not update list. Are you logged in?", "danger"));
});

/* ── Premium Toast Notification Helper ───────────────────────── */
function showToastMsg(msg, type = "success") {
  const existing = document.getElementById("globalToast");
  if (existing) existing.remove();

  const toastEl = document.createElement("div");
  toastEl.id = "globalToast";
  toastEl.className = `toast align-items-center text-bg-${type} border-0 show`;
  toastEl.style.cssText = "position:fixed;bottom:24px;right:24px;z-index:9999;min-width:260px;border-radius:4px;";
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body fw-bold">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              onclick="this.closest('.toast').remove()"></button>
    </div>`;
  document.body.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 3500);
}

/* ── Smooth Page Transition Loading Overlays ────────────────── */
window.showLoading  = () => {
  const loader = document.getElementById("loadingOverlay");
  if (loader) loader.style.display = "flex";
};
window.hideLoading  = () => {
  const loader = document.getElementById("loadingOverlay");
  if (loader) loader.style.display = "none";
};

document.addEventListener("click", e => {
  const link = e.target.closest("a[href]");
  if (!link) return;
  const href = link.getAttribute("href");
  if (!href || href.startsWith("#") || href.startsWith("http") ||
      href.startsWith("mailto") || link.dataset.bsToggle || link.classList.contains('dropdown-toggle')) return;
  showLoading();
});
window.addEventListener("pageshow", () => hideLoading());

/* ── Card Intersection Fade-in ───────────────────────────────── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.05 });

document.querySelectorAll(".movie-card, .feature-card, .stat-card").forEach(el => {
  el.style.opacity = "0";
  el.style.transform = "translateY(15px)";
  el.style.transition = "opacity 0.4s ease, transform 0.4s ease";
  observer.observe(el);
});

const visibleStyle = document.createElement("style");
visibleStyle.textContent = `.visible { opacity:1 !important; transform:translateY(0) !important; }`;
document.head.appendChild(visibleStyle);
