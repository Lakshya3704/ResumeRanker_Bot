/* ═══════════════════════════════════════════════
   DRCode – Frontend JavaScript
   Animations, particles, interactions
   ═══════════════════════════════════════════════ */


/* ═══════════════════════════════════════════════
   NAVIGATION
   ═══════════════════════════════════════════════ */

function toggleNav() {
    const links = document.getElementById("navLinks");
    links.classList.toggle("open");
}

// Close mobile nav on link click
document.querySelectorAll(".nav-links a").forEach(link => {
    link.addEventListener("click", () => {
        document.getElementById("navLinks").classList.remove("open");
    });
});

// Navbar scroll effect
window.addEventListener("scroll", () => {
    const navbar = document.getElementById("navbar");
    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});


/* ═══════════════════════════════════════════════
   SCROLL REVEAL ANIMATIONS
   ═══════════════════════════════════════════════ */

const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add("visible");
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
);

document.querySelectorAll(".reveal").forEach(el => observer.observe(el));


/* ═══════════════════════════════════════════════
   PARTICLE BACKGROUND (Canvas)
   ═══════════════════════════════════════════════ */

(function initParticles() {
    const canvas = document.getElementById("particles-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let particles = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.4;
            this.speedY = (Math.random() - 0.5) * 0.4;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.color = Math.random() > 0.5
                ? `rgba(0, 212, 255, ${this.opacity})`
                : `rgba(124, 58, 237, ${this.opacity})`;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();
        }
    }

    const count = window.innerWidth < 768 ? 40 : 80;
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }

    function connectParticles() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(0, 212, 255, ${0.05 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        connectParticles();
        requestAnimationFrame(animate);
    }

    animate();
})();


/* ═══════════════════════════════════════════════
   SMOOTH SCROLL FOR ANCHOR LINKS
   ═══════════════════════════════════════════════ */

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});


/* ═══════════════════════════════════════════════
   COUNTER ANIMATION (Hero stats)
   ═══════════════════════════════════════════════ */

function animateCounter(el, target, suffix = "") {
    let current = 0;
    const increment = target / 60;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.floor(current) + suffix;
    }, 25);
}

const heroObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statEl = document.getElementById("stat-users");
                if (statEl && !statEl.dataset.animated) {
                    animateCounter(statEl, 500, "+");
                    statEl.dataset.animated = "true";
                }
                heroObserver.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.5 }
);

const heroSection = document.getElementById("hero");
if (heroSection) heroObserver.observe(heroSection);


/* ═══════════════════════════════════════════════
   WEB APP LOGIC (Phase 3)
   ═══════════════════════════════════════════════ */

let globalJdText = "";
let globalResumeText = "";
let globalMissingSkills = [];
let globalSuggestions = [];

// ── Drag & Drop Logic ──
function setupDropArea(areaId, inputId) {
    const dropArea = document.getElementById(areaId);
    if (!dropArea) return;
    const input = document.getElementById(inputId);
    const msg = dropArea.querySelector(".file-msg");

    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ["dragenter", "dragover"].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add("dragover"), false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove("dragover"), false);
    });

    dropArea.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files[0];
        if (file) {
            input.files = e.dataTransfer.files;
            handleFileSelect(dropArea, msg, file);
        }
    }, false);

    input.addEventListener("change", function() {
        if (this.files.length > 0) {
            handleFileSelect(dropArea, msg, this.files[0]);
        }
    });
}

function handleFileSelect(dropArea, msgEl, file) {
    msgEl.textContent = file.name;
    dropArea.classList.add("has-file");
}

setupDropArea("jd-drop", "jd-file");
setupDropArea("resume-drop", "resume-file");

// ── Form Submit (Analyze) ──
const analyzeForm = document.getElementById("analyze-form");
if (analyzeForm) {
    analyzeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const jdInput = document.getElementById("jd-file");
        const resInput = document.getElementById("resume-file");
        const errorEl = document.getElementById("analyze-error");
        
        if (!jdInput.files[0] || !resInput.files[0]) {
            errorEl.style.display = "block";
            errorEl.textContent = "Please provide both JD and Resume.";
            return;
        }
        
        errorEl.style.display = "none";
        
        // Switch UI to loading
        document.getElementById("results-initial").style.display = "none";
        document.getElementById("results-content").style.display = "none";
        document.getElementById("results-loading").style.display = "flex";
        
        const btn = document.getElementById("analyze-btn");
        btn.disabled = true;
        btn.textContent = "⏳ Analyzing...";

        const formData = new FormData();
        formData.append("jd_file", jdInput.files[0]);
        formData.append("resume_file", resInput.files[0]);

        try {
            const resp = await fetch("/analyze", {
                method: "POST",
                body: formData
            });
            
            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || "Analysis failed");
            }
            
            const data = await resp.json();
            
            // Save global state for chat and downloads
            globalJdText = data.jd_text;
            globalResumeText = data.resume_text;
            globalMissingSkills = data.missing_skills;
            globalSuggestions = data.recommendations.suggestions;

            // Render Results
            document.getElementById("res-score").innerHTML = `${data.score.total_score}<span style="font-size:1rem;">/10</span>`;
            document.getElementById("res-grade").textContent = `Grade: ${data.score.grade}`;
            
            let color = "var(--green)";
            if (data.score.total_score < 6) color = "var(--pink)";
            else if (data.score.total_score < 8) color = "var(--orange)";
            document.getElementById("res-grade").style.color = color;

            document.getElementById("res-matched").innerHTML = data.matched_skills.length > 0
                ? data.matched_skills.slice(0, 10).join(", ")
                : "None";
            
            document.getElementById("res-missing").innerHTML = data.missing_skills.length > 0
                ? data.missing_skills.slice(0, 10).join(", ")
                : "None";

            const sugList = document.getElementById("res-suggestions");
            sugList.innerHTML = "";
            let allSugs = [...data.recommendations.weak_areas, ...data.recommendations.suggestions].slice(0, 5);
            if (allSugs.length === 0) allSugs.push("Your resume looks great! Follow the standard ATS format.");
            allSugs.forEach(s => {
                const li = document.createElement("li");
                li.style.marginBottom = "0.4rem";
                li.textContent = s;
                sugList.appendChild(li);
            });

            // Show Results pane
            document.getElementById("results-loading").style.display = "none";
            document.getElementById("results-content").style.display = "block";
            
            // Reset chat
            const chatBox = document.getElementById("chat-messages");
            chatBox.innerHTML = `
                <div class="chat-bubble ai-bubble">
                    Hello! I've analyzed your resume against the job description. Do you have any questions about how to improve it further?
                </div>
            `;

        } catch (err) {
            document.getElementById("results-loading").style.display = "none";
            document.getElementById("results-initial").style.display = "block";
            errorEl.style.display = "block";
            errorEl.textContent = `Error: ${err.message}`;
        } finally {
            btn.disabled = false;
            btn.textContent = "🚀 Analyze Resume";
        }
    });
}


// ── Downloads ──
async function downloadResume(format) {
    if (!globalResumeText || !globalJdText) {
        alert("Please analyze a resume first.");
        return;
    }
    
    alert(`Getting ${format.toUpperCase()} ready. This may take a few seconds as AI improves your resume…`);

    try {
        // First get improved text
        const imprResp = await fetch("/improve-resume", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                resume_text: globalResumeText,
                jd_text: globalJdText,
                missing_skills: globalMissingSkills,
                suggestions: globalSuggestions
            })
        });

        if (!imprResp.ok) throw new Error("Failed to improve resume");
        const imprData = await imprResp.json();
        
        // Now generate file
        const genResp = await fetch("/generate-resume", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                improved_text: imprData.improved_text,
                format: format
            })
        });

        if (!genResp.ok) throw new Error("Failed to generate document");
        
        // Download blob
        const blob = await genResp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `improved_resume.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (err) {
        alert(`Error downloading resume: ${err.message}`);
    }
}


// ── Chat Logic ──
const chatForm = document.getElementById("chat-form");
if (chatForm) {
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("chat-input");
        const msg = input.value.trim();
        if (!msg) return;

        input.value = "";
        
        const chatBox = document.getElementById("chat-messages");
        
        // Add user msg
        const userDiv = document.createElement("div");
        userDiv.className = "chat-bubble user-bubble";
        userDiv.textContent = msg;
        chatBox.appendChild(userDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Add loading bubble
        const loadDiv = document.createElement("div");
        loadDiv.className = "chat-bubble ai-bubble";
        loadDiv.textContent = "Thinking...";
        chatBox.appendChild(loadDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const resp = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: msg,
                    resume_text: globalResumeText,
                    jd_text: globalJdText
                })
            });

            if (!resp.ok) throw new Error("Failed to get answer");
            const data = await resp.json();
            
            // Replace loading with real answer
            loadDiv.textContent = data.answer;
        } catch (err) {
            loadDiv.textContent = "❌ Error getting response: " + err.message;
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}
