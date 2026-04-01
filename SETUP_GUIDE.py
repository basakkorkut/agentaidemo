# Agentic AI Demo — Setup Guide
# ================================

## Step 1: LM Studio Server Setup
# --------------------------------
# 1. LM Studio'yu aç
# 2. Sol menüden "Developer" sekmesine git (</> ikonu)
# 3. Üstte model seçiciden "Qwen2.5-7B-Instruct" seç
# 4. "Start Server" butonuna bas
# 5. Status: "Server running on port 1234" yazmalı
# 6. Sol altta "Logs" panelini aç — buradan tüm API call'ları göreceksin
#
# Server ayarları (opsiyonel ama önerilen):
#   - Context Length: 4096 (yeterli)
#   - GPU Offload: Maximum (hızlı response için)

## Step 2: Python Dependencies
# --------------------------------
# VS Code terminalinde çalıştır:
#
#   pip install openai rich
#
# Bu kadar! Başka bir şey gerekmiyor.

## Step 3: Çalıştırma
# --------------------------------
# VS Code'da demo klasörünü aç, terminalde:
#
#   python react_agent.py           # Demo 1: ReAct
#   python multi_agent.py           # Demo 2: Multi-Agent
#   python tree_of_thoughts.py      # Demo 3: Tree-of-Thoughts
#
# Her script çalışırken:
#   - VS Code terminali: Renkli çıktı (thought, action, observation vs.)
#   - LM Studio Logs: Her API request/response detayı

## Step 4: Sunumda Demo Sırası
# --------------------------------
# 1. Önce LM Studio'yu göster — "Bu bir local LLM server, OpenAI API uyumlu"
# 2. react_agent.py çalıştır — step-by-step Thought→Action→Observation göster
# 3. multi_agent.py çalıştır — 4 farklı ajanın sırayla çalıştığını göster
# 4. tree_of_thoughts.py çalıştır — branching + scoring + pruning göster
# 5. Son olarak karşılaştır:
#    - ReAct: ~3-5 LLM calls, sequential
#    - Multi-Agent: 4 LLM calls, pipeline
#    - ToT: 7+ LLM calls, branching

## Troubleshooting
# --------------------------------
# "Connection refused" → LM Studio server açık değil, Start Server bas
# "Model not found" → Script'teki MODEL değişkenini kontrol et
# Yavaş response → GPU offload'u artır veya context length'i düşür
