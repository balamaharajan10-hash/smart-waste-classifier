// classifier.js — handles upload, drag-drop, webcam capture, and rendering results

(() => {
  let currentImageBlob = null;   // File or Blob to send to the API
  let currentImageSource = "upload"; // "upload" | "webcam"
  let webcamStream = null;

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropzoneEmpty = document.getElementById("dropzoneEmpty");
  const dropzonePreview = document.getElementById("dropzonePreview");
  const previewImg = document.getElementById("previewImg");
  const clearImgBtn = document.getElementById("clearImgBtn");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const explainToggle = document.getElementById("explainToggle");

  const modeTabs = document.querySelectorAll(".mode-tab");
  const uploadMode = document.getElementById("uploadMode");
  const webcamMode = document.getElementById("webcamMode");

  const webcamVideo = document.getElementById("webcamVideo");
  const webcamCanvas = document.getElementById("webcamCanvas");
  const webcamCapturedImg = document.getElementById("webcamCapturedImg");
  const startWebcamBtn = document.getElementById("startWebcamBtn");
  const captureBtn = document.getElementById("captureBtn");
  const retakeBtn = document.getElementById("retakeBtn");
  const webcamHint = document.getElementById("webcamHint");

  const loadingState = document.getElementById("loadingState");
  const emptyState = document.getElementById("emptyState");
  const errorState = document.getElementById("errorState");
  const errorMessage = document.getElementById("errorMessage");
  const resultCard = document.getElementById("resultCard");

  // ---------------- Mode switching ----------------
  modeTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      modeTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const mode = tab.dataset.mode;
      uploadMode.classList.toggle("active", mode === "upload");
      webcamMode.classList.toggle("active", mode === "webcam");
      currentImageSource = mode;
      stopWebcamIfInactive(mode);
    });
  });

  function stopWebcamIfInactive(mode) {
    if (mode !== "webcam" && webcamStream) {
      webcamStream.getTracks().forEach(t => t.stop());
      webcamStream = null;
    }
  }

  // ---------------- Upload / drag & drop ----------------
  browseBtn.addEventListener("click", () => fileInput.click());
  dropzoneEmpty.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", e => {
    if (e.target.files[0]) handleFileSelected(e.target.files[0]);
  });

  ["dragenter", "dragover"].forEach(evt =>
    dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach(evt =>
    dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove("dragover"); })
  );
  dropzone.addEventListener("drop", e => {
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelected(file);
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith("image/")) {
      showError("Unsupported file type. Please upload a JPG, PNG, or WEBP image.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      showError("This image is too large. Please upload a file under 8MB.");
      return;
    }
    currentImageBlob = file;
    currentImageSource = "upload";
    const reader = new FileReader();
    reader.onload = e => {
      previewImg.src = e.target.result;
      dropzoneEmpty.style.display = "none";
      dropzonePreview.style.display = "block";
    };
    reader.readAsDataURL(file);
    analyzeBtn.disabled = false;
    resetResultPanels();
  }

  clearImgBtn.addEventListener("click", () => {
    currentImageBlob = null;
    fileInput.value = "";
    dropzoneEmpty.style.display = "block";
    dropzonePreview.style.display = "none";
    analyzeBtn.disabled = true;
  });

  // ---------------- Webcam ----------------
  startWebcamBtn.addEventListener("click", async () => {
    try {
      webcamStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }, audio: false,
      });
      webcamVideo.srcObject = webcamStream;
      webcamVideo.style.display = "block";
      webcamCapturedImg.style.display = "none";
      startWebcamBtn.style.display = "none";
      captureBtn.style.display = "inline-flex";
      retakeBtn.style.display = "none";
      webcamHint.textContent = "Position the item in frame, then capture.";
    } catch (err) {
      webcamHint.textContent = "Camera access was denied or is unavailable on this device.";
    }
  });

  captureBtn.addEventListener("click", () => {
    const w = webcamVideo.videoWidth, h = webcamVideo.videoHeight;
    webcamCanvas.width = w;
    webcamCanvas.height = h;
    const ctx = webcamCanvas.getContext("2d");
    ctx.drawImage(webcamVideo, 0, 0, w, h);
    const dataUrl = webcamCanvas.toDataURL("image/png");

    webcamCapturedImg.src = dataUrl;
    webcamCapturedImg.style.display = "block";
    webcamVideo.style.display = "none";
    captureBtn.style.display = "none";
    retakeBtn.style.display = "inline-flex";

    currentImageBlob = dataUrl; // base64 data URL for webcam captures
    currentImageSource = "webcam";
    analyzeBtn.disabled = false;
    resetResultPanels();

    if (webcamStream) {
      webcamStream.getTracks().forEach(t => t.stop());
      webcamStream = null;
    }
  });

  retakeBtn.addEventListener("click", () => {
    startWebcamBtn.click();
  });

  // ---------------- Analyze ----------------
  analyzeBtn.addEventListener("click", async () => {
    if (!currentImageBlob) return;
    setLoading(true);

    try {
      const explain = explainToggle.checked;
      let response;

      if (currentImageSource === "webcam") {
        response = await fetch(`/api/predict?explain=${explain}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_data: currentImageBlob }),
        });
      } else {
        const formData = new FormData();
        formData.append("image", currentImageBlob);
        response = await fetch(`/api/predict?explain=${explain}`, {
          method: "POST",
          body: formData,
        });
      }

      const data = await response.json();
      setLoading(false);

      if (!response.ok) {
        showError(data.message || "Something went wrong. Please try again.");
        return;
      }
      renderResult(data);
    } catch (err) {
      setLoading(false);
      showError("Could not reach the server. Please check your connection and try again.");
    }
  });

  // ---------------- Rendering ----------------
  function setLoading(isLoading) {
    loadingState.style.display = isLoading ? "block" : "none";
    if (isLoading) {
      emptyState.style.display = "none";
      errorState.style.display = "none";
      resultCard.style.display = "none";
    }
  }

  function resetResultPanels() {
    errorState.style.display = "none";
    resultCard.style.display = "none";
    emptyState.style.display = "block";
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorState.style.display = "block";
    emptyState.style.display = "none";
    resultCard.style.display = "none";
  }

  function renderResult(data) {
    emptyState.style.display = "none";
    errorState.style.display = "none";
    resultCard.style.display = "block";

    const banner = document.getElementById("confidenceBanner");
    banner.className = "confidence-banner " + data.confidence_level;
    document.getElementById("confidenceMessage").textContent = data.confidence_message;

    document.getElementById("predictedClassName").textContent = data.waste_info.display_name;
    document.getElementById("predictedMaterial").textContent = data.waste_info.material;
    document.getElementById("confidenceValue").textContent = data.confidence + "%";

    const circle = document.getElementById("confidenceCircle");
    circle.style.background = `conic-gradient(var(--color-primary) ${data.confidence * 3.6}deg, var(--color-border) 0deg)`;

    const top3List = document.getElementById("top3List");
    top3List.innerHTML = "";
    data.top3.forEach(item => {
      const row = document.createElement("div");
      row.className = "top3-row";
      row.innerHTML = `
        <span>${item.class}</span>
        <div class="top3-bar-track"><div class="top3-bar-fill" style="width:${item.confidence}%"></div></div>
        <span>${item.confidence}%</span>
      `;
      top3List.appendChild(row);
    });

    const bio = data.waste_info.biodegradable;
    document.getElementById("biodegradableBadge").textContent =
      bio === true ? "Biodegradable" : bio === false ? "Non-Biodegradable" : bio;
    document.getElementById("recyclableBadge").textContent = data.waste_info.recyclable;

    const hazardBadge = document.getElementById("hazardBadge");
    hazardBadge.style.display = data.waste_info.special_handling ? "inline-flex" : "none";

    document.getElementById("disposalText").textContent = data.waste_info.disposal;

    const reuseList = document.getElementById("reuseList");
    reuseList.innerHTML = "";
    (data.waste_info.reuse_ideas || []).forEach(idea => {
      const li = document.createElement("li");
      li.textContent = idea;
      reuseList.appendChild(li);
    });

    document.getElementById("environmentText").textContent = data.waste_info.environmental_impact;

    const safetyBlock = document.getElementById("safetyBlock");
    if (data.waste_info.safety_warning) {
      safetyBlock.style.display = "block";
      document.getElementById("safetyText").textContent = data.waste_info.safety_warning;
    } else {
      safetyBlock.style.display = "none";
    }

    const gradcamBlock = document.getElementById("gradcamBlock");
    if (data.gradcam) {
      gradcamBlock.style.display = "block";
      document.getElementById("gradcamImg").src = data.gradcam;
    } else {
      gradcamBlock.style.display = "none";
    }

    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
})();
