const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speechSynthesis = window.speechSynthesis;

const directionSelect = document.getElementById("directionSelect");
const inputText = document.getElementById("inputText");
const micButton = document.getElementById("micButton");
const translateButton = document.getElementById("translateButton");
const sourcePreview = document.getElementById("sourcePreview");
const targetPreview = document.getElementById("targetPreview");
const speakButton = document.getElementById("speakButton");
const copySourceBtn = document.getElementById("copySourceBtn");
const copyTargetBtn = document.getElementById("copyTargetBtn");
const statusText = document.getElementById("statusText");
const voiceStatus = document.getElementById("voiceStatus");
const DEFAULT_REMOTE_TRANSLATE_BASE = "https://winfredkuo-translator.theoder.workers.dev";
const TRANSLATE_API_BASE = (window.TRANSLATOR_API_BASE_URL || DEFAULT_REMOTE_TRANSLATE_BASE).replace(/\/$/, "");

const DIRECTION_MAP = {
  "zh-en": { source: "zh-TW", target: "en-US", sourceLabel: "繁體中文", targetLabel: "英文" },
  "zh-ja": { source: "zh-TW", target: "ja-JP", sourceLabel: "繁體中文", targetLabel: "日文" },
  "en-zh": { source: "en-US", target: "zh-TW", sourceLabel: "英文", targetLabel: "繁體中文" },
  "ja-zh": { source: "ja-JP", target: "zh-TW", sourceLabel: "日文", targetLabel: "繁體中文" },
  "auto-zh": { source: "auto", target: "zh-TW", sourceLabel: "自動辨識", targetLabel: "繁體中文" },
};

let activeRecognition = null;
let isRecording = false;
let latestTranslation = "";

function getDirection() {
  return DIRECTION_MAP[directionSelect.value] || DIRECTION_MAP["zh-en"];
}

function setStatus(message) {
  statusText.textContent = message;
}

function setVoiceStatus(message) {
  voiceStatus.textContent = message;
}

function setSourceText(text) {
  sourcePreview.textContent = text || "輸入的內容會顯示在這裡。";
  sourcePreview.classList.toggle("muted", !text);
}

function setTargetText(text) {
  latestTranslation = text || "";
  targetPreview.textContent = text || "翻譯結果會顯示在這裡。";
  targetPreview.classList.toggle("muted", !text);
  speakButton.disabled = !text;
  copyTargetBtn.disabled = !text;
}

function getSpeechRecognitionLanguage() {
  const direction = getDirection();
  return direction.source === "auto" ? "zh-TW" : direction.source;
}

function getTtsLanguage() {
  const direction = getDirection();
  return direction.target;
}

async function translateText(text) {
  const direction = getDirection();
  const sourceLang = direction.source === "auto" ? "auto" : direction.source;
  const targetLang = direction.target;
  const translateEndpoint = `${TRANSLATE_API_BASE}/api/translate`;

  const response = await fetch(translateEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "翻譯失敗");
  }
  return data.translated_text || "";
}

function explainFetchFailure(error) {
  if (error instanceof TypeError && /fetch/i.test(error.message)) {
    return "翻譯服務連不上。請確認 Cloudflare Worker 與前端網域設定。";
  }
  return error.message || "翻譯失敗";
}

function pickVoice(langCode) {
  if (!speechSynthesis) return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;

  const normalized = langCode.toLowerCase();
  const exact = voices.find((voice) => voice.lang?.toLowerCase() === normalized);
  if (exact) return exact;

  if (normalized.startsWith("zh")) {
    return (
      voices.find((voice) => voice.lang?.toLowerCase().startsWith("zh")) ||
      voices.find((voice) => /taiwan|mei-jia|zh/.test((voice.name || "").toLowerCase()))
    );
  }

  if (normalized.startsWith("ja")) {
    return (
      voices.find((voice) => voice.lang?.toLowerCase().startsWith("ja")) ||
      voices.find((voice) => /kyoko|otoya|japanese/.test((voice.name || "").toLowerCase()))
    );
  }

  if (normalized.startsWith("en")) {
    return (
      voices.find((voice) => voice.lang?.toLowerCase().startsWith("en")) ||
      voices.find((voice) => /english|samantha|google us english/.test((voice.name || "").toLowerCase()))
    );
  }

  return voices[0] || null;
}

function speakText(text, langCode) {
  if (!speechSynthesis || !text) return;
  speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = langCode;
  utterance.rate = 0.95;
  utterance.pitch = 1;

  const voice = pickVoice(langCode);
  if (voice) {
    utterance.voice = voice;
  }

  speechSynthesis.speak(utterance);
}

function stopRecording() {
  if (activeRecognition) {
    activeRecognition.stop();
    activeRecognition = null;
  }
  isRecording = false;
  micButton.classList.remove("recording");
  setVoiceStatus("語音未啟用");
}

function finishRecording(text) {
  setSourceText(text);
  setStatus("翻譯中...");
  translateButton.disabled = true;
  return translateText(text)
    .then((translated) => {
      setTargetText(translated);
      setStatus(`翻譯完成：${getDirection().sourceLabel} → ${getDirection().targetLabel}`);
    })
    .catch((error) => {
      setTargetText("");
      setStatus(explainFetchFailure(error));
    })
    .finally(() => {
      translateButton.disabled = false;
    });
}

function startRecognition() {
  if (!SpeechRecognition) {
    setStatus("此瀏覽器不支援語音辨識。");
    return;
  }

  if (isRecording) {
    stopRecording();
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = getSpeechRecognitionLanguage();
  recognition.interimResults = true;
  recognition.continuous = false;

  activeRecognition = recognition;
  isRecording = true;
  micButton.classList.add("recording");
  setVoiceStatus("正在聆聽...");
  setStatus("請開始說話，辨識完成後會自動翻譯。");

  let finalTranscript = "";

  recognition.onresult = (event) => {
    let interimTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    const preview = (finalTranscript + interimTranscript).trim();
    if (preview) {
      setSourceText(preview);
    }
  };

  recognition.onerror = (event) => {
    setStatus(`語音辨識失敗：${event.error}`);
    stopRecording();
  };

  recognition.onend = () => {
    const text = finalTranscript.trim() || inputText.value.trim() || sourcePreview.textContent.trim();
    stopRecording();
    if (text) {
      inputText.value = text;
      void finishRecording(text);
    } else {
      setStatus("沒有偵測到聲音，請再試一次。");
    }
  };

  recognition.start();
}

async function copyText(text) {
  if (!text) return;
  await navigator.clipboard.writeText(text);
}

directionSelect.addEventListener("change", () => {
  const direction = getDirection();
  setStatus(`目前方向：${direction.sourceLabel} → ${direction.targetLabel}`);
  if (latestTranslation) {
    speakButton.disabled = false;
  }
});

micButton.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
    return;
  }
  startRecognition();
});

translateButton.addEventListener("click", () => {
  const text = inputText.value.trim();
  if (!text) {
    setStatus("請先輸入文字，或使用語音輸入。");
    return;
  }
  setSourceText(text);
  void finishRecording(text);
});

speakButton.addEventListener("click", () => {
  if (!latestTranslation) return;
  speakText(latestTranslation, getTtsLanguage());
});

copySourceBtn.addEventListener("click", async () => {
  const text = sourcePreview.textContent.trim();
  if (!text || sourcePreview.classList.contains("muted")) return;
  await copyText(text);
  setStatus("原文已複製。");
});

copyTargetBtn.addEventListener("click", async () => {
  if (!latestTranslation) return;
  await copyText(latestTranslation);
  setStatus("翻譯結果已複製。");
});

if (speechSynthesis) {
  speechSynthesis.onvoiceschanged = () => {
    if (latestTranslation) {
      speakButton.disabled = false;
    }
  };
}

setStatus("準備好了。");
setVoiceStatus("服務正常");
