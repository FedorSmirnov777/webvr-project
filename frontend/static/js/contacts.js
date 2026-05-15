const formEl = document.getElementById("cs-form-1388");
const statusEl = document.getElementById("lead-status");

function setStatus(text, type = "") {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.className = `cs-form-status ${type}`.trim();
}

async function submitLead(event) {
  event.preventDefault();
  if (!formEl) return;

  const fullName = document.getElementById("name-1388")?.value?.trim();
  const email = document.getElementById("email-1388")?.value?.trim();
  const phone = document.getElementById("phone-1388")?.value?.trim();
  const note = document.getElementById("message-1388")?.value?.trim() || null;

  if (!fullName || !email || !phone) {
    setStatus("Заполни имя, email и телефон.", "error");
    return;
  }

  const payload = {
    car_id: null,
    full_name: fullName,
    email,
    phone,
    lead_type: "test_drive",
    note,
    payload: {
      source: "contacts_page",
      page: window.location.pathname,
      submitted_at: new Date().toISOString()
    }
  };

  const submitBtn = formEl.querySelector('button[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;
  setStatus("Отправляем заявку...", "pending");

  try {
    const response = await fetch("/api/v1/commerce/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }

    formEl.reset();
    setStatus("Готово. Заявка отправлена, мы скоро свяжемся с вами.", "success");
  } catch (error) {
    console.error("lead submit failed", error);
    setStatus("Не удалось отправить заявку. Попробуйте ещё раз.", "error");
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

if (formEl) {
  formEl.addEventListener("submit", submitLead);
}
