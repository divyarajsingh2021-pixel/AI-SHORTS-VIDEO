// Global State
let currentScenes = [];
let selectedVoice = "en-US-ChristopherNeural";
let selectedVoiceSpeed = "+15%";
let selectedVisualStyle = "cinematic";
let selectedSubtitleStyle = "hormozi";
let selectedLayout = "fullscreen";
let activeSessionId = null;

document.addEventListener("DOMContentLoaded", async () => {
  lucide.createIcons();
  await loadInitialData();
  setupEventListeners();
});

// Load Presets, Voices, Styles from Backend
async function loadInitialData() {
  try {
    // 1. Fetch Presets
    const resPresets = await fetch("/api/presets");
    const presets = await resPresets.json();
    renderPresetButtons(presets);

    // 2. Fetch Voices
    const resVoices = await fetch("/api/voices");
    const voices = await resVoices.json();
    populateVoices(voices);

    // Load default preset (Space Facts)
    await loadPreset("space_facts");
  } catch (err) {
    console.error("Failed to load initial data:", err);
  }
}

function renderPresetButtons(presets) {
  const container = document.getElementById("preset-buttons");
  container.innerHTML = "";

  const icons = {
    space_facts: "rocket",
    dark_psychology: "brain",
    stoic_motivation: "shield",
    history_mystery: "compass"
  };

  for (const [key, val] of Object.entries(presets)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "flex items-center gap-2 p-2.5 rounded-xl border border-gray-800 bg-[#0a0d14] hover:border-gray-700 text-left transition";
    btn.onclick = () => loadPreset(key);
    btn.innerHTML = `
      <i data-lucide="${icons[key] || 'film'}" class="w-4 h-4 text-rose-400"></i>
      <div class="truncate">
        <div class="text-xs font-semibold text-gray-200 truncate">${val.title}</div>
        <div class="text-[10px] text-gray-500">${val.scene_count} scenes</div>
      </div>
    `;
    container.appendChild(btn);
  }
  lucide.createIcons();
}

function populateVoices(voices) {
  const select = document.getElementById("voice-select");
  select.innerHTML = "";
  voices.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v.id;
    opt.textContent = `${v.name} (${v.gender})`;
    if (v.id === selectedVoice) opt.selected = true;
    select.appendChild(opt);
  });
}

async function loadPreset(presetKey) {
  try {
    const res = await fetch(`/api/preset/${presetKey}`);
    const data = await res.json();
    
    // Set script text
    const fullText = data.scenes.map(s => s.text).join(" ");
    const scriptInput = document.getElementById("script-input");
    scriptInput.value = fullText;
    updateWordCount(fullText);

    // Update style if preset specifies one
    if (data.default_style) {
      selectedVisualStyle = data.default_style;
      const vStyleSelect = document.getElementById("visual-style-select");
      if (vStyleSelect) vStyleSelect.value = data.default_style;
    }

    // Set scenes
    currentScenes = data.scenes;
    renderScenes();
  } catch (err) {
    console.error("Error loading preset:", err);
  }
}

function updateWordCount(text) {
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  // Calculate seconds taking speed into account (1.15x is ~3 words/sec)
  const speedFactor = selectedVoiceSpeed === "+15%" ? 3.0 : selectedVoiceSpeed === "+25%" ? 3.4 : 2.5;
  document.getElementById("word-count").textContent = `${words} words (~${Math.round(words / speedFactor)}s at ${selectedVoiceSpeed})`;
}

function renderScenes() {
  const container = document.getElementById("scenes-container");
  container.innerHTML = "";

  document.getElementById("scene-counter-badge").textContent = `${currentScenes.length} Scenes`;

  currentScenes.forEach((scene, index) => {
    const card = document.createElement("div");
    card.className = "scene-card bg-[#0d121f] border border-gray-800/80 hover:border-amber-500/40 rounded-xl p-4 space-y-3 transition duration-200";
    card.id = `scene-card-${scene.id}`;

    const subjectBadge = scene.subject 
      ? `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">${escapeHtml(scene.subject)}</span>`
      : '';
    const shotBadge = scene.shot_type
      ? `<span class="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">${escapeHtml(scene.shot_type)}</span>`
      : '';

    const thumbHtml = scene.image_url 
      ? `<div class="relative group cursor-pointer overflow-hidden rounded-xl border border-gray-700 shadow-lg">
           <img src="${scene.image_url}" class="w-20 h-36 object-cover rounded-xl transition duration-300 group-hover:scale-105">
           <button onclick="regenerateScene(${scene.id})" title="Regenerate this 1:1 image" class="absolute bottom-1 right-1 p-1 bg-black/80 hover:bg-amber-500 hover:text-black text-amber-400 rounded-md transition shadow">
             <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
           </button>
         </div>`
      : `<div class="w-20 h-36 bg-[#090c13] rounded-xl border border-dashed border-gray-700/80 flex flex-col items-center justify-center text-gray-500 hover:border-amber-500/50 transition cursor-pointer" onclick="regenerateScene(${scene.id})">
           <i data-lucide="sparkles" class="w-5 h-5 mb-1.5 text-amber-400"></i>
           <span class="text-[9px] uppercase font-mono tracking-wider font-semibold text-gray-400">1:1 MATCH</span>
           <span class="text-[8px] text-gray-600 mt-0.5">Click to preview</span>
         </div>`;

    card.innerHTML = `
      <div class="flex items-center justify-between border-b border-gray-800/60 pb-2">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono text-xs font-bold">SCENE ${index + 1}</span>
          ${subjectBadge}
          ${shotBadge}
        </div>
        <div class="flex items-center gap-2">
          <label class="text-[11px] text-gray-400">Camera:</label>
          <select onchange="updateSceneMotion(${scene.id}, this.value)" class="bg-[#090c13] border border-gray-700 text-xs text-gray-300 rounded px-2 py-0.5 focus:outline-none">
            <option value="zoom_in" ${scene.camera_motion === 'zoom_in' ? 'selected' : ''}>Zoom In</option>
            <option value="zoom_out" ${scene.camera_motion === 'zoom_out' ? 'selected' : ''}>Zoom Out</option>
            <option value="pan_up" ${scene.camera_motion === 'pan_up' ? 'selected' : ''}>Pan Up</option>
            <option value="pan_down" ${scene.camera_motion === 'pan_down' ? 'selected' : ''}>Pan Down</option>
          </select>
        </div>
      </div>

      <div class="flex gap-4 items-start">
        <div class="flex-shrink-0">
          ${thumbHtml}
        </div>

        <div class="flex-1 space-y-2.5">
          <!-- Spoken text -->
          <div>
            <label class="text-[11px] font-semibold text-gray-300">Spoken Voice Line:</label>
            <input type="text" value="${escapeHtml(scene.text)}" onchange="updateSceneText(${scene.id}, this.value)"
              class="w-full bg-[#080b12] border border-gray-700/80 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-rose-500 transition">
          </div>

          <!-- 1:1 Focused Visual Prompt -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-[11px] font-semibold text-amber-400 flex items-center gap-1">
                <i data-lucide="focus" class="w-3.5 h-3.5"></i> Focused 1:1 Visual Match Prompt:
              </label>
              <button onclick="regenerateScene(${scene.id})" class="text-[11px] text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 font-medium">
                <i data-lucide="refresh-cw" class="w-3 h-3"></i> Regenerate Image
              </button>
            </div>
            <textarea rows="2" onchange="updateScenePrompt(${scene.id}, this.value)"
              class="w-full bg-[#080b12] border border-amber-500/30 rounded-lg p-2 text-xs text-gray-200 focus:outline-none focus:border-amber-400 resize-none font-mono text-[11px] leading-snug">${escapeHtml(scene.visual_prompt)}</textarea>
          </div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
  lucide.createIcons();
}

function updateSceneMotion(id, motion) {
  const s = currentScenes.find(sc => sc.id === id);
  if (s) s.camera_motion = motion;
}

function updateSceneText(id, text) {
  const s = currentScenes.find(sc => sc.id === id);
  if (s) s.text = text;
}

function updateScenePrompt(id, prompt) {
  const s = currentScenes.find(sc => sc.id === id);
  if (s) s.visual_prompt = prompt;
}

function setupEventListeners() {
  const scriptInput = document.getElementById("script-input");
  scriptInput.addEventListener("input", (e) => {
    updateWordCount(e.target.value);
  });

  // Voice Speed Selector
  const voiceSpeedSelect = document.getElementById("voice-speed-select");
  if (voiceSpeedSelect) {
    voiceSpeedSelect.addEventListener("change", (e) => {
      selectedVoiceSpeed = e.target.value;
      updateWordCount(scriptInput.value);
    });
  }

  // Visual Art Style Selector
  const visualStyleSelect = document.getElementById("visual-style-select");
  if (visualStyleSelect) {
    visualStyleSelect.addEventListener("change", (e) => {
      selectedVisualStyle = e.target.value;
    });
  }

  // Parse Script button
  document.getElementById("btn-parse-script").addEventListener("click", async () => {
    const text = scriptInput.value.trim();
    if (!text) return alert("Please enter script text first.");
    
    const res = await fetch("/api/parse-script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_script: text,
        visual_style: selectedVisualStyle
      })
    });
    const data = await res.json();
    currentScenes = data.scenes;
    renderScenes();
  });

  // Preview & Focus Visuals Button (Generates images for all scenes)
  const btnPreviewVisuals = document.getElementById("btn-preview-visuals");
  if (btnPreviewVisuals) {
    btnPreviewVisuals.addEventListener("click", async () => {
      if (!currentScenes || currentScenes.length === 0) return alert("Please parse a script first.");

      btnPreviewVisuals.disabled = true;
      btnPreviewVisuals.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Generating 1:1 Previews...`;
      lucide.createIcons();

      try {
        const res = await fetch("/api/preview-visuals", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scenes: currentScenes,
            session_id: activeSessionId
          })
        });
        const data = await res.json();
        activeSessionId = data.session_id;
        currentScenes = data.scenes;
        renderScenes();
      } catch (err) {
        alert("Failed to preview visuals: " + err.message);
      } finally {
        btnPreviewVisuals.disabled = false;
        btnPreviewVisuals.innerHTML = `<i data-lucide="eye" class="w-3.5 h-3.5"></i> Focus & Preview 1:1 Visuals`;
        lucide.createIcons();
      }
    });
  }

  // Voice Selection
  document.getElementById("voice-select").addEventListener("change", (e) => {
    selectedVoice = e.target.value;
  });

  // Subtitle Style Radios
  document.querySelectorAll("input[name='sub_style']").forEach(radio => {
    radio.addEventListener("change", (e) => {
      selectedSubtitleStyle = e.target.value;
      document.querySelectorAll("#subtitle-style-picker label").forEach(lbl => {
        lbl.classList.remove("border-rose-500/60", "bg-rose-500/10");
        lbl.classList.add("border-gray-800", "bg-[#0a0d14]");
      });
      const selectedLabel = e.target.closest("label");
      selectedLabel.classList.add("border-rose-500/60", "bg-rose-500/10");
      selectedLabel.classList.remove("border-gray-800", "bg-[#0a0d14]");
    });
  });

  // Layout switcher
  const btnFull = document.getElementById("btn-layout-fullscreen");
  const btnSplit = document.getElementById("btn-layout-split");

  btnFull.addEventListener("click", () => {
    selectedLayout = "fullscreen";
    btnFull.className = "p-3 rounded-xl border border-rose-500 bg-rose-500/10 text-left transition flex items-start gap-3";
    btnSplit.className = "p-3 rounded-xl border border-gray-800 bg-[#0a0d14] text-left hover:border-gray-700 transition flex items-start gap-3";
  });

  btnSplit.addEventListener("click", () => {
    selectedLayout = "split_screen";
    btnSplit.className = "p-3 rounded-xl border border-rose-500 bg-rose-500/10 text-left transition flex items-start gap-3";
    btnFull.className = "p-3 rounded-xl border border-gray-800 bg-[#0a0d14] text-left hover:border-gray-700 transition flex items-start gap-3";
  });

  // One-Click Render Button
  document.getElementById("btn-render-all").addEventListener("click", startRendering);
}

async function startRendering() {
  if (!currentScenes || currentScenes.length === 0) {
    return alert("Please enter a script or select a preset first.");
  }

  const musicTrack = document.getElementById("music-select").value;
  const renderCard = document.getElementById("render-status-card");
  const resultCard = document.getElementById("result-video-card");

  renderCard.classList.remove("hidden");
  renderCard.scrollIntoView({ behavior: "smooth" });
  resultCard.classList.add("hidden");

  const renderBtn = document.getElementById("btn-render-all");
  renderBtn.disabled = true;
  renderBtn.classList.add("opacity-50", "cursor-not-allowed");

  try {
    const res = await fetch("/api/render-short", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenes: currentScenes,
        voice: selectedVoice,
        voice_speed: selectedVoiceSpeed,
        visual_style: selectedVisualStyle,
        subtitle_style: selectedSubtitleStyle,
        layout_mode: selectedLayout,
        music_track: musicTrack === "none" ? null : musicTrack
      })
    });

    const data = await res.json();
    activeSessionId = data.session_id;

    pollRenderStatus(activeSessionId);
  } catch (err) {
    alert("Error starting render: " + err.message);
    renderBtn.disabled = false;
    renderBtn.classList.remove("opacity-50", "cursor-not-allowed");
  }
}

async function pollRenderStatus(sessionId) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/render-status/${sessionId}`);
      const statusData = await res.json();

      const pBar = document.getElementById("status-progress-bar");
      const pText = document.getElementById("status-percent");
      const pDesc = document.getElementById("status-desc");

      pBar.style.width = `${statusData.progress}%`;
      pText.textContent = `${statusData.progress}%`;
      pDesc.textContent = statusData.message;

      if (statusData.status === "completed") {
        clearInterval(interval);
        finishRendering(statusData);
      } else if (statusData.status === "error") {
        clearInterval(interval);
        alert("Rendering error: " + statusData.message);
        document.getElementById("btn-render-all").disabled = false;
        document.getElementById("btn-render-all").classList.remove("opacity-50", "cursor-not-allowed");
      }
    } catch (err) {
      console.error("Poll error:", err);
    }
  }, 1000);
}

async function finishRendering(result) {
  const renderCard = document.getElementById("render-status-card");
  const resultCard = document.getElementById("result-video-card");
  const renderBtn = document.getElementById("btn-render-all");

  renderBtn.disabled = false;
  renderBtn.classList.remove("opacity-50", "cursor-not-allowed");

  if (result.scenes) {
    currentScenes = result.scenes;
    renderScenes();
  }

  const player = document.getElementById("player-video");
  player.src = result.video_url;
  player.load();

  document.getElementById("btn-download-video").href = result.video_url;

  const metaRes = await fetch("/api/generate-metadata", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentScenes)
  });
  const meta = await metaRes.json();
  document.getElementById("meta-title").value = meta.title;
  document.getElementById("meta-desc").value = meta.description;

  renderCard.classList.add("hidden");
  resultCard.classList.remove("hidden");
  resultCard.scrollIntoView({ behavior: "smooth" });
}

async function regenerateScene(sceneId) {
  const scene = currentScenes.find(s => s.id === sceneId);
  if (!scene) return;

  if (!activeSessionId) {
    activeSessionId = "edit_" + Math.random().toString(36).substring(2, 8);
  }

  const card = document.getElementById(`scene-card-${sceneId}`);
  if (card) {
    const btn = card.querySelector("button[onclick*='regenerateScene']");
    if (btn) btn.innerHTML = `<i data-lucide="loader" class="w-3 h-3 animate-spin"></i> Regenerating...`;
    lucide.createIcons();
  }

  try {
    const res = await fetch("/api/regenerate-scene-visual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_id: sceneId,
        prompt: scene.visual_prompt,
        session_id: activeSessionId,
        motion: scene.camera_motion || "zoom_in",
        duration: scene.duration || 3.0
      })
    });
    const data = await res.json();
    scene.image_url = data.image_url;
    scene.clip_url = data.clip_url;
    renderScenes();
  } catch (err) {
    alert("Error regenerating image: " + err.message);
  }
}

function copyMeta(elementId) {
  const el = document.getElementById(elementId);
  el.select();
  navigator.clipboard.writeText(el.value);
  alert("Copied to clipboard!");
}

function escapeHtml(string) {
  if (!string) return "";
  return String(string)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
